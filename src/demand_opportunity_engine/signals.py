"""Conservative, inspectable source-only rules. No analyst prose is scored."""
import re

SELLER = re.compile(r"\[for\s*hire\]|\bseeking (?:freelance\b|work|a job)|looking for (?:a |an )?(?:role|gig|job)|i (?:offer|provide) (?:services|automation)", re.I)
SUPPLY = re.compile(r"\bfor hire\b|looking for (?:remote work|remote opportunit|n8n automation opportunit)|open to (?:remote|freelance) opportunit|available for (?:freelance|hire)|builder available|saw your post looking for|want to build my .{0,25}skills|what i (?:deliver|can work with)|\bi(?: am|['’]m)\s+(?:a|an)\s+(?:(?:beginner|experienced|senior|junior|ai|automation|n8n|freelance|software)\s+){0,5}(?:developer|freelancer|engineer)|i build .{0,40}(?:engine|workflow)", re.I)
NEGATIVE = re.compile(r"not hiring|not looking to hire|no (?:money|budget)|not (?:interested in |willing to )?pay|free (?:help|solution)|can't afford|cannot afford|no upfront|pay(?:ment)? (?:only )?after", re.I)
REQUEST = re.compile(r"looking for|i need|we need|seeking|can anyone|how (?:can|do) i|help (?:me|us)|feature request|\[hiring\]", re.I)
PAIN = re.compile(r"manual|repetitive|every (?:day|week)|hours|workflow|automation|supplier|sourcing|rfq|invoice", re.I)
PITCH = re.compile(r"(?:i|we) can help|(?:i|we) (?:offer|provide|build)|dm me|contact (?:me|us)|my (?:agency|company)|our (?:agency|company)|happy to help", re.I)

def payment_truth(op):
    # Field claims are ignored. Only buyer-authored sentences can trigger intent.
    if commercial_truth(op)[0] == "NONE":
        return "INFERRED", "", 0
    text = op.source_text
    if NEGATIVE.search(text):
        return "INFERRED", "", 0
    sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    rules = [
        ("EXPLICIT_BUDGET", r"(?:budget|pay|offering|bounty|reward|compensation).{0,60}(?:[$€£₹]\s*\[?\d|\d+\s*(?:usd|eur|dollars))|[$€£]\s*\d.{0,40}(?:budget|pay|bounty)", 25),
        ("FEE_REQUEST", r"(?:fee|commission|pricing|charges).{0,25}(?:structure|quote)|(?:send|share|include).{0,50}(?:fee|charges|commission)|request (?:a )?quote", 20),
        ("HIRING", r"\[hiring\]|\b(?:seeking freelancer|we are hiring|i am hiring|looking to hire|want to hire|paid (?:help|project|job))\b", 22),
        ("COMMERCIAL_INTENT", r"ready to buy|paid (?:pilot|trial)|willing to pay|pay someone|commercial (?:project|order)", 15),
    ]
    for kind, pattern, points in rules:
        for sentence in sentences:
            if re.search(pattern, sentence, re.I):
                return kind, sentence.strip(), points
    kind, quote = commercial_truth(op)
    if kind != "NONE":
        return "COMMERCIAL_INTENT", quote, 15
    return "INFERRED", "", 0

def cluster_for(text):
    patterns = [
        ("supplier_verification", r"supplier.{0,25}(?:verif|background|legit)|factory.{0,20}verif|sourcing agent"),
        ("rfq_translation", r"\brfq\b|request for quotation|translate.{0,20}(?:supplier|chinese)"),
        ("sample_comparison", r"(?:sample|samples).{0,30}(?:compar|evaluat|test)"),
        ("supplier_sourcing", r"\bsuppliers?\b|\bmanufacturers?\b|\b(?:china|product|factory)\s+sourcing\b|\bsourcing (?:agent|partner|products?|suppliers?)\b"),
        ("lead_research", r"lead.{0,20}(?:research|generat|gen\b|crm)"),
        ("browser_automation", r"browser|playwright|selenium"),
        ("workflow_reliability", r"workflow|trigger|retry|webhook|automation"),
    ]
    for name, pattern in patterns:
        if re.search(pattern, text, re.I | re.S):
            return name
    return "unclassified"

