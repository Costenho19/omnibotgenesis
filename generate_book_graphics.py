"""
Ghost Compliance — Book Graphics Generator
Produces 11 institutional-quality charts for both EN and ES PDFs.
Color scheme: Navy / Gold / Slate (matches book brand).
"""
import os, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patches as mpl_patches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Arc
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.gridspec import GridSpec

OUT = '/tmp/book_imgs'
os.makedirs(OUT, exist_ok=True)

# ── Brand palette ──────────────────────────────────────────────────────────────
NAVY      = '#0A1628'
NAVY_MID  = '#0D1E35'
GOLD      = '#C9A227'
GOLD_L    = '#E8D08A'
SLATE     = '#2C3E50'
LIGHT_BG  = '#F4F1EB'
MID_GRAY  = '#888888'
WHITE     = '#FFFFFF'
RED_ALERT = '#C0392B'
GREEN_OK  = '#27AE60'
AMBER     = '#E67E22'

DPI = 180
FIG_W, FIG_H = 12, 7

def base_fig(w=FIG_W, h=FIG_H, bg=LIGHT_BG):
    fig = plt.figure(figsize=(w, h), facecolor=bg)
    return fig

def add_branding(fig, title_left='', title_right='OMNIX QUANTUM'):
    fig.text(0.015, 0.985, title_left, ha='left', va='top',
             fontsize=7.5, color=MID_GRAY, fontweight='normal',
             fontfamily='DejaVu Sans')
    fig.text(0.985, 0.985, title_right, ha='right', va='top',
             fontsize=7.5, color=GOLD, fontweight='bold',
             fontfamily='DejaVu Sans')
    fig.add_artist(plt.Line2D([0.015, 0.985], [0.968, 0.968],
                              transform=fig.transFigure,
                              color=GOLD, linewidth=0.8, alpha=0.7))

