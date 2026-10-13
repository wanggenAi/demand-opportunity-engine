import hashlib
import re
from collections import defaultdict
from .signals import payment_truth

CLUSTER_DETAILS = {
    "workflow_reliability": {
        "repeated_pain": "Operators cannot trust workflow execution status; triggers, responses or saved definitions fail.",
        "current_alternatives": "Vendor bug tracker and native fixes (free), internal engineering, n8n support, freelance automation providers.",
        "potential": "Standardize reproduction, health checks and recovery runbooks; current category still too broad for one packaged product.",
        "form": "Service package + Workflow checklist",
        "distribution": "Consent-based workflow diagnostic referrals; do not pitch to all bug reporters.",
        "narrow": False,
    },
    "supplier_verification": {
        "repeated_pain": "Verify a supplier before sending a deposit.",
        "current_alternatives": "Alibaba badges, public company records, sourcing agents, third-party due diligence.",
        "potential": "One supplier desk-verification memo with evidence links and missing checks.",
        "form": "Skill + Service package",
        "distribution": "Reply only to buyers who explicitly invite agent quotations.",
        "narrow": True,
    },
    "rfq_translation": {
        "repeated_pain": "Turn a product brief into comparable bilingual supplier quotations.",
        "current_alternatives": "Translation tools, spreadsheets, sourcing agencies.",
        "potential": "Standardized RFQ translation/comparison with evidence and no invented specs.",
        "form": "Template + Skill",
        "distribution": "Sourcing buyers requesting quotations.",
        "narrow": True,
    },
    "browser_automation": {
        "repeated_pain": "Repeated manual browser work is costly or brittle.",
        "current_alternatives": "Playwright, Selenium, vendor APIs and open-source browser agents.",
        "potential": "Needs one repeated workflow and paying buyers before standardization.",
        "form": "Workflow + Service package",
        "distribution": "Authorized workflow audit and referrals.",
        "narrow": False,
    },
}

def observation_eligible(op):
    if not op.source_verified or not op.source_open:
        return False
    if op.buyer_role not in {"BUYER", "PROBLEM_OBSERVER"} or op.cluster_name == "unclassified":
        return False
    if op.source_platform == "GitHub":
        # Broad issue-search matches often contain autonomous task logs or ads.
        genuine = re.search(r"\bbug description\b|\bto reproduce\b|\bfeature request\b|\bi need\b|\bwe need\b|looking to hire|willing to pay", op.source_text, re.I)
        if not genuine or re.search(r"weekly digest|newsletter|seo daily|commit.monitor|market summary|zero.upfront.cost distribution", op.title + " " + op.source_text, re.I):
            return False
    return True

def clusters(opportunities):
    grouped = defaultdict(list)
    for op in opportunities:
        if observation_eligible(op):
            grouped[op.cluster_name].append(op)
    result = []
    for name, rows in grouped.items():
        unique = {}
        content = set()
        for op in sorted(rows, key=lambda o: o.published_at, reverse=True):
            normalized = re.sub(r"\W+", " ", op.source_text.lower()).strip()
            fingerprint = hashlib.sha256(normalized.encode()).hexdigest()
            if fingerprint not in content and op.buyer_id not in unique:
                content.add(fingerprint)
                unique[op.buyer_id] = op
        rows = list(unique.values())
        count = len(rows)
        paid = sum(payment_truth(op)[0] != "INFERRED" for op in rows)
        platforms = sorted({op.source_platform for op in rows})
        communities = sorted({op.community for op in rows})
        details = CLUSTER_DETAILS.get(name, {
            "repeated_pain": name.replace("_", " "),
            "current_alternatives": "Manual research, spreadsheets and existing service providers.",
            "potential": "Needs a narrower job-to-be-done and payment evidence.",
            "form": "Service package", "distribution": "Not yet demonstrated", "narrow": False,
        })
        gates = []
        if count < 5:
            gates.append("fewer than 5 independent observations")
        if len(set(communities)) < 2:
            gates.append("only one community; cross-source validation missing")
        if paid < 2:
            gates.append("fewer than 2 primary payment/commercial signals; paid-market proof not independently verified")
        if not details["narrow"]:
            gates.append("problem too broad to standardize")
        result.append({
            "cluster_name": name, "independent_demand_count": count, "payment_evidence_count": paid,
            "platforms": platforms, "communities": communities,
            "evidence_urls": [op.source_url for op in rows],
            "repeated_pain": details["repeated_pain"], "current_alternatives": details["current_alternatives"],
            "productization_potential": details["potential"], "suggested_product_form": details["form"],
            "distribution": details["distribution"], "status": "PRODUCT OPPORTUNITY" if not gates else "UNVALIDATED CLUSTER",
            "gates_failed": gates,
            "prebuild_validation": "Ask consenting operators to purchase one scoped diagnostic/verification pilot; record quotes and outcomes before building any product.",
        })
    return sorted(result, key=lambda c: (-c["independent_demand_count"], c["cluster_name"]))
