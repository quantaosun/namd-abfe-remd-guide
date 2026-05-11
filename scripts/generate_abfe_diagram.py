#!/usr/bin/env python3
"""
Generate a clean ABFE thermodynamic cycle diagram using matplotlib.
- No overlapping text or arrows
- No references inside the image
- Correct full equation with restraint correction terms
Output: docs/abfe_thermodynamic_cycle.png
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os

# ── Colour palette ────────────────────────────────────────────────────────────
C_PHYS    = '#D6EAF8'
C_BLUE    = '#2980B9'
C_SITE    = '#EBF5FB'
C_SOLV    = '#EAFAF1'
C_GREEN   = '#1E8449'
C_ORANGE  = '#D35400'
C_ORANGE_L= '#FEF9E7'
C_PURPLE  = '#7D3C98'
C_PURPLE_L= '#F5EEF8'
C_GREY    = '#717D7E'
C_GREY_L  = '#F2F3F4'
C_DARK    = '#1A252F'
C_RED     = '#C0392B'

def rbox(ax, cx, cy, w, h, fc, ec, lw=1.8):
    """Draw a rounded box centred at (cx, cy)."""
    b = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                       boxstyle="round,pad=0.12", linewidth=lw,
                       edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(b)

def txt(ax, x, y, s, fs=9, bold=False, color=C_DARK, ha='center', va='center',
        italic=False):
    kw = dict(ha=ha, va=va, fontsize=fs, color=color, zorder=5)
    if bold:   kw['fontweight'] = 'bold'
    if italic: kw['fontstyle']  = 'italic'
    ax.text(x, y, s, **kw)

def harrow(ax, x0, x1, y, color=C_DARK, lw=2.0, dashed=False):
    ls = 'dashed' if dashed else 'solid'
    ax.annotate('', xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                linestyle=ls), zorder=4)

def varrow(ax, x, y0, y1, color=C_GREY, lw=1.4, dashed=True):
    ls = 'dashed' if dashed else 'solid'
    ax.annotate('', xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                linestyle=ls), zorder=4)

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(18, 14))
ax.set_xlim(0, 18)
ax.set_ylim(0, 14)
ax.axis('off')
fig.patch.set_facecolor('white')

# ═══════════════════════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════════════════════
txt(ax, 9, 13.5,
    'Absolute Binding Free Energy (ABFE) — Alchemical Thermodynamic Cycle',
    fs=15, bold=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 1 — Physical states  (y ≈ 12)
# ═══════════════════════════════════════════════════════════════════════════════
Y1 = 12.0
BW, BH = 4.0, 1.2

# State A: bound complex
rbox(ax, 3.5, Y1, BW, BH, C_PHYS, C_BLUE, lw=2)
txt(ax, 3.5, Y1 + 0.28, 'Protein · Ligand  [P·L]', fs=10, bold=True, color=C_BLUE)
txt(ax, 3.5, Y1 - 0.10, 'Ligand bound in protein pocket', fs=9)
txt(ax, 3.5, Y1 - 0.38, '(fully interacting,  λ = 0)', fs=8.5, color=C_GREY)

# State B: unbound
rbox(ax, 14.5, Y1, BW, BH, C_PHYS, C_BLUE, lw=2)
txt(ax, 14.5, Y1 + 0.28, 'Protein  +  Ligand  [P + L]', fs=10, bold=True, color=C_BLUE)
txt(ax, 14.5, Y1 - 0.10, 'Ligand free in solution', fs=9)
txt(ax, 14.5, Y1 - 0.38, '(fully interacting,  λ = 0)', fs=8.5, color=C_GREY)

# ΔG_bind dashed arrow
harrow(ax, 5.5, 12.5, Y1, C_PURPLE, lw=2.5, dashed=True)
txt(ax, 9.0, Y1 + 0.38, 'ΔG_bind  (target — not directly simulated)',
    fs=9, italic=True, color=C_PURPLE)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 2 — Alchemical legs  (y ≈ 9.5)
# ═══════════════════════════════════════════════════════════════════════════════
Y2 = 9.5
LBW, LBH = 3.2, 1.3   # lambda endpoint box size

# ─── LEG 1: Complex (site) ───────────────────────────────────────────────────
# Header band
rbox(ax, 4.0, Y2 + 1.25, 6.8, 0.45, C_SITE, C_BLUE, lw=1.5)
txt(ax, 4.0, Y2 + 1.25, 'LEG 1 — Complex (Site)', fs=10, bold=True, color=C_BLUE)

# λ=0 box
rbox(ax, 1.8, Y2, LBW, LBH, C_SITE, C_BLUE, lw=1.5)
txt(ax, 1.8, Y2 + 0.30, '[P·L]  λ = 0', fs=9.5, bold=True, color=C_BLUE)
txt(ax, 1.8, Y2 + 0.00, 'Ligand fully coupled', fs=8.5)
txt(ax, 1.8, Y2 - 0.28, 'in protein pocket', fs=8.5)

# λ=1 box
rbox(ax, 6.2, Y2, LBW, LBH, C_GREY_L, C_GREY, lw=1.5)
txt(ax, 6.2, Y2 + 0.30, '[P·L*]  λ = 1', fs=9.5, bold=True, color=C_GREY)
txt(ax, 6.2, Y2 + 0.00, 'Ligand decoupled', fs=8.5, color=C_GREY)
txt(ax, 6.2, Y2 - 0.28, '(ghost in pocket)', fs=8.5, color=C_GREY)

# Arrow with label ABOVE
harrow(ax, 3.4, 4.6, Y2, C_BLUE, lw=2.5)
txt(ax, 4.0, Y2 + 0.60, '−ΔG_site_elec  −  ΔG_site_vdW  −  ΔG_restr_on',
    fs=8.5, bold=True, color=C_BLUE)

# ─── LEG 2: Solvation (solv) ─────────────────────────────────────────────────
# Header band
rbox(ax, 13.8, Y2 + 1.25, 6.8, 0.45, C_SOLV, C_GREEN, lw=1.5)
txt(ax, 13.8, Y2 + 1.25, 'LEG 2 — Solvation (Solv)', fs=10, bold=True, color=C_GREEN)

# λ=0 box
rbox(ax, 11.2, Y2, LBW, LBH, C_SOLV, C_GREEN, lw=1.5)
txt(ax, 11.2, Y2 + 0.30, '[L]  λ = 0', fs=9.5, bold=True, color=C_GREEN)
txt(ax, 11.2, Y2 + 0.00, 'Ligand fully coupled', fs=8.5)
txt(ax, 11.2, Y2 - 0.28, 'in water', fs=8.5)

# λ=1 box
rbox(ax, 16.4, Y2, LBW, LBH, C_GREY_L, C_GREY, lw=1.5)
txt(ax, 16.4, Y2 + 0.30, '[L*]  λ = 1', fs=9.5, bold=True, color=C_GREY)
txt(ax, 16.4, Y2 + 0.00, 'Ligand decoupled', fs=8.5, color=C_GREY)
txt(ax, 16.4, Y2 - 0.28, '(ghost in water)', fs=8.5, color=C_GREY)

# Arrow with label ABOVE
harrow(ax, 12.8, 14.8, Y2, C_GREEN, lw=2.5)
txt(ax, 13.8, Y2 + 0.60, '−ΔG_solv_elec  −  ΔG_solv_vdW',
    fs=8.5, bold=True, color=C_GREEN)

# Vertical connectors: physical states → leg headers (well-separated)
varrow(ax, 3.5, Y1 - 0.60, Y2 + 1.48, C_GREY, lw=1.4, dashed=True)
varrow(ax, 14.5, Y1 - 0.60, Y2 + 1.48, C_GREY, lw=1.4, dashed=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 3 — Lambda window strip  (y ≈ 7.5)
# ═══════════════════════════════════════════════════════════════════════════════
Y3 = 7.5
txt(ax, 9.0, Y3 + 0.85,
    'λ-Windows: REMD exchanges configurations between adjacent windows at each step',
    fs=9, italic=True, color=C_DARK)

n = 9
lambdas  = np.linspace(0, 1, n)
lcolors  = plt.cm.RdYlGn(lambdas)
bw_lam   = 1.55   # box width
gap_lam  = 0.15   # gap between boxes
total_w  = n * bw_lam + (n - 1) * gap_lam
x0_lam   = (18 - total_w) / 2

for i, (lam, col) in enumerate(zip(lambdas, lcolors)):
    bx = x0_lam + i * (bw_lam + gap_lam)
    b = FancyBboxPatch((bx, Y3), bw_lam, 0.65,
                       boxstyle="round,pad=0.06", linewidth=1.2,
                       edgecolor='#888', facecolor=col, alpha=0.90, zorder=3)
    ax.add_patch(b)
    tc = 'white' if lam < 0.35 or lam > 0.75 else C_DARK
    ax.text(bx + bw_lam/2, Y3 + 0.325,
            f'λ={lam:.2f}', ha='center', va='center',
            fontsize=8.5, fontweight='bold', color=tc, zorder=5)
    # ⇌ symbol in the gap (not overlapping boxes)
    if i < n - 1:
        sx = bx + bw_lam + gap_lam / 2
        ax.text(sx, Y3 + 0.325, '⇌', ha='center', va='center',
                fontsize=12, color='#888888', zorder=5)

txt(ax, x0_lam + bw_lam/2, Y3 - 0.22, 'fully coupled', fs=8, color=C_RED)
txt(ax, x0_lam + (n-1)*(bw_lam+gap_lam) + bw_lam/2, Y3 - 0.22,
    'fully decoupled', fs=8, color=C_GREY)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 4 — Restraint correction box  (y ≈ 5.2)
# ═══════════════════════════════════════════════════════════════════════════════
Y4 = 5.2
rbox(ax, 9.0, Y4, 16.4, 1.6, C_ORANGE_L, C_ORANGE, lw=2)
txt(ax, 9.0, Y4 + 0.62,
    'Restraint Correction  —  Required to remove artefact energy introduced during decoupling',
    fs=10, bold=True, color=C_ORANGE)
txt(ax, 9.0, Y4 + 0.22,
    '① ΔG_restr_on :  free energy cost of applying DBC restraints while ligand is still interacting  '
    '(computed numerically from restraint λ-windows)',
    fs=9, color=C_DARK)
txt(ax, 9.0, Y4 - 0.18,
    '② ΔG_restr_analytical :  Boresch standard-state correction — releases restrained ghost ligand to 1 M standard concentration',
    fs=9, color=C_DARK)
txt(ax, 9.0, Y4 - 0.52,
    '(computed analytically from restraint force constants and equilibrium values — no additional simulation needed)',
    fs=8.5, italic=True, color=C_GREY)

# ═══════════════════════════════════════════════════════════════════════════════
# EQUATION BOX  (y ≈ 3.7)
# ═══════════════════════════════════════════════════════════════════════════════
Y_EQ = 3.7
rbox(ax, 9.0, Y_EQ, 16.8, 0.75, C_PURPLE_L, C_PURPLE, lw=2.5)
txt(ax, 9.0, Y_EQ,
    'ΔG_bind  =  ΔG_site  −  ΔG_solv  +  ΔG_restr_on  +  ΔG_restr_analytical',
    fs=12, bold=True, color=C_PURPLE)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 5 — NAMD workflow steps  (y ≈ 1.8)
# ═══════════════════════════════════════════════════════════════════════════════
Y5 = 1.8
SW, SH = 3.6, 1.8
step_data = [
    (2.3,  'Step 1\nEquilibration',
     'equ_site.namd\nequ_solv.namd',
     '#FDEDEC', C_RED),
    (6.4,  'Step 2\nREMD FEP Run',
     'namd3 +replicas N\nFEP_remd_softcore.namd',
     C_ORANGE_L, C_ORANGE),
    (10.5, 'Step 3\nSort Replicas',
     'sort_replicas.py\n(un-shuffle λ trajectories)',
     C_SOLV, C_GREEN),
    (14.6, 'Step 4\nBAR Analysis',
     'calc_bar_fe.py\nΔG_site, ΔG_solv → ΔG_bind',
     C_PURPLE_L, C_PURPLE),
]

for cx, title, body, fc, ec in step_data:
    rbox(ax, cx, Y5, SW, SH, fc, ec, lw=1.8)
    lines = title.split('\n')
    txt(ax, cx, Y5 + 0.52, lines[0], fs=10, bold=True, color=ec)
    txt(ax, cx, Y5 + 0.18, lines[1], fs=10, bold=True, color=ec)
    for j, line in enumerate(body.split('\n')):
        txt(ax, cx, Y5 - 0.22 - j * 0.30, line, fs=8.5, color=C_DARK)

# Arrows between steps (in the gap between boxes, not overlapping)
for x0, x1 in [(4.1, 4.6), (8.2, 8.7), (12.3, 12.8)]:
    harrow(ax, x0, x1, Y5, C_GREY, lw=2.0)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(facecolor=C_PHYS,   edgecolor=C_BLUE,   label='Physical state (real)'),
    mpatches.Patch(facecolor=C_SITE,   edgecolor=C_BLUE,   label='Complex leg (site)'),
    mpatches.Patch(facecolor=C_SOLV,   edgecolor=C_GREEN,  label='Solvation leg (solv)'),
    mpatches.Patch(facecolor=C_GREY_L, edgecolor=C_GREY,   label='Decoupled state (λ=1)'),
    mpatches.Patch(facecolor=C_ORANGE_L,edgecolor=C_ORANGE,label='Restraint correction'),
    mpatches.Patch(facecolor=C_PURPLE_L,edgecolor=C_PURPLE,label='Final equation / BAR'),
]
ax.legend(handles=legend_items, loc='lower right', fontsize=9,
          framealpha=0.95, edgecolor='#BDC3C7',
          bbox_to_anchor=(0.998, 0.002))

# ── Save ──────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'docs', 'abfe_thermodynamic_cycle.png')
plt.tight_layout(pad=0.3)
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {os.path.abspath(out)}")
