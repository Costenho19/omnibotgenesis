#!/usr/bin/env python3
"""
OMNIX Quantum -- Pilot Program Proposal PDF Generator
Enterprise-grade design. English + Spanish. Exactly 2 pages each.
"""
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "business", "pdfs")
LOGO_PATH  = os.path.join(BASE_DIR, "docs", "business", "omnix_logo.png")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_DIR     = os.path.join(
    os.path.expanduser("~"),
    "workspace/.pythonlibs/lib/python3.11/site-packages/kaleido/executable/xdg/fonts/truetype/dejavu"
)
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD    = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY       = (8,  22,  58)
NAVY_LIGHT = (18, 42, 100)
GOLD       = (212, 175, 55)
GOLD_LIGHT = (245, 232, 170)
WHITE      = (255, 255, 255)
OFF_WHITE  = (250, 251, 255)
LIGHT_BG   = (243, 246, 254)
BORDER     = (210, 218, 236)
MID_GRAY   = (115, 128, 155)
DARK       = (18,  24,  48)
GREEN_BG   = (234, 250, 241)
GREEN_TXT  = (0,  108,  60)
BLUE_BG    = (233, 242, 255)
BLUE_TXT   = (12,  52, 130)
RED_SOFT   = (255, 242, 242)
RED_TXT    = (160,  20,  20)

HEADER_H = 26
TOP_M    = 34
LMARGIN  = 18
RMARGIN  = 18

