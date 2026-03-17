#!/usr/bin/env python3
"""
OMNIX Quantum -- Pilot Program Proposal PDF Generator
Generates two PDFs: English (EN) and Spanish (ES).
"""
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "business", "pdfs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_DIR     = os.path.join(
    os.path.expanduser("~"),
    "workspace/.pythonlibs/lib/python3.11/site-packages/kaleido/executable/xdg/fonts/truetype/dejavu"
)
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD    = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

NAVY      = (10, 25, 60)
GOLD      = (212, 175, 55)
WHITE     = (255, 255, 255)
LIGHT_BG  = (240, 244, 252)
MID_GRAY  = (110, 120, 140)
GREEN_BG  = (235, 248, 240)
GREEN_TXT = (0, 100, 55)
BLUE_BG   = (235, 242, 255)
DARK      = (25, 25, 45)
DIVIDER   = (200, 210, 230)


# ── CONTENT DICTIONARIES ──────────────────────────────────────────────────────

CONTENT = {
    "EN": {
        "header_title": "OMNIX QUANTUM  --  Decision Governance Infrastructure",
        "header_sub":   "omnixquantum.net   |   contacto@omnixquantum.net   |   Abu Dhabi, UAE",
        "footer_text":  "Confidential  --  Pilot Program Proposal   |   Harold Nunes, Founder & CEO   |   SSRN 6321298   |   Zenodo DOI: 10.5281/zenodo.19056919",

        "hero_title":   "30-Day Pilot Program",
        "hero_sub":     "Governance Infrastructure for Automated Decision Systems  --  No Cost",

        "sec_offer":    "What We Are Offering",
        "offer_body": (
            "OMNIX Quantum provides a 30-day complimentary pilot of our Decision Governance "
            "Infrastructure. Your automated decision pipeline connects to our governance engine, "
            "which validates each decision through an 8-checkpoint veto system before execution "
            "and generates a cryptographically signed receipt for every outcome.\n\n"
            "There is no integration fee, no licensing cost, and no commitment required. "
            "The pilot is designed for organizations that want to evaluate governance "
            "infrastructure before a procurement decision."
        ),

        "sec_structure": "Pilot Structure at a Glance",
        "col1_title":   "What you provide",
        "col1_items": [
            "Your decision signals (API or JSON)",
            "Your risk thresholds / parameters",
            "30-min onboarding call",
        ],
        "col2_title":   "What you receive",
        "col2_items": [
            "Governance receipt per decision",
            "Full audit trail (PQC-signed)",
            "Governance report at Day 30",
        ],

        "sec_pipeline": "The 8-Checkpoint Governance Pipeline",
        "pipeline_sub": "Every decision passes through the full production pipeline in real time:",
        "checkpoints": [
            ("1.", "Signal Integrity Validation:",  "Is the input signal coherent and within bounds?"),
            ("2.", "Regime Assessment:",            "Is the current market/operational regime appropriate?"),
            ("3.", "Monte Carlo VETO Engine:",      "Does probability distribution support the action?"),
            ("4.", "Black Swan Detector:",          "Are there tail-risk conditions present?"),
            ("5.", "Coherence Engine (6 tiers):",   "Is there internal consistency across all signals?"),
            ("6.", "Risk Management System (RMS):", "Does the action satisfy portfolio risk constraints?"),
            ("7.", "Kelly Criterion Sizing:",       "Is the proposed position size within safe bounds?"),
            ("8.", "Final Authorization:",          "All gates passed -- governance receipt generated"),
        ],
        "receipt_box": (
            "Every decision that passes generates a cryptographically signed receipt -- "
            "independently verifiable at  omnixquantum.net/r/{receipt_id}"
        ),

        "sec_why":  "Why Governance Infrastructure Matters Now",
        "why_body": (
            "Most governance controls in automated systems are applied after execution -- "
            "audits, compliance reviews, and regulatory checks that arrive after the decision "
            "has already produced its outcome. When an automated system fails, it fails at "
            "machine speed.\n\n"
            "OMNIX moves governance to the execution boundary: decisions are validated before "
            "they are committed. The result is a structural governance property -- not an "
            "advisory layer that can be overridden."
        ),

        "sec_regs": "Regulatory Drivers",
        "regs": [
            ("EU AI Act (2025+)",     "High-risk AI systems require pre-execution auditability."),
            ("MiCA (2024-2025)",      "Crypto service providers must demonstrate operational risk controls."),
            ("BCB Resolution 538",   "Brazil mandates cryptographic audit trails for automated decisions."),
            ("ADGM / SEC frameworks","Governance-by-design is emerging as baseline for AI in finance."),
        ],

        "sec_stats": "What OMNIX Has Produced in Production",
        "stats": [
            ("72,443",  "real governance decisions processed  (Feb 21 -- Mar 16, 2026)"),
            ("100%",    "post-quantum signed  (Dilithium-3 / ML-DSA-65, NIST-standardized)"),
            ("SHA-256", "hash chain -- each receipt links to the previous, independently verifiable"),
            ("0",       "approved decisions without passing all 8 checkpoints"),
        ],
        "dataset_box": (
            "Full dataset publicly available: Zenodo DOI 10.5281/zenodo.19056919   |   "
            "Academic preprint: SSRN Working Paper 6321298  (under peer review)"
        ),

        "sec_terms": "Pilot Terms",
        "terms": [
            ("Duration",     "30 days from integration date"),
            ("Cost",         "Complimentary -- no charge"),
            ("Commitment",   "No obligation after pilot completion"),
            ("Data privacy", "Decision signals encrypted at rest (AES-256 / Fernet)"),
            ("Output",       "Full governance audit trail + Day-30 governance performance report"),
            ("Next step",    "30-minute onboarding call to define signal format and thresholds"),
        ],

        "cta_title":   "Ready to start the pilot?",
        "contact": [
            ("Email",    "contacto@omnixquantum.net"),
            ("WhatsApp", "+1 (650) 481-5494"),
            ("Demo",     "omnixquantum.net/try   (live, no login required)"),
        ],
    },

    "ES": {
        "header_title": "OMNIX QUANTUM  --  Infraestructura de Gobernanza de Decisiones",
        "header_sub":   "omnixquantum.net   |   contacto@omnixquantum.net   |   Abu Dhabi, UAE",
        "footer_text":  "Confidencial  --  Propuesta de Programa Piloto   |   Harold Nunes, Fundador y CEO   |   SSRN 6321298   |   Zenodo DOI: 10.5281/zenodo.19056919",

        "hero_title":   "Programa Piloto de 30 Dias",
        "hero_sub":     "Infraestructura de Gobernanza para Sistemas de Decision Automatizados  --  Sin Costo",

        "sec_offer":    "Que Ofrecemos",
        "offer_body": (
            "OMNIX Quantum ofrece un piloto gratuito de 30 dias de nuestra Infraestructura de "
            "Gobernanza de Decisiones. Tu pipeline de decisiones automatizadas se conecta a nuestro "
            "motor de gobernanza, que valida cada decision a traves de un sistema de veto de "
            "8 puntos de control antes de la ejecucion y genera un recibo firmado criptograficamente "
            "por cada resultado.\n\n"
            "No hay costo de integracion, ni licencias, ni compromiso posterior. El piloto esta "
            "disenado para organizaciones que desean evaluar la infraestructura de gobernanza "
            "antes de tomar una decision de adquisicion."
        ),

        "sec_structure": "Estructura del Piloto",
        "col1_title":   "Lo que aportas",
        "col1_items": [
            "Tus senales de decision (API o JSON)",
            "Tus umbrales de riesgo / parametros",
            "Llamada de onboarding de 30 min",
        ],
        "col2_title":   "Lo que recibes",
        "col2_items": [
            "Recibo de gobernanza por decision",
            "Auditoria completa (firmada PQC)",
            "Reporte de gobernanza al Dia 30",
        ],

        "sec_pipeline": "El Pipeline de Gobernanza de 8 Puntos de Control",
        "pipeline_sub": "Cada decision pasa por el pipeline de produccion completo en tiempo real:",
        "checkpoints": [
            ("1.", "Validacion de Integridad de Senal:", "La senal de entrada es coherente y esta dentro de limites?"),
            ("2.", "Evaluacion de Regimen:",             "El regimen operativo actual es apropiado?"),
            ("3.", "Motor de VETO Monte Carlo:",         "La distribucion de probabilidad soporta la accion?"),
            ("4.", "Detector de Cisne Negro:",           "Hay condiciones de riesgo de cola presentes?"),
            ("5.", "Motor de Coherencia (6 capas):",     "Hay consistencia interna entre todas las senales?"),
            ("6.", "Sistema de Gestion de Riesgo (RMS):","La accion satisface las restricciones de riesgo?"),
            ("7.", "Tamano por Criterio de Kelly:",      "El tamano de posicion propuesto esta dentro de limites?"),
            ("8.", "Autorizacion Final:",                "Todos los controles pasados -- recibo de gobernanza generado"),
        ],
        "receipt_box": (
            "Cada decision que pasa genera un recibo firmado criptograficamente -- "
            "verificable de forma independiente en  omnixquantum.net/r/{receipt_id}"
        ),

        "sec_why":  "Por Que la Gobernanza Importa Ahora",
        "why_body": (
            "La mayoria de los controles de gobernanza en sistemas automatizados se aplican "
            "despues de la ejecucion: auditorias, revisiones de cumplimiento y verificaciones "
            "regulatorias que llegan despues de que la decision ya produjo su resultado. Cuando "
            "un sistema automatizado falla, falla a velocidad de maquina.\n\n"
            "OMNIX mueve la gobernanza a la frontera de ejecucion: las decisiones se validan "
            "antes de confirmarse. El resultado es una propiedad estructural de gobernanza, "
            "no una capa de advertencia que puede ignorarse."
        ),

        "sec_regs": "Marco Regulatorio",
        "regs": [
            ("EU AI Act (2025+)",      "Los sistemas de IA de alto riesgo requieren auditabilidad previa a la ejecucion."),
            ("MiCA (2024-2025)",       "Los proveedores de criptoactivos deben demostrar controles de riesgo operativo."),
            ("BCB Resolucion 538",     "Brasil exige trazabilidad criptografica para decisiones financieras automatizadas."),
            ("ADGM / SEC frameworks",  "La gobernanza por diseno es estandar emergente para IA en finanzas."),
        ],

        "sec_stats": "Lo Que OMNIX Ha Producido en Produccion",
        "stats": [
            ("72,443",  "decisiones de gobernanza reales procesadas  (21 Feb -- 16 Mar 2026)"),
            ("100%",    "firmadas post-cuanticas  (Dilithium-3 / ML-DSA-65, estandar NIST)"),
            ("SHA-256", "cadena de hash -- cada recibo enlaza al anterior, verificable de forma independiente"),
            ("0",       "decisiones aprobadas sin pasar los 8 puntos de control"),
        ],
        "dataset_box": (
            "Dataset publico: Zenodo DOI 10.5281/zenodo.19056919   |   "
            "Preprint academico: SSRN Working Paper 6321298  (en revision por pares)"
        ),

        "sec_terms": "Terminos del Piloto",
        "terms": [
            ("Duracion",        "30 dias desde la fecha de integracion"),
            ("Costo",           "Gratuito -- sin cargo"),
            ("Compromiso",      "Sin obligacion al finalizar el piloto"),
            ("Privacidad",      "Senales cifradas en reposo (AES-256 / Fernet)"),
            ("Entregables",     "Auditoria completa + reporte de gobernanza al Dia 30"),
            ("Primer paso",     "Llamada de onboarding de 30 min para definir formato y parametros"),
        ],

        "cta_title":  "Listo para comenzar el piloto?",
        "contact": [
            ("Email",    "contacto@omnixquantum.net"),
            ("WhatsApp", "+1 (650) 481-5494"),
            ("Demo",     "omnixquantum.net/try   (en vivo, sin login)"),
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
        self.set_margins(18, 28, 18)
        self.set_auto_page_break(auto=True, margin=22)

    def header(self):
        c = self.c
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 20, style="F")
        self.set_fill_color(*GOLD)
        self.rect(0, 19.5, self.w, 0.7, style="F")
        self.set_xy(0, 5)
        self.set_font("B", size=10.5)
        self.set_text_color(*GOLD)
        self.cell(self.w, 6, c["header_title"], align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_x(0)
        self.set_font("R", size=7.5)
        self.set_text_color(*WHITE)
        self.cell(self.w, 5, c["header_sub"], align="C")

    def footer(self):
        c = self.c
        self.set_draw_color(*GOLD)
        self.set_line_width(0.4)
        self.line(0, self.h - 12, self.w, self.h - 12)
        self.set_fill_color(*NAVY)
        self.rect(0, self.h - 11.5, self.w, 12, style="F")
        self.set_y(self.h - 9.5)
        self.set_font("R", size=6)
        self.set_text_color(*GOLD)
        self.cell(self.w, 4, c["footer_text"], align="C")

    # ── layout helpers ────────────────────────────────────────────────────────

    def section_bar(self, text):
        self.set_fill_color(*NAVY)
        self.rect(self.l_margin, self.get_y(), 3, 7, style="F")
        self.set_xy(self.l_margin + 5, self.get_y())
        self.set_font("B", size=10.5)
        self.set_text_color(*NAVY)
        self.cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def body(self, text, size=9.5, indent=0):
        self.set_x(self.l_margin + indent)
        self.set_font("R", size=size)
        self.set_text_color(*DARK)
        self.multi_cell(self.w - self.l_margin - self.r_margin - indent, 5.2, text)
        self.ln(2)

    def gold_rule(self):
        self.set_draw_color(*GOLD)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def light_rule(self):
        self.set_draw_color(*DIVIDER)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def two_col_table(self, col1_title, col1_items, col2_title, col2_items):
        usable = self.w - self.l_margin - self.r_margin
        col_w  = (usable - 2) / 2
        row_h  = 6.2
        x0     = self.l_margin
        y0     = self.get_y()

        self.set_fill_color(*NAVY)
        self.set_xy(x0, y0)
        self.set_font("B", size=9)
        self.set_text_color(*WHITE)
        self.cell(col_w, 8, f"  {col1_title}", fill=True)
        self.cell(2, 8, "", fill=True)
        self.cell(col_w, 8, f"  {col2_title}", fill=True,
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        n_rows = max(len(col1_items), len(col2_items))
        for i in range(n_rows):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            left  = col1_items[i] if i < len(col1_items) else ""
            right = col2_items[i] if i < len(col2_items) else ""
            self.set_font("R", size=9)
            self.set_text_color(*DARK)
            self.set_x(x0)
            self.cell(col_w, row_h, f"  {left}",  fill=True)
            self.cell(2,     row_h, "",            fill=True)
            self.cell(col_w, row_h, f"  {right}", fill=True,
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_draw_color(*DIVIDER)
        self.set_line_width(0.3)
        height = 8 + n_rows * row_h
        self.rect(x0, y0, usable + 2, height)
        self.line(x0 + col_w, y0, x0 + col_w, y0 + height)
        self.ln(4)

    def checkpoint_row(self, num, name, desc):
        w_no = 8
        w_nm = 68
        w_ds = self.w - self.l_margin - self.r_margin - w_no - w_nm
        h    = 6
        self.set_x(self.l_margin)
        self.set_font("B", size=9)
        self.set_text_color(*NAVY)
        self.cell(w_no, h, num)
        self.cell(w_nm, h, name)
        self.set_font("R", size=9)
        self.set_text_color(*DARK)
        self.cell(w_ds, h, desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def info_box(self, text, bg, fg):
        self.set_fill_color(*bg)
        self.set_font("B", size=9)
        self.set_text_color(*fg)
        self.set_x(self.l_margin)
        self.multi_cell(self.w - self.l_margin - self.r_margin, 6, f"  {text}  ", fill=True)
        self.ln(3)

    def stat_row(self, val, desc):
        self.set_font("B", size=11)
        self.set_text_color(*NAVY)
        self.set_x(self.l_margin)
        self.cell(24, 7, val)
        self.set_font("R", size=9.5)
        self.set_text_color(*DARK)
        self.cell(0, 7, desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def term_row(self, label, val):
        self.set_font("B", size=9)
        self.set_text_color(*NAVY)
        self.set_x(self.l_margin)
        self.cell(36, 6, f"{label}:")
        self.set_font("R", size=9)
        self.set_text_color(*DARK)
        self.multi_cell(0, 6, val)

    def reg_table(self, regs):
        for i, (reg, desc) in enumerate(regs):
            bg = LIGHT_BG if i % 2 == 0 else WHITE
            self.set_fill_color(*bg)
            self.set_x(self.l_margin)
            self.set_font("B", size=9)
            self.set_text_color(*NAVY)
            self.cell(54, 6.5, f"  {reg}", fill=True)
            self.set_font("R", size=9)
            self.set_text_color(*DARK)
            self.multi_cell(0, 6.5, f"  {desc}", fill=True)
        self.ln(3)

    def cta_box(self, title, contact):
        usable = self.w - self.l_margin - self.r_margin
        box_h  = 10 + len(contact) * 6 + 4
        box_y  = self.get_y()
        self.set_fill_color(*NAVY)
        self.rect(self.l_margin, box_y, usable, box_h, style="F")
        self.set_fill_color(*GOLD)
        self.rect(self.l_margin, box_y, 3, box_h, style="F")

        self.set_xy(self.l_margin + 7, box_y + 4)
        self.set_font("B", size=11)
        self.set_text_color(*GOLD)
        self.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        for label, val in contact:
            self.set_x(self.l_margin + 7)
            self.set_font("B", size=8.5)
            self.set_text_color(180, 190, 210)
            self.cell(22, 5.5, f"{label}:")
            self.set_font("R", size=8.5)
            self.set_text_color(*WHITE)
            self.cell(0, 5.5, val, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ── pages ─────────────────────────────────────────────────────────────────

    def build_page_one(self):
        self.add_page()
        c = self.c
        self.ln(2)

        self.set_font("B", size=22)
        self.set_text_color(*NAVY)
        self.cell(0, 11, c["hero_title"], align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("R", size=10)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 6, c["hero_sub"], align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)
        self.gold_rule()

        self.section_bar(c["sec_offer"])
        self.body(c["offer_body"])
        self.ln(1)

        self.section_bar(c["sec_structure"])
        self.two_col_table(
            c["col1_title"], c["col1_items"],
            c["col2_title"], c["col2_items"]
        )

        self.section_bar(c["sec_pipeline"])
        self.body(c["pipeline_sub"])
        self.ln(1)
        for num, name, desc in c["checkpoints"]:
            self.checkpoint_row(num, name, desc)
        self.ln(3)
        self.info_box(c["receipt_box"], bg=BLUE_BG, fg=NAVY)

    def build_page_two(self):
        self.add_page()
        c = self.c
        self.ln(2)

        self.section_bar(c["sec_why"])
        self.body(c["why_body"])
        self.ln(1)

        self.section_bar(c["sec_regs"])
        self.reg_table(c["regs"])
        self.light_rule()

        self.section_bar(c["sec_stats"])
        for val, desc in c["stats"]:
            self.stat_row(val, desc)
        self.ln(2)
        self.info_box(c["dataset_box"], bg=GREEN_BG, fg=GREEN_TXT)
        self.light_rule()

        self.section_bar(c["sec_terms"])
        for label, val in c["terms"]:
            self.term_row(label, val)
        self.ln(5)

        self.cta_box(c["cta_title"], c["contact"])


# ── MAIN ──────────────────────────────────────────────────────────────────────

def generate_lang(lang, filename):
    pdf = PilotPDF(lang=lang)
    pdf.build_page_one()
    pdf.build_page_two()
    out = os.path.join(OUTPUT_DIR, filename)
    pdf.output(out)
    size_kb = os.path.getsize(out) / 1024
    print(f"[{lang}] Generated: {out}  ({size_kb:.1f} KB)")


def generate():
    generate_lang("EN", "OMNIX_Pilot_Proposal_EN.pdf")
    generate_lang("ES", "OMNIX_Pilot_Proposal_ES.pdf")
    print("Done.")


if __name__ == "__main__":
    generate()
