"""
Generate OMNIX Demo Video Guide PDF
90-second demo script + screen recording steps + text overlay guide
"""
import os
from fpdf import FPDF, XPos, YPos

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "business", "pdfs")
FONT_DIR = os.path.join(
    os.path.expanduser("~"),
    "workspace/.pythonlibs/lib/python3.11/site-packages/kaleido/executable/xdg/fonts/truetype/dejavu"
)
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD    = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

NAVY      = (10, 25, 60)
GOLD      = (195, 155, 65)
BLUE      = (0, 80, 160)
GREEN     = (20, 130, 80)
LIGHT_BG  = (245, 247, 252)
GRAY      = (120, 130, 145)
WHITE     = (255, 255, 255)
RED       = (160, 30, 30)

SCRIPT_EN = [
    ("0:00 – 0:15", "Open with the problem",
     "Every second, automated systems make financial decisions worth millions — "
     "with no governance layer to validate, constrain, or stop them if something goes wrong. "
     "When these systems fail, they fail at machine speed."),
    ("0:15 – 0:35", "Introduce OMNIX",
     "OMNIX is the governance infrastructure that sits above automated systems. "
     "Before any decision reaches execution, it passes through 8 validation checkpoints — "
     "including Monte Carlo simulation, risk scoring, coherence analysis, and cryptographic signing. "
     "Every decision leaves a permanent, verifiable audit trail."),
    ("0:35 – 0:55", "Show the live system",
     "This is the governance engine running in production right now. "
     "728,868 shadow evaluations completed. 50,688 cryptographically signed governance receipts. "
     "100 percent veto accuracy on 50 independently validated outcomes. "
     "Every receipt is signed with NIST-standardized post-quantum cryptography — "
     "tamper-proof and publicly verifiable."),
    ("0:55 – 1:10", "Show the regulatory angle",
     "Brazil's Central Bank now mandates exactly this — "
     "cryptographic audit trails, explainable automated decisions, full traceability. "
     "Compliance deadline: March 2026. Over 1,600 financial institutions must comply. "
     "OMNIX is ready today."),
    ("1:10 – 1:25", "Close with the ask",
     "OMNIX is a semifinalist at Eureka Dubai GCC 2026. "
     "We are raising 500,000 dollars in pre-seed funding — "
     "16.7 percent equity at a 3 million dollar pre-money valuation — "
     "to deploy the first institutional pilots and scale globally. "
     "Intelligence may propose. OMNIX decides whether it is allowed to act."),
]

SCRIPT_ES = [
    ("0:00 – 0:15", "Abre con el problema",
     "Cada segundo, los sistemas automatizados toman decisiones financieras por millones — "
     "sin ninguna capa de gobernanza que las valide, controle o detenga si algo sale mal. "
     "Cuando estos sistemas fallan, fallan a la velocidad de una máquina."),
    ("0:15 – 0:35", "Presenta OMNIX",
     "OMNIX es la infraestructura de gobernanza que se coloca por encima de los sistemas automatizados. "
     "Antes de que cualquier decisión llegue a ejecutarse, pasa por 8 puntos de validación — "
     "incluyendo simulación Monte Carlo, puntuación de riesgo, análisis de coherencia y firma criptográfica. "
     "Cada decisión deja un rastro de auditoría permanente y verificable."),
    ("0:35 – 0:55", "Muestra el sistema en vivo",
     "Este es el motor de gobernanza corriendo en producción ahora mismo. "
     "728,868 evaluaciones completadas. 50,688 recibos de gobernanza firmados criptográficamente. "
     "100% de precisión en los 50 resultados validados de forma independiente. "
     "Cada recibo está firmado con criptografía post-cuántica estandarizada por NIST — "
     "a prueba de manipulaciones y verificable públicamente."),
    ("0:55 – 1:10", "El ángulo regulatorio",
     "El Banco Central de Brasil ahora exige exactamente esto — "
     "trazabilidad criptográfica, decisiones automatizadas explicables, auditoría completa. "
     "Plazo de cumplimiento: marzo 2026. Más de 1,600 instituciones financieras deben cumplir. "
     "OMNIX está listo hoy."),
    ("1:10 – 1:25", "Cierra con el ask",
     "OMNIX es semifinalista en Eureka Dubai GCC 2026. "
     "Estamos levantando 500,000 dólares en pre-seed — "
     "16.7% de equity a una valoración pre-money de 3 millones de dólares — "
     "para lanzar los primeros pilotos institucionales y escalar globalmente. "
     "La inteligencia propone. OMNIX decide si se le permite actuar."),
]