# ── CONTENT ───────────────────────────────────────────────────────────────────
CONTENT = {
"EN": {
    "footer": "Confidential  --  Pilot Program Proposal   |   Harold Nunes, Founder & CEO   |   SSRN 6321298   |   Zenodo DOI: 10.5281/zenodo.19056919",
    "contact_line": "omnixquantum.net   |   contacto@omnixquantum.net",
    "tagline": "Decision Governance Infrastructure",

    # ── Page 1 ──
    "problem_label": "THE PROBLEM",
    "problem_headline": "When automated systems fail,\nthey fail at machine speed.",
    "problem_body": (
        "Most governance controls -- audits, compliance reviews, risk alerts -- "
        "are applied after execution. By the time a human intervenes, "
        "the automated system has already produced its outcome."
    ),
    "case_label1": "Terra Luna",  "case_val1": "$40B lost",  "case_sub1": "in 72 hours, May 2022",
    "case_label2": "SVB",         "case_val2": "$42B withdrawn", "case_sub2": "in one day, March 2023",
    "case_label3": "Knight Capital","case_val3": "$440M lost", "case_sub3": "in 45 minutes, Aug 2012",

    "solution_label": "THE SOLUTION",
    "solution_headline": "Governance at the execution boundary -- not after.",
    "solution_body": (
        "OMNIX is a Decision Governance Infrastructure that validates every automated "
        "decision through an 8-checkpoint veto pipeline before it is committed. "
        "If a decision does not pass, it is blocked. If it passes, it receives a "
        "cryptographically signed governance receipt -- independently verifiable by any party.\n\n"
        "This is not an advisory layer. It is a structural control embedded at the "
        "point of execution. Decisions that should not happen do not happen."
    ),

    "pipeline_label": "THE 8-CHECKPOINT PIPELINE",
    "pipeline_sub": "Every decision passes all 8 gates before execution -- in real time.",
    "checkpoints": [
        ("01", "Signal Integrity Validation",   "Is the input signal coherent and within expected bounds?"),
        ("02", "Regime Assessment",             "Is the current operational regime appropriate for this action?"),
        ("03", "Monte Carlo VETO Engine",       "Does the probability distribution of outcomes support execution?"),
        ("04", "Black Swan Detector",           "Are tail-risk or extreme-event conditions present?"),
        ("05", "Coherence Engine  (6 tiers)",   "Is there internal consistency across all input signals?"),
        ("06", "Risk Management System",        "Does the action satisfy all portfolio risk constraints?"),
        ("07", "Kelly Criterion Sizing",        "Is the proposed position size within calibrated safe bounds?"),
        ("08", "Final Authorization",           "All gates passed -- governance receipt generated and signed."),
    ],
    "receipt_note": (
        "Every approved decision generates a PQC-signed receipt verifiable at "
        "omnixquantum.net/r/{receipt_id}"
    ),

    "sandbox_label":   "TRY IT RIGHT NOW -- NO LOGIN REQUIRED",
    "sandbox_url":     "omnixquantum.net/try",
    "sandbox_desc": (
        "Type any decision scenario in plain language. Our AI converts it into 8 governance "
        "signals and runs them through the real OMNIX pipeline in under 2 seconds. "
        "You receive a live, cryptographically signed governance receipt -- the same one "
        "produced in production."
    ),
    "sandbox_cta":     "See the governance engine in action before any conversation.",

    # ── Page 2 ──
    "evidence_label": "PRODUCTION EVIDENCE",
    "stats": [
        ("72,443",  "governance decisions\nprocessed in production"),
        ("100%",    "post-quantum signed\n(NIST-standardized)"),
        ("0",       "approved without passing\nall 8 checkpoints"),
    ],
    "evidence_note": (
        "Full dataset: Zenodo DOI 10.5281/zenodo.19056919   "
        "|   Academic preprint: SSRN 6321298 (under peer review)"
    ),

    "regs_label": "WHY NOW  --  REGULATORY PRESSURE",
    "regs": [
        ("EU AI Act (2025+)",      "High-risk AI systems require pre-execution auditability and full traceability."),
        ("MiCA (2024-2025)",       "Crypto service providers must demonstrate documented operational risk controls."),
        ("BCB Resolution 538",    "Brazil mandates cryptographic audit trails for all automated financial decisions."),
        ("ADGM / SEC frameworks", "Governance-by-design is emerging as the compliance baseline for AI in finance."),
    ],

    "offer_label": "THE 30-DAY PILOT  --  NO COST",
    "offer_intro": "We are onboarding the first pilot partners now. No fee, no commitment.",
    "terms": [
        ("What you provide",  "Your decision signals via API or JSON  |  Your risk thresholds  |  30-min onboarding call"),
        ("What you receive",  "Signed receipt per decision  |  Full audit trail  |  Day-30 governance report"),
        ("Duration",          "30 days from integration date"),
        ("Cost",              "Complimentary -- no charge"),
        ("After the pilot",   "No obligation. If there is a fit, we discuss a commercial arrangement."),
    ],

    "cta_label":  "READY TO START?",
    "cta_body":   "Reach out and we will walk you through the integration in 30 minutes.",
    "contact": [
        ("Email",     "contacto@omnixquantum.net"),
        ("WhatsApp",  "+1 (650) 481-5494"),
        ("Live demo", "omnixquantum.net/try   (no login required)"),
        ("LinkedIn",  "linkedin.com/in/harold-nunes"),
    ],
},

"ES": {
    "footer": "Confidencial  --  Propuesta Programa Piloto   |   Harold Nunes, Fundador y CEO   |   SSRN 6321298   |   Zenodo DOI: 10.5281/zenodo.19056919",
    "contact_line": "omnixquantum.net   |   contacto@omnixquantum.net",
    "tagline": "Infraestructura de Gobernanza de Decisiones",

    "problem_label": "EL PROBLEMA",
    "problem_headline": "Cuando un sistema automatizado falla,\nfalla a velocidad de maquina.",
    "problem_body": (
        "La mayoria de los controles de gobernanza -- auditorias, revisiones de cumplimiento, "
        "alertas de riesgo -- se aplican despues de la ejecucion. Para cuando un humano "
        "puede intervenir, el sistema ya produjo su resultado."
    ),
    "case_label1": "Terra Luna",  "case_val1": "$40B perdidos",  "case_sub1": "en 72 horas, mayo 2022",
    "case_label2": "SVB",         "case_val2": "$42B retirados", "case_sub2": "en un dia, marzo 2023",
    "case_label3": "Knight Capital","case_val3": "$440M perdidos","case_sub3": "en 45 minutos, ago 2012",

    "solution_label": "LA SOLUCION",
    "solution_headline": "Gobernanza en la frontera de ejecucion -- no despues.",
    "solution_body": (
        "OMNIX es una Infraestructura de Gobernanza de Decisiones que valida cada decision "
        "automatizada a traves de un pipeline de veto de 8 puntos de control antes de "
        "ejecutarse. Si una decision no pasa, se bloquea. Si pasa, recibe un recibo de "
        "gobernanza firmado criptograficamente -- verificable de forma independiente.\n\n"
        "Esto no es una capa de advertencia. Es un control estructural embebido en el "
        "punto de ejecucion. Las decisiones que no deben ocurrir, no ocurren."
    ),

    "pipeline_label": "EL PIPELINE DE 8 PUNTOS DE CONTROL",
    "pipeline_sub": "Cada decision pasa los 8 controles antes de ejecutarse -- en tiempo real.",
    "checkpoints": [
        ("01", "Validacion de Integridad de Senal",  "La senal de entrada es coherente y esta dentro de limites?"),
        ("02", "Evaluacion de Regimen",              "El regimen operativo actual es apropiado para esta accion?"),
        ("03", "Motor de VETO Monte Carlo",          "La distribucion de probabilidad de resultados soporta la ejecucion?"),
        ("04", "Detector de Cisne Negro",            "Hay condiciones de riesgo extremo o de cola?"),
        ("05", "Motor de Coherencia  (6 capas)",     "Hay consistencia interna entre todas las senales de entrada?"),
        ("06", "Sistema de Gestion de Riesgo",       "La accion satisface todas las restricciones de riesgo?"),
        ("07", "Tamano por Criterio de Kelly",       "El tamano propuesto esta dentro de los limites calibrados?"),
        ("08", "Autorizacion Final",                 "Todos los controles pasados -- recibo de gobernanza generado."),
    ],
    "receipt_note": (
        "Cada decision aprobada genera un recibo firmado con PQC, verificable en "
        "omnixquantum.net/r/{receipt_id}"
    ),

    "sandbox_label":   "PRUEBALO AHORA -- SIN LOGIN, SIN REGISTRO",
    "sandbox_url":     "omnixquantum.net/try",
    "sandbox_desc": (
        "Escribe cualquier escenario de decision en lenguaje natural. Nuestra IA lo convierte "
        "en 8 senales de gobernanza y las pasa por el pipeline REAL de OMNIX en menos de "
        "2 segundos. Recibes un recibo de gobernanza firmado criptograficamente en vivo -- "
        "el mismo que se produce en produccion."
    ),
    "sandbox_cta":     "Ve el motor de gobernanza en accion antes de cualquier conversacion.",

    "evidence_label": "EVIDENCIA EN PRODUCCION",
    "stats": [
        ("72,443",  "decisiones de gobernanza\nprocesadas en produccion"),
        ("100%",    "firmadas post-cuanticas\n(estandar NIST)"),
        ("0",       "aprobadas sin pasar\nlos 8 puntos de control"),
    ],
    "evidence_note": (
        "Dataset publico: Zenodo DOI 10.5281/zenodo.19056919   "
        "|   Preprint: SSRN 6321298 (en revision por pares)"
    ),

    "regs_label": "POR QUE AHORA  --  PRESION REGULATORIA",
    "regs": [
        ("EU AI Act (2025+)",      "Los sistemas de IA de alto riesgo requieren auditabilidad previa a la ejecucion."),
        ("MiCA (2024-2025)",       "Los proveedores de criptoactivos deben demostrar controles de riesgo operativo."),
        ("BCB Resolucion 538",    "Brasil exige trazabilidad criptografica para todas las decisiones automatizadas."),
        ("ADGM / SEC frameworks", "La gobernanza por diseno es el estandar emergente para IA en finanzas."),
    ],

    "offer_label": "EL PILOTO DE 30 DIAS  --  SIN COSTO",
    "offer_intro": "Estamos incorporando los primeros socios piloto ahora. Sin costo, sin compromiso.",
    "terms": [
        ("Lo que aportas",   "Senales de decision via API o JSON  |  Tus umbrales de riesgo  |  Llamada de onboarding 30 min"),
        ("Lo que recibes",   "Recibo firmado por decision  |  Auditoria completa  |  Reporte de gobernanza al Dia 30"),
        ("Duracion",         "30 dias desde la fecha de integracion"),
        ("Costo",            "Gratuito -- sin cargo"),
        ("Despues del piloto","Sin obligacion. Si hay encaje, conversamos sobre un acuerdo comercial."),
    ],

    "cta_label":  "LISTO PARA COMENZAR?",
    "cta_body":   "Escribenos y coordinamos la integracion en una reunion de 30 minutos.",
    "contact": [
        ("Email",    "contacto@omnixquantum.net"),
        ("WhatsApp", "+1 (650) 481-5494"),
        ("Demo",     "omnixquantum.net/try   (sin login)"),
        ("LinkedIn", "linkedin.com/in/harold-nunes"),
    ],
},
}