def save(fig, fname):
    path = os.path.join(OUT, fname)
    fig.savefig(path, dpi=DPI, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  ✓ {fname}')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 01 — Ghost Compliance: The Photograph vs. Reality Gap
# ──────────────────────────────────────────────────────────────────────────────
def g01():
    fig, ax = base_fig(12, 6.5), None
    fig.patch.set_facecolor(LIGHT_BG)
    ax = fig.add_subplot(111, facecolor=LIGHT_BG)

    t = np.linspace(0, 36, 360)

    # Reality: drifts down steadily then collapses
    reality = np.where(t < 24,
                       100 - 0.8*t - 0.04*t**2 + np.random.normal(0, 1.2, 360),
                       100 - 0.8*24 - 0.04*576 - 8*(t-24)**1.4)
    reality = np.clip(reality, -20, 100)

    # Governance snapshot: flat between audit events (discrete steps)
    audit_times = [0, 6, 12, 18, 24, 30]
    gov = np.ones_like(t) * 100
    for i in range(len(audit_times)-1):
        mask = (t >= audit_times[i]) & (t < audit_times[i+1])
        val = np.interp(audit_times[i], t, reality)
        gov[mask] = val
    mask = t >= 30
    gov[mask] = np.interp(30, t, reality)

    ax.fill_between(t, gov, reality,
                    where=(gov > reality),
                    alpha=0.18, color=RED_ALERT, label='_nolegend_')

    ax.plot(t, gov, color=GOLD, linewidth=2.8, label='Governance Snapshot',
            linestyle='--', dashes=(6, 3))
    ax.plot(t, reality, color=NAVY, linewidth=2.8, label='Entity Reality')

    # Audit event markers
    for at in audit_times[1:]:
        rv = np.interp(at, t, reality)
        ax.axvline(at, color=MID_GRAY, linewidth=0.7, linestyle=':', alpha=0.6)
        ax.scatter([at], [rv], color=GOLD, s=60, zorder=5)

    # Annotations
    ax.annotate('GHOST COMPLIANCE\nZONE', xy=(20, 55), xytext=(16, 30),
                fontsize=9, color=RED_ALERT, fontweight='bold',
                ha='center',
                arrowprops=dict(arrowstyle='->', color=RED_ALERT, lw=1.5))
    ax.annotate('Governance assumes\nentity still valid', xy=(28, gov[280]),
                xytext=(26, 78),
                fontsize=8, color=GOLD, ha='center',
                arrowprops=dict(arrowstyle='->', color=GOLD, lw=1.2))
    ax.annotate('Reality: structural\ndegradation underway', xy=(28, reality[280]),
                xytext=(31.5, 20),
                fontsize=8, color=NAVY, ha='center',
                arrowprops=dict(arrowstyle='->', color=NAVY, lw=1.2))

    ax.set_xlabel('Months Since Admission', fontsize=10, color=SLATE, labelpad=8)
    ax.set_ylabel('Governance Validity Score', fontsize=10, color=SLATE, labelpad=8)
    ax.set_title('The Photograph Problem: Governance Snapshot vs. Entity Reality',
                 fontsize=13, color=NAVY, fontweight='bold', pad=14)
    ax.legend(fontsize=9, loc='upper right', framealpha=0.85)
    ax.set_xlim(0, 36); ax.set_ylim(-25, 108)
    ax.set_xticks(audit_times)
    ax.set_xticklabels([f'M{x}' for x in audit_times], color=SLATE, fontsize=9)
    ax.yaxis.set_tick_params(labelcolor=SLATE, labelsize=9)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(MID_GRAY); ax.spines['bottom'].set_color(MID_GRAY)
    ax.set_facecolor(LIGHT_BG)
    add_branding(fig, 'FIGURE 1 — The Photograph vs. Reality Gap')
    save(fig, '01_ghost_compliance.png')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 02 — AVM Six Signals Radar
# ──────────────────────────────────────────────────────────────────────────────
def g02():
    fig = base_fig(13, 7.5)
    fig.patch.set_facecolor(LIGHT_BG)

    labels = ['Probability\nScore', 'Signal\nCoherence', 'Risk\nExposure',
              'Stress\nResilience', 'Trend\nPersistence', 'Logic\nConsistency']
    N = len(labels)
    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1]

    # Three scenarios: at admission, current (healthy), current (degraded)
    admission   = [0.88, 0.91, 0.85, 0.87, 0.84, 0.90]
    healthy     = [0.82, 0.85, 0.78, 0.81, 0.79, 0.86]
    degraded    = [0.52, 0.61, 0.38, 0.47, 0.31, 0.44]

    for vals, color, label, lw, ls in [
        (admission, GOLD,      'At Admission (Reference State)', 2.2, '--'),
        (healthy,   GREEN_OK,  'Current — Nominal',              2.0, '-'),
        (degraded,  RED_ALERT, 'Current — Governance Alert',     2.2, '-'),
    ]:
        v = vals + vals[:1]
        ax_r = fig.add_subplot(111, polar=True)
        ax_r.clear()
        break

    ax_r = fig.add_subplot(111, polar=True)
    ax_r.set_facecolor('#EEE9DF')

    for vals, color, label, lw, ls, alpha in [
        (admission, GOLD,      'At Admission (Reference State)', 2.2, '--', 0.25),
        (healthy,   GREEN_OK,  'Current — Nominal',              2.0, '-',  0.20),
        (degraded,  RED_ALERT, 'Current — Alert',                2.2, '-',  0.25),
    ]:
        v = vals + vals[:1]
        ax_r.plot(angles, v, color=color, linewidth=lw, linestyle=ls, label=label)
        ax_r.fill(angles, v, alpha=alpha, color=color)

    ax_r.set_xticks(angles[:-1])
    ax_r.set_xticklabels(labels, size=10, color=NAVY, fontweight='bold')
    ax_r.set_ylim(0, 1)
    ax_r.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax_r.set_yticklabels(['0.25', '0.50', '0.75', '1.00'],
                          size=7.5, color=MID_GRAY)
    ax_r.tick_params(pad=16)
    ax_r.spines['polar'].set_color(MID_GRAY)
    ax_r.grid(color=MID_GRAY, alpha=0.4, linewidth=0.6)

    ax_r.set_title('AVM — Six-Signal Assumption Validity Monitor',
                   fontsize=13, color=NAVY, fontweight='bold', pad=28)

    ax_r.legend(loc='lower center', bbox_to_anchor=(0.5, -0.22),
                ncol=3, fontsize=9, framealpha=0.85)
    fig.subplots_adjust(left=0.10, right=0.90, top=0.84, bottom=0.18)
    add_branding(fig, 'FIGURE 2 — AVM Six Signals Radar')
    save(fig, '02_avm_signals.png')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 03 — OMNIX Full Architecture Five-Layer Diagram