def competition(comments, complete, op_text, applications=False):
    application = re.compile(r'\bapplication\b|\bportfolio\b|\bexperience\b|my (?:rate|agency)|\bavailable\b|account.{0,30}(?:new|dm)|(?:^|\n)\s*rate:', re.I)
    pitches = [c for c in comments if PITCH.search(c["text"]) or (applications and application.search(c["text"]))]
    mature = any(re.search(r"[$€£]\s*\d|(?:our|my) (?:rate|price)", c["text"], re.I) for c in pitches)
    many = bool(re.search(r"(?:many|lots of|50|dozens of).{0,25}(?:dm|pitch|agenc|freelancer)", op_text, re.I))
    count = len({c["author"] for c in pitches})
    pressure = "HIGH" if count >= 5 or mature or many else ("MEDIUM" if count >= 2 else "LOW")
    if not complete and pressure != "HIGH":
        pressure = "UNKNOWN"
    return count, pressure, mature, many, [c["url"] for c in pitches]

# Primary text only. These labels do not add a second payment score.
COMMERCIAL_RULES = [
    ('BUDGET_STATED', r'(?:budget|pay|offering|compensation).{0,60}(?:[$€£₹]\s*\[?\d|\d+\s*(?:usd|eur|dollars))'),
    ('BOUNTY', r'\bbounty\b.{0,60}(?:[$€£]\s*\d|paid|reward)'),
    ('QUOTE_REQUESTED', r'request (?:a |for )?(?:quote|quotation)|(?:send|share|include).{0,40}(?:pricing|quote|fee)|seeking estimates|(?:fee|commission).{0,25}structure'),
    ('HIRING', r"\[hiring\]|\b(?:^hiring|we(?: are|['’]re) hiring|i(?: am|['’]m) hiring|looking to hire|want to hire|seeking (?:a )?freelancer|developer (?:needed|required)|freelancer needed)\b"),
    ('PAID_TASK', r'\bpaid (?:task|help|project|job|pilot|trial|qa|stress testing)\b|\(paid\)'),
    ('WILLING_TO_PAY', r'willing to pay|pay someone|ready to buy|pay (?:a )?flat fee'),
    ('AGENT_OR_VENDOR_REQUEST', r'(?:looking for|need|seeking).{0,35}(?:sourcing agent|sourcing partner|supplier verification (?:service|agent)|vendor|consultant|automation specialist|automation developer|n8n developer|n8n freelancer|n8n builder)'),
    ('PROCUREMENT_REQUEST', r'\brfq\b|request for quotation|request for proposal|\brfp\b|procurement request'),
]

def commercial_truth(op):
    if op.source_platform == 'GitHub' and re.search(r'weekly digest|newsletter|category [a-z].{0,20}matrix|market summary|seo daily|commit.monitor', op.title, re.I):
        return 'NONE', ''
    if op.buyer_role != 'BUYER' or SELLER.search(op.title) or SUPPLY.search(op.title) or SUPPLY.search(op.source_text[:600]) or NEGATIVE.search(op.source_text):
        return 'NONE', ''
    for kind, pattern in COMMERCIAL_RULES:
        for sentence in re.split(r'(?<=[.!?])\s+|\n', op.source_text):
            if re.search(pattern, sentence, re.I):
                return kind, sentence.strip()
    return 'NONE', ''

def normalize_intent(op):
    # Inspect the author's introduction, not another user's hiring sentence later in a service ad.
    if SELLER.search(op.title) or SUPPLY.search(op.title) or SUPPLY.search(op.source_text[:600]):
        op.buyer_role = 'SELLER'
    op.commercial_intent_type, op.commercial_intent_quote = commercial_truth(op)
    if op.commercial_intent_type == 'NONE':
        if op.buyer_role == 'BUYER':
            op.buyer_role = 'PROBLEM_OBSERVER'
        op.routes = [r for r in op.routes if r != 'DIRECT_LEAD'] or ['PRODUCT_SIGNAL']
    elif 'DIRECT_LEAD' not in op.routes:
        op.routes.insert(0, 'DIRECT_LEAD')
    op.payment_signal_type, op.payment_evidence_quote, _ = payment_truth(op)
    return op
