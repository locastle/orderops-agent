"""Canonical vocabulary for the order-fulfilment domain.

Every enum here is part of a contract:

* `EventType` / `PaymentEventType` / `TaskStatus` ... describe facts that the
  simulated enterprise systems report.
* `RootCauseCode` is the *ground truth label* used by the evaluation harness.
  The agent must never be able to read it, and it is the only thing the
  evaluator compares against.

Root cause codes are grouped by anomaly family: the letter is the family,
the digit identifies the specific failure inside that family. Keep the codes
stable once the evaluation set exists - renaming them silently breaks every
historical result.
"""

from enum import StrEnum


class Channel(StrEnum):
    """Sales channel. Different channels use different order state machines."""

    SELF_OPERATED = "self_operated"
    THIRD_PARTY = "third_party"
    MINI_PROGRAM = "mini_program"


class OrderStatus(StrEnum):
    """Lifecycle of an order. `STUCK` means the order is alive but not progressing."""

    CREATED = "CREATED"
    PAID = "PAID"
    ALLOCATED = "ALLOCATED"
    WAREHOUSING = "WAREHOUSING"
    SHIPPED = "SHIPPED"
    COMPLETED = "COMPLETED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    STUCK = "STUCK"
    CANCELLED = "CANCELLED"


class EventType(StrEnum):
    """Order lifecycle events recorded in `order_events` (event sourcing)."""

    ORDER_CREATED = "ORDER_CREATED"
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PAYMENT_SUCCEEDED = "PAYMENT_SUCCEEDED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    ORDER_PAID = "ORDER_PAID"
    INVENTORY_LOCKED = "INVENTORY_LOCKED"
    INVENTORY_RELEASED = "INVENTORY_RELEASED"
    WMS_TASK_CREATED = "WMS_TASK_CREATED"
    WMS_TASK_PICKED = "WMS_TASK_PICKED"
    WMS_TASK_DISPATCHED = "WMS_TASK_DISPATCHED"
    SHIPMENT_CREATED = "SHIPMENT_CREATED"
    SHIPMENT_PICKED_UP = "SHIPMENT_PICKED_UP"
    ORDER_SHIPPED = "ORDER_SHIPPED"
    ORDER_COMPLETED = "ORDER_COMPLETED"


class PaymentStatus(StrEnum):
    INIT = "INIT"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentEventType(StrEnum):
    """Callback / reconciliation events produced by the payment gateway."""

    CALLBACK_RECEIVED = "CALLBACK_RECEIVED"
    CALLBACK_TIMEOUT = "CALLBACK_TIMEOUT"
    CALLBACK_REJECTED = "CALLBACK_REJECTED"
    RECONCILED = "RECONCILED"
    REFUND_REQUESTED = "REFUND_REQUESTED"


class LockStatus(StrEnum):
    LOCKED = "LOCKED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    PICKING = "PICKING"
    PICKED = "PICKED"
    DISPATCHED = "DISPATCHED"
    FAILED = "FAILED"
    DONE = "DONE"


class LabelStatus(StrEnum):
    """Status of the shipping label handed over to the carrier."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class LogisticsEventType(StrEnum):
    LABEL_CREATED = "LABEL_CREATED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    EXCEPTION = "EXCEPTION"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyFamily(StrEnum):
    """Coarse classification of an order anomaly, used to route the agent."""

    NONE = "NONE"
    UNKNOWN = "UNKNOWN"
    PAYMENT_SUCCESS_NOT_PROPAGATED = "PAYMENT_SUCCESS_NOT_PROPAGATED"
    INVENTORY_LOCKED_NO_WMS_TASK = "INVENTORY_LOCKED_NO_WMS_TASK"
    SHIPPED_NO_PICKUP = "SHIPPED_NO_PICKUP"


class RootCauseCode(StrEnum):
    """Ground truth labels for the evaluation set.

    The agent must infer these from evidence; it must never be able to read
    them. `OK_*` marks a healthy order, `INSUFFICIENT_*` and `CONFLICT_*`
    mark cases where the correct behaviour is to escalate to a human rather
    than to guess.
    """

    # family A - payment succeeded but the order did not move on
    A1_PAYMENT_CALLBACK_TIMEOUT = "A1_PAYMENT_CALLBACK_TIMEOUT"
    A2_IDEMPOTENCY_CONFLICT = "A2_IDEMPOTENCY_CONFLICT"
    A3_STATE_MACHINE_RULE_MISMATCH = "A3_STATE_MACHINE_RULE_MISMATCH"

    # family B - inventory locked but no warehouse task
    B1_MQ_MESSAGE_LOST = "B1_MQ_MESSAGE_LOST"
    B2_WMS_INTERFACE_RETRY_EXHAUSTED = "B2_WMS_INTERFACE_RETRY_EXHAUSTED"
    B3_TASK_CREATION_RULE_MISMATCH = "B3_TASK_CREATION_RULE_MISMATCH"

    # family C - shipped but the carrier never collected the parcel
    C1_CARRIER_CALLBACK_MISSING = "C1_CARRIER_CALLBACK_MISSING"
    C2_WAREHOUSE_NOT_PACKED = "C2_WAREHOUSE_NOT_PACKED"
    C3_CARRIER_PICKUP_DELAY = "C3_CARRIER_PICKUP_DELAY"

    # healthy / must-escalate labels
    OK_NO_ANOMALY = "OK_NO_ANOMALY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class DiagnosisVerdict(StrEnum):
    """Human feedback on a diagnosis."""

    ACCEPT = "accept"
    REJECT = "reject"
    ESCALATE = "escalate"


class ToolErrorCode(StrEnum):
    """Uniform error vocabulary returned by every tool."""

    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    NOT_FOUND = "NOT_FOUND"
    PARAM_INVALID = "PARAM_INVALID"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