# ──────────────────────────────────────────────────────────────────────────────
def g03():
    fig = base_fig(12, 7.2)
    fig.patch.set_facecolor(LIGHT_BG)
    ax = fig.add_axes([0.02, 0.03, 0.96, 0.84])
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.2)
    ax.axis('off')

    layers = [
        (6.2, NAVY,      WHITE,  'LAYER 0 — Structural Admissibility Engine (SAE)',
         'Pre-validation: schema, jurisdiction gate, conditional bind gate'),
        (5.0, SLATE,     WHITE,  'LAYER 1 — Context Admission Gate (CAG)',
         'Four-axis screening: market · regulatory · counterparty · temporal'),
        (3.8, '#1A5276', WHITE,  'LAYER 2 — Assumption Validity Monitor (AVM)',
         'Six-signal continuous monitoring: drift detection · AVM recalibration · WAL chain'),
        (2.6, '#1E8449', WHITE,  'LAYER 3 — Systemic Risk Radar (SRR)',
         'Cross-entity contagion detection · correlation monitoring · concentration limits'),
        (1.4, '#784212', WHITE,  'LAYER 4 — Forensic Audit Trail (FAT)',
         'PQC-signed receipts · human override records · anti-replay protection'),
    ]

    for y, bg, fg, title, desc in layers:
        rect = FancyBboxPatch((0.4, y - 0.52), 11.2, 0.95,
                              boxstyle='round,pad=0.06',
                              facecolor=bg, edgecolor=GOLD, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(6.0, y + 0.12, title, ha='center', va='center',
                fontsize=10.5, color=fg, fontweight='bold')
        ax.text(6.0, y - 0.22, desc, ha='center', va='center',
                fontsize=8.2, color=GOLD_L, style='italic')

    # Arrows between layers
    for y_top in [5.48, 4.28, 3.08, 1.88]:
        ax.annotate('', xy=(6, y_top - 0.26), xytext=(6, y_top),
                    arrowprops=dict(arrowstyle='->', color=GOLD, lw=2))

    ax.text(6.0, 6.98, 'OMNIX QUANTUM — Decision Governance Architecture',
            ha='center', va='top', fontsize=14, color=NAVY,
            fontweight='bold')
    ax.text(6.0, 6.72, 'Five-Layer Defense · Eleven-Checkpoint Pipeline · Post-Quantum Cryptography',
            ha='center', va='top', fontsize=9, color=SLATE, style='italic')

    # Decision output
    rect2 = FancyBboxPatch((3.5, 0.08), 5.0, 0.65,
                            boxstyle='round,pad=0.06',
                            facecolor=GOLD, edgecolor=NAVY, linewidth=2)
    ax.add_patch(rect2)
    ax.text(6.0, 0.42, 'GOVERNANCE DECISION + PQC-SIGNED FAT RECEIPT',
            ha='center', va='center', fontsize=9.5, color=NAVY, fontweight='bold')

    add_branding(fig, 'FIGURE 3 — Five-Layer Architecture')
    save(fig, '03_architecture.png')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 04 — Nine Governance Verticals
# ──────────────────────────────────────────────────────────────────────────────
def g04():
    fig = base_fig(12, 7)
    fig.patch.set_facecolor(LIGHT_BG)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.84])
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.8)
    ax.axis('off')

    # Center
    cx, cy = 6.0, 3.7
    circle_c = plt.Circle((cx, cy), 0.9, facecolor=NAVY, edgecolor=GOLD, linewidth=3)
    ax.add_patch(circle_c)
    ax.text(cx, cy + 0.15, 'OMNIX', ha='center', va='center',
            fontsize=11, color=WHITE, fontweight='bold')
    ax.text(cx, cy - 0.22, 'CORE', ha='center', va='center',
            fontsize=8, color=GOLD)

    domains = [
        ('Trading',        '#1A5276', 'TRD'),
        ('Islamic Credit', '#784212', 'CRD'),
        ('Insurance',      '#1E8449', 'INS'),
        ('Robotics',       '#6C3483', 'RBT'),
        ('Medical AI',     '#C0392B', 'MED'),
        ('Real Estate',    '#117A65', 'REP'),
        ('Energy',         '#935116', 'EGV'),
        ('Stablecoins',    '#1F618D', 'STB'),
        ('Autonomous\nAgents', '#2C3E50', 'AGT'),
    ]

    for i, (name, color, code) in enumerate(domains):
        angle = (i / 9) * 2 * math.pi - math.pi / 2
        r = 2.7
        dx = r * math.cos(angle)
        dy = r * math.sin(angle)
        x, y = cx + dx, cy + dy

        # spoke
        ax.annotate('', xy=(cx + 0.9*math.cos(angle), cy + 0.9*math.sin(angle)),
                    xytext=(x - 0.6*math.cos(angle), y - 0.6*math.sin(angle)),
                    arrowprops=dict(arrowstyle='-', color=GOLD, lw=1.2, alpha=0.7))

        circle = plt.Circle((x, y), 0.65,
                              facecolor=color, edgecolor=GOLD, linewidth=1.8, alpha=0.92)
        ax.add_patch(circle)
        ax.text(x, y + 0.10, code, ha='center', va='center',
                fontsize=8, color=WHITE, fontweight='bold')
        ax.text(x, y - 0.20, name, ha='center', va='center',
                fontsize=6.8, color=GOLD_L)

    ax.text(cx, 6.75, 'Nine Governance Verticals — Universal Architecture, Domain Calibration',
            ha='center', va='top', fontsize=13, color=NAVY, fontweight='bold')
    ax.text(cx, 6.48, 'Same six signals · Same eleven checkpoints · Same PQC receipt — calibrated per domain',
            ha='center', va='top', fontsize=8.8, color=SLATE, style='italic')

    add_branding(fig, 'FIGURE 4 — Nine Governance Verticals')
    save(fig, '04_nine_domains.png')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 05 — Forensic Audit Trail Four-Round Process
