#!/usr/bin/env python3
"""
Generate two clean black-and-white ABFE diagrams with large fonts and no overlaps:
  1. docs/abfe_thermodynamic_cycle.png
  2. docs/abfe_restraint_correction.png
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs')

# ── shared helpers ────────────────────────────────────────────────────────────
def rbox(ax, cx, cy, w, h, lw=2.0, fill='white', ec='black'):
    b = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                       boxstyle="round,pad=0.15", linewidth=lw,
                       edgecolor=ec, facecolor=fill, zorder=3)
    ax.add_patch(b)

def txt(ax, x, y, s, fs=12, bold=False, ha='center', va='center', italic=False):
    kw = dict(ha=ha, va=va, fontsize=fs, color='black', zorder=5,
              wrap=False, clip_on=False)
    if bold:   kw['fontweight'] = 'bold'
    if italic: kw['fontstyle']  = 'italic'
    ax.text(x, y, s, **kw)

def harrow(ax, x0, x1, y, lw=2.0, dashed=False):
    ls = 'dashed' if dashed else 'solid'
    ax.annotate('', xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle='->', color='black', lw=lw,
                                linestyle=ls), zorder=4)

def varrow(ax, x, y0, y1, lw=1.8, dashed=True):
    ls = 'dashed' if dashed else 'solid'
    ax.annotate('', xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle='->', color='black', lw=lw,
                                linestyle=ls), zorder=4)


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 1 — Thermodynamic Cycle
# ══════════════════════════════════════════════════════════════════════════════
# Canvas: 20 wide × 14 tall (inches at 150 dpi → 3000×2100 px)
W, H = 20, 14
fig, ax = plt.subplots(figsize=(W, H))
ax.set_xlim(0, W); ax.set_ylim(0, H)
ax.axis('off')
fig.patch.set_facecolor('white')

# ── Title ─────────────────────────────────────────────────────────────────────
txt(ax, W/2, H - 0.55,
    'ABFE Alchemical Thermodynamic Cycle',
    fs=18, bold=True)

# ── ROW 1: physical states (y centre = 11.5) ─────────────────────────────────
Y1 = 11.5
BW, BH = 6.0, 1.8   # box width / height

# Left box: P·L
rbox(ax, 4.0, Y1, BW, BH, lw=2.5)
txt(ax, 4.0, Y1 + 0.45, 'Protein · Ligand  [P·L]', fs=13, bold=True)
txt(ax, 4.0, Y1 + 0.00, 'Ligand bound in protein pocket', fs=12)
txt(ax, 4.0, Y1 - 0.45, '(fully interacting,  λ = 0)', fs=11, italic=True)

# Right box: P + L
rbox(ax, 16.0, Y1, BW, BH, lw=2.5)
txt(ax, 16.0, Y1 + 0.45, 'Protein  +  Ligand  [P + L]', fs=13, bold=True)
txt(ax, 16.0, Y1 + 0.00, 'Ligand free in solution', fs=12)
txt(ax, 16.0, Y1 - 0.45, '(fully interacting,  λ = 0)', fs=11, italic=True)

# ΔG_bind dashed arrow between boxes
harrow(ax, 7.1, 12.9, Y1, lw=2.0, dashed=True)
txt(ax, 10.0, Y1 + 0.60,
    'ΔG_bind  (target — not directly simulated)',
    fs=11, italic=True)

# ── ROW 2: leg headers (y = 9.1) ─────────────────────────────────────────────
Y2h = 9.1
rbox(ax, 4.8, Y2h, 7.8, 0.70, lw=1.8, fill='#eeeeee')
txt(ax, 4.8, Y2h, 'LEG 1 — Complex (Site)', fs=13, bold=True)

rbox(ax, 15.2, Y2h, 7.8, 0.70, lw=1.8, fill='#eeeeee')
txt(ax, 15.2, Y2h, 'LEG 2 — Solvation (Solv)', fs=13, bold=True)

# Vertical connectors: physical boxes → leg headers
varrow(ax, 4.0,  Y1 - BH/2, Y2h + 0.35, lw=1.8, dashed=True)
varrow(ax, 16.0, Y1 - BH/2, Y2h + 0.35, lw=1.8, dashed=True)

# ── ROW 2: alchemical state boxes (y = 7.2) ──────────────────────────────────
Y2 = 7.2
SW, SH = 3.4, 1.8   # state box width / height

# LEG 1 left: [P·L] λ=0
rbox(ax, 2.2, Y2, SW, SH, lw=2.0)
txt(ax, 2.2, Y2 + 0.45, '[P·L]  λ = 0', fs=13, bold=True)
txt(ax, 2.2, Y2 + 0.00, 'Ligand fully coupled', fs=12)
txt(ax, 2.2, Y2 - 0.45, 'in protein pocket', fs=12)

# LEG 1 right: [P·L*] λ=1
rbox(ax, 7.4, Y2, SW, SH, lw=2.0, fill='#f5f5f5', ec='#666666')
txt(ax, 7.4, Y2 + 0.45, '[P·L*]  λ = 1', fs=13, bold=True)
txt(ax, 7.4, Y2 + 0.00, 'Ligand decoupled', fs=12)
txt(ax, 7.4, Y2 - 0.45, '(ghost in pocket)', fs=12)

# Arrow LEG 1
harrow(ax, 3.9, 5.7, Y2, lw=2.5)
txt(ax, 4.8, Y2 + 1.20,
    '−ΔG_site_elec − ΔG_site_vdW − ΔG_restr_on',
    fs=11, bold=True)

# LEG 2 left: [L] λ=0
rbox(ax, 12.6, Y2, SW, SH, lw=2.0)
txt(ax, 12.6, Y2 + 0.45, '[L]  λ = 0', fs=13, bold=True)
txt(ax, 12.6, Y2 + 0.00, 'Ligand fully coupled', fs=12)
txt(ax, 12.6, Y2 - 0.45, 'in water', fs=12)

# LEG 2 right: [L*] λ=1
rbox(ax, 17.8, Y2, SW, SH, lw=2.0, fill='#f5f5f5', ec='#666666')
txt(ax, 17.8, Y2 + 0.45, '[L*]  λ = 1', fs=13, bold=True)
txt(ax, 17.8, Y2 + 0.00, 'Ligand decoupled', fs=12)
txt(ax, 17.8, Y2 - 0.45, '(ghost in water)', fs=12)

# Arrow LEG 2
harrow(ax, 14.3, 16.1, Y2, lw=2.5)
txt(ax, 15.2, Y2 + 1.20,
    '−ΔG_solv_elec − ΔG_solv_vdW',
    fs=11, bold=True)

# ── ROW 3: equation box (y = 5.0) ────────────────────────────────────────────
Y3 = 5.0
rbox(ax, W/2, Y3, 18.0, 1.0, lw=2.5)
txt(ax, W/2, Y3,
    'ΔG_bind  =  ΔG_site  −  ΔG_solv  +  ΔG_restr_on  +  ΔG_restr_analytical',
    fs=14, bold=True)

# ── ROW 4: workflow steps (y = 2.5) ──────────────────────────────────────────
Y4 = 2.5
EW, EH = 3.8, 2.2   # step box width / height
steps = [
    (2.2,  'Step 1',       'Equilibration',    'equ_site.namd\nequ_solv.namd'),
    (6.6,  'Step 2',       'REMD FEP Run',     'namd3 +replicas N\nFEP_remd_softcore.namd'),
    (11.0, 'Step 3',       'Sort Replicas',    'sort_replicas.py'),
    (15.4, 'Step 4',       'BAR Analysis',     'calc_bar_fe.py'),
]
for cx, s1, s2, s3 in steps:
    rbox(ax, cx, Y4, EW, EH, lw=2.0)
    txt(ax, cx, Y4 + 0.65, s1, fs=12, bold=True)
    txt(ax, cx, Y4 + 0.20, s2, fs=13, bold=True)
    # split italic line if it contains \n
    lines = s3.split('\n')
    if len(lines) == 1:
        txt(ax, cx, Y4 - 0.35, lines[0], fs=11, italic=True)
    else:
        txt(ax, cx, Y4 - 0.20, lines[0], fs=11, italic=True)
        txt(ax, cx, Y4 - 0.60, lines[1], fs=11, italic=True)

# Arrows between steps
for x0, x1 in [(4.1, 4.7), (8.5, 9.1), (12.9, 13.5)]:
    harrow(ax, x0, x1, Y4, lw=2.0)

plt.tight_layout(pad=0.5)
out1 = os.path.join(DOCS, 'abfe_thermodynamic_cycle.png')
plt.savefig(out1, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {out1}")


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 2 — Restraint Correction
# ══════════════════════════════════════════════════════════════════════════════
W2, H2 = 18, 10
fig2, ax2 = plt.subplots(figsize=(W2, H2))
ax2.set_xlim(0, W2); ax2.set_ylim(0, H2)
ax2.axis('off')
fig2.patch.set_facecolor('white')

# Title
txt(ax2, W2/2, H2 - 0.55,
    'ABFE Restraint Correction — Why It Is Needed',
    fs=18, bold=True)

# Problem box
rbox(ax2, W2/2, 8.2, 16.0, 1.2, lw=2.0, fill='#eeeeee')
txt(ax2, W2/2, 8.45,
    'Problem: During decoupling, DBC restraints hold the ghost ligand in place.',
    fs=13)
txt(ax2, W2/2, 8.00,
    'These restraints introduce artificial free energy that must be removed.',
    fs=12, italic=True)

# Term 1 box
rbox(ax2, 4.5, 5.8, 7.5, 2.4, lw=2.0)
txt(ax2, 4.5, 6.75, '①  ΔG_restr_on', fs=14, bold=True)
txt(ax2, 4.5, 6.20, 'Cost of switching ON restraints', fs=13)
txt(ax2, 4.5, 5.75, 'while ligand is still interacting', fs=13)
txt(ax2, 4.5, 5.20, '→ computed numerically from simulation', fs=12, italic=True)

# Plus sign
txt(ax2, W2/2, 5.8, '+', fs=24, bold=True)

# Term 2 box
rbox(ax2, 13.5, 5.8, 7.5, 2.4, lw=2.0)
txt(ax2, 13.5, 6.75, '②  ΔG_restr_analytical', fs=14, bold=True)
txt(ax2, 13.5, 6.20, 'Boresch standard-state correction:', fs=13)
txt(ax2, 13.5, 5.75, 'releases ghost ligand to 1 M standard state', fs=13)
txt(ax2, 13.5, 5.20, '→ computed analytically, no extra simulation', fs=12, italic=True)

# Total correction box
rbox(ax2, W2/2, 3.5, 14.0, 1.0, lw=2.0)
txt(ax2, W2/2, 3.5,
    'Total correction  =  ΔG_restr_on  +  ΔG_restr_analytical',
    fs=14, bold=True)

# Full equation box
rbox(ax2, W2/2, 1.9, 16.5, 1.0, lw=2.5)
txt(ax2, W2/2, 1.9,
    'ΔG_bind  =  ΔG_site  −  ΔG_solv  +  ΔG_restr_on  +  ΔG_restr_analytical',
    fs=14, bold=True)

# Citation
txt(ax2, W2/2, 0.55,
    'Boresch et al. (2003) J. Phys. Chem. B 107, 9535–9551',
    fs=11, italic=True)

plt.tight_layout(pad=0.5)
out2 = os.path.join(DOCS, 'abfe_restraint_correction.png')
plt.savefig(out2, dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {out2}")
