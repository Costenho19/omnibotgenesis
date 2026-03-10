#!/usr/bin/env python3
"""
OMNIX Eureka Dubai GCC 2026 — PowerPoint Presentation Generator
Virtual pitch presentation for March 18, 2026 (3-4 minutes)
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "business", "pdfs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors
BLUE      = RGBColor(0, 80, 160)
BLUE2     = RGBColor(0, 110, 200)
DARK      = RGBColor(20, 20, 40)
WHITE     = RGBColor(255, 255, 255)
GRAY      = RGBColor(150, 155, 170)
LIGHT_BG  = RGBColor(240, 244, 252)
GREEN     = RGBColor(20, 130, 70)
YELLOW    = RGBColor(220, 160, 0)

W = Inches(13.33)
H = Inches(7.5)


def add_slide(prs, layout_idx=6):
    layout = prs.slide_layouts[layout_idx]
    return prs.slides.add_slide(layout)


def bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def rect(slide, x, y, w, h, color, alpha=None):
    shape = slide.shapes.add_shape(1, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def txbox(slide, text, x, y, w, h, size=18, bold=False, color=None,
          align=PP_ALIGN.LEFT, wrap=True, italic=False):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color or DARK
    return tb


def bullet_box(slide, items, x, y, w, h, size=14, color=None, spacing=1.1):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.space_before = Pt(2)
        run = p.add_run()
        run.text = ("- " if not item.startswith("  ") else "") + item.lstrip()
        run.font.size = Pt(size)
        run.font.color.rgb = color or DARK
    return tb


def slide_header(slide, number, title, subtitle=None):
    rect(slide, 0, 0, W, Inches(1.1), BLUE)
    num_str = f"0{number}" if number < 10 else str(number)
    txbox(slide, num_str, Inches(0.3), Inches(0.1), Inches(0.7), Inches(0.5),
          size=28, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txbox(slide, title.upper(), Inches(1.1), Inches(0.15), Inches(10), Inches(0.6),
          size=24, bold=True, color=WHITE)
    if subtitle:
        txbox(slide, subtitle, Inches(1.1), Inches(0.72), Inches(11), Inches(0.35),
              size=13, color=RGBColor(180, 210, 255), italic=True)
    txbox(slide, "OMNIX -- Decision Governance Infrastructure  |  Eureka Dubai GCC 2026",
          Inches(0), Inches(7.1), W, Inches(0.35), size=9, color=GRAY, align=PP_ALIGN.CENTER)
    txbox(slide, f"{number}/10", Inches(12.5), Inches(7.1), Inches(0.8), Inches(0.35),
          size=9, color=GRAY, align=PP_ALIGN.RIGHT)


def generate():
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H

    # ── SLIDE 1: COVER ───────────────────────────────────────────────────────
    s = add_slide(prs)
    bg(s, WHITE)
    rect(s, 0, 0, W, H * 0.55, BLUE)

    txbox(s, "OMNIX", Inches(0), Inches(0.8), W, Inches(1.5),
          size=72, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txbox(s, "Decision Governance Infrastructure", Inches(0), Inches(2.35), W, Inches(0.7),
          size=24, color=RGBColor(180, 210, 255), align=PP_ALIGN.CENTER)
    txbox(s, "for Automated Financial Systems", Inches(0), Inches(2.95), W, Inches(0.5),
          size=16, color=RGBColor(160, 195, 240), align=PP_ALIGN.CENTER, italic=True)

    rect(s, Inches(3.5), Inches(3.85), Inches(6.33), Inches(0.04), BLUE2)

    info = [
        ("Eureka Dubai GCC 2026  --  SEMIFINALIST", 22, True, BLUE),
        ("Pre-Seed Round  |  $500,000 USD  |  16.7% equity  |  $3M pre-money", 14, False, DARK),
        ("Founder & CEO: Harold Nunes  |  omnixquantum.net  |  March 2026", 13, False, GRAY),
    ]
    y_pos = 4.05
    for text, sz, bld, clr in info:
        txbox(s, text, Inches(0), Inches(y_pos), W, Inches(0.5),
              size=sz, bold=bld, color=clr, align=PP_ALIGN.CENTER)
        y_pos += 0.45

    # ── SLIDE 2: PROBLEM ─────────────────────────────────────────────────────
    s = add_slide(prs)
    bg(s, WHITE)
    slide_header(s, 2, "The Problem", "Automated systems fail -- and they fail at machine speed")

    rect(s, Inches(0.4), Inches(1.3), Inches(12.5), Inches(1.0), LIGHT_BG)
    txbox(s, "\"When automated systems fail, they do not fail slowly. They fail at machine speed.\"",
          Inches(0.5), Inches(1.38), Inches(12.3), Inches(0.85),
          size=17, bold=True, color=BLUE, align=PP_ALIGN.CENTER, italic=True)

    bullet_box(s, [
        "No governance layer between signal and execution -- every automated decision is an uncontrolled risk event",
        "Signal failure: systems act on false signals during volatile conditions",
        "Coherence failure: multiple internal signals disagree, yet the system still executes",
        "Tail risk failure: Black Swan events are not detected until losses are already cascading",
        "MiCA (EU 2025+), ADGM, DIFC: regulators now require decision accountability documentation",
        "Prop trading firms lose 15-40% of capital in their first year of automated deployment",
    ], Inches(0.5), Inches(2.5), Inches(12.3), Inches(3.8), size=16)

    # ── SLIDE 3: SOLUTION ────────────────────────────────────────────────────
    s = add_slide(prs)
    bg(s, WHITE)
    slide_header(s, 3, "The Solution", "A fail-closed governance engine that authorizes every decision")

    rect(s, 0, Inches(1.15), W, Inches(0.9), BLUE)
    txbox(s, "OMNIX is Decision Governance Infrastructure --", Inches(0.4), Inches(1.25),
          W - Inches(0.8), Inches(0.4), size=20, bold=True, color=WHITE)
    txbox(s, "the control layer between automated systems and execution.",
          Inches(0.4), Inches(1.65), W - Inches(0.8), Inches(0.35), size=16, color=RGBColor(180, 210, 255))

    col_w = Inches(5.8)
    y_start = Inches(2.25)

    rect(s, Inches(0.4), y_start - Inches(0.05), col_w, Inches(0.35), LIGHT_BG)
    txbox(s, "OMNIX DOES:", Inches(0.5), y_start, col_w, Inches(0.3), size=13, bold=True, color=BLUE)
    does = [
        "Intercepts every signal before execution",
        "Runs 8 independent validation checkpoints",
        "Blocks decisions that fail any single checkpoint",
        "Signs every decision with post-quantum cryptography",
        "Maintains a tamper-proof verifiable audit trail",
    ]
    bullet_box(s, does, Inches(0.5), y_start + Inches(0.35), col_w, Inches(3), size=14, color=GREEN)

    rect(s, Inches(6.9), y_start - Inches(0.05), col_w, Inches(0.35), LIGHT_BG)
    txbox(s, "OMNIX DOES NOT:", Inches(7.0), y_start, col_w, Inches(0.3), size=13, bold=True, color=BLUE)
    does_not = [
        "Generate trading signals or strategies",
        "Compete with existing trading platforms",
        "Manage or hold client assets",
        "Require replacing existing infrastructure",
        "Optimize for returns -- only for capital safety",
    ]
    bullet_box(s, does_not, Inches(7.0), y_start + Inches(0.35), col_w, Inches(3),
               size=14, color=RGBColor(160, 40, 40))

    rect(s, Inches(0.4), Inches(6.3), Inches(12.5), Inches(0.7), BLUE)
    txbox(s, "\"Intelligence may propose. OMNIX decides whether it is allowed to act.\"",
          Inches(0.5), Inches(6.38), Inches(12.3), Inches(0.5),
          size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER, italic=True)

    # ── SLIDE 4: HOW IT WORKS ────────────────────────────────────────────────
    s = add_slide(prs)
    bg(s, WHITE)
    slide_header(s, 4, "How It Works", "8 independent checkpoints + 3-gate exit governance")

    checkpoints = [
        ("CP-0", "Signal Integrity Validator", "Rejects corrupted or stale market data before evaluation"),
        ("CP-1", "Monte Carlo VETO", "10,000 simulation paths -- blocks trades with negative expected return"),
        ("CP-2", "RMS VETO", "Enforces hard exposure limits and position sizing rules"),
        ("CP-3", "VETO Early Return", "Immediate halt if critical risk thresholds are breached"),
        ("CP-4", "Coherence Engine (6-tier)", "Measures signal agreement across 6 dimensions"),
        ("CP-5", "Adaptive Coherence Gate", "Adjusts threshold dynamically based on market regime"),
        ("CP-7", "Temporal Coherence Validator", "Validates decision consistency with recent market history"),
        ("CP-8", "Edge Confirmation Window", "Requires 2 consecutive cycles of confirmed edge"),
    ]

    col1_x = Inches(0.3)
    col2_x = Inches(1.5)
    col3_x = Inches(3.5)
    y = Inches(1.25)
    row_h = Inches(0.6)

    for i, (cp, name, desc) in enumerate(checkpoints):
        row_y = y + i * row_h
        if i % 2 == 0:
            rect(s, col1_x, row_y, Inches(12.7), row_h - Inches(0.04), LIGHT_BG)
        txbox(s, cp, col1_x, row_y + Inches(0.08), Inches(1.1), row_h,
              size=11, bold=True, color=BLUE)
        txbox(s, name, col2_x, row_y + Inches(0.08), Inches(2.1), row_h,
              size=11, bold=True, color=DARK)
        txbox(s, desc, col3_x, row_y + Inches(0.08), Inches(9.6), row_h,
              size=10, color=DARK)

    rect(s, Inches(0.3), Inches(6.2), Inches(12.7), Inches(0.55), BLUE)
    txbox(s, "Exit Governance Layer (3 gates): Regime-Adjusted Thresholds -> Exit Coherence Gate -> TCV Exit Check",
          Inches(0.5), Inches(6.28), Inches(12.5), Inches(0.4),
          size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    # ── SLIDE 5: TRACTION ────────────────────────────────────────────────────
    s = add_slide(prs)
    bg(s, WHITE)
    slide_header(s, 5, "Traction", "Live system -- verified governance metrics")

    metrics = [
        ("50,688", "Governance decisions"),
        ("728,868", "Shadow evaluations"),
        ("100%", "Veto accuracy"),
        ("Semifinalist", "Eureka Dubai GCC 2026"),
    ]
    box_w = Inches(3.0)
    box_h = Inches(1.4)
    for i, (val, label) in enumerate(metrics):
        bx = Inches(0.3) + i * (box_w + Inches(0.12))
        rect(s, bx, Inches(1.25), box_w, box_h, BLUE)
        txbox(s, val, bx, Inches(1.3), box_w, Inches(0.85),
              size=26, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        txbox(s, label, bx, Inches(2.05), box_w, Inches(0.55),
              size=11, color=RGBColor(180, 210, 255), align=PP_ALIGN.CENTER)

    txbox(s, "3 real veto examples:", Inches(0.4), Inches(2.85), Inches(12.5), Inches(0.4),
          size=14, bold=True, color=BLUE)

    examples = [
        "XRP/USD -- Jan 9, 2026: BLACK SWAN veto (50% crash probability detected). XRP fell -1.96% in 7 days. Capital protected.",
        "AVAX/USD -- Jan 9, 2026: COHERENCE GATE veto (coherence 26.3%, below threshold). AVAX fell -1.08% in 24h. Uncertainty detected.",
        "BTC/USD -- Jan 15+: 396,067 Black Swan alerts. Zero executions. System correctly blocked each time. Capital intact.",
    ]
    bullet_box(s, examples, Inches(0.4), Inches(3.25), Inches(12.5), Inches(2.5), size=13)

    rect(s, Inches(0.4), Inches(6.1), Inches(12.5), Inches(0.65), LIGHT_BG)
    txbox(s, "Phase 0 (Jul-Aug 2025): 1,115 real trades on Kraken (real capital, pre-governance)  |  "
          "Learning Baseline (Nov 2025-Jan 14, 2026): paper trading, calibration  |  "
          "Official Track Record: Jan 15, 2026-present (paper trading)",
          Inches(0.5), Inches(6.18), Inches(12.3), Inches(0.5),
          size=9, color=GRAY, align=PP_ALIGN.CENTER, italic=True)

    # ── SLIDE 6: MARKET ──────────────────────────────────────────────────────
    s = add_slide(prs)
    bg(s, WHITE)
    slide_header(s, 6, "Market Opportunity", "$5.4B TAM -- compliance-driven demand accelerating")

    mets = [
        ("18,000", "Institutional targets"),
        ("$5.4B", "Total Addressable Market"),
        ("$540M", "Serviceable (Y1-3)"),
        ("2025+", "MiCA in force"),
    ]
    bw = Inches(3.0)
    for i, (v, l) in enumerate(mets):
        bx = Inches(0.3) + i * (bw + Inches(0.12))
        rect(s, bx, Inches(1.25), bw, Inches(1.2), LIGHT_BG)
        txbox(s, v, bx, Inches(1.3), bw, Inches(0.7),
              size=26, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
        txbox(s, l, bx, Inches(1.95), bw, Inches(0.45),
              size=11, color=DARK, align=PP_ALIGN.CENTER)

    txbox(s, "Market drivers:", Inches(0.4), Inches(2.7), Inches(12), Inches(0.4),
          size=14, bold=True, color=BLUE)
    drivers = [
        "MiCA (EU 2025+): mandates decision accountability and audit trails for all automated crypto systems",
        "ADGM & DIFC: regulatory frameworks actively requiring AI governance documentation for market access",
        "Sharia compliance: GCC institutions require documented decision validation for Sharia audit",
        "Post-quantum mandate: regulated GCC institutions beginning to require quantum-resistant cryptography",
        "Institutional automation accelerating faster than governance frameworks -- the gap is widening",
    ]
    bullet_box(s, drivers, Inches(0.4), Inches(3.15), Inches(12.5), Inches(3.5), size=13)

    # ── SLIDE 7: BUSINESS MODEL ───────────────────────────────────────────────
    s = add_slide(prs)
    bg(s, WHITE)
    slide_header(s, 7, "Business Model & Financials", "Recurring SaaS + API + institutional licensing")

    tiers = [
        ("Enterprise Pilot", "$10K-$15K/mo", "Prop firms, exchanges"),
        ("Enterprise Full", "$20K-$35K/mo", "Hedge funds, reg. funds"),
        ("API Platform", "$0.01-$0.05/call", "High-volume platforms"),
        ("B2C Advanced", "$149-$499/mo", "Advanced retail traders"),
    ]
    tw = Inches(3.1)
    for i, (name, price, target) in enumerate(tiers):
        bx = Inches(0.3) + i * (tw + Inches(0.07))
        rect(s, bx, Inches(1.25), tw, Inches(1.5), LIGHT_BG)
        txbox(s, name, bx, Inches(1.3), tw, Inches(0.35), size=12, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
        txbox(s, price, bx, Inches(1.65), tw, Inches(0.55), size=20, bold=True, color=DARK, align=PP_ALIGN.CENTER)
        txbox(s, target, bx, Inches(2.2), tw, Inches(0.45), size=10, color=GRAY, align=PP_ALIGN.CENTER)

    txbox(s, "Revenue projections:", Inches(0.4), Inches(3.0), Inches(12), Inches(0.4),
          size=14, bold=True, color=BLUE)

    proj = [
        ("Y1 (2026)", "$300K", "2-3 pilots, break-even Q4"),
        ("Y2 (2027)", "$1.2M", "10 clients + API"),
        ("Y3 (2028)", "$4.8M", "30 clients + platform"),
        ("Y5 (2030)", "$26M", "150+ clients + white-label"),
    ]
    pw = Inches(3.0)
    for i, (yr, rev, note) in enumerate(proj):
        bx = Inches(0.3) + i * (pw + Inches(0.12))
        rect(s, bx, Inches(3.5), pw, Inches(1.0), BLUE)
        txbox(s, yr, bx, Inches(3.55), pw, Inches(0.35), size=12, color=WHITE, align=PP_ALIGN.CENTER)
        txbox(s, rev, bx, Inches(3.88), pw, Inches(0.4), size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        txbox(s, note, bx, Inches(4.28), pw, Inches(0.18), size=9, color=RGBColor(180, 210, 255), align=PP_ALIGN.CENTER)

    bullet_box(s, [
        "MOIC scenarios: 14.7x (conservative) / 41x (base) / 102x (optimistic) on pre-seed entry",
        "Break-even Q4 2026  |  First revenue Q2-Q3 2026  |  Series A ready by Y3",
    ], Inches(0.4), Inches(4.7), Inches(12.5), Inches(1.0), size=13, color=DARK)

    # ── SLIDE 8: COMPETITIVE ADVANTAGE ────────────────────────────────────────
    s = add_slide(prs)
    bg(s, WHITE)
    slide_header(s, 8, "Competitive Advantage", "The only fail-closed governance layer with PQC audit trail")

    headers = ["Feature", "Retail Bots", "Risk Platforms", "Quant Funds", "OMNIX"]
    rows = [
        ["Fail-closed architecture", "No", "Partial", "No", "YES"],
        ["8 independent checkpoints", "No", "No", "No", "YES"],
        ["Post-quantum audit trail", "No", "No", "No", "YES"],
        ["Public verifiable receipts", "No", "No", "No", "YES"],
        ["MiCA / ADGM ready", "No", "Partial", "No", "YES"],
        ["Shadow portfolio engine", "No", "No", "Internal", "YES"],
    ]
    col_ws = [Inches(3.8), Inches(2.0), Inches(2.0), Inches(2.0), Inches(2.0)]
    y = Inches(1.25)
    rh = Inches(0.52)

    rect(s, Inches(0.3), y, sum(col_ws) + Inches(0.3), rh, BLUE)
    x = Inches(0.35)
    for i, h in enumerate(headers):
        txbox(s, h, x, y + Inches(0.08), col_ws[i], rh,
              size=12, bold=True, color=WHITE)
        x += col_ws[i]

    for ri, row in enumerate(rows):
        ry = y + (ri + 1) * rh
        if ri % 2 == 0:
            rect(s, Inches(0.3), ry, sum(col_ws) + Inches(0.3), rh, LIGHT_BG)
        x = Inches(0.35)
        for ci, cell in enumerate(row):
            clr = GREEN if cell == "YES" else (RGBColor(180, 40, 40) if cell == "No" else DARK)
            bld = cell == "YES"
            txbox(s, cell, x, ry + Inches(0.1), col_ws[ci], rh - Inches(0.1),
                  size=12, bold=bld, color=clr)
            x += col_ws[ci]

    txbox(s, "The fundamental difference: OMNIX is fail-CLOSED. Every other system is fail-OPEN.",
          Inches(0.35), Inches(5.5), Inches(12.5), Inches(0.5),
          size=14, bold=True, color=BLUE, align=PP_ALIGN.CENTER)

    # ── SLIDE 9: EXPERT VALIDATION ────────────────────────────────────────────
    s = add_slide(prs)
    bg(s, WHITE)
    slide_header(s, 9, "Expert Validation", "6 domain leaders independently validated the architecture")

    experts = [
        ("James Moore", "Founder/CEO, Nova Jema AI",
         "\"Exactly the layer I've been trying to articulate... the boundary between recommendation and binding authority.\""),
        ("William Fedorich", "AI Risk Analyst",
         "\"Ensuring every AI decision is vetted through multiple checkpoints is critical for high-stakes environments like trading and insurance.\""),
        ("Christopher Turk", "Quantum Security Architecture",
         "\"This is honestly pretty good.\" -- Deep technical exchange validating Dilithium-3 selection and PQC design."),
        ("Guomin Yang", "RDL Framework Creator",
         "Cited Harold by name in a published article, mapping OMNIX to his 3-layer governance model (Policy > Operational > Structural)."),
        ("HIL-AIW", "AI Governance Platform",
         "\"Your 8-checkpoint system with Monte Carlo VETO is brilliant -- most teams aren't thinking about quantum-resistant auditability yet.\""),
        ("Mostafa Monsour", "ULTRA MATRIX",
         "\"Your work with OMNIX Quantum appears to be exploring an important part of that stack.\""),
    ]

    ew = Inches(6.15)
    eh = Inches(1.5)
    for i, (name, role, quote) in enumerate(experts):
        col = i % 2
        row = i // 2
        bx = Inches(0.3) + col * (ew + Inches(0.2))
        by = Inches(1.25) + row * (eh + Inches(0.1))
        rect(s, bx, by, ew, eh, LIGHT_BG)
        txbox(s, name, bx + Inches(0.1), by + Inches(0.08), ew - Inches(0.2), Inches(0.35),
              size=12, bold=True, color=BLUE)
        txbox(s, role, bx + Inches(0.1), by + Inches(0.42), ew - Inches(0.2), Inches(0.28),
              size=10, color=GRAY, italic=True)
        txbox(s, quote, bx + Inches(0.1), by + Inches(0.72), ew - Inches(0.2), Inches(0.72),
              size=9.5, color=DARK)

    # ── SLIDE 10: THE ASK + CLOSE ─────────────────────────────────────────────
    s = add_slide(prs)
    bg(s, WHITE)
    slide_header(s, 10, "The Investment", "$500K pre-seed -- governance layer for a $5.4B market")

    asks = [
        ("$500K", "Raise target"),
        ("16.7%", "Equity offered"),
        ("$3M", "Pre-money valuation"),
        ("Q4 2026", "Break-even"),
    ]
    bw = Inches(3.0)
    for i, (v, l) in enumerate(asks):
        bx = Inches(0.3) + i * (bw + Inches(0.12))
        rect(s, bx, Inches(1.25), bw, Inches(1.2), BLUE)
        txbox(s, v, bx, Inches(1.3), bw, Inches(0.7), size=28, bold=True,
              color=WHITE, align=PP_ALIGN.CENTER)
        txbox(s, l, bx, Inches(1.95), bw, Inches(0.4), size=12, color=RGBColor(180, 210, 255),
              align=PP_ALIGN.CENTER)

    txbox(s, "Use of funds:", Inches(0.4), Inches(2.65), Inches(6), Inches(0.4),
          size=13, bold=True, color=BLUE)
    funds = [
        "40% -- Infrastructure & Security ($200K): hardening, PQC audit, compliance certs",
        "35% -- Sales & Business Development ($175K): institutional pilots, ADGM, Sharia assessment",
        "25% -- Team & Operations ($125K): first hire, legal, runway through Q4 2026",
    ]
    bullet_box(s, funds, Inches(0.4), Inches(3.05), Inches(6.2), Inches(1.8), size=12)

    txbox(s, "Investor returns:", Inches(6.8), Inches(2.65), Inches(6), Inches(0.4),
          size=13, bold=True, color=BLUE)
    returns = [
        "Conservative: MOIC 14.7x  (~72% IRR)",
        "Base scenario: MOIC 41x   (~110% IRR)",
        "Optimistic:    MOIC 102x  (~160% IRR)",
    ]
    bullet_box(s, returns, Inches(6.8), Inches(3.05), Inches(6.0), Inches(1.5), size=14)

    rect(s, 0, Inches(5.1), W, Inches(1.3), BLUE)
    txbox(s, "The governance layer is missing. OMNIX is building it.",
          Inches(0), Inches(5.2), W, Inches(0.55),
          size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txbox(s,
          "Harold Nunes -- Founder & CEO  |  contacto@omnixquantum.net  |  omnixquantum.net  |  omnixquantum.net/verify",
          Inches(0), Inches(5.72), W, Inches(0.45),
          size=12, color=RGBColor(180, 210, 255), align=PP_ALIGN.CENTER)
    txbox(s, "SEMIFINALIST -- Eureka Dubai GCC 2026",
          Inches(0), Inches(6.2), W, Inches(0.4),
          size=13, bold=True, color=YELLOW, align=PP_ALIGN.CENTER)

    out = os.path.join(OUTPUT_DIR, "OMNIX_Eureka_Presentation.pptx")
    prs.save(out)
    size_kb = os.path.getsize(out) / 1024
    print(f"Generated: {out}")
    print(f"File size: {size_kb:.1f} KB")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    generate()
