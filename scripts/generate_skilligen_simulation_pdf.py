"""
Generate PDF report for Skilligen HDI life insurance simulation.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.simulation_skilligen_life_insurance import run_simulation, SCENARIOS
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

OUTPUT = "docs/partners/skilligen/OMNIX_Skilligen_Simulation_LifeInsurance_v1.pdf"

DARK   = colors.HexColor("#060F1E")
GOLD   = colors.HexColor("#C9A227")
WHITE  = colors.white
LIGHT  = colors.HexColor("#E2E8F0")
MID    = colors.HexColor("#94A3B8")
ROW    = colors.HexColor("#0D1829")
RED    = colors.HexColor("#ef4444")
GREEN  = colors.HexColor("#10b981")
W, H   = A4

results = run_simulation()

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.restoreState()

doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=18*mm, rightMargin=18*mm,
    topMargin=14*mm, bottomMargin=14*mm,
)

def s(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9, textColor=LIGHT,
                leading=14, spaceAfter=3)
    base.update(kw)
    return ParagraphStyle(name, **base)

S = {
    "logo":    s("logo", fontSize=20, fontName="Helvetica-Bold", textColor=WHITE),
    "tag":     s("tag",  fontSize=7,  textColor=GOLD),
    "tagr":    s("tagr", fontSize=7,  textColor=MID, alignment=TA_CENTER),
    "title":   s("title",fontSize=14, fontName="Helvetica-Bold", textColor=GOLD, spaceBefore=4),
    "sub":     s("sub",  fontSize=8,  textColor=MID),
    "sect":    s("sect", fontSize=9,  fontName="Helvetica-Bold", textColor=GOLD, spaceBefore=8, spaceAfter=3),
    "body":    s("body", fontSize=8,  textColor=LIGHT, alignment=TA_JUSTIFY),
    "scen":    s("scen", fontSize=9,  fontName="Helvetica-Bold", textColor=GOLD),
    "desc":    s("desc", fontSize=7.5,textColor=MID,  alignment=TA_JUSTIFY),
    "foot":    s("foot", fontSize=6.5,textColor=MID,  alignment=TA_CENTER),
    "approved":s("approved", fontSize=9, fontName="Helvetica-Bold", textColor=GREEN),
    "blocked": s("blocked",  fontSize=9, fontName="Helvetica-Bold", textColor=RED),
}

story = []

# ── HEADER ──────────────────────────────────────────────────────────────────
hdr = Table([[
    Paragraph("<b>OMNIX</b> QUANTUM", S["logo"]),
    Paragraph("omnixquantum.net  ·  Decision Governance Infrastructure", S["tagr"]),
]], colWidths=[90*mm, None])
hdr.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                          ("BOTTOMPADDING",(0,0),(-1,-1),0),
                          ("TOPPADDING",(0,0),(-1,-1),0)]))
story.append(hdr)
story.append(Paragraph("Decision Governance Infrastructure", S["tag"]))
story.append(Spacer(1,2*mm))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=4))

story.append(Paragraph("GOVERNANCE SIMULATION REPORT", S["title"]))
story.append(Paragraph(
    "Domain: Life Insurance Underwriting  ·  Scenario Design: Dr. Amanulla Khan, Skilligen HDI  ·  "
    "Executed by: Harold Nunes, OMNIX Quantum Ltd  ·  Date: 22 April 2026", S["sub"]))
story.append(Spacer(1,3*mm))

# ── SCENARIO CONTEXT ────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#1E2D45"), spaceAfter=3))
story.append(Paragraph("SCENARIO CONTEXT", S["sect"]))
story.append(Paragraph(
    "A mid-level underwriting team processes life insurance applications near quarter-end under "
    "increasing operational pressure. Four decision scenarios are evaluated using an identical "
    "borderline-risk applicant profile with varying pressure and override conditions. "
    "The simulation identifies the precise checkpoint where admissibility breaks under operational stress.",
    S["body"]))
story.append(Spacer(1,3*mm))

# ── SUMMARY TABLE ───────────────────────────────────────────────────────────
story.append(Paragraph("SIMULATION SUMMARY", S["sect"]))
sum_headers = ["ID", "Scenario", "Pressure Level", "Decision", "Checkpoints"]
sum_rows = []
for r in results:
    decision_text = "APPROVED" if r["decision"] == "APPROVED" else "BLOCKED"
    rate = f"{r['checkpoints_passed']}/{r['checkpoints_total']}"
    pressure = {
        "SCN-A": "None — Control",
        "SCN-B": "Moderate — Sales push",
        "SCN-C": "High — Escalation + Backlog",
        "SCN-D": "Peak — Quarter-end override",
    }.get(r["scenario_id"], "")
    sum_rows.append([r["scenario_id"], r["label"][:38], pressure, decision_text, rate])

sum_data = [sum_headers] + sum_rows
sum_table = Table(sum_data, colWidths=[14*mm, 60*mm, 46*mm, 24*mm, 24*mm])
sum_table.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0), GOLD),
    ("TEXTCOLOR",(0,0),(-1,0), DARK),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
    ("FONTSIZE",(0,0),(-1,0), 7.5),
    ("ALIGN",(0,0),(-1,0),"CENTER"),
    ("TOPPADDING",(0,0),(-1,0),5),
    ("BOTTOMPADDING",(0,0),(-1,0),5),
    ("BACKGROUND",(0,1),(-1,-1), ROW),
    ("TEXTCOLOR",(0,1),(-1,-1), WHITE),
    ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
    ("FONTSIZE",(0,1),(-1,-1), 7.5),
    ("ALIGN",(0,1),(-1,-1),"LEFT"),
    ("ALIGN",(3,1),(4,-1),"CENTER"),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,1),(-1,-1),5),
    ("BOTTOMPADDING",(0,1),(-1,-1),5),
    ("GRID",(0,0),(-1,-1), 0.4, colors.HexColor("#1E2D45")),
]))

for i, r in enumerate(results):
    tc = GREEN if r["decision"] == "APPROVED" else RED
    sum_table.setStyle(TableStyle([("TEXTCOLOR",(3,i+1),(3,i+1), tc),
                                    ("FONTNAME",(3,i+1),(3,i+1),"Helvetica-Bold"),
                                    ("TEXTCOLOR",(0,i+1),(0,i+1), GOLD)]))
story.append(sum_table)
story.append(Spacer(1,3*mm))

# ── ADMISSIBILITY BREAKPOINT ─────────────────────────────────────────────────
story.append(Paragraph("KEY FINDING — ADMISSIBILITY BREAKPOINT", S["sect"]))
story.append(Paragraph(
    "Admissibility breaks at SCN-B — the first introduction of moderate sales pressure. "
    "CP-4 (Trend Persistence) detected underwriting condition instability (score 46.8 < threshold 50) "
    "before any fraud or AML signals were triggered. The engine blocked the decision based on "
    "structural instability in the underwriting environment, not on the applicant's individual profile.",
    S["body"]))
story.append(Spacer(1,4*mm))

# ── SCENARIO DETAIL ──────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#1E2D45"), spaceAfter=3))
story.append(Paragraph("SCENARIO DETAIL — CHECKPOINT RESULTS", S["sect"]))

for r in results:
    scn_info = next(s for s in SCENARIOS if s["id"] == r["scenario_id"])
    decision_color = GREEN if r["decision"] == "APPROVED" else RED
    decision_label = "✓ APPROVED" if r["decision"] == "APPROVED" else "✗ BLOCKED"

    header_data = [[
        Paragraph(f"{r['scenario_id']} — {r['label']}", S["scen"]),
        Paragraph(f"{r['checkpoints_passed']}/{r['checkpoints_total']} checkpoints passed", S["desc"]),
        Paragraph(f"<b>{decision_label}</b>",
                  ParagraphStyle("dl", fontName="Helvetica-Bold", fontSize=9,
                                 textColor=decision_color, alignment=TA_CENTER)),
    ]]
    ht = Table(header_data, colWidths=[90*mm, 50*mm, None])
    ht.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#0D1829")),
        ("TOPPADDING",(0,0),(-1,0),5), ("BOTTOMPADDING",(0,0),(-1,0),5),
        ("LEFTPADDING",(0,0),(-1,0),6), ("VALIGN",(0,0),(-1,0),"MIDDLE"),
    ]))
    story.append(ht)
    story.append(Paragraph(scn_info["description"], S["desc"]))
    story.append(Spacer(1,2*mm))

    cp_headers = ["CP", "Checkpoint Name", "Signal", "Score", "Threshold", "Result"]
    cp_rows = []
    for gate in r["gate_results"]:
        status = gate.get("result","?")
        cp_rows.append([
            gate.get("checkpoint",""),
            gate.get("name",""),
            gate.get("signal",""),
            f"{gate.get('score',0):.1f}",
            str(gate.get("threshold","")),
            status,
        ])
    cp_data = [cp_headers] + cp_rows
    cp_table = Table(cp_data, colWidths=[14*mm, 46*mm, 38*mm, 16*mm, 22*mm, 18*mm])
    cp_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), GOLD),
        ("TEXTCOLOR",(0,0),(-1,0), DARK),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,0), 7),
        ("ALIGN",(0,0),(-1,0),"CENTER"),
        ("TOPPADDING",(0,0),(-1,0),4),("BOTTOMPADDING",(0,0),(-1,0),4),
        ("BACKGROUND",(0,1),(-1,-1), ROW),
        ("TEXTCOLOR",(0,1),(-1,-1), WHITE),
        ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
        ("FONTSIZE",(0,1),(-1,-1), 7),
        ("ALIGN",(0,1),(-1,-1),"LEFT"),
        ("ALIGN",(3,1),(5,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,1),(-1,-1),4),("BOTTOMPADDING",(0,1),(-1,-1),4),
        ("GRID",(0,0),(-1,-1), 0.3, colors.HexColor("#1E2D45")),
    ]))
    for i, gate in enumerate(r["gate_results"]):
        status = gate.get("result","?")
        col = GREEN if status == "PASS" else RED
        cp_table.setStyle(TableStyle([("TEXTCOLOR",(5,i+1),(5,i+1), col),
                                       ("FONTNAME",(5,i+1),(5,i+1),"Helvetica-Bold")]))
    story.append(cp_table)
    story.append(Spacer(1,4*mm))

# ── HASH CHAIN ──────────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#1E2D45"), spaceAfter=3))
story.append(Paragraph("RECEIPT HASH CHAIN", S["sect"]))
hash_headers = ["Scenario", "Content Hash", "Prev Hash"]
hash_rows = [[r["scenario_id"], r["content_hash"], r["prev_hash"]] for r in results]
hash_data = [hash_headers] + hash_rows
hash_table = Table(hash_data, colWidths=[20*mm, 60*mm, 60*mm])
hash_table.setStyle(TableStyle([
    ("BACKGROUND",(0,0),(-1,0), GOLD),
    ("TEXTCOLOR",(0,0),(-1,0), DARK),
    ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
    ("FONTSIZE",(0,0),(-1,0), 7.5),
    ("ALIGN",(0,0),(-1,0),"CENTER"),
    ("TOPPADDING",(0,0),(-1,0),5),("BOTTOMPADDING",(0,0),(-1,0),5),
    ("BACKGROUND",(0,1),(-1,-1), ROW),
    ("FONTNAME",(0,1),(-1,-1),"Courier"),
    ("FONTSIZE",(0,1),(-1,-1), 7),
    ("TEXTCOLOR",(0,1),(-1,-1), GOLD),
    ("ALIGN",(0,1),(-1,-1),"LEFT"),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,1),(-1,-1),5),("BOTTOMPADDING",(0,1),(-1,-1),5),
    ("GRID",(0,0),(-1,-1), 0.4, colors.HexColor("#1E2D45")),
]))
story.append(hash_table)
story.append(Spacer(1,4*mm))

# ── FOOTER ──────────────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=4))
story.append(Paragraph(
    f"CONFIDENTIAL — For use by OMNIX Quantum Ltd and Skilligen HDI only.  ·  "
    f"Engine: OMNIX GovernanceEvaluationEngine v6.5.4e  ·  "
    f"Adapter: InsuranceSignalAdapter ADR-054  ·  "
    f"Timestamp: {results[0]['timestamp']}  ·  omnixquantum.net",
    S["foot"]))

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"PDF generated: {OUTPUT}")