# ──────────────────────────────────────────────────────────────────────────────
def g05():
    fig = base_fig(12, 6.8)
    fig.patch.set_facecolor(LIGHT_BG)
    ax = fig.add_axes([0.02, 0.03, 0.96, 0.84])
    ax.set_xlim(0, 12); ax.set_ylim(0, 6.8)
    ax.axis('off')

    rounds = [
        ('ROUND 1', 'Pre-Decision\nCapture',
         ['Entity state snapshot', 'Context hash', 'Signal inputs', 'AVM baseline'],
         '#1A5276'),
        ('ROUND 2', 'Pipeline\nEvaluation',
         ['11-checkpoint results', 'Hard block assessment', 'Override triggers', 'Composite score'],
         SLATE),
        ('ROUND 3', 'Decision\nRecord',
         ['Governance decision', 'Human override (if any)', 'Authority credentials', 'Timestamp'],
         '#1E8449'),
        ('ROUND 4', 'Execution\nBinding',
         ['Execution intent', 'Execution receipt', 'Outcome binding', 'PQC final seal'],
         '#784212'),
    ]

    box_w = 2.5
    starts = [0.3, 3.2, 6.1, 9.0]

    for i, ((rnd, title, items, color), x0) in enumerate(zip(rounds, starts)):
        # Header
        rect = FancyBboxPatch((x0, 4.2), box_w, 1.7,
                               boxstyle='round,pad=0.07',
                               facecolor=color, edgecolor=GOLD, linewidth=1.8)
        ax.add_patch(rect)
        ax.text(x0 + box_w/2, 5.52, rnd, ha='center', va='center',
                fontsize=9, color=GOLD, fontweight='bold')
        ax.text(x0 + box_w/2, 5.08, title, ha='center', va='center',
                fontsize=10.5, color=WHITE, fontweight='bold')

        # Items
        for j, item in enumerate(items):
            y_item = 3.7 - j*0.55
            ax.add_patch(FancyBboxPatch((x0, y_item - 0.2), box_w, 0.38,
                                         boxstyle='round,pad=0.04',
                                         facecolor=WHITE, edgecolor=color, linewidth=1))
            ax.text(x0 + box_w/2, y_item, item,
                    ha='center', va='center', fontsize=8, color=SLATE)

        # Arrow to next
        if i < 3:
            ax.annotate('', xy=(starts[i+1], 5.08),
                        xytext=(x0 + box_w + 0.02, 5.08),
                        arrowprops=dict(arrowstyle='->', color=GOLD, lw=2.2))

    # PQC seal indicator
    ax.add_patch(FancyBboxPatch((3.5, 0.15), 5.0, 0.7,
                                 boxstyle='round,pad=0.07',
                                 facecolor=NAVY, edgecolor=GOLD, linewidth=2))
    ax.text(6.0, 0.52, 'ML-DSA-65 (Dilithium-3)  ·  Post-Quantum Signed  ·  Immutable',
            ha='center', va='center', fontsize=9, color=GOLD, fontweight='bold')

    ax.text(6.0, 6.62, 'Forensic Audit Trail — Four-Round Governance Evidence Chain',
            ha='center', va='top', fontsize=13, color=NAVY, fontweight='bold')

    add_branding(fig, 'FIGURE 5 — Forensic Audit Trail')
    save(fig, '05_forensic_trail.png')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 06 — Post-Quantum Threat Timeline
# ──────────────────────────────────────────────────────────────────────────────
def g06():
    fig, ax = plt.subplots(figsize=(12, 6.5), facecolor=LIGHT_BG)
    ax.set_facecolor(LIGHT_BG)

    years = np.array([2020, 2024, 2028, 2032, 2035, 2040])
    quantum_threat = np.array([5, 15, 40, 72, 88, 98])
    classical_safe = np.array([98, 90, 68, 35, 18, 4])
    pqc_protected  = np.array([0, 82, 90, 93, 96, 98])

    ax.fill_between(years, classical_safe, alpha=0.15, color=RED_ALERT)
    ax.fill_between(years, pqc_protected,  alpha=0.15, color=GREEN_OK)

    ax.plot(years, quantum_threat, color=RED_ALERT, linewidth=2.8,
            label='Quantum Threat Level', marker='o', markersize=6)
    ax.plot(years, classical_safe, color=AMBER,     linewidth=2.8,
            label='Classical Cryptography Safety', marker='s', markersize=6,
            linestyle='--', dashes=(6,3))
    ax.plot(years, pqc_protected,  color=GREEN_OK,  linewidth=2.8,
            label='PQC-Protected Records (OMNIX)', marker='^', markersize=7)

    # Key events
    events = {
        2024: ('NIST PQC\nStandards\nPublished', 0.52),
        2028: ('Migration\nWindow\nCloses', 0.42),
        2035: ('Quantum\nThreat\nPeak', 0.90),
    }
    for yr, (lbl, y_frac) in events.items():
        ax.axvline(yr, color=MID_GRAY, linewidth=0.9, linestyle=':', alpha=0.7)
        ax.text(yr, y_frac * 100 + 3, lbl, ha='center', fontsize=7.5,
                color=NAVY, style='italic',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=WHITE,
                          edgecolor=GOLD, alpha=0.85))

    ax.set_xlim(2020, 2040)
    ax.set_ylim(0, 105)
    ax.set_xlabel('Year', fontsize=10, color=SLATE, labelpad=8)
    ax.set_ylabel('Index (0–100)', fontsize=10, color=SLATE, labelpad=8)
    ax.set_title('Post-Quantum Cryptography Threat Timeline — 2020 to 2040',
                 fontsize=13, color=NAVY, fontweight='bold', pad=14)
    ax.legend(fontsize=9, loc='center right', framealpha=0.88)
    ax.set_xticks(years)
    ax.tick_params(colors=SLATE)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(MID_GRAY); ax.spines['bottom'].set_color(MID_GRAY)

    add_branding(fig, 'FIGURE 6 — Post-Quantum Threat Timeline')
    save(fig, '06_pqc_timeline.png')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 07 — MiCA Framework Three Asset Categories