RECORDING_STEPS = [
    ("Step 1 — Open the institutional website",
     "URL: https://omnixquantum.net\n"
     "Show: Hero section with live market data loading. Scroll slowly to show the stats "
     "(728,868 evaluations, 50,688 receipts). Duration: ~10 seconds."),
    ("Step 2 — Open the Governance Demo",
     "URL: https://omnixquantum.net/governance-demo\n"
     "Show: The governance pipeline interface. Click 'Run Governance Check' or equivalent button. "
     "Let the 8 checkpoints animate through — CP-0 SIV, CP-1 Monte Carlo, CP-2 RMS, etc. "
     "Duration: ~20 seconds."),
    ("Step 3 — Show a generated governance receipt",
     "Show: The receipt that appears after the governance check completes. "
     "Zoom in on the PQC signature field and the decision_id hash. "
     "Duration: ~10 seconds."),
    ("Step 4 — Open the Public Verification Server",
     "URL: https://omnibotgenesis-production.up.railway.app/verify\n"
     "Show: Paste the receipt hash into the verification field. "
     "Show the system confirming the receipt is authentic and tamper-proof. "
     "Duration: ~10 seconds."),
    ("Step 5 — End on the website or a still frame",
     "Return to https://omnixquantum.net or show the OMNIX logo + tagline: "
     "'Decision Governance Infrastructure for Automated Systems'. "
     "Duration: ~5 seconds."),
]

OVERLAY_GUIDE = [
    ("0:00 – 0:15", "TEXT ON SCREEN (white bold on dark background):",
     '"Automated systems make $1T+ in decisions daily\\nWith zero governance layer"'),
    ("0:15 – 0:35", "TEXT ON SCREEN (gold on navy):",
     '"OMNIX — 8-Checkpoint Governance Pipeline\\nEvery decision validated before execution"'),
    ("0:35 – 0:45", "TEXT ON SCREEN (white, bottom third):",
     '"728,868 shadow evaluations\\n50,688 PQC-signed receipts\\n100% veto accuracy"'),
    ("0:45 – 0:55", "TEXT ON SCREEN (white, bottom third):",
     '"Post-Quantum Cryptography\\nNIST-standardized · Tamper-proof · Publicly verifiable"'),
    ("0:55 – 1:10", "TEXT ON SCREEN (gold on dark):",
     '"Brazil BCB Resolution 538 — March 2026\\n1,600+ institutions must comply NOW\\nOMNIX is ready"'),
    ("1:10 – 1:25", "TEXT ON SCREEN (white bold, centered):",
     '"$500K Pre-Seed · 16.7% Equity · $3M Pre-Money\\nEureka GCC 2026 Semifinalist"'),
]

TOOLS = [
    ("Screen Recording", "Loom (free at loom.com) — records screen + optional webcam. "
     "Press record, navigate the URLs in order, stop when done. "
     "Download as MP4."),
    ("Adding Text Overlays", "CapCut (free, mobile or desktop) — import the MP4, "
     "add text layers at the exact timestamps shown in Section 4. "
     "Use white or gold text on semi-transparent dark background."),
    ("Adding Voiceover", "Once you have the MP3 audio file (OMNIX_Demo_Voiceover.mp3), "
     "import both the video and the audio into CapCut. "
     "Mute the original video audio, sync the voiceover to the visuals."),
    ("Export Settings", "Export at 1080p (1920x1080), MP4 format, H.264 codec. "
     "Keep file size under 100MB for easy upload to Eureka submission portal."),
]


