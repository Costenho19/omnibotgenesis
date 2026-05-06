"""
generate_cover.py
Premium editorial cover — Ghost Compliance
Colors pulled directly from the OMNIX Quantum logo palette:
  Gold ring   : #C9A227
  Blue arrow  : #2E86C1
  Green arrow : #1E8449
  Orange arrow: #CA6F1E
  Purple base : #6C3483
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Rectangle, Polygon, FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image as PILImage

LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'omnix_web', 'public', 'book_logo.png')

DPI   = 200
W_IN  = 8.27
H_IN  = 11.69

# ── Logo palette ─────────────────────────────────────────────────────
BG      = '#040D1A'      # near-black navy — matches logo bg
NAVY    = '#0A1628'
NAVY2   = '#0E1E38'
GOLD    = '#C9A227'      # golden ring
GOLD_L  = '#E8C97A'      # lighter gold
BLUE    = '#2E86C1'      # blue arrow
BLUE_L  = '#5DADE2'      # lighter blue
GREEN   = '#1E8449'      # green arrow
ORANGE  = '#CA6F1E'      # orange arrow
PURPLE  = '#5B2C6F'      # purple base of ring
WHITE   = '#FFFFFF'
CREAM   = '#F4F1EB'


def _rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))


def _cmap(colors):
    return LinearSegmentedColormap.from_list('x', colors)


def make_cover(subtitle_lines, outfile, edition_label='First Edition'):
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor=BG)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W_IN)
    ax.set_ylim(0, H_IN)
    ax.axis('off')
    ax.set_facecolor(BG)

    # ── Full background
    ax.add_patch(Rectangle((0, 0), W_IN, H_IN, facecolor=BG, zorder=0))

    # ── Left vertical color stripe — logo colors top-to-bottom
    stripe_w = 0.28
    colors_stripe = [PURPLE, BLUE, GREEN, ORANGE, GOLD]
    n = len(colors_stripe)
    seg_h = H_IN / n
    for i, col in enumerate(colors_stripe):
        y0 = i * seg_h
        alpha = 0.62
        ax.add_patch(Rectangle((0, y0), stripe_w, seg_h + 0.02,
                                facecolor=col, alpha=alpha, zorder=2))
    # thin navy separator to separate stripe from content
    ax.add_patch(Rectangle((stripe_w, 0), 0.04, H_IN,
                            facecolor=BG, alpha=0.85, zorder=3))

    # ── Right accent stripe — thinner, gold+blue
    rs_w = 0.12
    for i, (col, al) in enumerate([(GOLD, 0.5), (BLUE, 0.45)]):
        ax.add_patch(Rectangle((W_IN - rs_w, i * H_IN / 2),
                                rs_w, H_IN / 2,
                                facecolor=col, alpha=al, zorder=2))

    # ── Top bar: gold → blue gradient
    bar_h = 0.22
    top_cmap = _cmap([GOLD, BLUE])
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    ax.imshow(grad, extent=[stripe_w + 0.04, W_IN - rs_w, H_IN - bar_h, H_IN],
              aspect='auto', cmap=top_cmap, zorder=4, alpha=0.95)
    # thin gold inner line
    ax.plot([stripe_w + 0.1, W_IN - rs_w - 0.1],
            [H_IN - bar_h - 0.05, H_IN - bar_h - 0.05],
            color=GOLD_L, linewidth=0.7, alpha=0.45, zorder=4)

    # ── Bottom bar: blue → gold gradient (mirrored)
    bot_cmap = _cmap([BLUE, GOLD])
    ax.imshow(grad, extent=[stripe_w + 0.04, W_IN - rs_w, 0, bar_h],
              aspect='auto', cmap=bot_cmap, zorder=4, alpha=0.95)
    ax.plot([stripe_w + 0.1, W_IN - rs_w - 0.1],
            [bar_h + 0.05, bar_h + 0.05],
            color=BLUE_L, linewidth=0.7, alpha=0.45, zorder=4)

    # ── Subtle diagonal accent (top-right)
    tr = Polygon([[W_IN, H_IN], [W_IN - 3.2, H_IN], [W_IN, H_IN - 4.5]],
                 facecolor=NAVY2, alpha=0.35, zorder=1, edgecolor='none')
    ax.add_patch(tr)

    # ── OMNIX logo — centered top section
    logo_w = 3.80
    logo_h = logo_w * (608 / 892)       # ≈ 2.59 in
    logo_x = stripe_w + 0.04 + ((W_IN - rs_w - stripe_w - 0.08) - logo_w) / 2
    logo_y = H_IN - bar_h - 0.30 - logo_h
    if os.path.exists(LOGO):
        logo_img = PILImage.open(LOGO)
        ax.imshow(logo_img,
                  extent=[logo_x, logo_x + logo_w, logo_y, logo_y + logo_h],
                  zorder=5, aspect='auto', interpolation='lanczos')

    # ── Gold + blue separator rule below logo
    rule_y = logo_y - 0.28
    mid_x  = (stripe_w + 0.1 + W_IN - rs_w - 0.1) / 2
    lx0    = stripe_w + 0.20
    lx1    = W_IN - rs_w - 0.20
    # gold left half
    ax.plot([lx0, mid_x], [rule_y, rule_y],
            color=GOLD, linewidth=3.0, solid_capstyle='round', zorder=5)
    # blue right half
    ax.plot([mid_x, lx1], [rule_y, rule_y],
            color=BLUE, linewidth=3.0, solid_capstyle='round', zorder=5)

    # ── "GHOST" — gold, enormous
    ghost_y = rule_y - 1.48
    # blue glow underneath via path_effects
    ax.text(W_IN / 2, ghost_y, 'GHOST',
            ha='center', va='center',
            fontsize=128, color=GOLD, fontweight='bold', zorder=6,
            path_effects=[
                pe.withStroke(linewidth=10, foreground=BLUE, alpha=0.25),
                pe.withStroke(linewidth=4,  foreground=BG),
            ])

    # ── "COMPLIANCE" — electric blue-white
    comp_y = ghost_y - 1.28
    ax.text(W_IN / 2, comp_y, 'COMPLIANCE',
            ha='center', va='center',
            fontsize=64, color=BLUE_L, fontweight='bold', zorder=6,
            path_effects=[pe.withStroke(linewidth=3, foreground=BG)])

    # ── Decorative rule: orange · green · gold
    thin_y = comp_y - 0.68
    seg_w  = (lx1 - lx0) / 3
    for col, x0, x1 in [
        (ORANGE, lx0,          lx0 + seg_w),
        (GREEN,  lx0 + seg_w,  lx0 + 2*seg_w),
        (GOLD,   lx0 + 2*seg_w, lx1),
    ]:
        ax.plot([x0, x1], [thin_y, thin_y],
                color=col, linewidth=1.4, solid_capstyle='butt', zorder=5)

    # ── Subtitle
    sub_y = thin_y - 0.46
    for i, line in enumerate(subtitle_lines):
        ax.text(W_IN / 2, sub_y - i * 0.38, line,
                ha='center', va='center',
                fontsize=13, color=CREAM, style='italic',
                alpha=0.88, zorder=6)

    # ── Colored dot ornament row
    dot_y   = 2.62
    colors_dots = [PURPLE, BLUE, GREEN, ORANGE, GOLD, ORANGE, GREEN, BLUE, PURPLE]
    xs_dots = np.linspace(lx0 + 0.3, lx1 - 0.3, len(colors_dots))
    for x_d, c_d in zip(xs_dots, colors_dots):
        ax.plot(x_d, dot_y, 'o', color=c_d,
                markersize=3.5, alpha=0.75, zorder=5)

    # ── Thin divider above author
    ax.plot([lx0, lx1], [2.38, 2.38],
            color=GOLD_L, linewidth=0.7, alpha=0.40, zorder=5)

    # ── Author name
    ax.text(W_IN / 2, 2.10, 'Harold Nunes',
            ha='center', va='center',
            fontsize=19, color=WHITE, fontweight='bold', zorder=6)

    # ── Publisher row
    ax.text(W_IN / 2, 1.66,
            'OMNIX Quantum  ·  omnixquantum.net',
            ha='center', va='center',
            fontsize=10, color=GOLD, fontweight='bold', zorder=6)

    # ── Edition / copyright
    ax.text(W_IN / 2, 1.28,
            f'© 2026 Harold Nunes  ·  {edition_label}',
            ha='center', va='center',
            fontsize=8.5, color=CREAM, alpha=0.42, zorder=6)

    plt.savefig(outfile, dpi=DPI, bbox_inches='tight', pad_inches=0,
                facecolor=BG, edgecolor='none')
    plt.close(fig)
    print(f'  {outfile}  ({os.path.getsize(outfile) // 1024} KB)')


if __name__ == '__main__':
    print('Generating premium covers...')
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