# ──────────────────────────────────────────────────────────────────────────────
def g07():
    fig = base_fig(12, 7.2)
    fig.patch.set_facecolor(LIGHT_BG)
    ax = fig.add_axes([0.02, 0.03, 0.96, 0.84])
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.2)
    ax.axis('off')

    # ── Main title (top, clear of everything)
    ax.text(6.0, 7.10, 'MiCA Framework — Three Asset Categories and OMNIX Alignment',
            ha='center', va='top', fontsize=13, color=NAVY, fontweight='bold')

    # ── Regulation header banner (below title, does NOT overlap category boxes)
    rect_top = FancyBboxPatch((1.0, 6.30), 10.0, 0.58,
                               boxstyle='round,pad=0.08',
                               facecolor=NAVY, edgecolor=GOLD, linewidth=2)
    ax.add_patch(rect_top)
    ax.text(6.0, 6.59, 'MiCA — Regulation (EU) 2023/1114 — Markets in Crypto-Assets',
            ha='center', va='center', fontsize=11, color=WHITE, fontweight='bold')

    # ── Three category boxes  (top=6.10, clear of header bottom=6.30 with 0.20 gap)
    categories = [
        ('Asset-Referenced\nTokens (ART)',
         ['Backed by basket of assets', 'Art. 36: continuous reserve',
          'Monthly reserve attestation', 'Redemption rights guaranteed',
          'OMNIX: Signal 1 + Signal 3'],
         '#1A5276', 2.0),
        ('Electronic Money\nTokens (EMT)',
         ['Pegged to single fiat currency', 'Credit institution required',
          'EBA oversight', 'Daily redemption at par',
          'OMNIX: Anti-replay + Signal 2'],
         '#1E8449', 6.0),
        ('Other Crypto-Assets\n(General MiCA)',
         ['Utility tokens, NFTs', 'Whitepaper requirement',
          'Marketing restrictions', 'Insider dealing rules',
          'OMNIX: Systemic Risk Radar'],
         SLATE, 10.0),
    ]
    box_h = 2.75
    box_w = 3.2
    box_y0 = 3.25   # bottom of category boxes

    for title, items, color, x_center in categories:
        x0 = x_center - box_w / 2
        rect = FancyBboxPatch((x0, box_y0), box_w, box_h,
                               boxstyle='round,pad=0.08',
                               facecolor=color, edgecolor=GOLD, linewidth=2)
        ax.add_patch(rect)
        ax.text(x_center, box_y0 + box_h - 0.38, title,
                ha='center', va='center',
                fontsize=10, color=WHITE, fontweight='bold')

        for j, item in enumerate(items):
            y_i = box_y0 + box_h - 0.95 - j * 0.40
            bullet = '▸ ' if 'OMNIX' not in item else '● '
            fc = GOLD_L if 'OMNIX' in item else WHITE
            fs = 7.8 if 'OMNIX' in item else 7.5
            fw = 'bold' if 'OMNIX' in item else 'normal'
            ax.text(x_center, y_i, bullet + item,
                    ha='center', va='center', fontsize=fs, color=fc, fontweight=fw)

    # ── Common requirements bar (bottom)
    rect_bot = FancyBboxPatch((0.5, 0.14), 11.0, 1.65,
                               boxstyle='round,pad=0.08',
                               facecolor='#F0EBE0', edgecolor=MID_GRAY, linewidth=1)
    ax.add_patch(rect_bot)
    ax.text(6.0, 1.55, 'Common MiCA Requirements across all categories:',
            ha='center', va='center', fontsize=8.5, color=NAVY, fontweight='bold')
    commons = ('Whitepaper disclosure  ·  Conflicts of interest rules  ·  '
               'Complaint handling  ·  Cybersecurity requirements  ·  Reserve custody standards')
    ax.text(6.0, 1.10, commons,
            ha='center', va='center', fontsize=8, color=SLATE)
    ax.text(6.0, 0.58,
            'OMNIX satisfies all cross-cutting requirements through continuous monitoring, '
            'PQC-signed receipts, and the Anti-Replay gate.',
            ha='center', va='center', fontsize=7.8, color=NAVY, style='italic')

    add_branding(fig, 'FIGURE 7 — MiCA Framework')
    save(fig, '07_mica_framework.png')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 08 — VARA Framework Eight Rulebooks
