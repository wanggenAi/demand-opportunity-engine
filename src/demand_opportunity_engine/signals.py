"""Conservative, inspectable source-only rules. No analyst prose is scored."""
import re

SELLER = re.compile(r"\[for\s*hire\]|\bseeking (?:freelance\b|work|a job)|looking for (?:a |an )?(?:role|gig|job)|i (?:offer|provide) (?:services|automation)", re.I)
NEGATIVE = re.compile(r"no (?:money|budget)|not (?:interested in |willing to )?pay|free (?:help|solution)|can't afford|cannot afford|no upfront|pay(?:ment)? (?:only )?after", re.I)
REQUEST = re.compile(r"looking for|i need|we need|seeking|can anyone|how (?:can|do) i|help (?:me|us)|feature request|\[hiring\]", re.I)
PAIN = re.compile(r"manual|repetitive|every (?:day|week)|hours|workflow|automation|supplier|sourcing|rfq|invoice", re.I)
PITCH = re.compile(r"(?:i|we) can help|(?:i|we) (?:offer|provide|build)|dm me|contact (?:me|us)|my (?:agency|company)|our (?:agency|company)|happy to help", re.I)

def payment_truth(op):
    # Field claims are ignored. Only buyer-authored sentences can trigger intent.
    if op.buyer_role != "BUYER" or SELLER.search(op.title):
        return "INFERRED", "", 0
    text = op.source_text
    if NEGATIVE.search(text):
        return "INFERRED", "", 0
    sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    rules = [
        ("EXPLICIT_BUDGET", r"(?:budget|pay|offering|bounty|reward|compensation).{0,60}(?:[$€£]\s*\d|\d+\s*(?:usd|eur|dollars))|[$€£]\s*\d.{0,40}(?:budget|pay|bounty)", 25),
        ("FEE_REQUEST", r"(?:fee|commission|pricing|charges).{0,25}(?:structure|quote)|(?:send|share|include).{0,50}(?:fee|charges|commission)|request (?:a )?quote", 20),
        ("HIRING", r"\[hiring\]|\b(?:seeking freelancer|we are hiring|i am hiring|looking to hire|want to hire|paid (?:help|project|job))\b", 22),
        ("COMMERCIAL_INTENT", r"ready to buy|paid (?:pilot|trial)|willing to pay|pay someone|commercial (?:project|order)", 15),
    ]
    for kind, pattern, points in rules:
        for sentence in sentences:
            if re.search(pattern, sentence, re.I):
                return kind, sentence.strip(), points
    return "INFERRED", "", 0

def cluster_for(text):
    patterns = [
        ("supplier_verification", r"supplier.{0,25}(?:verif|background|legit)|factory.{0,20}verif|sourcing agent"),
        ("rfq_translation", r"\brfq\b|request for quotation|translate.{0,20}(?:supplier|chinese)"),
        ("sample_comparison", r"(?:sample|samples).{0,30}(?:compar|evaluat|test)"),
        ("supplier_sourcing", r"\bsuppliers?\b|\bmanufacturers?\b|\b(?:china|product|factory)\s+sourcing\b|\bsourcing (?:agent|partner|products?|suppliers?)\b"),
        ("lead_research", r"lead.{0,20}(?:research|generat|crm)"),
        ("browser_automation", r"browser|playwright|selenium"),
        ("workflow_reliability", r"workflow|trigger|retry|webhook|automation"),
    ]
    for name, pattern in patterns:
        if re.search(pattern, text, re.I | re.S):
            return name
    return "unclassified"

def competition(comments, complete, op_text):
    pitches = [c for c in comments if PITCH.search(c["text"])]
    mature = any(re.search(r"[$€£]\s*\d|(?:our|my) (?:rate|price)", c["text"], re.I) for c in pitches)
    many = bool(re.search(r"(?:many|lots of|50|dozens of).{0,25}(?:dm|pitch|agenc|freelancer)", op_text, re.I))
    count = len({c["author"] for c in pitches})
    pressure = "HIGH" if count >= 5 or mature or many else ("MEDIUM" if count >= 2 else "LOW")
    if not complete and pressure != "HIGH":
        pressure = "UNKNOWN"
    return count, pressure, mature, many, [c["url"] for c in pitches]
