"""Pydantic models for the business domain, the agent output and tool payloads.

Design notes worth keeping in mind while reading:

* Amounts use `Decimal`, never `float`. Pydantic serialises `Decimal` as a
  JSON string, which keeps `100.10` from turning into `100.0999999`.
* Every record that the agent may cite carries an identifier and a
  timestamp. The agent's evidence chain is validated against those ids, so
  they must be stable and unique.
* The tool payload models (`Order`, `Payment`, ...) are what
  `enterprise-sim` returns. The agent-side models (`Case`, `Diagnosis`, ...)
  are what `ai-api` owns. They live in one package because both sides must
  agree on the vocabulary.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from orderops_shared.enums import (
    AnomalyFamily,
    Channel,
    DiagnosisVerdict,
    EventType,
    LabelStatus,
    LockStatus,
    LogLevel,
    OrderStatus,
    PaymentEventType,
    PaymentStatus,
    RootCauseCode,
    Severity,
    TaskStatus,
)


class OrderItem(BaseModel):
    """A single line of an order. `category` drives some warehouse rules."""

    model_config = ConfigDict(frozen=True)

    sku: str
    name: str
    qty: int = Field(gt=0)
    category: str


class Order(BaseModel):
    """Order header as reported by the OMS."""

    model_config = ConfigDict(frozen=True)

    order_no: str
    channel: Channel
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    paid_at: datetime | None = None
    shipped_at: datetime | None = None
    customer_id: str
    items: list[OrderItem]
    address_region: str
    priority: str = "normal"


class OrderEvent(BaseModel):
    """One entry of the order timeline. The timeline is the primary evidence."""

    model_config = ConfigDict(frozen=True)

    event_id: str
    order_no: str
    event_type: EventType
    occurred_at: datetime
    actor: str
    payload: dict[str, object] = Field(default_factory=dict)
    trace_id: str | None = None


class PaymentEvent(BaseModel):
    """Gateway callback / reconciliation event."""

    model_config = ConfigDict(frozen=True)

    event_id: str
    event_type: PaymentEventType
    occurred_at: datetime
    http_status: int | None = None
    latency_ms: int | None = None
    message: str | None = None


class Payment(BaseModel):
    """Payment record including its callback timeline.

    `idempotency_key` is the physical carrier of the `A2_IDEMPOTENCY_CONFLICT`
    root cause: two payment rows for one order sharing a key.
    """

    model_config = ConfigDict(frozen=True)

    payment_id: str
    order_no: str
    channel: str
    amount: Decimal
    status: PaymentStatus
    idempotency_key: str
    paid_at: datetime | None = None
    events: list[PaymentEvent] = Field(default_factory=list)


class InventoryLock(BaseModel):
    """Stock reservation held for one order line."""

    model_config = ConfigDict(frozen=True)

    lock_id: str
    order_no: str
    sku: str
    qty: int = Field(gt=0)
    lock_status: LockStatus
    locked_at: datetime
    released_at: datetime | None = None


class WarehouseTask(BaseModel):
    """A warehouse work order.

    `rule_matched` records which rule of the task-creation engine fired. It
    is the decisive evidence for `B3_TASK_CREATION_RULE_MISMATCH`.
    """

    model_config = ConfigDict(frozen=True)

    task_id: str
    order_no: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    picked_at: datetime | None = None
    dispatched_at: datetime | None = None
    fail_reason: str | None = None
    rule_matched: str | None = None


class LogisticsEvent(BaseModel):
    """One tracking event of a shipment."""

    model_config = ConfigDict(frozen=True)

    event_id: str
    event_type: str
    occurred_at: datetime
    location: str | None = None
    description: str | None = None


class Shipment(BaseModel):
    """Shipping label and tracking events of one order."""

    model_config = ConfigDict(frozen=True)

    shipment_id: str
    order_no: str
    carrier: str
    tracking_no: str
    label_status: LabelStatus
    created_at: datetime
    picked_up_at: datetime | None = None
    events: list[LogisticsEvent] = Field(default_factory=list)


class LogLine(BaseModel):
    """A single log line. `trace_id` links lines into one request."""

    model_config = ConfigDict(frozen=True)

    ts: datetime
    service: str
    level: LogLevel
    message: str
    trace_id: str | None = None


class SlaClause(BaseModel):
    """One measurable commitment plus what to do when it is breached."""

    model_config = ConfigDict(frozen=True)

    name: str
    threshold_seconds: int = Field(gt=0)
    action: str
    severity: Severity


class SlaPolicy(BaseModel):
    """A named policy document, returned as structured clauses.

    Returning clauses instead of prose keeps the arithmetic (is this overdue?)
    in code rather than in the model's head.
    """

    model_config = ConfigDict(frozen=True)

    policy_key: str
    title: str
    clauses: list[SlaClause]


class Case(BaseModel):
    """A diagnostic case opened against one order."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    order_no: str
    symptom: str
    anomaly_family: AnomalyFamily = AnomalyFamily.UNKNOWN
    severity: Severity = Severity.MEDIUM
    source: str = "synthetic"
    created_at: datetime


class EvidenceRef(BaseModel):
    """A pointer to one piece of collected evidence.

    `evidence_id` must be the id of a record a tool actually returned. The
    agent output validator rejects any id it cannot find, which is the main
    defence against hallucinated citations.
    """

    model_config = ConfigDict(frozen=True)

    evidence_id: str
    source: str
    observed_at: datetime
    summary: str


class RootCause(BaseModel):
    """One candidate root cause, always tied back to evidence."""

    code: RootCauseCode
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    evidence_ids: list[str] = Field(min_length=1)


class Action(BaseModel):
    """A recommended remediation step. V1 never executes these."""

    type: str
    description: str
    risk: Literal["low", "medium", "high"] = "medium"
    requires_approval: bool = True
    owner_role: str = "运营专员"


class Recommendation(BaseModel):
    actions: list[Action] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    """A reference to a knowledge-base chunk used in the reasoning."""

    chunk_id: str
    document_id: str
    title: str
    heading_path: str
    version: str


class Impact(BaseModel):
    scope: str = "单订单"
    affected_order_count: int = Field(default=1, ge=1)
    sla_breached: bool = False


class Diagnosis(BaseModel):
    """The structured output of one diagnostic run.

    This is the contract the LLM must satisfy and the contract the evaluation
    harness scores. It is deliberately strict: `root_causes` is capped, every
    root cause needs at least one evidence id, and `needs_human` is the
    default rather than the exception.
    """

    case_id: str
    anomaly_family: AnomalyFamily
    summary: str
    root_causes: list[RootCause] = Field(max_length=3)
    impact: Impact = Field(default_factory=Impact)
    recommendation: Recommendation = Field(default_factory=Recommendation)
    citations: list[Citation] = Field(default_factory=list)
    needs_human: bool = True
    escalate_reason: str | None = None
    confidence_overall: float = Field(ge=0.0, le=1.0)


class Feedback(BaseModel):
    """Human verdict on a diagnosis."""

    verdict: DiagnosisVerdict
    reason: str | None = None
    created_at: datetime | None = None