# ──────────────────────────────────────────────────────────────────────────────
def g08():
    fig = base_fig(12, 7)
    fig.patch.set_facecolor(LIGHT_BG)
    ax = fig.add_axes([0.02, 0.03, 0.96, 0.84])
    ax.set_xlim(0, 12); ax.set_ylim(0, 7)
    ax.axis('off')

    rulebooks = [
        ('VA Issuance\nRulebook',      '#1A5276'),
        ('VA Transfer &\nSettlement',   '#1E8449'),
        ('VA Exchange\nRulebook',       '#784212'),
        ('VA Broker-Dealer\nRulebook',  '#6C3483'),
        ('VA Management &\nInvestment', '#117A65'),
        ('Lending & Borrowing\nRulebook','#935116'),
        ('VA Custody\nRulebook',        '#1F618D'),
        ('VA Advisory\nRulebook',       SLATE),
    ]

    positions = [
        (1.5, 5.2), (4.0, 5.2), (6.5, 5.2), (9.5, 5.2),
        (1.5, 3.2), (4.0, 3.2), (6.5, 3.2), (9.5, 3.2),
    ]

    for (name, color), (x, y) in zip(rulebooks, positions):
        rect = FancyBboxPatch((x - 1.3, y - 0.65), 2.6, 1.25,
                               boxstyle='round,pad=0.07',
                               facecolor=color, edgecolor=GOLD, linewidth=1.8)
        ax.add_patch(rect)
        ax.text(x, y, name, ha='center', va='center',
                fontsize=8.5, color=WHITE, fontweight='bold')

    # Center connector
    for (x, y) in positions:
        ax.plot([x, 6.0], [y, 4.22], color=GOLD, lw=0.7, alpha=0.4, linestyle=':')

    circle_c = plt.Circle((6.0, 4.22), 0.72,
                            facecolor=NAVY, edgecolor=GOLD, linewidth=3)
    ax.add_patch(circle_c)
    ax.text(6.0, 4.32, 'VARA', ha='center', va='center',
            fontsize=11, color=WHITE, fontweight='bold')
    ax.text(6.0, 4.08, 'CORE', ha='center', va='center',
            fontsize=7.5, color=GOLD)

    # OMNIX alignment bar
    rect_bot = FancyBboxPatch((0.5, 0.15), 11.0, 1.5,
                               boxstyle='round,pad=0.08',
                               facecolor=NAVY, edgecolor=GOLD, linewidth=2)
    ax.add_patch(rect_bot)
    ax.text(6.0, 1.22, 'OMNIX Alignment with VARA Requirements',
            ha='center', va='center', fontsize=10, color=GOLD, fontweight='bold')
    ax.text(6.0, 0.85, 'Continuous governance  ·  PQC-signed receipts  ·  Documented decision trail',
            ha='center', va='center', fontsize=8.5, color=WHITE)
    ax.text(6.0, 0.50, 'Technology-native compliance  ·  Regulatory-ready audit trail  ·  Real-time AVM monitoring',
            ha='center', va='center', fontsize=8.5, color=GOLD_L)

    ax.text(6.0, 6.85, 'VARA Framework — Eight Activity Rulebooks',
            ha='center', va='top', fontsize=13, color=NAVY, fontweight='bold')
    ax.text(6.0, 6.58, 'Virtual Assets Regulatory Authority — Dubai Law No. 4 of 2022',
            ha='center', va='top', fontsize=9, color=SLATE, style='italic')

    add_branding(fig, 'FIGURE 8 — VARA Framework')
    save(fig, '08_vara_framework.png')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 09 — EU AI Act Risk Pyramid
# ──────────────────────────────────────────────────────────────────────────────
def g09():
    fig = base_fig(12, 7)
    fig.patch.set_facecolor(LIGHT_BG)
    ax = fig.add_axes([0.05, 0.05, 0.52, 0.88])
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.axis('off')

    # Pyramid levels
    levels = [
        (1.0, 1.8, RED_ALERT,  'UNACCEPTABLE RISK',
         'Prohibited AI practices\nSocial scoring · Subliminal manipulation'),
        (3.0, 2.6, AMBER,      'HIGH RISK',
         'Annex III systems — strict requirements\nMedical AI · Robotics · Critical infrastructure'),
        (5.8, 3.4, '#F39C12',  'LIMITED RISK',
         'Transparency obligations\nChatbots · Emotion recognition'),
        (8.2, 4.8, GREEN_OK,   'MINIMAL RISK',
         'Voluntary code of conduct\nSpam filters · AI in games'),
    ]

    pyramid_x = [5, 1.2, 8.8]
    pyramid_y = [9.5, 0.5, 0.5]
    ax.fill(pyramid_x, pyramid_y, alpha=0.06, color=NAVY)
    ax.plot(pyramid_x + [pyramid_x[0]], pyramid_y + [pyramid_y[0]],
            color=MID_GRAY, lw=1.2, alpha=0.5)

    boundaries = [2.5, 4.7, 6.8]
    for b in boundaries:
        x_left  = 5 - (5-1.2) * (9.5-b)/9.0
        x_right = 5 + (8.8-5) * (9.5-b)/9.0
        ax.plot([x_left, x_right], [b, b], color=MID_GRAY, lw=0.9, alpha=0.6)

    for (y_mid, bar_h, color, title, desc) in levels:
        ax.text(5, y_mid + 0.35, title, ha='center', va='center',
                fontsize=8.5, color=WHITE if color == RED_ALERT else NAVY,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.92))
        ax.text(5, y_mid - 0.25, desc, ha='center', va='center',
                fontsize=6.8, color=SLATE)

    ax.text(5, 9.8, 'EU AI Act\nRisk Pyramid', ha='center', va='top',
            fontsize=11, color=NAVY, fontweight='bold')

    # Right panel: OMNIX mapping
    ax2 = fig.add_axes([0.58, 0.05, 0.40, 0.88])
    ax2.set_xlim(0, 4); ax2.set_ylim(0, 10)
    ax2.axis('off')

    ax2.text(2.0, 9.7, 'OMNIX Article Mapping', ha='center', va='top',
             fontsize=11, color=NAVY, fontweight='bold')

    articles = [
        ('Art. 9', 'Risk Management System',
         'AVM continuous risk\nmonitoring per domain', '#1A5276'),
        ('Art. 14', 'Human Oversight',
         'Three-tier override\narchitecture', '#1E8449'),
        ('Art. 17', 'Quality Management',
         'Eleven-checkpoint pipeline\n+ SAE pre-validation', SLATE),
        ('Art. 72', 'Post-Market Monitoring',
         'Continuous AVM + WAL\nchain verification', '#784212'),
        ('Art. 13', 'Transparency',
         'PQC-signed FAT receipts\nregulator-ready format', '#6C3483'),
    ]
    for i, (art, title, desc, color) in enumerate(articles):
        y0 = 8.6 - i * 1.7
        rect = FancyBboxPatch((0.1, y0 - 0.95), 3.8, 1.35,
                               boxstyle='round,pad=0.06',
                               facecolor=color, edgecolor=GOLD, linewidth=1.5,
                               alpha=0.92)
        ax2.add_patch(rect)
        ax2.text(0.45, y0, art, ha='left', va='center',
                 fontsize=9.5, color=GOLD, fontweight='bold')
        ax2.text(1.25, y0 + 0.18, title, ha='left', va='center',
                 fontsize=8, color=WHITE, fontweight='bold')
        ax2.text(1.25, y0 - 0.28, desc, ha='left', va='center',
                 fontsize=7.2, color=GOLD_L)

    add_branding(fig, 'FIGURE 9 — EU AI Act Risk Classification')
    save(fig, '09_eu_ai_act.png')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 10 — Case Study Failures Timeline
