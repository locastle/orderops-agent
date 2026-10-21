"""Acceptance suite for the synthetic dataset generator (Week 1 Day 2).

This file is the specification of the generator, written as executable
checks. It fails with `NotImplementedError` until `generate_dataset` is
implemented - that is the intended starting point of the task.

The invariants it enforces are the ones the rest of the project depends on:

* the dataset is deterministic, so evaluation results are reproducible;
* the ground truth is complete and only reachable by the evaluator;
* an anomaly is a *structural* difference (a missing event, a missing
  record), not a hint hidden in a log message;
* the data is dirty enough that the agent has to reason rather than look up.
"""

import re
from collections import defaultdict

import pytest
from orderops_shared.enums import EventType, LabelStatus, PaymentStatus, RootCauseCode
from orderops_synthetic import DatasetConfig, generate_dataset

CARRIER_PICKUP_SLA_SECONDS = 3600
SEED = 20261021


@pytest.fixture(scope="module")
def dataset():
    return generate_dataset(DatasetConfig(seed=SEED, orders=24))


def _events_by_order(dataset) -> dict[str, list]:
    grouped = defaultdict(list)
    for event in dataset.events:
        grouped[event.order_no].append(event)
    return grouped


def _orders_by_code(dataset) -> dict[str, list[str]]:
    grouped = defaultdict(list)
    for order_no, code in dataset.ground_truth.items():
        grouped[code].append(order_no)
    return grouped


def test_every_order_has_one_case(dataset) -> None:
    order_nos = {order.order_no for order in dataset.orders}
    case_order_nos = [case.order_no for case in dataset.cases]
    assert len(case_order_nos) == len(set(case_order_nos)), "a case per order, no duplicates"
    assert set(case_order_nos) == order_nos
    assert len(order_nos) == len(dataset.orders)


def test_ground_truth_covers_every_order(dataset) -> None:
    order_nos = {order.order_no for order in dataset.orders}
    assert set(dataset.ground_truth) == order_nos
    assert all(isinstance(code, RootCauseCode) for code in dataset.ground_truth.values())


def test_events_are_ordered_and_never_go_backwards(dataset) -> None:
    for order_no, events in _events_by_order(dataset).items():
        timestamps = [event.occurred_at for event in events]
        assert timestamps == sorted(timestamps), f"{order_no} events are not time ordered"


def test_healthy_orders_have_the_full_chain(dataset) -> None:
    events = _events_by_order(dataset)
    healthy = _orders_by_code(dataset)[RootCauseCode.OK_NO_ANOMALY]
    assert healthy, "the dataset must contain healthy orders"

    for order_no in healthy:
        types = {event.event_type for event in events[order_no]}
        assert EventType.ORDER_PAID in types
        assert EventType.INVENTORY_LOCKED in types
        assert EventType.ORDER_SHIPPED in types
        paid = [
            p
            for p in dataset.payments
            if p.order_no == order_no and p.status == PaymentStatus.SUCCESS
        ]
        assert paid
        assert any(t.order_no == order_no for t in dataset.warehouse_tasks)
        assert any(s.order_no == order_no for s in dataset.shipments)


def test_family_a_is_paid_but_not_advanced(dataset) -> None:
    events = _events_by_order(dataset)
    family_a = _orders_by_code(dataset)[RootCauseCode.A1_PAYMENT_CALLBACK_TIMEOUT]
    family_a += _orders_by_code(dataset)[RootCauseCode.A2_IDEMPOTENCY_CONFLICT]
    family_a += _orders_by_code(dataset)[RootCauseCode.A3_STATE_MACHINE_RULE_MISMATCH]
    assert family_a, "the dataset must contain family A cases"

    for order_no in family_a:
        types = {event.event_type for event in events[order_no]}
        assert EventType.ORDER_PAID not in types, "the missing ORDER_PAID is the anomaly"


def test_family_b_is_locked_without_warehouse_task(dataset) -> None:
    family_b = _orders_by_code(dataset)[RootCauseCode.B1_MQ_MESSAGE_LOST]
    family_b += _orders_by_code(dataset)[RootCauseCode.B2_WMS_INTERFACE_RETRY_EXHAUSTED]
    family_b += _orders_by_code(dataset)[RootCauseCode.B3_TASK_CREATION_RULE_MISMATCH]
    assert family_b, "the dataset must contain family B cases"

    for order_no in family_b:
        assert any(lock.order_no == order_no for lock in dataset.inventory_locks)
        assert not any(task.order_no == order_no for task in dataset.warehouse_tasks)


def test_family_c_is_shipped_without_pickup(dataset) -> None:
    shipments = {s.order_no: s for s in dataset.shipments}
    no_pickup = _orders_by_code(dataset)[RootCauseCode.C1_CARRIER_CALLBACK_MISSING]
    no_pickup += _orders_by_code(dataset)[RootCauseCode.C2_WAREHOUSE_NOT_PACKED]
    late_pickup = _orders_by_code(dataset)[RootCauseCode.C3_CARRIER_PICKUP_DELAY]
    assert no_pickup and late_pickup, "the dataset must contain family C cases"

    for order_no in no_pickup:
        shipment = shipments[order_no]
        assert shipment.label_status == LabelStatus.SUCCESS
        assert shipment.picked_up_at is None
        assert not shipment.events, "no tracking event at all"

    for order_no in late_pickup:
        shipment = shipments[order_no]
        assert shipment.picked_up_at is not None
        assert (shipment.picked_up_at - shipment.created_at).total_seconds() >= (
            CARRIER_PICKUP_SLA_SECONDS
        )


def test_amounts_match_except_for_the_idempotency_conflict(dataset) -> None:
    orders = {order.order_no: order for order in dataset.orders}
    payments_per_order = defaultdict(list)
    for payment in dataset.payments:
        payments_per_order[payment.order_no].append(payment)

    for order_no, payments in payments_per_order.items():
        if dataset.ground_truth.get(order_no) == RootCauseCode.A2_IDEMPOTENCY_CONFLICT:
            assert len(payments) >= 2, "the conflict needs two payment records"
            assert len({p.idempotency_key for p in payments}) == 1, "same key, two rows"
            continue
        assert len(payments) == 1
        assert payments[0].amount == orders[order_no].total_amount


def test_customer_ids_look_synthetic(dataset) -> None:
    pattern = re.compile(r"^C\d{4}$")
    for order in dataset.orders:
        assert pattern.match(order.customer_id), f"{order.customer_id} is not synthetic"


def test_generation_is_deterministic() -> None:
    first = generate_dataset(DatasetConfig(seed=SEED, orders=8))
    second = generate_dataset(DatasetConfig(seed=SEED, orders=8))
    assert [o.model_dump(mode="json") for o in first.orders] == [
        o.model_dump(mode="json") for o in second.orders
    ]
    assert first.ground_truth == second.ground_truth
