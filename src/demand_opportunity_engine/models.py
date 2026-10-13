from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
from urllib.parse import urlparse

ROUTES = {"DIRECT_LEAD", "PRODUCT_SIGNAL", "INFO_EDGE"}

@dataclass
class Opportunity:
    id: str
    routes: list[str]
    title: str
    problem: str
    source_platform: str
    source_url: str
    published_at: str
    observed_at: str
    evidence_text: str
    payment_intent_evidence: str
    urgency: int
    reachability: int
    operator_fit: int
    repeatability: int
    competition_gap: int
    information_decay_risk: int
    confidence: int
    suggested_next_action: str
    suggested_offer: str
    estimated_effort: str
    risk: str
    contact_path: str

    def validate(self) -> None:
        if not self.id or not self.title:
            raise ValueError("id and title are required")
        if not self.routes or not set(self.routes) <= ROUTES:
            raise ValueError(f"routes must be a non-empty subset of {ROUTES}")
        parsed = urlparse(self.source_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("source_url must be an https URL")
        required = {
            "evidence_text": self.evidence_text,
            "payment_intent_evidence": self.payment_intent_evidence,
            "suggested_next_action": self.suggested_next_action,
            "suggested_offer": self.suggested_offer,
            "contact_path": self.contact_path,
        }
        if any(not str(v).strip() for v in required.values()):
            raise ValueError("evidence, payment intent, next action, offer and contact path are required")
        for field in ("urgency", "reachability", "operator_fit", "repeatability", "competition_gap", "information_decay_risk", "confidence"):
            value = getattr(self, field)
            if not isinstance(value, int) or not 0 <= value <= 5:
                raise ValueError(f"{field} must be an integer in [0, 5]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class Outcome:
    opportunity_id: str
    contacted_at: str
    channel: str
    reply: str = "unknown"
    qualified: str = "unknown"
    quoted_amount: float | None = None
    currency: str | None = None
    status: str = "open"
    revenue: float = 0.0
    loss_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
