#!/usr/bin/env python3
"""
OMNIX Quantum -- Pilot Proposal PDF
3 pages. Fixed layout. No auto-page-break. No overflow.
"""
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

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

# ── Palette ────────────────────────────────────────────────────────────────
NAVY      = (8,  22,  58)
GOLD      = (212, 175, 55)
GOLD_LT   = (245, 232, 170)
WHITE     = (255, 255, 255)
LIGHT_BG  = (243, 246, 254)
MID_GRAY  = (115, 128, 155)
DARK      = (28,  36,  70)
GREEN_BG  = (234, 250, 241)
GREEN_TX  = (0,  108,  60)
BLUE_BG   = (233, 242, 255)
BLUE_TX   = (12,  52, 130)

PW   = 210           # A4 width mm
PH   = 297           # A4 height mm
LM   = 18            # left margin
RM   = 18            # right margin
UW   = PW - LM - RM # usable width = 174mm
HDR  = 26            # header height
FTR  = 12            # footer height
T0   = HDR + 6       # first content Y
BMAX = PH - FTR - 4  # last safe Y before footer


# ── CONTENT ────────────────────────────────────────────────────────────────
C = {
"EN": {
    "tagline"     : "Decision Governance Infrastructure",
    "contact_line": "omnixquantum.net   |   contacto@omnixquantum.net",
    "footer"      : "Confidential  |  Pilot Program Proposal  |  Harold Nunes, Founder & CEO  |  Zenodo DOI 10.5281/zenodo.19056919  |  SSRN 6321298",

    # PAGE 1 ──────────────────────────────────────────────────────────────
    "p1_tag1"     : "THE PROBLEM",
    "p1_h1"       : "When automated systems fail,\nthey fail at machine speed.",
    "p1_body1"    : "Most governance controls — audits, compliance reviews, risk alerts — are applied after execution. By the time a human intervenes, the outcome has already been produced. In high-stakes environments, that is already too late.",
    "p1_cases_hdr": "Real examples of governance failure in automated systems:",
    "p1_cases"    : [
        ("Terra Luna",     "$40 billion",   "lost in 72 hours",   "May 2022 — algorithmic depegging cascade. No execution controls existed to halt the process."),
        ("SVB",            "$42 billion",   "withdrawn in 1 day", "March 2023 — automated sell signals triggered before any governance layer could respond."),
        ("Knight Capital", "$440 million",  "lost in 45 min",     "August 2012 — a single misconfigured automated system operated unchecked for 45 minutes."),
    ],
    "p1_insight"  : "In each case, the system operated exactly as programmed. The failure was the absence of a governance layer that could stop it.",

    "p1_tag2"     : "THE SOLUTION",
    "p1_h2"       : "Governance at the execution boundary — not after.",
    "p1_body2"    : "OMNIX is a Decision Governance Infrastructure. It sits between an automated system and its execution environment, validating every decision before it is committed. If a decision does not pass all checkpoints, it is blocked. If it passes, it receives a cryptographically signed governance receipt.",
    "p1_props"    : [
        ("Pre-execution validation",   "Every decision is assessed before it is committed, not reviewed after the fact."),
        ("Cryptographic audit trail",  "Every outcome — approved or blocked — is PQC-signed and hash-chained for independent verification."),
        ("Domain-agnostic",            "Designed for any automated decision system: trading, credit, insurance, logistics, healthcare AI."),
        ("Fail-closed by design",      "If the governance engine is unavailable, no decision passes. The system halts — it does not bypass."),
    ],

    # PAGE 2 ──────────────────────────────────────────────────────────────
    "p2_tag1"     : "THE 8-CHECKPOINT GOVERNANCE PIPELINE",
    "p2_intro"    : "Every decision passes through all 8 checkpoints in sequence, in real time, before authorization. One failed checkpoint blocks the decision. No exceptions, no overrides.",
    "p2_checks"   : [
        ("01", "Signal Integrity Validation",  "Verifies the input is coherent and within operational bounds. Malformed inputs are rejected before entering the pipeline."),
        ("02", "Regime Assessment",            "Evaluates the current operational regime to determine whether it supports the proposed decision type."),
        ("03", "Monte Carlo VETO Engine",      "Runs probabilistic simulations on the outcome distribution. If expected value does not justify the action, a veto is issued."),
        ("04", "Black Swan Detector",          "Scans for tail-risk conditions and extreme-event patterns. High-risk environments trigger automatic holds."),
        ("05", "Coherence Engine  (6 tiers)",  "Measures internal consistency across all input signals. Contradictory signals — even individually valid — can produce a hold."),
        ("06", "Risk Management System",       "Enforces portfolio-level and position-level risk constraints. Exceeding configured thresholds blocks the decision."),
        ("07", "Kelly Criterion Sizing",       "Validates that the proposed action size is within mathematically calibrated safe bounds given current exposure."),
        ("08", "Final Authorization",          "All 7 prior checkpoints passed. The decision is authorized and a PQC-signed receipt is generated and appended to the immutable audit chain."),
    ],
    "p2_receipt"  : "Every authorized decision produces a verifiable receipt at  omnixquantum.net/r/{receipt_id}",

    "p2_tag2"     : "TRY THE LIVE GOVERNANCE ENGINE  —  NO LOGIN REQUIRED",
    "p2_url"      : "omnixquantum.net/try",
    "p2_sandbox1" : "The OMNIX Public Governance Sandbox is open to anyone, right now. Describe any decision scenario in plain language — a trading position, a credit application, an operational risk scenario.",
    "p2_sandbox2" : "Our AI interprets it into 8 governance signals and runs them through the real production pipeline. In under 2 seconds you receive a live, PQC-signed governance receipt — the same artifact produced in production. No account. No demo mode. The real engine.",
    "p2_cta"      : "See what OMNIX actually does before any conversation.",

    # PAGE 3 ──────────────────────────────────────────────────────────────
    "p3_tag1"     : "PRODUCTION EVIDENCE",
    "p3_stats"    : [
        ("72,443",  "Governance decisions\nin production",      "Feb 21 – Mar 16, 2026"),
        ("100%",    "Post-quantum signed\n(NIST ML-DSA-65)",   "Every single receipt"),
        ("0",       "Decisions approved\nwithout all 8 gates", "No exceptions. Ever."),
    ],
    "p3_pub"      : "Full dataset: Zenodo DOI 10.5281/zenodo.19056919  |  Academic preprint: SSRN 6321298  (under peer review)",

    "p3_tag2"     : "WHY NOW — REGULATORY PRESSURE",
    "p3_regs"     : [
        ("EU AI Act",        "High-risk AI systems require pre-execution auditability, traceability, and documented risk controls."),
        ("MiCA",             "Crypto asset service providers must demonstrate documented operational risk controls and governance frameworks."),
        ("BCB Res. 538",     "Brazil's Central Bank mandates cryptographic audit trails for all automated financial decisions. 1,600+ institutions."),
        ("ADGM / SEC",       "Governance-by-design is the emerging compliance baseline for AI systems in finance globally."),
    ],

    "p3_tag3"     : "THE 30-DAY PILOT — NO COST, NO COMMITMENT",
    "p3_terms"    : [
        ("You provide",   "Decision signals via API or JSON  |  Risk thresholds  |  30-min onboarding call"),
        ("You receive",   "Signed receipt per decision  |  Full audit trail  |  Day-30 governance performance report"),
        ("Duration",      "30 days from integration date"),
        ("Cost",          "Complimentary"),
        ("Data handling", "All signals encrypted at rest (AES-256). No data shared between clients."),
        ("After pilot",   "No obligation. If there is mutual fit, we discuss a commercial arrangement."),
    ],

    "p3_cta_h"    : "READY TO CONNECT?",
    "p3_cta_b"    : "Reach out and we will walk you through the integration in 30 minutes.",
    "p3_contacts" : [
        ("Email",     "contacto@omnixquantum.net"),
        ("WhatsApp",  "+1 (650) 481-5494"),
        ("Live demo", "omnixquantum.net/try"),
        ("LinkedIn",  "linkedin.com/in/harold-nunes"),
    ],
},

"ES": {
    "tagline"     : "Infraestructura de Gobernanza de Decisiones",
    "contact_line": "omnixquantum.net   |   contacto@omnixquantum.net",
    "footer"      : "Confidencial  |  Propuesta Programa Piloto  |  Harold Nunes, Fundador y CEO  |  Zenodo DOI 10.5281/zenodo.19056919  |  SSRN 6321298",

    "p1_tag1"     : "EL PROBLEMA",
    "p1_h1"       : "Cuando un sistema automatizado falla,\nfalla a velocidad de maquina.",
    "p1_body1"    : "La mayoria de los controles de gobernanza — auditorias, revisiones de cumplimiento, alertas de riesgo — se aplican despues de la ejecucion. Para cuando un humano puede intervenir, el resultado ya fue producido. En entornos de alto riesgo, ya es demasiado tarde.",
    "p1_cases_hdr": "Ejemplos reales de falla de gobernanza en sistemas automatizados:",
    "p1_cases"    : [
        ("Terra Luna",     "$40 mil millones", "perdidos en 72 horas",  "Mayo 2022 — cascada algoritmica de desviculacion. No existian controles de ejecucion para detenerlo."),
        ("SVB",            "$42 mil millones", "retirados en 1 dia",    "Marzo 2023 — senales de venta activadas antes de que cualquier capa de gobernanza pudiera responder."),
        ("Knight Capital", "$440 millones",    "perdidos en 45 min",    "Agosto 2012 — un sistema mal configurado opero sin controles durante 45 minutos."),
    ],
    "p1_insight"  : "En cada caso, el sistema opero exactamente como fue programado. La falla fue la ausencia de una capa de gobernanza capaz de detenerlo.",

    "p1_tag2"     : "LA SOLUCION",
    "p1_h2"       : "Gobernanza en la frontera de ejecucion — no despues.",
    "p1_body2"    : "OMNIX es una Infraestructura de Gobernanza de Decisiones. Se ubica entre un sistema automatizado y su entorno de ejecucion, validando cada decision antes de que se confirme. Si no pasa todos los controles, se bloquea. Si pasa, recibe un recibo de gobernanza firmado criptograficamente.",
    "p1_props"    : [
        ("Validacion previa a la ejecucion", "Cada decision se evalua antes de confirmarse, no se revisa despues del hecho."),
        ("Auditoria criptografica",           "Cada resultado — aprobado o bloqueado — firmado con PQC y encadenado en hash para verificacion independiente."),
        ("Agnos al dominio",                  "Para cualquier sistema de decision automatizada: trading, credito, seguros, logistica, IA en salud."),
        ("Fail-closed por diseno",            "Si el motor no esta disponible, ninguna decision pasa. El sistema se detiene — no evade el control."),
    ],

    "p2_tag1"     : "EL PIPELINE DE GOBERNANZA DE 8 PUNTOS DE CONTROL",
    "p2_intro"    : "Cada decision pasa por los 8 puntos de control en secuencia, en tiempo real, antes de ser autorizada. Un punto de control fallido bloquea la decision. Sin excepciones ni anulaciones.",
    "p2_checks"   : [
        ("01", "Validacion de Integridad de Senal",  "Verifica que la entrada sea coherente y este dentro de los limites operativos. Las entradas anomalas se rechazan antes del pipeline."),
        ("02", "Evaluacion de Regimen",              "Evalua el regimen operativo actual para determinar si soporta el tipo de decision propuesta."),
        ("03", "Motor de VETO Monte Carlo",          "Ejecuta simulaciones probabilisticas sobre la distribucion de resultados. Si el valor esperado no justifica la accion, se emite veto."),
        ("04", "Detector de Cisne Negro",            "Analiza condiciones de riesgo de cola y patrones de eventos extremos. Entornos de alto riesgo activan paradas automaticas."),
        ("05", "Motor de Coherencia  (6 capas)",     "Mide consistencia interna entre todas las senales. Senales contradictorias — incluso individualmente validas — pueden generar parada."),
        ("06", "Sistema de Gestion de Riesgo",       "Aplica restricciones de riesgo a nivel de portafolio y posicion. Superar los umbrales configurados bloquea la decision."),
        ("07", "Tamano por Criterio de Kelly",       "Valida que el tamano de accion propuesto este dentro de los limites seguros calibrados matematicamente segun la exposicion actual."),
        ("08", "Autorizacion Final",                 "Los 7 puntos anteriores pasados. La decision es autorizada y se genera un recibo firmado PQC, anexado a la cadena de auditoria inmutable."),
    ],
    "p2_receipt"  : "Cada decision autorizada produce un recibo verificable en  omnixquantum.net/r/{receipt_id}",

    "p2_tag2"     : "PRUEBA EL MOTOR EN VIVO  —  SIN LOGIN",
    "p2_url"      : "omnixquantum.net/try",
    "p2_sandbox1" : "El Sandbox Publico de OMNIX esta disponible para cualquiera, ahora mismo. Describe cualquier escenario de decision en lenguaje natural — una posicion de trading, una solicitud de credito, un escenario de riesgo operativo.",
    "p2_sandbox2" : "Nuestra IA lo interpreta en 8 senales de gobernanza y las pasa por el pipeline de produccion real. En menos de 2 segundos recibes un recibo firmado PQC en vivo — el mismo artefacto de produccion. Sin cuenta. Sin modo demo. El motor real.",
    "p2_cta"      : "Ve lo que OMNIX realmente hace antes de cualquier conversacion.",

    "p3_tag1"     : "EVIDENCIA EN PRODUCCION",
    "p3_stats"    : [
        ("72,443",  "Decisiones de gobernanza\nen produccion",       "21 Feb – 16 Mar 2026"),
        ("100%",    "Firmadas post-cuanticas\n(NIST ML-DSA-65)",    "Cada recibo, sin excepcion"),
        ("0",       "Decisiones aprobadas\nsin los 8 controles",    "Sin excepciones. Nunca."),
    ],
    "p3_pub"      : "Dataset completo: Zenodo DOI 10.5281/zenodo.19056919  |  Preprint academico: SSRN 6321298  (en revision por pares)",

    "p3_tag2"     : "POR QUE AHORA — PRESION REGULATORIA",
    "p3_regs"     : [
        ("EU AI Act",        "Los sistemas de IA de alto riesgo requieren auditabilidad previa, trazabilidad y controles de riesgo documentados."),
        ("MiCA",             "Los proveedores de criptoactivos deben demostrar controles de riesgo operativo y marcos de gobernanza documentados."),
        ("BCB Res. 538",     "El Banco Central de Brasil exige trazabilidad criptografica para decisiones financieras automatizadas. +1,600 instituciones."),
        ("ADGM / SEC",       "La gobernanza por diseno es el estandar de cumplimiento emergente para sistemas de IA en finanzas a nivel global."),
    ],

    "p3_tag3"     : "EL PILOTO DE 30 DIAS — SIN COSTO, SIN COMPROMISO",
    "p3_terms"    : [
        ("Lo que aportas",   "Senales de decision via API o JSON  |  Umbrales de riesgo  |  Llamada de onboarding 30 min"),
        ("Lo que recibes",   "Recibo firmado por decision  |  Auditoria completa  |  Reporte de gobernanza al Dia 30"),
        ("Duracion",         "30 dias desde la fecha de integracion"),
        ("Costo",            "Gratuito"),
        ("Manejo de datos",  "Senales cifradas en reposo (AES-256). Sin datos compartidos entre clientes."),
        ("Despues del piloto","Sin obligacion. Si hay encaje mutuo, conversamos sobre un acuerdo comercial."),
    ],

    "p3_cta_h"    : "CONECTEMOS",
    "p3_cta_b"    : "Escribenos y coordinamos la integracion en una reunion de 30 minutos.",
    "p3_contacts" : [
        ("Email",    "contacto@omnixquantum.net"),
        ("WhatsApp", "+1 (650) 481-5494"),
        ("Demo",     "omnixquantum.net/try"),
        ("LinkedIn", "linkedin.com/in/harold-nunes"),
    ],
},
}


