#!/usr/bin/env python3
"""
OMNIX Pilot Proposal  —  4 pages, fixed layout, zero overflow.
Page 1: Problem + Solution
Page 2: 8-Checkpoint Pipeline + Sandbox
Page 3: Evidence + Regulatory
Page 4: Pilot Terms + CTA
"""
import os
from fpdf import FPDF

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "business", "pdfs")
LOGO_PATH  = os.path.join(BASE_DIR, "docs", "business", "omnix_logo.png")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_DIR = os.path.join(
    os.path.expanduser("~"),
    "workspace/.pythonlibs/lib/python3.11/site-packages/kaleido/executable/xdg/fonts/truetype/dejavu"
)
FONT_R = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

# ── Palette ────────────────────────────────────────────────────────────────────
NAVY     = (8,  22,  58)
GOLD     = (212, 175, 55)
GOLD_LT  = (245, 232, 170)
WHITE    = (255, 255, 255)
LIGHT_BG = (243, 246, 254)
MID_GRAY = (115, 128, 155)
DARK     = (28,  36,  70)
GREEN_BG = (234, 250, 241)
GREEN_TX = (0,  108,  60)
BLUE_BG  = (233, 242, 255)
BLUE_TX  = (12,  52, 130)

PW  = 210        # A4 width
PH  = 297        # A4 height
LM  = 18         # left margin
RM  = 18         # right margin
UW  = PW-LM-RM  # usable width = 174 mm
HDR = 26         # header height
FTR = 12         # footer height
T0  = HDR + 7   # first content Y  (33 mm)
BOT = PH - FTR  # last safe Y      (285 mm)

