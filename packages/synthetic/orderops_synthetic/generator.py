"""Contract for the synthetic dataset generator (Week 1 Day 2).

This module is a **specification, not an implementation**. The generator is
the first module you write yourself; the shapes below are the contract you
implement against, and `tests/test_generator.py` is the acceptance suite that
judges it.

## Why a generator and not a fixture file

* The evaluation set is split into dev / test / holdout with *different fault
  parameters* (retry counts, delays, log wording). A static file would leak:
  the model could memorise surface patterns instead of learning to read
  evidence.
* Noise injection (unrelated logs, missing fields, duplicate log lines) has
  to be parameterised, otherwise the dataset becomes unrealistically clean and
  the accuracy numbers are inflated.

## The contract

```python
@dataclass(frozen=True)
class DatasetConfig:
    seed: int = 20261021
    orders: int = 20
    include_anomalies: bool = True

def generate_dataset(config: DatasetConfig) -> OrderDataset: ...
```

`OrderDataset` holds the generated records grouped by table plus the ground
truth mapping:

```python
@dataclass
class OrderDataset:
    orders: list[Order]
    events: list[OrderEvent]
    payments: list[Payment]
    inventory_locks: list[InventoryLock]
    warehouse_tasks: list[WarehouseTask]
    shipments: list[Shipment]
    logs: list[LogLine]
    cases: list[Case]
    ground_truth: dict[str, RootCauseCode]   # order_no -> root cause code
```

The record types come from `orderops_shared.models`, the codes from
`orderops_shared.enums`. Reuse them; do not define parallel structures.

## Invariants the acceptance suite checks

1. Every order has exactly one case, and every case references a generated
   order.
2. `order_events` for one order are sorted by `occurred_at` and never go
   backwards in time.
3. Every order appears in `ground_truth`; no ground truth key points at an
   unknown order.
4. A healthy order (`OK_NO_ANOMALY`) has the full chain: payment succeeded,
   `ORDER_PAID`, inventory locked, a warehouse task, a shipment and
   `ORDER_SHIPPED`.
5. Family A orders have `PaymentStatus.SUCCESS` **and** no `ORDER_PAID`
   event - that absence is the anomaly.
6. Family B orders have an inventory lock and **no** warehouse task.
7. Family C orders have a shipment whose `label_status` is `SUCCESS` but no
   `PICKED_UP` event (C1, C2) or a pickup later than the SLA window (C3).
8. Payment amount equals the order total, except for the deliberate
   idempotency-conflict case.
9. No customer identifier looks like a real person or account: `customer_id`
   is `C` plus four digits.
10. Generating twice with the same seed yields identical output.

## Ground truth you must be able to produce

| Family | Root cause codes |
|---|---|
| A | `A1_PAYMENT_CALLBACK_TIMEOUT`, `A2_IDEMPOTENCY_CONFLICT`, `A3_STATE_MACHINE_RULE_MISMATCH` |
| B | `B1_MQ_MESSAGE_LOST`, `B2_WMS_INTERFACE_RETRY_EXHAUSTED`, `B3_TASK_CREATION_RULE_MISMATCH` |
| C | `C1_CARRIER_CALLBACK_MISSING`, `C2_WAREHOUSE_NOT_PACKED`, `C3_CARRIER_PICKUP_DELAY` |
| healthy | `OK_NO_ANOMALY` |
| must escalate | `INSUFFICIENT_DATA`, `CONFLICTING_EVIDENCE` |

The injection mechanics for each code are specified in
`nh/ai-agent/03-数据模型与合成数据.md`, section 3.
"""

from dataclasses import dataclass, field

from orderops_shared.enums import RootCauseCode
from orderops_shared.models import (
    Case,
    InventoryLock,
    LogLine,
    Order,
    OrderEvent,
    Payment,
    Shipment,
    WarehouseTask,
)


@dataclass(frozen=True)
class DatasetConfig:
    """Knobs of the generator. All randomness flows from `seed`."""

    seed: int = 20261021
    orders: int = 20
    include_anomalies: bool = True


@dataclass
class OrderDataset:
    """Generated records, grouped by the table they belong to."""

    orders: list[Order] = field(default_factory=list)
    events: list[OrderEvent] = field(default_factory=list)
    payments: list[Payment] = field(default_factory=list)
    inventory_locks: list[InventoryLock] = field(default_factory=list)
    warehouse_tasks: list[WarehouseTask] = field(default_factory=list)
    shipments: list[Shipment] = field(default_factory=list)
    logs: list[LogLine] = field(default_factory=list)
    cases: list[Case] = field(default_factory=list)
    ground_truth: dict[str, RootCauseCode] = field(default_factory=dict)


def generate_dataset(config: DatasetConfig) -> OrderDataset:
    """Build a deterministic dataset.

    TODO(week1-day2): implement me.

    Hints for the implementation, in the order I would tackle them:

    1. Build one *healthy* order end to end: order -> payment -> order events
       -> inventory lock -> warehouse task -> shipment -> logistics events.
       Get the timeline monotonic while you do it.
    2. Turn the healthy order into an anomalous one by *injecting* a fault at
       one known point, instead of generating the broken path from scratch.
       That is what keeps the normal and anomalous chains structurally
       identical.
    3. Write the log lines that the fault implies. The agent will have to
       find them, so the wording has to be realistic but not a giveaway -
       never mention the root cause code.
    4. Add noise: unrelated log lines, a null field here and there, a
       duplicated line.
    5. Emit the `Case` (a realistic symptom sentence) and the ground truth
       entry.

    Use `random.Random(config.seed)` - never the global `random` module - so
    that the output only depends on the seed.
    """
    raise NotImplementedError("implement the synthetic generator (Week 1 Day 2)")