# ── PDF CLASS ─────────────────────────────────────────────────────────────────
class PilotPDF(FPDF):
    def __init__(self, lang="EN"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.c = CONTENT[lang]
        self.add_font("R", fname=FONT_REGULAR)
        self.add_font("B", fname=FONT_BOLD)
        self.set_margins(LMARGIN, TOP_M, RMARGIN)
        self.set_auto_page_break(auto=True, margin=22)

    @property
    def usable_w(self):
        return self.w - LMARGIN - RMARGIN

    def header(self):
        c = self.c
        # Navy background
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, HEADER_H, style="F")
        # Gold bottom line
        self.set_fill_color(*GOLD)
        self.rect(0, HEADER_H - 0.8, self.w, 0.8, style="F")

        # Logo (only icon, left side) — include full image at constrained height
        logo_h = HEADER_H - 4
        logo_x = 5
        logo_y = 2
        if os.path.exists(LOGO_PATH):
            # Use width constraint to show only icon part (logo is ~square icon + text)
            # Setting w to same as h shows the square portion cleanly
            self.image(LOGO_PATH, x=logo_x, y=logo_y, w=logo_h, h=logo_h)

        # Right side text — no "OMNIX QUANTUM" since logo has it
        tx = logo_x + logo_h + 5
        tw = self.w - tx - 6

        self.set_xy(tx, 6)
        self.set_font("B", size=9)
        self.set_text_color(*GOLD)
        self.cell(tw, 5, c["tagline"])

        self.set_xy(tx, 13)
        self.set_font("R", size=7)
        self.set_text_color(160, 175, 205)
        self.cell(tw, 4, c["contact_line"])

    def footer(self):
        c = self.c
        self.set_draw_color(*GOLD)
        self.set_line_width(0.3)
        self.line(0, self.h - 11, self.w, self.h - 11)
        self.set_fill_color(*NAVY)
        self.rect(0, self.h - 10.5, self.w, 11, style="F")
        self.set_y(self.h - 8)
        self.set_font("R", size=5.8)
        self.set_text_color(*GOLD)
        self.cell(self.w, 4, c["footer"], align="C")

    # ── Drawing Helpers ───────────────────────────────────────────────────────

    def label_tag(self, text):
        """Small all-caps gold label tag above a section."""
        self.set_x(LMARGIN)
        self.set_font("B", size=7.5)
        self.set_text_color(*GOLD)
        self.cell(0, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def large_headline(self, text, size=16):
        self.set_x(LMARGIN)
        self.set_font("B", size=size)
        self.set_text_color(*NAVY)
        self.multi_cell(self.usable_w, size * 0.65, text)
        self.ln(2)

    def body_text(self, text, size=9, color=DARK, indent=0):
        self.set_x(LMARGIN + indent)
        self.set_font("R", size=size)
        self.set_text_color(*color)
        self.multi_cell(self.usable_w - indent, 5.3, text)
        self.ln(1)

    def gap(self, h=3):
        self.ln(h)

    def rule(self, color=BORDER, thickness=0.2):
        self.set_draw_color(*color)
        self.set_line_width(thickness)
        self.line(LMARGIN, self.get_y(), self.w - RMARGIN, self.get_y())
        self.ln(4)

    def gold_rule(self):
        self.rule(GOLD, 0.4)

    # ── Problem section ───────────────────────────────────────────────────────

    def problem_block(self):
        c = self.c
        # Dark full-width hero block
        bh = 52
        bx = 0
        by = self.get_y() - 2
        self.set_fill_color(*NAVY)
        self.rect(bx, by, self.w, bh, style="F")
        # Gold left stripe
        self.set_fill_color(*GOLD)
        self.rect(bx, by, 3.5, bh, style="F")

        # Label
        self.set_xy(LMARGIN + 2, by + 5)
        self.set_font("B", size=7.5)
        self.set_text_color(*GOLD)
        self.cell(0, 5, c["problem_label"])

        # Headline
        self.set_xy(LMARGIN + 2, by + 12)
        self.set_font("B", size=14)
        self.set_text_color(*WHITE)
        self.multi_cell(self.usable_w - 4, 8, c["problem_headline"])

        # Body
        self.set_x(LMARGIN + 2)
        self.set_font("R", size=8.5)
        self.set_text_color(185, 198, 225)
        self.multi_cell(self.usable_w - 4, 5, c["problem_body"])

        # Case examples — 3 columns inside the block
        cases = [
            (c["case_label1"], c["case_val1"], c["case_sub1"]),
            (c["case_label2"], c["case_val2"], c["case_sub2"]),
            (c["case_label3"], c["case_val3"], c["case_sub3"]),
        ]
        col_w = self.usable_w / 3
        case_y = by + bh - 18
        for i, (lbl, val, sub) in enumerate(cases):
            cx = LMARGIN + i * col_w + 2
            # Divider line between cases
            if i > 0:
                self.set_draw_color(*NAVY_LIGHT)
                self.set_line_width(0.2)
                self.line(LMARGIN + i * col_w, case_y, LMARGIN + i * col_w, by + bh - 2)
            self.set_xy(cx, case_y)
            self.set_font("B", size=7)
            self.set_text_color(*GOLD_LIGHT)
            self.cell(col_w, 4, lbl)
            self.set_xy(cx, case_y + 4)
            self.set_font("B", size=10)
            self.set_text_color(*WHITE)
            self.cell(col_w, 6, val)
            self.set_xy(cx, case_y + 10)
            self.set_font("R", size=7)
            self.set_text_color(160, 175, 205)
            self.cell(col_w, 4, sub)

        self.set_y(by + bh + 4)

    # ── Solution section ──────────────────────────────────────────────────────

    def solution_block(self):
        c = self.c
        self.label_tag(c["solution_label"])
        self.large_headline(c["solution_headline"], size=13)
        self.body_text(c["solution_body"])
        self.gap(2)

    # ── Pipeline ─────────────────────────────────────────────────────────────

    def pipeline_block(self):
        c = self.c
        self.label_tag(c["pipeline_label"])
        self.set_x(LMARGIN)
        self.set_font("R", size=8.5)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, c["pipeline_sub"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.gap(2)

        w_no = 10
        w_nm = 65
        w_ds = self.usable_w - w_no - w_nm
        row_h = 6.5

        for i, (num, name, desc) in enumerate(c["checkpoints"]):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            self.set_x(LMARGIN)
            # Number
            self.set_font("B", size=8)
            self.set_text_color(*GOLD)
            self.cell(w_no, row_h, num, fill=True)
            # Name
            self.set_font("B", size=8.5)
            self.set_text_color(*NAVY)
            self.cell(w_nm, row_h, name, fill=True)
            # Description
            self.set_font("R", size=8.5)
            self.set_text_color(*DARK)
            self.cell(w_ds, row_h, desc, fill=True,
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.gap(3)
        # Receipt note
        self.set_fill_color(*BLUE_BG)
        self.set_x(LMARGIN)
        self.set_font("R", size=8.5)
        self.set_text_color(*BLUE_TXT)
        self.multi_cell(self.usable_w, 5.5, f"  {c['receipt_note']}  ", fill=True)
        self.gap(2)

    # ── Sandbox callout ───────────────────────────────────────────────────────

    def sandbox_block(self):
        c = self.c
        bh = 36
        by = self.get_y()
        bx = LMARGIN
        bw = self.usable_w

        # Dark navy background with gold left stripe
        self.set_fill_color(*NAVY)
        self.rect(bx, by, bw, bh, style="F")
        self.set_fill_color(*GOLD)
        self.rect(bx, by, 3, bh, style="F")
        # Subtle top gold rule
        self.rect(bx, by, bw, 0.8, style="F")

        # Label tag
        self.set_xy(bx + 7, by + 5)
        self.set_font("B", size=7.5)
        self.set_text_color(*GOLD)
        self.cell(bw - 10, 5, c["sandbox_label"],
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Big URL
        self.set_xy(bx + 7, by + 11)
        self.set_font("B", size=14)
        self.set_text_color(*WHITE)
        self.cell(bw - 10, 8, c["sandbox_url"],
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Description
        self.set_xy(bx + 7, by + 20)
        self.set_font("R", size=8)
        self.set_text_color(185, 198, 225)
        self.multi_cell(bw - 12, 4.8, c["sandbox_desc"])

        # CTA italic line at bottom
        self.set_xy(bx + 7, by + bh - 7)
        self.set_font("B", size=8)
        self.set_text_color(*GOLD_LIGHT)
        self.cell(bw - 10, 5, c["sandbox_cta"])

        self.set_y(by + bh + 4)

    # ── Evidence / Stats ──────────────────────────────────────────────────────

    def evidence_block(self):
        c = self.c
        self.label_tag(c["evidence_label"])
        self.gap(1)

        col_w = self.usable_w / 3
        stat_y = self.get_y()
        for i, (val, desc) in enumerate(c["stats"]):
            cx = LMARGIN + i * col_w
            # Background card
            self.set_fill_color(*LIGHT_BG)
            self.rect(cx, stat_y, col_w - 2, 24, style="F")
            # Gold top bar
            self.set_fill_color(*GOLD)
            self.rect(cx, stat_y, col_w - 2, 1.5, style="F")
            # Value
            self.set_xy(cx + 4, stat_y + 4)
            self.set_font("B", size=18)
            self.set_text_color(*NAVY)
            self.cell(col_w - 8, 12, val)
            # Description
            self.set_xy(cx + 4, stat_y + 14)
            self.set_font("R", size=7.5)
            self.set_text_color(*MID_GRAY)
            self.multi_cell(col_w - 8, 4.5, desc)

        self.set_y(stat_y + 26)
        # Dataset note
        self.set_fill_color(*GREEN_BG)
        self.set_x(LMARGIN)
        self.set_font("R", size=8)
        self.set_text_color(*GREEN_TXT)
        self.multi_cell(self.usable_w, 5.5, f"  {c['evidence_note']}  ", fill=True)
        self.gap(4)
        self.rule()

    # ── Regulatory ────────────────────────────────────────────────────────────

    def regs_block(self):
        c = self.c
        self.label_tag(c["regs_label"])
        self.gap(1)
        w_label = 50
        w_desc  = self.usable_w - w_label
        for i, (reg, desc) in enumerate(c["regs"]):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            self.set_x(LMARGIN)
            self.set_font("B", size=8.5)
            self.set_text_color(*NAVY)
            self.cell(w_label, 7, f"  {reg}", fill=True)
            self.set_font("R", size=8.5)
            self.set_text_color(*DARK)
            self.multi_cell(w_desc, 7, f"  {desc}", fill=True)
        self.gap(4)
        self.rule()

    # ── Offer / Terms ─────────────────────────────────────────────────────────

    def offer_block(self):
        c = self.c
        self.label_tag(c["offer_label"])
        self.set_x(LMARGIN)
        self.set_font("R", size=8.5)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, c["offer_intro"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.gap(2)

        w_label = 42
        w_val   = self.usable_w - w_label
        for i, (label, val) in enumerate(c["terms"]):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            self.set_x(LMARGIN)
            self.set_font("B", size=8.5)
            self.set_text_color(*NAVY)
            self.cell(w_label, 7, f"  {label}:", fill=True)
            self.set_font("R", size=8.5)
            self.set_text_color(*DARK)
            self.multi_cell(w_val, 7, f"  {val}", fill=True)
        self.gap(5)

    # ── CTA ───────────────────────────────────────────────────────────────────

    def cta_block(self):
        c = self.c
        bh = 30 + len(c["contact"]) * 7
        by = self.get_y()
        # Navy block
        self.set_fill_color(*NAVY)
        self.rect(LMARGIN, by, self.usable_w, bh, style="F")
        # Gold left bar
        self.set_fill_color(*GOLD)
        self.rect(LMARGIN, by, 3, bh, style="F")
        # Gold top line
        self.rect(LMARGIN, by, self.usable_w, 0.8, style="F")

        # Label
        self.set_xy(LMARGIN + 7, by + 5)
        self.set_font("B", size=8)
        self.set_text_color(*GOLD)
        self.cell(0, 5, c["cta_label"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Headline
        self.set_x(LMARGIN + 7)
        self.set_font("B", size=11)
        self.set_text_color(*WHITE)
        self.cell(self.usable_w - 10, 7, c["cta_body"],
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.gap(2)

        # Contact rows
        for label, val in c["contact"]:
            self.set_x(LMARGIN + 7)
            self.set_font("B", size=8.5)
            self.set_text_color(*GOLD_LIGHT)
            self.cell(26, 6.5, f"{label}:")
            self.set_font("R", size=8.5)
            self.set_text_color(*WHITE)
            self.cell(0, 6.5, val, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── Page builders ─────────────────────────────────────────────────────────

    def build_page_one(self):
        self.add_page()
        self.problem_block()
        self.solution_block()
        self.gold_rule()
        self.pipeline_block()
        self.sandbox_block()

    def build_page_two(self):
        self.add_page()
        self.ln(2)
        self.evidence_block()
        self.regs_block()
        self.offer_block()
        self.cta_block()


# ── MAIN ──────────────────────────────────────────────────────────────────────

def generate_lang(lang, filename):
    pdf = PilotPDF(lang=lang)
    pdf.build_page_one()
    pdf.build_page_two()
    out = os.path.join(OUTPUT_DIR, filename)
    pdf.output(out)
    size_kb = os.path.getsize(out) / 1024
    print(f"[{lang}] {out}  ({size_kb:.1f} KB)")


def generate():
    generate_lang("EN", "OMNIX_Pilot_Proposal_EN.pdf")
    generate_lang("ES", "OMNIX_Pilot_Proposal_ES.pdf")
    print("Done.")


if __name__ == "__main__":
    generate()