# ── CONTENT ────────────────────────────────────────────────────────────────────
DATA = {
"EN": {
    "tagline"   : "Decision Governance Infrastructure",
    "contact"   : "omnixquantum.net   |   contacto@omnixquantum.net",
    "footer"    : "Confidential  |  Pilot Program Proposal  |  Harold Nunes, Founder & CEO  |  Zenodo 10.5281/zenodo.19056919  |  SSRN 6321298",
    "pages"     : 4,

    # ── PAGE 1 ───────────────────────────────────────────────────────────────
    "pb_tag"    : "THE PROBLEM",
    "pb_h1"     : "When automated systems fail,\nthey fail at machine speed.",
    "pb_body"   : "Most governance controls — audits, compliance reviews, risk alerts — are applied after execution. By the time a human can intervene, the outcome has already been produced. In high-stakes environments, that is already too late.",
    "pb_sub"    : "Real examples of governance failure in automated systems:",
    "pb_cases"  : [
        ("Terra Luna",     "$40 billion",   "lost in 72 hours",   "May 2022 — algorithmic depegging cascade with no execution controls to halt the process."),
        ("SVB",            "$42 billion",   "withdrawn in 1 day", "March 2023 — automated sell signals fired before any governance layer could respond."),
        ("Knight Capital", "$440 million",  "lost in 45 min",     "August 2012 — a single misconfigured automated system executed unchecked for 45 minutes."),
    ],
    "pb_close"  : "In each case the system operated exactly as programmed. The failure was the absence of a governance layer that could stop it.",

    "sl_tag"    : "THE SOLUTION",
    "sl_h2"     : "Governance at the execution boundary — not after.",
    "sl_body"   : "OMNIX is a Decision Governance Infrastructure. It sits between an automated system and its execution environment, validating every decision before it is committed. If a decision does not pass, it is blocked. If it passes, it receives a cryptographically signed governance receipt.",
    "sl_props"  : [
        ("Pre-execution validation",   "Every decision is assessed before it is committed — not reviewed after the fact."),
        ("Cryptographic audit trail",  "Every outcome — approved or blocked — is PQC-signed and hash-chained for independent verification."),
        ("Domain-agnostic",            "Designed for trading, credit, insurance, logistics, and healthcare AI — any automated decision system."),
        ("Fail-closed by design",      "If the governance engine is unavailable, no decision passes. The system halts — it does not bypass."),
    ],

    # ── PAGE 2 ───────────────────────────────────────────────────────────────
    "pp_tag"    : "THE 8-CHECKPOINT GOVERNANCE PIPELINE",
    "pp_intro"  : "Every decision passes through all 8 checkpoints in sequence, in real time, before authorization. One failed checkpoint blocks the decision. No exceptions, no overrides.",
    "pp_rows"   : [
        ("01", "Signal Integrity Validation",  "Verifies the input is coherent and within operational bounds. Malformed inputs are rejected before entering the pipeline."),
        ("02", "Regime Assessment",            "Evaluates the current operational regime to determine whether it supports the proposed decision type."),
        ("03", "Monte Carlo VETO Engine",      "Runs probabilistic simulations on the outcome distribution. If expected value does not justify the action, a veto is issued."),
        ("04", "Black Swan Detector",          "Scans for tail-risk conditions and extreme-event patterns. High-risk environments trigger automatic holds."),
        ("05", "Coherence Engine  (6 tiers)",  "Measures internal consistency across all input signals. Contradictory signals — even individually valid — can produce a hold."),
        ("06", "Risk Management System",       "Enforces portfolio-level and position-level risk constraints. Decisions exceeding configured thresholds are blocked."),
        ("07", "Kelly Criterion Sizing",       "Validates that the proposed action size is within mathematically calibrated safe bounds given current exposure."),
        ("08", "Final Authorization",          "All 7 prior checkpoints passed. Decision authorized. A PQC-signed receipt is generated and appended to the immutable audit chain."),
    ],
    "pp_note"   : "Every authorized decision produces a verifiable receipt at  omnixquantum.net/r/{receipt_id}",

    "sb_tag"    : "TRY THE LIVE GOVERNANCE ENGINE  —  NO LOGIN REQUIRED",
    "sb_url"    : "omnixquantum.net/try",
    "sb_body1"  : "The OMNIX Public Governance Sandbox is open to anyone, right now. Describe any decision scenario in plain language — a trading position, a credit application, an operational risk scenario.",
    "sb_body2"  : "Our AI interprets it into 8 governance signals and runs them through the real production pipeline. In under 2 seconds you receive a live, PQC-signed governance receipt — the same artifact produced in production. No account. No demo mode. The real engine.",
    "sb_cta"    : "See what OMNIX actually does before any conversation.",

    # ── PAGE 3 ───────────────────────────────────────────────────────────────
    "ev_tag"    : "PRODUCTION EVIDENCE",
    "ev_stats"  : [
        ("72,443",  "Governance decisions\nin production",     "Feb 21 – Mar 16, 2026"),
        ("100%",    "Post-quantum signed\n(NIST ML-DSA-65)",  "Every single receipt"),
        ("0",       "Decisions approved\nwithout all 8 gates","No exceptions. Ever."),
    ],
    "ev_pub"    : "Full dataset: Zenodo DOI 10.5281/zenodo.19056919   |   Academic preprint: SSRN 6321298  (under peer review)",

    "rg_tag"    : "WHY NOW — REGULATORY PRESSURE",
    "rg_intro"  : "Global regulators are making governance infrastructure mandatory.",
    "rg_rows"   : [
        ("EU AI Act",     "High-risk AI systems require pre-execution auditability, traceability, and documented risk controls."),
        ("MiCA",          "Crypto asset service providers must demonstrate documented operational risk controls and governance frameworks."),
        ("BCB Res. 538",  "Brazil's Central Bank mandates cryptographic audit trails for all automated financial decisions. 1,600+ institutions affected."),
        ("ADGM / SEC",    "Governance-by-design is the emerging compliance baseline for AI systems in finance globally."),
    ],

    # ── PAGE 4 ───────────────────────────────────────────────────────────────
    "tm_tag"    : "THE 30-DAY PILOT — NO COST, NO COMMITMENT",
    "tm_intro"  : "We are onboarding the first pilot partners now. The goal is to validate OMNIX across multiple industries with real decision data.",
    "tm_rows"   : [
        ("You provide",   "Decision signals via API or JSON  |  Risk thresholds  |  30-min onboarding call"),
        ("You receive",   "Signed receipt per decision  |  Full audit trail  |  Day-30 governance performance report"),
        ("Duration",      "30 days from integration date"),
        ("Cost",          "Complimentary — no charge"),
        ("Data handling", "All signals encrypted at rest (AES-256). No data shared between clients."),
        ("After pilot",   "No obligation. If there is mutual fit, we discuss a commercial arrangement."),
    ],

    "ct_tag"    : "LET'S CONNECT",
    "ct_body"   : "Reach out and we will walk you through the integration in 30 minutes.",
    "ct_items"  : [
        ("Email",     "contacto@omnixquantum.net"),
        ("WhatsApp",  "+1 (650) 481-5494"),
        ("Live demo", "omnixquantum.net/try   (no login required)"),
        ("LinkedIn",  "linkedin.com/in/harold-nunes"),
    ],
},
"ES": {
    "tagline"   : "Infraestructura de Gobernanza de Decisiones",
    "contact"   : "omnixquantum.net   |   contacto@omnixquantum.net",
    "footer"    : "Confidencial  |  Propuesta Programa Piloto  |  Harold Nunes, Fundador y CEO  |  Zenodo 10.5281/zenodo.19056919  |  SSRN 6321298",
    "pages"     : 4,

    "pb_tag"    : "EL PROBLEMA",
    "pb_h1"     : "Cuando un sistema automatizado falla,\nfalla a velocidad de maquina.",
    "pb_body"   : "La mayoria de los controles de gobernanza — auditorias, revisiones de cumplimiento, alertas de riesgo — se aplican despues de la ejecucion. Para cuando un humano puede intervenir, el resultado ya fue producido. En entornos de alto riesgo, ya es demasiado tarde.",
    "pb_sub"    : "Ejemplos reales de falla de gobernanza en sistemas automatizados:",
    "pb_cases"  : [
        ("Terra Luna",     "$40 mil millones", "perdidos en 72 horas",  "Mayo 2022 — cascada algoritmica de desviculacion sin controles de ejecucion para detenerlo."),
        ("SVB",            "$42 mil millones", "retirados en 1 dia",    "Marzo 2023 — senales de venta automatizadas activadas antes de que la gobernanza pudiera responder."),
        ("Knight Capital", "$440 millones",    "perdidos en 45 min",    "Agosto 2012 — un sistema mal configurado opero sin controles durante 45 minutos."),
    ],
    "pb_close"  : "En cada caso el sistema opero exactamente como fue programado. La falla fue la ausencia de una capa de gobernanza capaz de detenerlo.",

    "sl_tag"    : "LA SOLUCION",
    "sl_h2"     : "Gobernanza en la frontera de ejecucion — no despues.",
    "sl_body"   : "OMNIX es una Infraestructura de Gobernanza de Decisiones. Se ubica entre un sistema automatizado y su entorno de ejecucion, validando cada decision antes de que se confirme. Si no pasa todos los controles, se bloquea. Si pasa, recibe un recibo de gobernanza firmado criptograficamente.",
    "sl_props"  : [
        ("Validacion previa a la ejecucion", "Cada decision se evalua antes de confirmarse, no se revisa despues del hecho."),
        ("Auditoria criptografica",           "Cada resultado — aprobado o bloqueado — firmado con PQC y encadenado en hash para verificacion independiente."),
        ("Agn\u00f3stico al dominio",             "Para trading, cr\u00e9dito, seguros, log\u00edstica e IA en salud \u2014 cualquier sistema de decisi\u00f3n automatizada."),
        ("Fail-closed por diseno",            "Si el motor no esta disponible, ninguna decision pasa. El sistema se detiene, no evade el control."),
    ],

    "pp_tag"    : "EL PIPELINE DE GOBERNANZA DE 8 PUNTOS DE CONTROL",
    "pp_intro"  : "Cada decision pasa por los 8 puntos de control en secuencia, en tiempo real, antes de ser autorizada. Un punto fallido bloquea la decision. Sin excepciones ni anulaciones.",
    "pp_rows"   : [
        ("01", "Validacion de Integridad de Senal",  "Verifica que la entrada sea coherente y este dentro de los limites operativos. Entradas anomalas se rechazan antes del pipeline."),
        ("02", "Evaluacion de Regimen",              "Evalua el regimen operativo actual para determinar si soporta el tipo de decision propuesta."),
        ("03", "Motor de VETO Monte Carlo",          "Ejecuta simulaciones probabilisticas sobre la distribucion de resultados. Si el valor esperado no justifica la accion, se emite veto."),
        ("04", "Detector de Cisne Negro",            "Analiza condiciones de riesgo de cola y patrones de eventos extremos. Entornos de alto riesgo activan paradas automaticas."),
        ("05", "Motor de Coherencia  (6 capas)",     "Mide consistencia interna entre todas las senales. Senales contradictorias — incluso individualmente validas — pueden generar parada."),
        ("06", "Sistema de Gestion de Riesgo",       "Aplica restricciones de riesgo a nivel de portafolio y posicion. Superar los umbrales configurados bloquea la decision."),
        ("07", "Tamano por Criterio de Kelly",       "Valida que el tamano de accion este dentro de los limites seguros calibrados matematicamente segun la exposicion actual."),
        ("08", "Autorizacion Final",                 "Los 7 puntos anteriores pasados. Decision autorizada. Se genera un recibo firmado PQC, anexado a la cadena de auditoria inmutable."),
    ],
    "pp_note"   : "Cada decision autorizada produce un recibo verificable en  omnixquantum.net/r/{receipt_id}",

    "sb_tag"    : "PRUEBA EL MOTOR EN VIVO  —  SIN LOGIN",
    "sb_url"    : "omnixquantum.net/try",
    "sb_body1"  : "El Sandbox Publico de OMNIX esta disponible para cualquiera, ahora mismo. Describe cualquier escenario en lenguaje natural — una posicion de trading, una solicitud de credito, un escenario de riesgo operativo.",
    "sb_body2"  : "Nuestra IA lo interpreta en 8 senales de gobernanza y las pasa por el pipeline de produccion real. En menos de 2 segundos recibes un recibo firmado PQC en vivo — el mismo artefacto de produccion. Sin cuenta. Sin modo demo. El motor real.",
    "sb_cta"    : "Ve lo que OMNIX realmente hace antes de cualquier conversacion.",

    "ev_tag"    : "EVIDENCIA EN PRODUCCION",
    "ev_stats"  : [
        ("72,443",  "Decisiones de gobernanza\nen produccion",     "21 Feb – 16 Mar 2026"),
        ("100%",    "Firmadas post-cuanticas\n(NIST ML-DSA-65)",  "Cada recibo, sin excepcion"),
        ("0",       "Decisiones aprobadas\nsin los 8 controles",  "Sin excepciones. Nunca."),
    ],
    "ev_pub"    : "Dataset completo: Zenodo DOI 10.5281/zenodo.19056919   |   Preprint academico: SSRN 6321298  (en revision por pares)",

    "rg_tag"    : "POR QUE AHORA — PRESION REGULATORIA",
    "rg_intro"  : "Los reguladores globales estan haciendo obligatoria la infraestructura de gobernanza.",
    "rg_rows"   : [
        ("EU AI Act",     "Los sistemas de IA de alto riesgo requieren auditabilidad previa, trazabilidad y controles de riesgo documentados."),
        ("MiCA",          "Los proveedores de criptoactivos deben demostrar controles de riesgo operativo y marcos de gobernanza documentados."),
        ("BCB Res. 538",  "El Banco Central de Brasil exige trazabilidad criptografica para decisiones financieras automatizadas. +1,600 instituciones."),
        ("ADGM / SEC",    "La gobernanza por diseno es el estandar de cumplimiento emergente para sistemas de IA en finanzas a nivel global."),
    ],

    "tm_tag"    : "EL PILOTO DE 30 DIAS — SIN COSTO, SIN COMPROMISO",
    "tm_intro"  : "Estamos incorporando los primeros socios piloto ahora. El objetivo es validar OMNIX en multiples industrias con datos de decision reales.",
    "tm_rows"   : [
        ("Lo que aportas",   "Senales de decision via API o JSON  |  Umbrales de riesgo  |  Llamada de onboarding 30 min"),
        ("Lo que recibes",   "Recibo firmado por decision  |  Auditoria completa  |  Reporte de gobernanza al Dia 30"),
        ("Duracion",         "30 dias desde la fecha de integracion"),
        ("Costo",            "Gratuito"),
        ("Manejo de datos",  "Senales cifradas en reposo (AES-256). Sin datos compartidos entre clientes."),
        ("Despues del piloto","Sin obligacion. Si hay encaje mutuo, conversamos sobre un acuerdo comercial."),
    ],

    "ct_tag"    : "CONECTEMOS",
    "ct_body"   : "Escribenos y coordinamos la integracion en una reunion de 30 minutos.",
    "ct_items"  : [
        ("Email",    "contacto@omnixquantum.net"),
        ("WhatsApp", "+1 (650) 481-5494"),
        ("Demo",     "omnixquantum.net/try   (sin login)"),
        ("LinkedIn", "linkedin.com/in/harold-nunes"),
    ],
},
}

