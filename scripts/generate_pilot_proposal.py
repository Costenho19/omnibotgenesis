#!/usr/bin/env python3
"""
OMNIX Quantum -- Pilot Program Proposal PDF Generator
Enterprise-grade. 3 pages. English + Spanish.
Page 1: Problem + Solution
Page 2: 8-Checkpoint Pipeline + Live Sandbox
Page 3: Evidence + Regulatory + Pilot Terms + CTA
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
LIGHT_BG   = (243, 246, 254)
BORDER     = (210, 218, 236)
MID_GRAY   = (115, 128, 155)
DARK       = (18,  24,  48)
GREEN_BG   = (234, 250, 241)
GREEN_TXT  = (0,  108,  60)
BLUE_BG    = (233, 242, 255)
BLUE_TXT   = (12,  52, 130)

HEADER_H = 26
TOP_M    = 34
LM       = 18
RM       = 18

# ── CONTENT ───────────────────────────────────────────────────────────────────
CONTENT = {
"EN": {
    "footer": "Confidential  --  Pilot Program Proposal   |   Harold Nunes, Founder & CEO   |   SSRN 6321298   |   Zenodo DOI: 10.5281/zenodo.19056919",
    "contact_line": "omnixquantum.net   |   contacto@omnixquantum.net",
    "tagline": "Decision Governance Infrastructure",
    "page_of": "Page",

    # PAGE 1 ─────────────────────────────────────────────────────────────────
    "problem_label":    "THE PROBLEM",
    "problem_headline": "When automated systems fail,\nthey fail at machine speed.",
    "problem_body": (
        "Most governance controls -- audits, compliance reviews, risk alerts -- "
        "are applied after execution. By the time a human intervenes, "
        "the automated system has already produced its outcome. "
        "In high-stakes environments, that is already too late."
    ),
    "cases_title": "Real examples of governance failure in automated systems:",
    "cases": [
        ("Terra Luna",     "$40 billion",   "lost in 72 hours",           "May 2022 -- algorithmic depegging cascade with no execution controls."),
        ("SVB",            "$42 billion",   "withdrawn in one day",        "March 2023 -- automated sell signals triggered before any governance layer could respond."),
        ("Knight Capital", "$440 million",  "lost in 45 minutes",          "August 2012 -- a single misconfigured automated system executed unchecked for 45 minutes."),
    ],
    "problem_close": (
        "In each case, the automated system operated exactly as programmed -- "
        "the failure was the absence of a governance layer that could stop it."
    ),

    "solution_label":    "THE SOLUTION",
    "solution_headline": "Governance at the execution boundary -- not after.",
    "solution_body1": (
        "OMNIX is a Decision Governance Infrastructure. It sits between an automated "
        "system and its execution environment, validating every decision before it is "
        "committed. If a decision does not pass, it is blocked. If it passes, it "
        "receives a cryptographically signed governance receipt."
    ),
    "solution_body2": (
        "This is not an advisory layer. It is not a dashboard that shows you what "
        "happened. It is a structural control embedded at the point of execution -- "
        "decisions that should not happen, do not happen."
    ),
    "solution_props": [
        ("Pre-execution validation",  "Every decision is assessed before it is committed -- not reviewed after the fact."),
        ("Cryptographic audit trail", "Every outcome, approved or blocked, is PQC-signed and hash-chained for independent verification."),
        ("Domain-agnostic",           "Designed for any system that makes automated decisions: trading, credit, insurance, logistics, healthcare AI."),
        ("Fail-closed by design",     "If the governance engine is unavailable, no decision passes. The system halts, not bypasses."),
    ],

    # PAGE 2 ─────────────────────────────────────────────────────────────────
    "pipeline_label":   "THE 8-CHECKPOINT GOVERNANCE PIPELINE",
    "pipeline_intro": (
        "Every decision submitted to OMNIX passes through all 8 checkpoints in sequence, "
        "in real time, before it is authorized. A single failed checkpoint blocks the decision. "
        "There are no exceptions and no manual overrides."
    ),
    "checkpoints": [
        ("01", "Signal Integrity Validation",
         "Verifies that the input signal is coherent, complete, and within expected operational bounds. "
         "Malformed or anomalous inputs are rejected before they reach the pipeline."),
        ("02", "Regime Assessment",
         "Evaluates the current operational regime (market, credit, risk environment) to determine "
         "whether it is appropriate for the proposed decision type."),
        ("03", "Monte Carlo VETO Engine",
         "Runs probabilistic simulations across the decision's outcome distribution. "
         "If the expected value does not justify the action, a veto is issued."),
        ("04", "Black Swan Detector",
         "Scans for tail-risk conditions, extreme-event patterns, and historical analogues "
         "to current conditions. High-risk environments trigger automatic holds."),
        ("05", "Coherence Engine  (6 tiers)",
         "Measures internal consistency across all input signals. "
         "Contradictory signals -- even individually valid ones -- can produce a hold."),
        ("06", "Risk Management System  (RMS)",
         "Enforces portfolio-level and position-level risk constraints. "
         "Decisions that exceed configured thresholds are blocked regardless of signal quality."),
        ("07", "Kelly Criterion Sizing",
         "Validates that the proposed action size is within mathematically calibrated safe bounds "
         "based on edge, variance, and current exposure."),
        ("08", "Final Authorization",
         "All 7 prior checkpoints passed. The decision is authorized and a cryptographically "
         "signed governance receipt is generated and appended to the immutable audit chain."),
    ],
    "pipeline_close": (
        "Every authorized decision produces a receipt verifiable at  omnixquantum.net/r/{receipt_id}"
    ),

    "sandbox_label": "TRY THE LIVE GOVERNANCE ENGINE -- NO LOGIN REQUIRED",
    "sandbox_url":   "omnixquantum.net/try",
    "sandbox_body": (
        "The OMNIX Public Governance Sandbox is available to anyone, right now. "
        "Type any decision scenario in plain language -- a trading position, a credit "
        "application, an operational risk scenario. Our AI interprets it into 8 "
        "governance signals and runs them through the real production pipeline.\n\n"
        "In under 2 seconds you receive a live, cryptographically signed governance "
        "receipt -- the same artifact produced in production. No account. No demo mode. "
        "No simulated data. The real engine."
    ),
    "sandbox_cta": "See what OMNIX actually does before any conversation.",

    # PAGE 3 ─────────────────────────────────────────────────────────────────
    "evidence_label": "PRODUCTION EVIDENCE",
    "evidence_intro": "OMNIX has been running in production. These are the real numbers.",
    "stats": [
        ("72,443",  "Governance decisions\nprocessed in production",   "Feb 21 -- Mar 16, 2026"),
        ("100%",    "Post-quantum signed\n(NIST ML-DSA-65)",           "Every single receipt"),
        ("0",       "Decisions approved without\npassing all 8 gates", "No exceptions. Ever."),
    ],
    "evidence_note": (
        "Full dataset publicly available -- Zenodo DOI: 10.5281/zenodo.19056919\n"
        "Academic preprint -- SSRN Working Paper 6321298  (under peer review)"
    ),

    "regs_label": "WHY NOW -- REGULATORY PRESSURE",
    "regs_intro": "Global regulators are making governance infrastructure mandatory.",
    "regs": [
        ("EU AI Act (2025+)",      "High-risk AI systems require full pre-execution auditability, traceability, and documented risk controls."),
        ("MiCA (2024-2025)",       "Crypto asset service providers must demonstrate documented operational risk controls and governance frameworks."),
        ("BCB Resolution 538",    "Brazil's Central Bank mandates cryptographic audit trails for all automated financial decisions. 1,600+ institutions affected."),
        ("ADGM / SEC frameworks", "Governance-by-design is the emerging compliance baseline for AI systems in finance globally."),
    ],

    "offer_label": "THE 30-DAY PILOT -- NO COST, NO COMMITMENT",
    "offer_intro": (
        "We are onboarding the first pilot partners now. "
        "The goal is to validate OMNIX across multiple industries with real decision data."
    ),
    "terms": [
        ("What you provide",   "Your decision signals via API or JSON  |  Risk thresholds  |  30-min onboarding call"),
        ("What you receive",   "Signed receipt per decision  |  Full audit trail  |  Day-30 governance performance report"),
        ("Duration",           "30 days from integration date"),
        ("Cost",               "Complimentary -- no charge"),
        ("Data handling",      "All signals encrypted at rest (AES-256). No data shared between clients."),
        ("After the pilot",    "No obligation. If there is mutual fit, we discuss a commercial arrangement."),
    ],

    "cta_label": "LET'S CONNECT",
    "cta_body":  "Reach out and we will walk you through the integration in 30 minutes.",
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
    "page_of": "Pagina",

    "problem_label":    "EL PROBLEMA",
    "problem_headline": "Cuando un sistema automatizado falla,\nfalla a velocidad de maquina.",
    "problem_body": (
        "La mayoria de los controles de gobernanza -- auditorias, revisiones de cumplimiento, "
        "alertas de riesgo -- se aplican despues de la ejecucion. Para cuando un humano "
        "puede intervenir, el sistema ya produjo su resultado. "
        "En entornos de alto riesgo, ya es demasiado tarde."
    ),
    "cases_title": "Ejemplos reales de falla de gobernanza en sistemas automatizados:",
    "cases": [
        ("Terra Luna",     "$40 mil millones", "perdidos en 72 horas",       "Mayo 2022 -- cascada algoritmica sin ningun control de ejecucion."),
        ("SVB",            "$42 mil millones", "retirados en un dia",         "Marzo 2023 -- senales de venta automatizadas activadas antes de que pudiera responder cualquier capa de gobernanza."),
        ("Knight Capital", "$440 millones",    "perdidos en 45 minutos",      "Agosto 2012 -- un sistema automatizado mal configurado opero sin controles durante 45 minutos."),
    ],
    "problem_close": (
        "En cada caso, el sistema automatizado opero exactamente como fue programado -- "
        "la falla fue la ausencia de una capa de gobernanza capaz de detenerlo."
    ),

    "solution_label":    "LA SOLUCION",
    "solution_headline": "Gobernanza en la frontera de ejecucion -- no despues.",
    "solution_body1": (
        "OMNIX es una Infraestructura de Gobernanza de Decisiones. Se ubica entre un "
        "sistema automatizado y su entorno de ejecucion, validando cada decision antes "
        "de que se confirme. Si una decision no pasa, se bloquea. Si pasa, recibe "
        "un recibo de gobernanza firmado criptograficamente."
    ),
    "solution_body2": (
        "Esto no es una capa de advertencia. No es un panel que muestra lo que ocurrio. "
        "Es un control estructural embebido en el punto de ejecucion -- "
        "las decisiones que no deben ocurrir, no ocurren."
    ),
    "solution_props": [
        ("Validacion previa a la ejecucion", "Cada decision se evalua antes de confirmarse -- no se revisa despues del hecho."),
        ("Auditoria criptografica",          "Cada resultado, aprobado o bloqueado, esta firmado con PQC y encadenado en hash para verificacion independiente."),
        ("Agnos al dominio",                 "Disenado para cualquier sistema que tome decisiones automatizadas: trading, credito, seguros, logistica, IA en salud."),
        ("Fail-closed por diseno",           "Si el motor de gobernanza no esta disponible, ninguna decision pasa. El sistema se detiene, no evade el control."),
    ],

    "pipeline_label":   "EL PIPELINE DE GOBERNANZA DE 8 PUNTOS DE CONTROL",
    "pipeline_intro": (
        "Cada decision enviada a OMNIX pasa por los 8 puntos de control en secuencia, "
        "en tiempo real, antes de ser autorizada. Un solo punto de control fallido bloquea "
        "la decision. No hay excepciones ni anulaciones manuales."
    ),
    "checkpoints": [
        ("01", "Validacion de Integridad de Senal",
         "Verifica que la senal de entrada sea coherente, completa y este dentro de los limites operativos "
         "esperados. Las entradas malformadas o anomalas se rechazan antes de entrar al pipeline."),
        ("02", "Evaluacion de Regimen",
         "Evalua el regimen operativo actual (mercado, credito, entorno de riesgo) para determinar "
         "si es apropiado para el tipo de decision propuesta."),
        ("03", "Motor de VETO Monte Carlo",
         "Ejecuta simulaciones probabilisticas sobre la distribucion de resultados de la decision. "
         "Si el valor esperado no justifica la accion, se emite un veto."),
        ("04", "Detector de Cisne Negro",
         "Analiza condiciones de riesgo de cola, patrones de eventos extremos y analogos historicos "
         "a las condiciones actuales. Los entornos de alto riesgo generan paradas automaticas."),
        ("05", "Motor de Coherencia  (6 capas)",
         "Mide la consistencia interna entre todas las senales de entrada. "
         "Senales contradictorias -- incluso individualmente validas -- pueden generar una parada."),
        ("06", "Sistema de Gestion de Riesgo  (RMS)",
         "Aplica restricciones de riesgo a nivel de portafolio y de posicion. "
         "Las decisiones que superan los umbrales configurados se bloquean sin importar la calidad de la senal."),
        ("07", "Tamano por Criterio de Kelly",
         "Valida que el tamano de accion propuesto este dentro de los limites seguros calibrados "
         "matematicamente segun el edge, la varianza y la exposicion actual."),
        ("08", "Autorizacion Final",
         "Los 7 puntos de control anteriores pasados. La decision es autorizada y se genera "
         "un recibo de gobernanza firmado criptograficamente, anexado a la cadena de auditoria inmutable."),
    ],
    "pipeline_close": (
        "Cada decision autorizada produce un recibo verificable en  omnixquantum.net/r/{receipt_id}"
    ),

    "sandbox_label": "PRUEBA EL MOTOR DE GOBERNANZA EN VIVO -- SIN LOGIN",
    "sandbox_url":   "omnixquantum.net/try",
    "sandbox_body": (
        "El Sandbox Publico de Gobernanza de OMNIX esta disponible para cualquiera, ahora mismo. "
        "Escribe cualquier escenario de decision en lenguaje natural -- una posicion de trading, "
        "una solicitud de credito, un escenario de riesgo operativo. Nuestra IA lo interpreta "
        "en 8 senales de gobernanza y las pasa por el pipeline de produccion real.\n\n"
        "En menos de 2 segundos recibes un recibo de gobernanza firmado criptograficamente en "
        "vivo -- el mismo artefacto que se produce en produccion. Sin cuenta. Sin modo demo. "
        "Sin datos simulados. El motor real."
    ),
    "sandbox_cta": "Ve lo que OMNIX realmente hace antes de cualquier conversacion.",

    "evidence_label": "EVIDENCIA EN PRODUCCION",
    "evidence_intro": "OMNIX ha estado operando en produccion. Estos son los numeros reales.",
    "stats": [
        ("72,443",  "Decisiones de gobernanza\nprocesadas en produccion",    "21 Feb -- 16 Mar 2026"),
        ("100%",    "Firmadas post-cuanticas\n(NIST ML-DSA-65)",             "Cada recibo, sin excepcion"),
        ("0",       "Decisiones aprobadas sin\npasar los 8 controles",       "Sin excepciones. Nunca."),
    ],
    "evidence_note": (
        "Dataset completo disponible publicamente -- Zenodo DOI: 10.5281/zenodo.19056919\n"
        "Preprint academico -- SSRN Working Paper 6321298  (en revision por pares)"
    ),

    "regs_label": "POR QUE AHORA -- PRESION REGULATORIA",
    "regs_intro": "Los reguladores globales estan haciendo obligatoria la infraestructura de gobernanza.",
    "regs": [
        ("EU AI Act (2025+)",      "Los sistemas de IA de alto riesgo requieren auditabilidad previa, trazabilidad y controles de riesgo documentados."),
        ("MiCA (2024-2025)",       "Los proveedores de criptoactivos deben demostrar controles de riesgo operativo y marcos de gobernanza documentados."),
        ("BCB Resolucion 538",    "El Banco Central de Brasil exige trazabilidad criptografica para decisiones financieras automatizadas. Mas de 1,600 instituciones."),
        ("ADGM / SEC frameworks", "La gobernanza por diseno es el estandar de cumplimiento emergente para sistemas de IA en finanzas a nivel global."),
    ],

    "offer_label": "EL PILOTO DE 30 DIAS -- SIN COSTO, SIN COMPROMISO",
    "offer_intro": (
        "Estamos incorporando los primeros socios piloto ahora. "
        "El objetivo es validar OMNIX en multiples industrias con datos de decision reales."
    ),
    "terms": [
        ("Lo que aportas",       "Senales de decision via API o JSON  |  Umbrales de riesgo  |  Llamada de onboarding 30 min"),
        ("Lo que recibes",       "Recibo firmado por decision  |  Auditoria completa  |  Reporte de gobernanza al Dia 30"),
        ("Duracion",             "30 dias desde la fecha de integracion"),
        ("Costo",                "Gratuito -- sin cargo"),
        ("Manejo de datos",      "Todas las senales cifradas en reposo (AES-256). Sin datos compartidos entre clientes."),
        ("Despues del piloto",   "Sin obligacion. Si hay encaje mutuo, conversamos sobre un acuerdo comercial."),
    ],

    "cta_label": "CONECTEMOS",
    "cta_body":  "Escribenos y coordinamos la integracion en una reunion de 30 minutos.",
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
        self.c    = CONTENT[lang]
        self.lang = lang
        self.add_font("R", fname=FONT_REGULAR)
        self.add_font("B", fname=FONT_BOLD)
        self.set_margins(LM, TOP_M, RM)
        self.set_auto_page_break(auto=True, margin=20)

    @property
    def uw(self):
        return self.w - LM - RM

    # ── Header / Footer ───────────────────────────────────────────────────────
    def header(self):
        c = self.c
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, HEADER_H, style="F")
        self.set_fill_color(*GOLD)
        self.rect(0, HEADER_H - 0.8, self.w, 0.8, style="F")

        logo_h = HEADER_H - 5
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=5, y=2.5, w=logo_h, h=logo_h)

        tx = 5 + logo_h + 4
        self.set_xy(tx, 7)
        self.set_font("B", size=9)
        self.set_text_color(*GOLD)
        self.cell(self.w - tx - 5, 5, c["tagline"])

        self.set_xy(tx, 14)
        self.set_font("R", size=7)
        self.set_text_color(155, 170, 205)
        self.cell(self.w - tx - 5, 4, c["contact_line"])

        # Page number top-right
        pg = self.page_no()
        self.set_xy(self.w - 30, 8)
        self.set_font("R", size=7)
        self.set_text_color(120, 140, 180)
        self.cell(24, 5, f"{c['page_of']} {pg} / 3", align="R")

    def footer(self):
        c = self.c
        self.set_draw_color(*GOLD)
        self.set_line_width(0.25)
        self.line(0, self.h - 11, self.w, self.h - 11)
        self.set_fill_color(*NAVY)
        self.rect(0, self.h - 10.5, self.w, 11, style="F")
        self.set_y(self.h - 8)
        self.set_font("R", size=5.8)
        self.set_text_color(*GOLD)
        self.cell(self.w, 4, c["footer"], align="C")

    # ── Primitives ────────────────────────────────────────────────────────────
    def sp(self, h=4):
        self.ln(h)

    def tag(self, text):
        self.set_x(LM)
        self.set_font("B", size=7.5)
        self.set_text_color(*GOLD)
        self.cell(0, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def h1(self, text, size=18):
        self.set_x(LM)
        self.set_font("B", size=size)
        self.set_text_color(*NAVY)
        self.multi_cell(self.uw, size * 0.62, text)
        self.ln(2)

    def h2(self, text, size=11):
        self.set_x(LM)
        self.set_font("B", size=size)
        self.set_text_color(*NAVY)
        self.multi_cell(self.uw, size * 0.7, text)
        self.ln(2)

    def body(self, text, size=9.5, color=DARK, indent=0):
        self.set_x(LM + indent)
        self.set_font("R", size=size)
        self.set_text_color(*color)
        self.multi_cell(self.uw - indent, 5.5, text)
        self.ln(2)

    def rule(self, color=BORDER, h=0.2, gap=5):
        self.set_draw_color(*color)
        self.set_line_width(h)
        self.line(LM, self.get_y(), self.w - RM, self.get_y())
        self.ln(gap)

    def gold_rule(self, gap=6):
        self.rule(GOLD, 0.5, gap)

    def info_strip(self, text, bg, fg):
        self.set_fill_color(*bg)
        self.set_x(LM)
        self.set_font("R", size=9)
        self.set_text_color(*fg)
        self.multi_cell(self.uw, 6, f"   {text}   ", fill=True)
        self.ln(3)

    # ── PAGE 1 blocks ─────────────────────────────────────────────────────────

    def problem_section(self):
        c = self.c
        self.sp(3)
        self.tag(c["problem_label"])
        self.h1(c["problem_headline"], size=20)
        self.body(c["problem_body"])
        self.sp(2)

        # Cases title
        self.set_x(LM)
        self.set_font("B", size=9)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 6, c["cases_title"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.sp(2)

        # Case rows
        for company, amount, outcome, detail in c["cases"]:
            row_y = self.get_y()
            # Left accent bar
            self.set_fill_color(*GOLD)
            self.rect(LM, row_y, 2.5, 18, style="F")
            # Company
            self.set_xy(LM + 6, row_y + 1)
            self.set_font("B", size=10)
            self.set_text_color(*NAVY)
            self.cell(40, 6, company)
            # Amount
            self.set_font("B", size=14)
            self.set_text_color(*NAVY)
            self.cell(55, 6, amount)
            # Outcome
            self.set_font("R", size=9)
            self.set_text_color(*MID_GRAY)
            self.cell(0, 6, outcome, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            # Detail line
            self.set_xy(LM + 6, row_y + 8)
            self.set_font("R", size=8.5)
            self.set_text_color(*DARK)
            self.multi_cell(self.uw - 8, 5, detail)
            self.set_y(row_y + 20)
        self.sp(2)

        # Closing insight
        self.set_fill_color(*LIGHT_BG)
        self.set_x(LM)
        self.set_font("R", size=9)
        self.set_text_color(*DARK)
        self.multi_cell(self.uw, 6, f"   {c['problem_close']}   ", fill=True)
        self.sp(6)

    def solution_section(self):
        c = self.c
        self.gold_rule()
        self.tag(c["solution_label"])
        self.h1(c["solution_headline"], size=17)
        self.body(c["solution_body1"])
        self.body(c["solution_body2"])
        self.sp(4)

        # Property cards — 2x2 grid
        cw = (self.uw - 4) / 2
        props = c["solution_props"]
        for row in range(0, len(props), 2):
            row_y = self.get_y()
            for col in range(2):
                idx = row + col
                if idx >= len(props): break
                label, desc = props[idx]
                cx = LM + col * (cw + 4)
                # Card background
                self.set_fill_color(*LIGHT_BG)
                self.rect(cx, row_y, cw, 22, style="F")
                # Gold top stripe
                self.set_fill_color(*GOLD)
                self.rect(cx, row_y, cw, 1.2, style="F")
                # Label
                self.set_xy(cx + 4, row_y + 4)
                self.set_font("B", size=9)
                self.set_text_color(*NAVY)
                self.cell(cw - 6, 6, label)
                # Description
                self.set_xy(cx + 4, row_y + 11)
                self.set_font("R", size=8)
                self.set_text_color(*MID_GRAY)
                self.multi_cell(cw - 6, 4.5, desc)
            self.set_y(row_y + 25)

    # ── PAGE 2 blocks ─────────────────────────────────────────────────────────

    def pipeline_section(self):
        c = self.c
        self.sp(3)
        self.tag(c["pipeline_label"])
        self.body(c["pipeline_intro"], size=9.5, color=MID_GRAY)
        self.sp(2)

        w_no = 10
        w_nm = 62
        w_ds = self.uw - w_no - w_nm
        row_h = 14

        for i, (num, name, desc) in enumerate(c["checkpoints"]):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            row_y = self.get_y()
            self.set_x(LM)

            # Number cell
            self.set_font("B", size=10)
            self.set_text_color(*GOLD)
            self.cell(w_no, row_h, num, fill=True)

            # Name cell
            self.set_font("B", size=9)
            self.set_text_color(*NAVY)
            self.cell(w_nm, row_h, name, fill=True)

            # Description — multi-line
            desc_x = LM + w_no + w_nm
            self.set_xy(desc_x, row_y)
            self.set_font("R", size=8.5)
            self.set_text_color(*DARK)
            self.multi_cell(w_ds, row_h / 2, desc, fill=True)

            # Ensure consistent row height
            next_y = row_y + row_h
            if self.get_y() < next_y:
                self.set_y(next_y)

        self.sp(3)
        self.info_strip(c["pipeline_close"], BLUE_BG, BLUE_TXT)

    def sandbox_section(self):
        c = self.c
        self.sp(4)
        # Full-width dark box
        bh = 55
        by = self.get_y()
        bx = LM

        self.set_fill_color(*NAVY)
        self.rect(bx, by, self.uw, bh, style="F")
        self.set_fill_color(*GOLD)
        self.rect(bx, by, self.uw, 1, style="F")
        self.rect(bx, by, 3.5, bh, style="F")

        # Tag
        self.set_xy(bx + 8, by + 7)
        self.set_font("B", size=7.5)
        self.set_text_color(*GOLD)
        self.cell(self.uw - 12, 5, c["sandbox_label"])

        # Big URL
        self.set_xy(bx + 8, by + 14)
        self.set_font("B", size=18)
        self.set_text_color(*WHITE)
        self.cell(self.uw - 12, 10, c["sandbox_url"])

        # Body text
        self.set_xy(bx + 8, by + 26)
        self.set_font("R", size=8.5)
        self.set_text_color(185, 198, 225)
        self.multi_cell(self.uw - 14, 5.2, c["sandbox_body"])

        # CTA line
        self.set_xy(bx + 8, by + bh - 9)
        self.set_font("B", size=9)
        self.set_text_color(*GOLD_LIGHT)
        self.cell(self.uw - 12, 6, c["sandbox_cta"])

        self.set_y(by + bh + 4)

    # ── PAGE 3 blocks ─────────────────────────────────────────────────────────

    def evidence_section(self):
        c = self.c
        self.sp(3)
        self.tag(c["evidence_label"])
        self.set_x(LM)
        self.set_font("R", size=9)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 6, c["evidence_intro"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.sp(3)

        # 3 stat cards in a row
        col_w = (self.uw - 8) / 3
        stat_y = self.get_y()
        for i, (val, label, note) in enumerate(c["stats"]):
            cx = LM + i * (col_w + 4)
            # Card
            self.set_fill_color(*LIGHT_BG)
            self.rect(cx, stat_y, col_w, 30, style="F")
            self.set_fill_color(*GOLD)
            self.rect(cx, stat_y, col_w, 1.5, style="F")
            # Value
            self.set_xy(cx + 4, stat_y + 5)
            self.set_font("B", size=20)
            self.set_text_color(*NAVY)
            self.cell(col_w - 6, 12, val)
            # Label
            self.set_xy(cx + 4, stat_y + 16)
            self.set_font("R", size=7.5)
            self.set_text_color(*DARK)
            self.multi_cell(col_w - 6, 4.5, label)
            # Note
            self.set_xy(cx + 4, stat_y + 25)
            self.set_font("R", size=7)
            self.set_text_color(*MID_GRAY)
            self.cell(col_w - 6, 4, note)

        self.set_y(stat_y + 34)
        self.info_strip(c["evidence_note"], GREEN_BG, GREEN_TXT)
        self.sp(2)

    def regulatory_section(self):
        c = self.c
        self.rule()
        self.tag(c["regs_label"])
        self.set_x(LM)
        self.set_font("R", size=9)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, c["regs_intro"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.sp(2)

        w_label = 48
        w_desc  = self.uw - w_label
        for i, (reg, desc) in enumerate(c["regs"]):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            self.set_x(LM)
            self.set_font("B", size=8.5)
            self.set_text_color(*NAVY)
            self.cell(w_label, 8, f"  {reg}", fill=True)
            self.set_font("R", size=8.5)
            self.set_text_color(*DARK)
            self.multi_cell(w_desc, 8, f"  {desc}", fill=True)
        self.sp(4)

    def offer_section(self):
        c = self.c
        self.rule()
        self.tag(c["offer_label"])
        self.set_x(LM)
        self.set_font("R", size=9)
        self.set_text_color(*MID_GRAY)
        self.multi_cell(self.uw, 5.5, c["offer_intro"])
        self.sp(3)

        w_label = 42
        w_val   = self.uw - w_label
        for i, (label, val) in enumerate(c["terms"]):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            self.set_x(LM)
            self.set_font("B", size=8.5)
            self.set_text_color(*NAVY)
            self.cell(w_label, 8, f"  {label}:", fill=True)
            self.set_font("R", size=8.5)
            self.set_text_color(*DARK)
            self.multi_cell(w_val, 8, f"  {val}", fill=True)
        self.sp(5)

    def cta_section(self):
        c = self.c
        bh = 10 + len(c["contact"]) * 8 + 12
        by = self.get_y()

        self.set_fill_color(*NAVY)
        self.rect(LM, by, self.uw, bh, style="F")
        self.set_fill_color(*GOLD)
        self.rect(LM, by, self.uw, 1, style="F")
        self.rect(LM, by, 3.5, bh, style="F")

        self.set_xy(LM + 8, by + 6)
        self.set_font("B", size=8)
        self.set_text_color(*GOLD)
        self.cell(0, 5, c["cta_label"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_xy(LM + 8, by + 13)
        self.set_font("B", size=11)
        self.set_text_color(*WHITE)
        self.cell(self.uw - 12, 7, c["cta_body"],
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.sp(2)

        for label, val in c["contact"]:
            self.set_x(LM + 8)
            self.set_font("B", size=9)
            self.set_text_color(*GOLD_LIGHT)
            self.cell(28, 7.5, f"{label}:")
            self.set_font("R", size=9)
            self.set_text_color(*WHITE)
            self.cell(0, 7.5, val, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── Build ─────────────────────────────────────────────────────────────────
    def build(self):
        # Page 1: Problem + Solution
        self.add_page()
        self.problem_section()
        self.solution_section()

        # Page 2: Pipeline + Sandbox
        self.add_page()
        self.pipeline_section()
        self.sandbox_section()

        # Page 3: Evidence + Regulatory + Terms + CTA
        self.add_page()
        self.evidence_section()
        self.regulatory_section()
        self.offer_section()
        self.cta_section()


# ── MAIN ──────────────────────────────────────────────────────────────────────
def generate_lang(lang, filename):
    pdf = PilotPDF(lang=lang)
    pdf.build()
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