# ──────────────────────────────────────────────────────────────────────────────
def g10():
    fig = base_fig(12, 7)
    fig.patch.set_facecolor(LIGHT_BG)
    ax = fig.add_axes([0.06, 0.18, 0.90, 0.72])
    ax.set_facecolor(LIGHT_BG)

    cases = [
        ('LTCM\n1998',      1998.7, -125, 'Quant model\nassumption failure', RED_ALERT),
        ('Enron\n2001',     2001.9,  -63, 'Governance\nphantom structure',   AMBER),
        ('Lehman\n2008',    2008.7, -691, 'Systemic risk\nnot detected',     RED_ALERT),
        ('MF Global\n2011', 2011.8,  -41, 'Risk model\nphoto problem',       AMBER),
        ('Terra/Luna\n2022',2022.4,  -18, 'Mechanism\nghost compliance',     RED_ALERT),
        ('FTX\n2022',       2022.9,  -32, 'Audit trail\ncomplete absence',   RED_ALERT),
        ('SVB\n2023',       2023.2,  -20, 'Rate risk\nassumption drift',     AMBER),
    ]

    xs = [c[1] for c in cases]
    ys = [max(c[2]/691 * 90 + 15, -88) for c in cases]

    # Custom label positions to avoid crowding at 2022-2023
    custom_label = {
        'Terra/Luna\n2022': dict(x_off=-0.8, y_off=-10, ha='right',  va='top',   reason_y_off=-20),
        'FTX\n2022':        dict(x_off= 0.0, y_off= 20, ha='center', va='bottom', reason_y_off= 18),
        'SVB\n2023':        dict(x_off= 0.9, y_off=-10, ha='left',   va='top',   reason_y_off=-20),
    }

    ax.axhline(0, color=NAVY, linewidth=1.5, alpha=0.7)

    for (name, yr, loss_bn, reason, color), y in zip(cases, ys):
        ax.axvline(yr, color=color, linewidth=1.2, alpha=0.5, linestyle='--')
        ax.scatter([yr], [y], color=color, s=100, zorder=5)

        if name in custom_label:
            cl = custom_label[name]
            lx = yr + cl['x_off']
            ly = y  + cl['y_off']
            ax.text(lx, ly, name, ha=cl['ha'], va=cl['va'],
                    fontsize=8, color=NAVY, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor=WHITE,
                              edgecolor=color, alpha=0.9, linewidth=1.5))
            ax.text(lx, ly + cl['reason_y_off'], reason,
                    ha=cl['ha'], va=cl['va'],
                    fontsize=6.5, color=SLATE, style='italic')
        else:
            offset = -12 if y > -40 else 12
            va = 'top' if y > -40 else 'bottom'
            ax.text(yr, y + offset, name, ha='center', va=va,
                    fontsize=8, color=NAVY, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor=WHITE,
                              edgecolor=color, alpha=0.9, linewidth=1.5))
            ax.text(yr, y + offset - (18 if va == 'top' else -18),
                    reason, ha='center', va=va,
                    fontsize=6.8, color=SLATE, style='italic')

    ax.set_xlim(1996, 2026)
    ax.set_ylim(-95, 40)
    ax.set_xticks(range(1998, 2026, 4))
    ax.set_xticklabels([str(y) for y in range(1998, 2026, 4)],
                       color=SLATE, fontsize=8.5)
    ax.set_ylabel('Severity Index', fontsize=9, color=SLATE)
    ax.yaxis.set_ticklabels([])
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(MID_GRAY); ax.spines['bottom'].set_color(MID_GRAY)

    ax.text(0.5, 1.07, 'Documented Governance Failures — Each Showed Detectable Signals Before Collapse',
            transform=ax.transAxes, ha='center', va='bottom',
            fontsize=12, color=NAVY, fontweight='bold')

    legend_elements = [
        mpatches.Patch(facecolor=RED_ALERT, label='Structural governance failure'),
        mpatches.Patch(facecolor=AMBER,     label='Assumption drift — photograph problem'),
    ]
    ax.legend(handles=legend_elements, fontsize=8.5, loc='lower left', framealpha=0.88)

    add_branding(fig, 'FIGURE 10 — Case Study Failure Timeline')
    save(fig, '10_case_study_failures.png')