# ── PDF ────────────────────────────────────────────────────────────────────────
class PDF(FPDF):
    def __init__(self, lang):
        super().__init__("P", "mm", "A4")
        self.lang = lang
        self.d    = DATA[lang]
        self.add_font("R", fname=FONT_R)
        self.add_font("B", fname=FONT_B)
        self.set_margins(LM, 0, RM)
        self.set_auto_page_break(auto=False)

    # ── header / footer ────────────────────────────────────────────────────────
    def header(self):
        d = self.d
        self.set_fill_color(*NAVY);  self.rect(0, 0, PW, HDR, "F")
        self.set_fill_color(*GOLD);  self.rect(0, HDR-0.7, PW, 0.7, "F")
        lh = HDR - 6
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=5, y=3, w=lh, h=lh)
        tx = 5 + lh + 5
        self.set_xy(tx, 7);  self.set_font("B", size=9);  self.set_text_color(*GOLD)
        self.cell(PW-tx-40, 5, d["tagline"])
        self.set_xy(tx, 14); self.set_font("R", size=7);  self.set_text_color(155,170,205)
        self.cell(PW-tx-40, 4, d["contact"])
        self.set_xy(PW-36, 9); self.set_font("R", size=7); self.set_text_color(120,140,180)
        self.cell(30, 5, f"Page {self.page_no()} / {self.d['pages']}", align="R")

    def footer(self):
        self.set_fill_color(*NAVY); self.rect(0, PH-FTR, PW, FTR, "F")
        self.set_draw_color(*GOLD); self.set_line_width(0.3)
        self.line(0, PH-FTR, PW, PH-FTR)
        self.set_y(PH-FTR+3); self.set_font("R", size=5.5); self.set_text_color(*GOLD)
        self.cell(PW, 4, self.d["footer"], align="C")

    # ── primitives ─────────────────────────────────────────────────────────────
    def tag(self, y, text):
        self.set_xy(LM, y); self.set_font("B", size=7.5); self.set_text_color(*GOLD)
        self.cell(UW, 5, text)
        return y + 8

    def h1(self, y, text, size=19):
        lh = round(size * 0.62, 1)
        self.set_xy(LM, y); self.set_font("B", size=size); self.set_text_color(*NAVY)
        self.multi_cell(UW, lh, text)
        return self.get_y() + 3

    def body(self, y, text, size=9.2, color=DARK, w=None, lh=5.4):
        self.set_xy(LM, y); self.set_font("R", size=size); self.set_text_color(*color)
        self.multi_cell(w or UW, lh, text)
        return self.get_y() + 2

    def rule(self, y, color=GOLD, thick=0.4, gap=6):
        self.set_draw_color(*color); self.set_line_width(thick)
        self.line(LM, y, PW-RM, y)
        return y + gap

    def strip(self, y, text, bg, fg, h=9, size=8):
        self.set_fill_color(*bg); self.rect(LM, y, UW, h, "F")
        self.set_xy(LM+4, y+2); self.set_font("R", size=size); self.set_text_color(*fg)
        self.multi_cell(UW-6, 5, text)
        return y + h + 3

    def table_row(self, y, bg, lbl, val, w_l, size_v=8.2, lh_v=5.5):
        """Draw a 2-col table row sized to actual text height."""
        w_v = UW - w_l - 2
        # measure lines in right column
        self.set_font("R", size=size_v)
        cpl = max(1, int(w_v / (size_v * 0.43)))
        n = sum(
            max(1, -(-len(p) // cpl)) if p.strip() else 1
            for p in val.split("\n")
        )
        rh = max(10, n * lh_v + 5)
        # background
        self.set_fill_color(*bg); self.rect(LM, y, UW, rh, "F")
        # left label (vertically centered)
        cy = y + (rh - 6) / 2
        self.set_xy(LM+2, cy); self.set_font("B", size=8.5); self.set_text_color(*NAVY)
        self.cell(w_l, 6, lbl)
        # right value
        self.set_xy(LM+w_l, y+2); self.set_font("R", size=size_v); self.set_text_color(*DARK)
        self.multi_cell(w_v, lh_v, val)
        return y + rh + 1

    # ── PAGE 1 ─────────────────────────────────────────────────────────────────
    def page1(self):
        self.add_page(); d = self.d; y = T0

        y = self.tag(y, d["pb_tag"])
        y = self.h1(y, d["pb_h1"], size=19)
        y = self.body(y, d["pb_body"])
        y += 3

        # cases sub-header
        self.set_xy(LM, y); self.set_font("B", size=8.5); self.set_text_color(*MID_GRAY)
        self.cell(UW, 5, d["pb_sub"]); y += 8

        # case rows
        for company, amount, outcome, detail in d["pb_cases"]:
            self.set_fill_color(*GOLD); self.rect(LM, y, 2.5, 16, "F")
            self.set_xy(LM+6, y+1);   self.set_font("B", size=9.5); self.set_text_color(*NAVY)
            self.cell(38, 6, company)
            self.set_font("B", size=13); self.cell(48, 6, amount)
            self.set_font("R", size=8.5); self.set_text_color(*MID_GRAY); self.cell(0, 6, outcome)
            self.set_xy(LM+6, y+9);   self.set_font("R", size=8); self.set_text_color(*DARK)
            self.cell(UW-8, 5, detail)
            y += 19

        y += 2
        y = self.strip(y, d["pb_close"], LIGHT_BG, DARK, h=10, size=8.5)
        y += 3
        y = self.rule(y)

        y = self.tag(y, d["sl_tag"])
        y = self.h1(y, d["sl_h2"], size=16)
        y = self.body(y, d["sl_body"])
        y += 4

        # 2×2 property cards
        cw = (UW - 5) / 2
        ch = 26
        for r in range(2):
            for c in range(2):
                idx = r*2 + c
                cx  = LM + c*(cw+5)
                ry  = y + r*(ch+4)
                title, desc = d["sl_props"][idx]
                self.set_fill_color(*LIGHT_BG); self.rect(cx, ry, cw, ch, "F")
                self.set_fill_color(*GOLD);     self.rect(cx, ry, cw, 1.2, "F")
                self.set_xy(cx+4, ry+5);  self.set_font("B", size=8.5); self.set_text_color(*NAVY)
                self.cell(cw-6, 5, title)
                self.set_xy(cx+4, ry+12); self.set_font("R", size=7.8); self.set_text_color(*MID_GRAY)
                self.multi_cell(cw-6, 4.8, desc)

    # ── PAGE 2 ─────────────────────────────────────────────────────────────────
    def page2(self):
        self.add_page(); d = self.d; y = T0

        y = self.tag(y, d["pp_tag"])
        self.set_xy(LM, y); self.set_font("R", size=8.8); self.set_text_color(*MID_GRAY)
        self.multi_cell(UW, 5.2, d["pp_intro"]); y = self.get_y() + 4

        # checkpoint table
        w_no, w_nm, w_ds = 10, 58, UW-68
        ROW = 11.5
        for i, (num, name, desc) in enumerate(d["pp_rows"]):
            bg = LIGHT_BG if i%2==0 else WHITE
            self.set_fill_color(*bg); self.rect(LM, y, UW, ROW, "F")
            self.set_xy(LM+2, y+(ROW-8)/2);  self.set_font("B", size=8.5); self.set_text_color(*GOLD); self.cell(w_no-2, 8, num)
            self.set_xy(LM+w_no, y+(ROW-8)/2); self.set_font("B", size=8);  self.set_text_color(*NAVY); self.cell(w_nm, 8, name)
            self.set_xy(LM+w_no+w_nm, y+2);   self.set_font("R", size=7.8); self.set_text_color(*DARK); self.multi_cell(w_ds, 4.5, desc)
            y += ROW

        y += 3
        y = self.strip(y, d["pp_note"], BLUE_BG, BLUE_TX, h=9, size=8)
        y += 5

        # sandbox dark box — fill remaining page space
        bh = BOT - FTR - y - 4
        bx = LM
        self.set_fill_color(*NAVY); self.rect(bx, y, UW, bh, "F")
        self.set_fill_color(*GOLD); self.rect(bx, y, UW, 1, "F"); self.rect(bx, y, 3.5, bh, "F")

        iy = y + 8
        self.set_xy(bx+9, iy); self.set_font("B", size=7.5); self.set_text_color(*GOLD)
        self.cell(UW-12, 5, d["sb_tag"]); iy += 10

        self.set_xy(bx+9, iy); self.set_font("B", size=17); self.set_text_color(*WHITE)
        self.cell(UW-12, 10, d["sb_url"]); iy += 14

        self.set_xy(bx+9, iy); self.set_font("R", size=8.5); self.set_text_color(185,198,225)
        self.multi_cell(UW-14, 5.3, d["sb_body1"]); iy = self.get_y() + 3

        self.set_xy(bx+9, iy); self.set_font("R", size=8.5); self.set_text_color(185,198,225)
        self.multi_cell(UW-14, 5.3, d["sb_body2"]); iy = self.get_y() + 4

        self.set_xy(bx+9, iy); self.set_font("B", size=9); self.set_text_color(*GOLD_LT)
        self.cell(UW-12, 6, d["sb_cta"])

    # ── PAGE 3 ─────────────────────────────────────────────────────────────────
    def page3(self):
        self.add_page(); d = self.d; y = T0

        y = self.tag(y, d["ev_tag"])

        # stat cards
        cw3 = (UW - 8) / 3
        for i, (val, lbl, note) in enumerate(d["ev_stats"]):
            cx = LM + i*(cw3+4)
            self.set_fill_color(*LIGHT_BG); self.rect(cx, y, cw3, 30, "F")
            self.set_fill_color(*GOLD);     self.rect(cx, y, cw3, 1.5, "F")
            self.set_xy(cx+4, y+5);   self.set_font("B", size=18); self.set_text_color(*NAVY); self.cell(cw3-6, 11, val)
            self.set_xy(cx+4, y+16);  self.set_font("R", size=7.5); self.set_text_color(*DARK); self.multi_cell(cw3-6, 4.5, lbl)
            self.set_xy(cx+4, y+26);  self.set_font("R", size=7);   self.set_text_color(*MID_GRAY); self.cell(cw3-6, 4, note)

        y += 34
        y = self.strip(y, d["ev_pub"], GREEN_BG, GREEN_TX, h=9, size=8)
        y += 6

        y = self.rule(y)
        y = self.tag(y, d["rg_tag"])

        self.set_xy(LM, y); self.set_font("R", size=8.8); self.set_text_color(*MID_GRAY)
        self.cell(UW, 5, d["rg_intro"]); y += 8

        w_l, w_v = 34, UW-36
        for i, (reg, desc) in enumerate(d["rg_rows"]):
            bg = LIGHT_BG if i%2==0 else WHITE
            y  = self.table_row(y, bg, reg, desc, w_l, size_v=8.2, lh_v=5.5)

    # ── PAGE 4 ─────────────────────────────────────────────────────────────────
    def page4(self):
        self.add_page(); d = self.d; y = T0

        y = self.tag(y, d["tm_tag"])
        self.set_xy(LM, y); self.set_font("R", size=9); self.set_text_color(*MID_GRAY)
        self.multi_cell(UW, 5.5, d["tm_intro"]); y = self.get_y() + 5

        w_l2, w_v2 = 36, UW-38
        for i, (lbl, val) in enumerate(d["tm_rows"]):
            bg = LIGHT_BG if i%2==0 else WHITE
            y  = self.table_row(y, bg, lbl, val, w_l2, size_v=8.2, lh_v=5.5)

        y += 6
        y = self.rule(y)
        y += 2

        # CTA dark box — fixed height to hold all 4 contacts
        ct_h = 72
        self.set_fill_color(*NAVY); self.rect(LM, y, UW, ct_h, "F")
        self.set_fill_color(*GOLD); self.rect(LM, y, UW, 1, "F"); self.rect(LM, y, 3.5, ct_h, "F")

        iy = y + 8
        self.set_xy(LM+9, iy); self.set_font("B", size=8); self.set_text_color(*GOLD)
        self.cell(UW-12, 5, d["ct_tag"]); iy += 10

        self.set_xy(LM+9, iy); self.set_font("B", size=11); self.set_text_color(*WHITE)
        self.multi_cell(UW-14, 6.5, d["ct_body"]); iy = self.get_y() + 5

        for lbl, val in d["ct_items"]:
            self.set_xy(LM+9, iy); self.set_font("B", size=9.5); self.set_text_color(*GOLD_LT)
            self.cell(28, 8, f"{lbl}:")
            self.set_font("R", size=9.5); self.set_text_color(*WHITE)
            self.cell(UW-34, 8, val)
            iy += 10

    # ── build ──────────────────────────────────────────────────────────────────
    def build(self):
        self.page1(); self.page2(); self.page3(); self.page4()


# ── MAIN ───────────────────────────────────────────────────────────────────────
def generate():
    for lang, fname in [("EN", "OMNIX_Pilot_Proposal_EN.pdf"),
                        ("ES", "OMNIX_Pilot_Proposal_ES.pdf")]:
        pdf = PDF(lang); pdf.build()
        out = os.path.join(OUTPUT_DIR, fname)
        pdf.output(out)
        print(f"[{lang}] {out}  ({os.path.getsize(out)//1024} KB)")
    print("Done.")

if __name__ == "__main__":
    generate()
