"""Guards for the shared domain vocabulary.

These tests exist because the evaluation harness compares root cause codes
by string. A silent rename or a typo in an enum would invalidate every
stored result without failing anything else.
"""

import pytest
from orderops_shared import Order, OrderItem, OrderStatus, RootCauseCode
from orderops_shared.models import Diagnosis, RootCause
from pydantic import ValidationError


def test_order_status_roundtrips_through_json() -> None:
    order = Order(
        order_no="NO202610210001",
        channel="self_operated",
        status=OrderStatus.PAID,
        total_amount="100.00",
        created_at="2026-10-21T10:00:00Z",
        customer_id="C001",
        items=[OrderItem(sku="SKU-1", name="试剂盒", qty=2, category="reagent")],
        address_region="浙江杭州",
    )
    payload = order.model_dump(mode="json")
    assert payload["status"] == "PAID"
    # amounts must not degrade into floats
    assert payload["total_amount"] == "100.00"


def test_negative_quantity_is_rejected() -> None:
    with pytest.raises(ValidationError):
        OrderItem(sku="SKU-1", name="试剂盒", qty=-1, category="reagent")


def test_root_cause_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        RootCause(
            code=RootCauseCode.A1_PAYMENT_CALLBACK_TIMEOUT,
            label="x",
            confidence=0.5,
            rationale="y",
            evidence_ids=[],
        )


def test_diagnosis_caps_root_causes_at_three() -> None:
    causes = [
        RootCause(
            code=RootCauseCode.A1_PAYMENT_CALLBACK_TIMEOUT,
            label=f"cause {i}",
            confidence=0.5,
            rationale="r",
            evidence_ids=[f"e{i}"],
        )
        for i in range(4)
    ]
    with pytest.raises(ValidationError):
        Diagnosis(
            case_id="case-1",
            anomaly_family="PAYMENT_SUCCESS_NOT_PROPAGATED",
            summary="s",
            root_causes=causes,
        )