# ──────────────────────────────────────────────────────────────────────────────
# GRAPHIC 11 — OMNIX Vision 2035 Strategic Roadmap
# ──────────────────────────────────────────────────────────────────────────────
def g11():
    fig = base_fig(12, 7)
    fig.patch.set_facecolor(LIGHT_BG)
    ax = fig.add_axes([0.02, 0.03, 0.96, 0.84])
    ax.set_xlim(0, 12); ax.set_ylim(0, 7)
    ax.axis('off')

    # bar_w=2.6, gap=0.37 → 4 boxes from 0.25 to 11.73 — all within xlim 0-12
    bar_w = 2.6
    phases = [
        ('2024–2025\nFoundation',
         ['9 verticals operational', 'PQC infrastructure live', 'SDK distribution',
          'VARA / MiCA alignment'],
         GREEN_OK, 0.25),
        ('2025–2027\nExpansion',
         ['B2B enterprise rollout', 'Regulatory recognition', 'SDK ecosystem growth',
          '3 new verticals'],
         '#1A5276', 3.22),
        ('2027–2030\nScale',
         ['Cross-jurisdiction network', 'ISO / NIST standard input', 'Federated governance',
          'Institutional adoption'],
         SLATE, 6.19),
        ('2030–2035\nStandard',
         ['Global governance standard', 'Quantum-safe infrastructure', 'Regulatory embedding',
          '20+ verticals'],
         NAVY, 9.13),
    ]

    for title, items, color, x0 in phases:
        rect = FancyBboxPatch((x0, 3.4), bar_w, 2.5,
                               boxstyle='round,pad=0.08',
                               facecolor=color, edgecolor=GOLD, linewidth=2)
        ax.add_patch(rect)
        cx = x0 + bar_w / 2
        ax.text(cx, 5.55, title, ha='center', va='center',
                fontsize=10, color=WHITE if color != GREEN_OK else NAVY,
                fontweight='bold')
        for j, item in enumerate(items):
            ax.text(cx, 4.98 - j*0.44, '▸ ' + item,
                    ha='center', va='center',
                    fontsize=7.8,
                    color=GOLD_L if color in [SLATE, NAVY, '#1A5276'] else WHITE)

    # Timeline bar — spans full width of boxes
    rect_t = FancyBboxPatch((0.25, 2.85), 11.48, 0.36,
                              boxstyle='round,pad=0.04',
                              facecolor=GOLD, edgecolor=NAVY, linewidth=1.5)
    ax.add_patch(rect_t)

    year_xs = [0.25, 3.22, 6.19, 9.13, 11.73]
    for x_tick, yr in zip(year_xs, [2024, 2025, 2027, 2030, 2035]):
        ax.text(x_tick, 2.58, str(yr), ha='center', va='top',
                fontsize=9, color=NAVY, fontweight='bold')

    # Bottom metrics — centered under each phase box
    metrics = [
        ('9→20+',        'Governance\nVerticals'),
        ('PQC',          'Cryptographic\nStandard'),
        ('VARA+MiCA\n+AI Act', 'Regulatory\nFrameworks'),
        ('< 50ms',       'Decision\nLatency'),
    ]
    centers = [0.25 + bar_w/2, 3.22 + bar_w/2, 6.19 + bar_w/2, 9.13 + bar_w/2]
    for (val, lbl), x_m in zip(metrics, centers):
        rect_m = FancyBboxPatch((x_m - 1.1, 0.18), 2.2, 1.55,
                                 boxstyle='round,pad=0.06',
                                 facecolor=WHITE, edgecolor=GOLD, linewidth=1.5)
        ax.add_patch(rect_m)
        ax.text(x_m, 1.18, val, ha='center', va='center',
                fontsize=13, color=NAVY, fontweight='bold')
        ax.text(x_m, 0.58, lbl, ha='center', va='center',
                fontsize=7.8, color=SLATE)

    ax.text(6.0, 6.88, 'OMNIX Quantum — Strategic Roadmap 2024–2035',
            ha='center', va='top', fontsize=13, color=NAVY, fontweight='bold')
    ax.text(6.0, 6.60, 'From working system to global governance standard',
            ha='center', va='top', fontsize=9, color=SLATE, style='italic')

    add_branding(fig, 'FIGURE 11 — Vision 2035 Roadmap')
    save(fig, '11_vision_2035.png')

# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f'Generating 11 institutional graphics → {OUT}')
    g01(); g02(); g03(); g04(); g05()
    g06(); g07(); g08(); g09(); g10(); g11()
    files = os.listdir(OUT)
    print(f'\nDone — {len(files)} files in {OUT}:')
    for f in sorted(files):
        size = os.path.getsize(os.path.join(OUT, f)) // 1024
        print(f'  {f}  ({size} KB)')