class DemoGuidePDF(FPDF):
    def header(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 12, "F")
        self.set_font("DejaVu", "B", 8)
        self.set_text_color(*GOLD)
        self.set_xy(10, 2)
        self.cell(0, 8, "OMNIX — Demo Video Guide  |  Eureka GCC 2026", align="L")
        self.ln(4)

    def footer(self):
        self.set_y(-13)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*GRAY)
        self.cell(0, 5, "March 2026  |  Confidential  |  Harold Nunes", align="L", new_x=XPos.RIGHT)
        self.cell(0, 5, f"Page {self.page_no()}", align="R")

    def section_title(self, text, color=None):
        self.set_font("DejaVu", "B", 12)
        self.set_text_color(*(color or NAVY))
        self.set_fill_color(*LIGHT_BG)
        self.ln(3)
        self.cell(0, 9, f"  {text}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def timestamp_block(self, ts, subtitle, body, bg=None):
        self.set_fill_color(*(bg or NAVY))
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(*GOLD)
        self.cell(36, 8, ts, fill=True, align="C")
        self.set_text_color(*(WHITE if bg else NAVY))
        self.cell(0, 8, f"  {subtitle}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("DejaVu", "", 9)
        self.set_text_color(40, 40, 60)
        self.multi_cell(0, 5, body)
        self.ln(3)


def generate():
    pdf = DemoGuidePDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("DejaVu", "", FONT_REGULAR)
    pdf.add_font("DejaVu", "B", FONT_BOLD)

    pdf.add_page()

    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 14, pdf.w, 38, "F")
    pdf.set_font("DejaVu", "B", 20)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(10, 18)
    pdf.cell(0, 10, "OMNIX — Demo Video Guide", align="L")
    pdf.set_font("DejaVu", "", 11)
    pdf.set_text_color(*GOLD)
    pdf.set_xy(10, 30)
    pdf.cell(0, 8, "90-Second Product Demo  |  Eureka GCC 2026 Submission", align="L")
    pdf.set_xy(10, 40)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(180, 195, 215)
    pdf.cell(0, 6, "English Script  |  Spanish Translation  |  Screen Recording Steps  |  Text Overlay Guide  |  Tools", align="L")
    pdf.ln(28)

    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(0, 5,
        "This guide contains everything needed to record a professional 90-second demo video of OMNIX. "
        "The video can be submitted to Eureka GCC 2026 as supporting evidence of a live, working system. "
        "Two versions are covered: (A) Silent video with text overlays, and (B) Video with AI voiceover.")
    pdf.ln(4)

    pdf.section_title("SECTION 1 — English Script (90 seconds)")
    for ts, subtitle, body in SCRIPT_EN:
        pdf.timestamp_block(ts, subtitle, body)

    pdf.section_title("SECTION 2 — Spanish Translation (Traduccion al Espanol)")
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, "Use this to understand the script or narrate in Spanish if the event allows it.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    for ts, subtitle, body in SCRIPT_ES:
        pdf.timestamp_block(ts, subtitle, body, bg=(30, 50, 100))

    pdf.add_page()
    pdf.section_title("SECTION 3 — Screen Recording Steps (What to Navigate)")
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, "Follow these steps in order while recording your screen.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    for i, (title, detail) in enumerate(RECORDING_STEPS):
        pdf.set_fill_color(*LIGHT_BG)
        pdf.set_font("DejaVu", "B", 9)
        pdf.set_text_color(*BLUE)
        pdf.cell(0, 8, f"  {title}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(40, 40, 60)
        pdf.multi_cell(0, 5, detail)
        pdf.ln(3)

    pdf.section_title("SECTION 4 — Text Overlay Guide (Silent Video Version)")
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, "Add these text overlays at the timestamps shown using CapCut or any video editor.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    for ts, label, text in OVERLAY_GUIDE:
        pdf.set_font("DejaVu", "B", 9)
        pdf.set_text_color(*WHITE)
        pdf.set_fill_color(*NAVY)
        pdf.cell(32, 7, ts, fill=True, align="C")
        pdf.set_text_color(*GOLD)
        pdf.cell(0, 7, f"  {label}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(40, 40, 60)
        pdf.set_fill_color(235, 240, 255)
        pdf.multi_cell(0, 5, text, fill=True)
        pdf.ln(3)

    pdf.add_page()
    pdf.section_title("SECTION 5 — Recommended Tools")
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, "All tools listed are free. No technical experience required.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    for tool, desc in TOOLS:
        pdf.set_fill_color(*NAVY)
        pdf.set_font("DejaVu", "B", 9)
        pdf.set_text_color(*WHITE)
        pdf.cell(0, 8, f"  {tool}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(40, 40, 60)
        pdf.multi_cell(0, 5, desc)
        pdf.ln(3)

    pdf.section_title("QUICK CHECKLIST — Before You Record")
    checklist = [
        "Open https://omnixquantum.net in a clean browser window (no other tabs visible)",
        "Close all notifications, Slack, email popups",
        "Set browser zoom to 100% — text should be clearly readable",
        "Check that https://omnixquantum.net/governance-demo loads correctly",
        "Have the Verification URL ready in another tab (see Section 3, Step 4)",
        "Start Loom recording — select 'Full Screen' or 'Browser Tab'",
        "Navigate slowly and deliberately — 2-3 seconds per action",
        "Stop recording after Step 5 (total: ~75-90 seconds)",
    ]
    col_w = pdf.w - pdf.l_margin - pdf.r_margin
    for item in checklist:
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(*NAVY)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(col_w, 6, f"• {item}")

    pdf.ln(5)
    pdf.set_fill_color(*NAVY)
    pdf.rect(pdf.l_margin, pdf.get_y(), pdf.w - pdf.l_margin - pdf.r_margin, 16, "F")
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(*GOLD)
    pdf.set_xy(pdf.l_margin + 4, pdf.get_y() + 3)
    pdf.cell(0, 10, "Intelligence may propose. OMNIX decides whether it is allowed to act.")

    out = os.path.join(OUTPUT_DIR, "OMNIX_Demo_Video_Guide.pdf")
    pdf.output(out)
    size_kb = os.path.getsize(out) / 1024
    print(f"Generated: {out}")
    print(f"File size: {size_kb:.1f} KB")


if __name__ == "__main__":
    generate()
