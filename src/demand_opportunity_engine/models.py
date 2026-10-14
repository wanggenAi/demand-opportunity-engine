"""Source truth is separate from the operator's interpretation."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from urllib.parse import urlparse

ROUTES = {"DIRECT_LEAD", "PRODUCT_SIGNAL", "INFO_EDGE"}
EVENTS = {"DISCOVERED", "CONTACTED", "REPLIED", "QUALIFIED", "QUOTED", "WON", "LOST", "REVENUE"}
MODES = {"REMOTE_NOW", "PARTNER_REQUIRED", "SPECIALIST_REQUIRED", "LOCAL_PHYSICAL"}
COMMERCIAL_INTENTS = {"BUDGET_STATED", "QUOTE_REQUESTED", "HIRING", "PAID_TASK", "BOUNTY", "AGENT_OR_VENDOR_REQUEST", "PROCUREMENT_REQUEST", "WILLING_TO_PAY", "NONE"}
ACQUISITION_COSTS = {"ZERO", "OPTIONAL_PAID", "REQUIRED_PAID", "UNKNOWN"}

def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)

def age(value, now):
    return (now - timestamp(value)).total_seconds() / 86400 if value else None

def https(value):
    p = urlparse(value)
    return p.scheme == "https" and bool(p.netloc)

@dataclass
class Opportunity:
    id: str
    title: str
    source_platform: str
    source_url: str
    published_at: str
    observed_at: str
    raw_evidence_quote: str
    source_text: str
    buyer_id: str
    target_profile_url: str
    routes: list[str] = field(default_factory=lambda: ["DIRECT_LEAD"])
    community: str = ""
    source_api_url: str = ""
    source_verified: bool = False
    source_snapshot: str = ""
    buyer_role: str = "UNKNOWN"
    source_open: bool = True
    buyer_activity_at: str | None = None
    buyer_activity_url: str = ""
    buyer_activity_verified: bool = False
    buyer_activity_author_id: str = ""
    buyer_activity_quote: str = ""
    last_activity_at: str | None = None
    payment_signal_type: str = "INFERRED"
    commercial_intent_type: str = "NONE"
    commercial_intent_quote: str = ""
    contact_path: str = ""
    acquisition_cost: str = "UNKNOWN"
    acquisition_cost_evidence: str = ""
    source_family: str = ""
    discovery_route: str = "PRODUCT_SIGNAL"
    payment_evidence_quote: str = ""
    derived_interpretation: str = ""
    comment_count: int | None = None
    seller_competition_count: int | None = None
    comments_complete: bool = False
    competition_pressure: str = "UNKNOWN"
    competition_evidence: list[str] = field(default_factory=list)
    mature_quote_present: bool = False
    many_dms_reported: bool = False
    commodity_market: bool = True
    differentiation: str = ""
    fulfillment_mode: str = "REMOTE_NOW"
    required_capabilities: list[str] = field(default_factory=list)
    cluster_name: str = "unclassified"
    suggested_offer: str = ""
    suggested_price_range: str = ""
    first_message: str = ""
    effort: str = ""
    risk: str = ""
    why_now: str = ""
    next_action: str = ""
    confidence: int = 2
    contact_channel: str = ""
    info_edge: dict = field(default_factory=dict)
    operator_advantage: dict = field(default_factory=dict)
    observed_budget: dict = field(default_factory=dict)

    def validate(self):
        if not self.id or not self.title or not https(self.source_url):
            raise ValueError("id/title/HTTPS source required")
        if not self.routes or not set(self.routes) <= ROUTES:
            raise ValueError("invalid routes")
        if not self.raw_evidence_quote.strip() or self.raw_evidence_quote not in self.source_text:
            raise ValueError("raw quote must be preserved in source_text")
        if self.payment_evidence_quote and self.payment_evidence_quote not in self.source_text:
            raise ValueError("payment quote must come from source_text")
        if self.commercial_intent_type not in COMMERCIAL_INTENTS:
            raise ValueError("invalid commercial intent")
        if self.acquisition_cost not in ACQUISITION_COSTS:
            raise ValueError("invalid acquisition cost")
        if self.commercial_intent_quote and self.commercial_intent_quote not in self.source_text:
            raise ValueError("commercial quote must come from source_text")
        for value in (self.published_at, self.observed_at, self.buyer_activity_at, self.last_activity_at):
            if value:
                timestamp(value)
        if self.fulfillment_mode not in MODES or not 0 <= self.confidence <= 5:
            raise ValueError("invalid capability/confidence")
        for count in (self.comment_count, self.seller_competition_count):
            if count is not None and (not isinstance(count, int) or count < 0):
                raise ValueError("invalid reply count")

    def to_dict(self):
        return asdict(self)

@dataclass
class Outcome:
    event_id: str
    opportunity_id: str
    event_type: str
    occurred_at: str
    channel: str = ""
    amount: float | None = None
    currency: str | None = None
    loss_reason: str = ""
    human_minutes: float | None = None  # Actual time reported by the human, never an estimate.

    def validate(self):
        if not self.event_id or self.event_type not in EVENTS:
            raise ValueError("invalid outcome event")
        timestamp(self.occurred_at)
        if self.event_type in {"QUOTED", "REVENUE"}:
            if self.amount is None or self.amount < 0 or not self.currency:
                raise ValueError("money events require nonnegative amount and currency")
        if self.event_type == "LOST" and not self.loss_reason:
            raise ValueError("LOST requires reason")
        if self.human_minutes is not None:
            import math
            if not math.isfinite(self.human_minutes) or self.human_minutes < 0:
                raise ValueError("human_minutes must be finite and nonnegative")

    def to_dict(self):
        return asdict(self)