# ── PDF ENGINE ─────────────────────────────────────────────────────────────
class PDF(FPDF):
    def __init__(self, lang):
        super().__init__("P", "mm", "A4")
        self.lang = lang
        self.d    = C[lang]
        self.add_font("R", fname=FONT_R)
        self.add_font("B", fname=FONT_B)
        self.set_margins(LM, 0, RM)
        self.set_auto_page_break(auto=False)

    # ── Header / Footer ─────────────────────────────────────────────────────
    def header(self):
        d = self.d
        self.set_fill_color(*NAVY)
        self.rect(0, 0, PW, HDR, "F")
        self.set_fill_color(*GOLD)
        self.rect(0, HDR - 0.8, PW, 0.8, "F")

        lh = HDR - 6
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=5, y=3, w=lh, h=lh)

        tx = 5 + lh + 5
        self.set_xy(tx, 7)
        self.set_font("B", size=9)
        self.set_text_color(*GOLD)
        self.cell(PW - tx - 40, 5, d["tagline"])

        self.set_xy(tx, 14)
        self.set_font("R", size=7)
        self.set_text_color(155, 170, 205)
        self.cell(PW - tx - 40, 4, d["contact_line"])

        self.set_xy(PW - 35, 9)
        self.set_font("R", size=7)
        self.set_text_color(120, 140, 180)
        pg = self.page_no()
        self.cell(28, 5, f"Page {pg} / 3", align="R")

    def footer(self):
        self.set_fill_color(*NAVY)
        self.rect(0, PH - FTR, PW, FTR, "F")
        self.set_draw_color(*GOLD)
        self.set_line_width(0.3)
        self.line(0, PH - FTR, PW, PH - FTR)
        self.set_y(PH - FTR + 3)
        self.set_font("R", size=5.5)
        self.set_text_color(*GOLD)
        self.cell(PW, 4, self.d["footer"], align="C")

    # ── Layout helpers ───────────────────────────────────────────────────────
    def _tag(self, y, text):
        self.set_xy(LM, y)
        self.set_font("B", size=7.5)
        self.set_text_color(*GOLD)
        self.cell(UW, 5, text)
        return y + 7

    def _h1(self, y, text, size=19):
        lh = size * 0.6
        self.set_xy(LM, y)
        self.set_font("B", size=size)
        self.set_text_color(*NAVY)
        lines = text.count("\n") + 1
        self.multi_cell(UW, lh, text)
        return y + lines * lh + 3

    def _body(self, y, text, size=9.2, color=DARK, w=None):
        if w is None: w = UW
        lh = 5.3
        self.set_xy(LM, y)
        self.set_font("R", size=size)
        self.set_text_color(*color)
        self.multi_cell(w, lh, text)
        lines = max(1, len(self.multi_cell_split(text, size, w)))
        return y + lines * lh + 2

    def multi_cell_split(self, text, size, w):
        """Estimate line count for a multi_cell block."""
        self.set_font("R", size=size)
        approx_chars = int(w / (size * 0.45))
        lines = []
        for para in text.split("\n"):
            if not para.strip():
                lines.append("")
                continue
            words = para.split()
            line = ""
            for word in words:
                if len(line) + len(word) + 1 <= approx_chars:
                    line = (line + " " + word).strip()
                else:
                    if line: lines.append(line)
                    line = word
            if line: lines.append(line)
        return lines or [""]

    def _rule(self, y, color=GOLD, h=0.4):
        self.set_draw_color(*color)
        self.set_line_width(h)
        self.line(LM, y, PW - RM, y)
        return y + 5

    def _strip(self, y, text, bg, fg, size=8.5, strip_h=9):
        self.set_fill_color(*bg)
        self.rect(LM, y, UW, strip_h, "F")
        self.set_xy(LM + 4, y + (strip_h - size) / 2)
        self.set_font("R", size=size)
        self.set_text_color(*fg)
        self.multi_cell(UW - 6, size * 0.65, text)
        return y + strip_h + 3

    # ── PAGE 1 ───────────────────────────────────────────────────────────────
    def page1(self):
        self.add_page()
        d = self.d
        y = T0

        # -- Problem --
        y = self._tag(y, d["p1_tag1"])
        y = self._h1(y, d["p1_h1"], size=19)
        y = self._body(y, d["p1_body1"], size=9.2)
        y += 4

        # Cases header
        self.set_xy(LM, y)
        self.set_font("B", size=8.5)
        self.set_text_color(*MID_GRAY)
        self.cell(UW, 5, d["p1_cases_hdr"])
        y += 8

        # Case rows
        for company, amount, outcome, detail in d["p1_cases"]:
            # Left gold bar
            self.set_fill_color(*GOLD)
            self.rect(LM, y, 2.5, 16, "F")
            # Company
            self.set_xy(LM + 6, y + 1)
            self.set_font("B", size=9.5)
            self.set_text_color(*NAVY)
            self.cell(36, 6, company)
            # Amount bold
            self.set_font("B", size=13)
            self.set_text_color(*NAVY)
            self.cell(48, 6, amount)
            # Outcome muted
            self.set_font("R", size=8.5)
            self.set_text_color(*MID_GRAY)
            self.cell(0, 6, outcome)
            # Detail
            self.set_xy(LM + 6, y + 8)
            self.set_font("R", size=8)
            self.set_text_color(*DARK)
            self.cell(UW - 8, 5, detail)
            y += 19

        y += 2
        # Closing insight strip
        y = self._strip(y, d["p1_insight"], LIGHT_BG, DARK, size=8.5, strip_h=10)
        y += 4

        # Divider
        y = self._rule(y)

        # -- Solution --
        y = self._tag(y, d["p1_tag2"])
        y = self._h1(y, d["p1_h2"], size=16)
        y = self._body(y, d["p1_body2"], size=9.2)
        y += 4

        # Properties — simple 2-column text list
        pw2 = (UW - 6) / 2
        props = d["p1_props"]
        for i in range(0, len(props), 2):
            row_y = y
            for j in range(2):
                idx = i + j
                if idx >= len(props): break
                title, desc = props[idx]
                cx = LM + j * (pw2 + 6)
                # card background
                self.set_fill_color(*LIGHT_BG)
                self.rect(cx, row_y, pw2, 20, "F")
                self.set_fill_color(*GOLD)
                self.rect(cx, row_y, pw2, 1.2, "F")
                # title
                self.set_xy(cx + 4, row_y + 4)
                self.set_font("B", size=8.5)
                self.set_text_color(*NAVY)
                self.cell(pw2 - 6, 5, title)
                # desc
                self.set_xy(cx + 4, row_y + 10.5)
                self.set_font("R", size=7.8)
                self.set_text_color(*MID_GRAY)
                self.multi_cell(pw2 - 6, 4.5, desc)
            y = row_y + 23

    # ── PAGE 2 ───────────────────────────────────────────────────────────────
    def page2(self):
        self.add_page()
        d = self.d
        y = T0

        # -- Pipeline --
        y = self._tag(y, d["p2_tag1"])

        self.set_xy(LM, y)
        self.set_font("R", size=8.8)
        self.set_text_color(*MID_GRAY)
        self.multi_cell(UW, 5, d["p2_intro"])
        y += 13

        # Checkpoint rows
        w_no = 10
        w_nm = 60
        w_ds = UW - w_no - w_nm
        ROW  = 11.5

        for i, (num, name, desc) in enumerate(d["p2_checks"]):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            self.rect(LM, y, UW, ROW, "F")

            # number
            self.set_xy(LM + 2, y + (ROW - 8) / 2)
            self.set_font("B", size=8.5)
            self.set_text_color(*GOLD)
            self.cell(w_no - 2, 8, num)

            # name
            self.set_xy(LM + w_no, y + (ROW - 8) / 2)
            self.set_font("B", size=8)
            self.set_text_color(*NAVY)
            self.cell(w_nm, 8, name)

            # description
            self.set_xy(LM + w_no + w_nm, y + (ROW - 8) / 2)
            self.set_font("R", size=7.8)
            self.set_text_color(*DARK)
            self.multi_cell(w_ds, 4.5, desc)
            y += ROW

        y += 3
        y = self._strip(y, d["p2_receipt"], BLUE_BG, BLUE_TX, size=8, strip_h=8)
        y += 5

        # -- Sandbox --
        # How much space is left?
        box_h = BMAX - y - 2
        if box_h < 50: box_h = 50

        # Dark navy box
        self.set_fill_color(*NAVY)
        self.rect(LM, y, UW, box_h, "F")
        self.set_fill_color(*GOLD)
        self.rect(LM, y, UW, 1, "F")
        self.rect(LM, y, 3.5, box_h, "F")

        iy = y + 7
        # Tag
        self.set_xy(LM + 9, iy)
        self.set_font("B", size=7.5)
        self.set_text_color(*GOLD)
        self.cell(UW - 12, 5, d["p2_tag2"])
        iy += 9

        # Big URL
        self.set_xy(LM + 9, iy)
        self.set_font("B", size=17)
        self.set_text_color(*WHITE)
        self.cell(UW - 12, 10, d["p2_url"])
        iy += 13

        # Body lines
        self.set_xy(LM + 9, iy)
        self.set_font("R", size=8.5)
        self.set_text_color(185, 198, 225)
        self.multi_cell(UW - 14, 5.2, d["p2_sandbox1"])
        iy += 14

        self.set_xy(LM + 9, iy)
        self.set_font("R", size=8.5)
        self.set_text_color(185, 198, 225)
        self.multi_cell(UW - 14, 5.2, d["p2_sandbox2"])
        iy += 18

        # CTA
        self.set_xy(LM + 9, iy)
        self.set_font("B", size=9)
        self.set_text_color(*GOLD_LT)
        self.cell(UW - 12, 6, d["p2_cta"])

    # ── PAGE 3 ───────────────────────────────────────────────────────────────
    def page3(self):
        self.add_page()
        d = self.d
        y = T0

        # -- Evidence --
        y = self._tag(y, d["p3_tag1"])

        # 3 stat cards
        cw  = (UW - 8) / 3
        sy  = y
        for i, (val, label, note) in enumerate(d["p3_stats"]):
            cx = LM + i * (cw + 4)
            self.set_fill_color(*LIGHT_BG)
            self.rect(cx, sy, cw, 28, "F")
            self.set_fill_color(*GOLD)
            self.rect(cx, sy, cw, 1.5, "F")

            self.set_xy(cx + 4, sy + 5)
            self.set_font("B", size=18)
            self.set_text_color(*NAVY)
            self.cell(cw - 6, 11, val)

            self.set_xy(cx + 4, sy + 15.5)
            self.set_font("R", size=7.5)
            self.set_text_color(*DARK)
            self.multi_cell(cw - 6, 4.5, label)

            self.set_xy(cx + 4, sy + 24)
            self.set_font("R", size=7)
            self.set_text_color(*MID_GRAY)
            self.cell(cw - 6, 4, note)

        y = sy + 32
        y = self._strip(y, d["p3_pub"], GREEN_BG, GREEN_TX, size=8, strip_h=9)
        y += 4

        # -- Regulatory --
        y = self._rule(y)
        y = self._tag(y, d["p3_tag2"])

        w_l = 32
        w_r = UW - w_l
        for i, (reg, desc) in enumerate(d["p3_regs"]):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            row_y = y
            self.rect(LM, row_y, UW, 9, "F")

            self.set_xy(LM + 2, row_y + 1)
            self.set_font("B", size=8.5)
            self.set_text_color(*NAVY)
            self.cell(w_l, 7, reg)

            self.set_xy(LM + w_l, row_y + 1)
            self.set_font("R", size=8.2)
            self.set_text_color(*DARK)
            self.multi_cell(w_r - 2, 4.5, desc)
            y += 10

        y += 5

        # -- Pilot terms --
        y = self._rule(y)
        y = self._tag(y, d["p3_tag3"])

        w_l2 = 34
        w_r2 = UW - w_l2
        for i, (label, val) in enumerate(d["p3_terms"]):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            row_y = y
            self.rect(LM, row_y, UW, 9, "F")

            self.set_xy(LM + 2, row_y + 1)
            self.set_font("B", size=8.5)
            self.set_text_color(*NAVY)
            self.cell(w_l2, 7, f"{label}:")

            self.set_xy(LM + w_l2, row_y + 1)
            self.set_font("R", size=8.2)
            self.set_text_color(*DARK)
            self.multi_cell(w_r2 - 2, 4.5, val)
            y += 10

        y += 5

        # -- CTA box --
        box_h = BMAX - y - 2
        if box_h < 44: box_h = 44

        self.set_fill_color(*NAVY)
        self.rect(LM, y, UW, box_h, "F")
        self.set_fill_color(*GOLD)
        self.rect(LM, y, UW, 1, "F")
        self.rect(LM, y, 3.5, box_h, "F")

        iy = y + 7
        self.set_xy(LM + 9, iy)
        self.set_font("B", size=8)
        self.set_text_color(*GOLD)
        self.cell(UW - 12, 5, d["p3_cta_h"])
        iy += 9

        self.set_xy(LM + 9, iy)
        self.set_font("B", size=10)
        self.set_text_color(*WHITE)
        self.multi_cell(UW - 14, 6, d["p3_cta_b"])
        iy += 12

        for label, val in d["p3_contacts"]:
            self.set_xy(LM + 9, iy)
            self.set_font("B", size=9)
            self.set_text_color(*GOLD_LT)
            self.cell(24, 7, f"{label}:")
            self.set_font("R", size=9)
            self.set_text_color(*WHITE)
            self.cell(UW - 30, 7, val)
            iy += 8

    # ── Build ─────────────────────────────────────────────────────────────────
    def build(self):
        self.page1()
        self.page2()
        self.page3()


# ── MAIN ───────────────────────────────────────────────────────────────────
def generate():
    for lang, fname in [("EN", "OMNIX_Pilot_Proposal_EN.pdf"),
                        ("ES", "OMNIX_Pilot_Proposal_ES.pdf")]:
        pdf = PDF(lang)
        pdf.build()
        out  = os.path.join(OUTPUT_DIR, fname)
        pdf.output(out)
        kb = os.path.getsize(out) / 1024
        print(f"[{lang}] {out}  ({kb:.1f} KB)")
    print("Done.")

if __name__ == "__main__":
    generate()
