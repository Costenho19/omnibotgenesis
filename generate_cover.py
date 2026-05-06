"""
generate_cover.py — Ghost Compliance premium cover v4
Design: enterprise/defense-tech aesthetic
Colors: GOLD (#C9A227) + BLUE (#2E86C1) only — from OMNIX logo
Clean, minimal, institutional.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image as PILImage

LOGO_COVER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'logo_cover.png')   # transparent bg version

DPI   = 200
W_IN  = 8.27
H_IN  = 11.69

BG     = '#040D1A'
GOLD   = '#C9A227'
GOLD_L = '#E8C97A'
BLUE   = '#2E86C1'
BLUE_L = '#5DADE2'
WHITE  = '#FFFFFF'
CREAM  = '#F4F1EB'
GRAY   = '#B0B8C8'


def make_cover(subtitle_lines, outfile, edition_label='First Edition'):
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor=BG)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W_IN)
    ax.set_ylim(0, H_IN)
    ax.axis('off')
    ax.set_facecolor(BG)

    # ── Full background
    ax.add_patch(Rectangle((0, 0), W_IN, H_IN, facecolor=BG, zorder=0))

    # ── Top bar: solid gold
    ax.add_patch(Rectangle((0, H_IN - 0.20), W_IN, 0.20,
                            facecolor=GOLD, zorder=2))

    # ── Bottom bar: solid blue
    ax.add_patch(Rectangle((0, 0), W_IN, 0.20,
                            facecolor=BLUE, zorder=2))

    # ── Left thin vertical accent: gold
    ax.add_patch(Rectangle((0, 0.20), 0.10, H_IN - 0.40,
                            facecolor=GOLD, alpha=0.70, zorder=2))

    # ── Right thin vertical accent: blue
    ax.add_patch(Rectangle((W_IN - 0.10, 0.20), 0.10, H_IN - 0.40,
                            facecolor=BLUE, alpha=0.70, zorder=2))

    # ── Content margins (inside the thin bars)
    lx = 0.28          # left content start
    rx = W_IN - 0.28   # right content end
    cx = W_IN / 2      # center

    # ── OMNIX logo — smaller, transparent bg, integrated
    logo_w = 2.60
    logo_h = logo_w * (608 / 892)    # ≈ 1.77 in
    logo_x = cx - logo_w / 2
    logo_y = H_IN - 0.20 - 0.35 - logo_h

    if os.path.exists(LOGO_COVER):
        logo_img = PILImage.open(LOGO_COVER)
        ax.imshow(logo_img,
                  extent=[logo_x, logo_x + logo_w, logo_y, logo_y + logo_h],
                  zorder=4, aspect='auto', interpolation='lanczos')

    # ── Single gold rule below logo
    rule_y = logo_y - 0.22
    ax.plot([lx, rx], [rule_y, rule_y],
            color=GOLD, linewidth=2.0, solid_capstyle='round', zorder=4)

    # ── "GHOST" — clean solid gold, no effects
    ghost_y = rule_y - 1.55
    ax.text(cx, ghost_y, 'GHOST',
            ha='center', va='center',
            fontsize=130, color=GOLD, fontweight='bold', zorder=5)

    # ── "COMPLIANCE" — clean solid blue-white
    comp_y = ghost_y - 1.32
    ax.text(cx, comp_y, 'COMPLIANCE',
            ha='center', va='center',
            fontsize=64, color=BLUE_L, fontweight='bold', zorder=5)

    # ── Thin two-tone rule: gold left half, blue right half
    thin_y = comp_y - 0.65
    ax.plot([lx, cx], [thin_y, thin_y],
            color=GOLD, linewidth=1.0, solid_capstyle='butt', zorder=4)
    ax.plot([cx, rx], [thin_y, thin_y],
            color=BLUE, linewidth=1.0, solid_capstyle='butt', zorder=4)

    # ── Subtitle
    sub_y = thin_y - 0.44
    for i, line in enumerate(subtitle_lines):
        ax.text(cx, sub_y - i * 0.37, line,
                ha='center', va='center',
                fontsize=13, color=CREAM, style='italic',
                alpha=0.85, zorder=5)

    # ── Thin gold rule above author section
    author_rule_y = 2.40
    ax.plot([lx + 0.8, rx - 0.8], [author_rule_y, author_rule_y],
            color=GOLD_L, linewidth=0.6, alpha=0.45, zorder=4)

    # ── Author
    ax.text(cx, 2.10, 'Harold Nunes',
            ha='center', va='center',
            fontsize=19, color=WHITE, fontweight='bold', zorder=5)

    # ── Publisher
    ax.text(cx, 1.68,
            'OMNIX Quantum  ·  omnixquantum.net',
            ha='center', va='center',
            fontsize=10, color=GOLD, fontweight='bold', zorder=5)

    # ── Edition / copyright
    ax.text(cx, 1.30,
            f'© 2026 Harold Nunes  ·  {edition_label}',
            ha='center', va='center',
            fontsize=8.5, color=GRAY, alpha=0.55, zorder=5)

    plt.savefig(outfile, dpi=DPI, bbox_inches='tight', pad_inches=0,
                facecolor=BG, edgecolor='none')
    plt.close(fig)
    print(f'  {outfile}  ({os.path.getsize(outfile) // 1024} KB)')


if __name__ == '__main__':
    print('Generating premium covers v4...')
    make_cover(
        ['The Governance Infrastructure',
         'Markets Have Not Yet Built'],
        'cover_en.png',
        edition_label='First Edition'
    )
    make_cover(
        ['La Infraestructura de Gobernanza',
         'Que los Mercados Aún No Han Construido'],
        'cover_es.png',
        edition_label='Primera Edición'
    )
    print('Done.')
