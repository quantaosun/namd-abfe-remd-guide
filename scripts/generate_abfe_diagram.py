#!/usr/bin/env python3
"""
Generate two clean black-and-white ABFE diagrams:
  1. docs/abfe_thermodynamic_cycle.png  — the thermodynamic cycle
  2. docs/abfe_restraint_correction.png — the restraint correction scheme
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import os

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs')

# ── shared helpers ────────────────────────────────────────────────────────────
def rbox(ax, cx, cy, w, h, lw=1.5, fill='white', ec='black'):
    b = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                       boxstyle="round,pad=0.10", linewidth=lw,
                       edgecolor=ec, facecolor=fill, zorder=3)
    ax.add_patch(b)

def txt(ax, x, y, s, fs=9, bold=False, ha='center', va='center', italic=False):
    kw = dict(ha=ha, va=va, fontsize=fs, color='black', zorder=5)
    if bold:   kw['fontweight'] = 'bold'
    if italic: kw['fontstyle']  = 'italic'
    ax.text(x, y, s, **kw)

def harrow(ax, x0, x1, y, lw=1.5, dashed=False):
    ls = 'dashed' if dashed else 'solid'
    ax.annotate('', xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle='->', color='black', lw=lw,
                                linestyle=ls), zorder=4)

def varrow(ax, x, y0, y1, lw=1.2, dashed=True):
    ls = 'dashed' if dashed else 'solid'
    ax.annotate('', xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle='->', color='black', lw=lw,
                                linestyle=ls), zorder=4)

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 1 — Thermodynamic Cycle
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 9))
ax.set_xlim(0, 14); ax.set_ylim(0, 9)
ax.axis('off')
fig.patch.set_facecolor('white')

# Title
txt(ax, 7, 8.65,
    'ABFE Alchemical Thermodynamic Cycle',
    fs=13, bold=True)

# ── Row 1: physical states ────────────────────────────────────────────────────
Y1 = 7.2
rbox(ax, 2.8, Y1, 4.2, 1.1, lw=2)
txt(ax, 2.8, Y1 + 0.28, 'Protein · Ligand  [P·L]', fs=10, bold=True)
txt(ax, 2.8, Y1 - 0.05, 'Ligand bound in protein pocket', fs=9)
txt(ax, 2.8, Y1 - 0.33, '(fully interacting,  λ = 0)', fs=8.5, italic=True)

rbox(ax, 11.2, Y1, 4.2, 1.1, lw=2)
txt(ax, 11.2, Y1 + 0.28, 'Protein  +  Ligand  [P + L]', fs=10, bold=True)
txt(ax, 11.2, Y1 - 0.05, 'Ligand free in solution', fs=9)
txt(ax, 11.2, Y1 - 0.33, '(fully interacting,  λ = 0)', fs=8.5, italic=True)

# ΔG_bind dashed arrow
harrow(ax, 4.9, 9.1, Y1, lw=2, dashed=True)
txt(ax, 7.0, Y1 + 0.38,
    'ΔG_bind  (target — not directly simulated)',
    fs=8.5, italic=True)

# ── Row 2: alchemical legs ────────────────────────────────────────────────────
Y2 = 4.6
LW, LH = 2.8, 1.1

# LEG 1 header
rbox(ax, 3.5, Y2 + 1.15, 5.8, 0.38, lw=1.2, fill='#f0f0f0')
txt(ax, 3.5, Y2 + 1.15, 'LEG 1 — Complex (Site)', fs=9.5, bold=True)

rbox(ax, 1.6, Y2, LW, LH, lw=1.5)
txt(ax, 1.6, Y2 + 0.25, '[P·L]  λ = 0', fs=9, bold=True)
txt(ax, 1.6, Y2 - 0.05, 'Ligand fully coupled', fs=8.5)
txt(ax, 1.6, Y2 - 0.30, 'in protein pocket', fs=8.5)

rbox(ax, 5.4, Y2, LW, LH, lw=1.5, fill='#f8f8f8', ec='#888888')
txt(ax, 5.4, Y2 + 0.25, '[P·L*]  λ = 1', fs=9, bold=True)
txt(ax, 5.4, Y2 - 0.05, 'Ligand decoupled', fs=8.5)
txt(ax, 5.4, Y2 - 0.30, '(ghost in pocket)', fs=8.5)

harrow(ax, 3.0, 4.0, Y2, lw=2)
txt(ax, 3.5, Y2 + 0.55,
    '−ΔG_site_elec  −  ΔG_site_vdW  −  ΔG_restr_on',
    fs=8, bold=True)

# LEG 2 header
rbox(ax, 10.5, Y2 + 1.15, 5.8, 0.38, lw=1.2, fill='#f0f0f0')
txt(ax, 10.5, Y2 + 1.15, 'LEG 2 — Solvation (Solv)', fs=9.5, bold=True)

rbox(ax, 8.6, Y2, LW, LH, lw=1.5)
txt(ax, 8.6, Y2 + 0.25, '[L]  λ = 0', fs=9, bold=True)
txt(ax, 8.6, Y2 - 0.05, 'Ligand fully coupled', fs=8.5)
txt(ax, 8.6, Y2 - 0.30, 'in water', fs=8.5)

rbox(ax, 12.4, Y2, LW, LH, lw=1.5, fill='#f8f8f8', ec='#888888')
txt(ax, 12.4, Y2 + 0.25, '[L*]  λ = 1', fs=9, bold=True)
txt(ax, 12.4, Y2 - 0.05, 'Ligand decoupled', fs=8.5)
txt(ax, 12.4, Y2 - 0.30, '(ghost in water)', fs=8.5)

harrow(ax, 10.0, 11.0, Y2, lw=2)
txt(ax, 10.5, Y2 + 0.55,
    '−ΔG_solv_elec  −  ΔG_solv_vdW',
    fs=8, bold=True)

# Vertical connectors: physical → leg headers
varrow(ax, 2.8, Y1 - 0.56, Y2 + 1.34, lw=1.2, dashed=True)
varrow(ax, 11.2, Y1 - 0.56, Y2 + 1.34, lw=1.2, dashed=True)

# ── Row 3: equation ───────────────────────────────────────────────────────────
Y3 = 2.7
rbox(ax, 7.0, Y3, 13.0, 0.70, lw=2)
txt(ax, 7.0, Y3,
    'ΔG_bind  =  ΔG_site  −  ΔG_solv  +  ΔG_restr_on  +  ΔG_restr_analytical',
    fs=11, bold=True)

# ── Row 4: NAMD workflow steps ────────────────────────────────────────────────
Y4 = 1.2
SW, SH = 2.6, 1.4
steps = [
    (1.6,  'Step 1',       'Equilibration',        'equ_site / equ_solv'),
    (4.7,  'Step 2',       'REMD FEP Run',          'namd3 +replicas N'),
    (7.8,  'Step 3',       'Sort Replicas',         'sort_replicas.py'),
    (10.9, 'Step 4',       'BAR Analysis',          'calc_bar_fe.py'),
]
for cx, s1, s2, s3 in steps:
    rbox(ax, cx, Y4, SW, SH, lw=1.5)
    txt(ax, cx, Y4 + 0.42, s1, fs=8.5, bold=True)
    txt(ax, cx, Y4 + 0.12, s2, fs=9,   bold=True)
    txt(ax, cx, Y4 - 0.22, s3, fs=8,   italic=True)

for x0, x1 in [(2.9, 3.4), (6.0, 6.5), (9.1, 9.6)]:
    harrow(ax, x0, x1, Y4, lw=1.5)

plt.tight_layout(pad=0.3)
out1 = os.path.join(DOCS, 'abfe_thermodynamic_cycle.png')
plt.savefig(out1, dpi=180, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {out1}")


# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 2 — Restraint Correction
# ══════════════════════════════════════════════════════════════════════════════
fig2, ax2 = plt.subplots(figsize=(12, 6))
ax2.set_xlim(0, 12); ax2.set_ylim(0, 6)
ax2.axis('off')
fig2.patch.set_facecolor('white')

txt(ax2, 6, 5.65,
    'ABFE Restraint Correction — Why It Is Needed',
    fs=13, bold=True)

# Problem statement box
rbox(ax2, 6, 4.85, 11.0, 0.65, lw=1.5, fill='#f0f0f0')
txt(ax2, 6, 4.95,
    'Problem: During decoupling, DBC restraints hold the ghost ligand in place.',
    fs=9.5)
txt(ax2, 6, 4.70,
    'These restraints introduce artificial free energy that must be removed.',
    fs=9.5, italic=True)

# Term 1
rbox(ax2, 3.0, 3.4, 5.2, 1.1, lw=1.5)
txt(ax2, 3.0, 3.75, '① ΔG_restr_on', fs=10, bold=True)
txt(ax2, 3.0, 3.45, 'Cost of switching ON restraints', fs=9)
txt(ax2, 3.0, 3.18, 'while ligand is still interacting', fs=9)
txt(ax2, 3.0, 2.92, '→ computed numerically from simulation', fs=8.5, italic=True)

# Term 2
rbox(ax2, 9.0, 3.4, 5.2, 1.1, lw=1.5)
txt(ax2, 9.0, 3.75, '② ΔG_restr_analytical', fs=10, bold=True)
txt(ax2, 9.0, 3.45, 'Boresch standard-state correction:', fs=9)
txt(ax2, 9.0, 3.18, 'releases ghost ligand to 1 M standard state', fs=9)
txt(ax2, 9.0, 2.92, '→ computed analytically, no extra simulation', fs=8.5, italic=True)

# Plus sign between
txt(ax2, 6.0, 3.4, '+', fs=18, bold=True)

# Correction equation
rbox(ax2, 6, 2.1, 10.0, 0.65, lw=2)
txt(ax2, 6, 2.1,
    'Total correction  =  ΔG_restr_on  +  ΔG_restr_analytical',
    fs=10, bold=True)

# Full equation
rbox(ax2, 6, 1.1, 11.2, 0.65, lw=2)
txt(ax2, 6, 1.1,
    'ΔG_bind  =  ΔG_site  −  ΔG_solv  +  ΔG_restr_on  +  ΔG_restr_analytical',
    fs=10, bold=True)

# Footnote
txt(ax2, 6, 0.35,
    'Boresch et al. (2003) J. Phys. Chem. B 107, 9535–9551',
    fs=8, italic=True)

plt.tight_layout(pad=0.3)
out2 = os.path.join(DOCS, 'abfe_restraint_correction.png')
plt.savefig(out2, dpi=180, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {out2}")
