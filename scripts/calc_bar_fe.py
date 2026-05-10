#!/usr/bin/env python3
"""
calc_bar_fe.py — BAR Free Energy Calculator for CHARMM-GUI ABFE REMD output.

Calculates the Bennett Acceptance Ratio (BAR) free energy from sorted NAMD
REMD history files. This is a Python 3 adaptation of the original CHARMM-GUI
calc_fe.pl, with configurable replica count.

Usage:
    python3 calc_bar_fe.py --leg <site|solv> --nreplicas <N> [--step <job_step>]

Example (4-replica test, both legs):
    python3 calc_bar_fe.py --leg site --nreplicas 4
    python3 calc_bar_fe.py --leg solv --nreplicas 4

The script reads from output_off/<window>/fep.job<step>.<window>.sort.history
"""

import math
import glob
import os
import argparse


BOLTZMANN = 0.001987191  # kcal/mol/K
TEMP = 300.0             # K
RT = BOLTZMANN * TEMP


def calc_bar(out_dir, leg, num_win, step):
    """
    Calculate BAR free energy from sorted history files.

    The .sort.history file columns are:
        step  cur_lambda_idx  next_lambda_idx  temp
        PE_cur  PE_next  PE_cur_at_next_lambda  PE_next_at_cur_lambda  doswap

    BAR formula (symmetric estimator):
        dG = -RT * ln( <exp(-dU_0 / 2RT)> / <exp(dU_1 / 2RT)> )
    where:
        dU_0 = PE(lambda+1) - PE(lambda)      [forward perturbation]
        dU_1 = PE_cur_at_next - PE_next_at_cur [reverse perturbation]
    """
    total_dG = 0.0
    files = sorted(glob.glob(f"{out_dir}/*/fep.job{step}.*.sort.history"))

    print(f"\n=== BAR Free Energy: {leg} leg ===")
    print(f"  Output directory : {out_dir}")
    print(f"  Found {len(files)} sorted history files")

    for f in files:
        win = int(os.path.basename(os.path.dirname(f)))
        if win >= num_win - 1:
            # Last window has no forward partner; skip
            continue

        count = 0
        sum0 = sum1 = 0.0

        with open(f) as fh:
            for line in fh:
                parts = line.split()
                if not parts or parts[0].startswith("#"):
                    continue
                try:
                    cur = int(parts[1])
                    nxt = int(parts[2])
                    PE_cur = float(parts[4])
                    PE_nxt = float(parts[5])
                    PE_cur_at_nxt = float(parts[6])
                    PE_nxt_at_cur = float(parts[7])
                except (IndexError, ValueError):
                    continue

                if cur < nxt:  # forward direction only
                    count += 1
                    dU_0 = PE_nxt - PE_cur
                    dU_1 = PE_cur_at_nxt - PE_nxt_at_cur
                    sum0 += math.exp(-dU_0 / (2.0 * RT))
                    sum1 += math.exp(dU_1 / (2.0 * RT))

        if count > 0:
            dG_win = -RT * math.log((sum0 / count) / (sum1 / count))
            total_dG += dG_win
            lam_cur = win / (num_win - 1)
            lam_nxt = (win + 1) / (num_win - 1)
            print(f"  Window {win}→{win+1} (λ={lam_cur:.3f}→{lam_nxt:.3f}): "
                  f"n={count}, dG={dG_win:+.4f} kcal/mol")
        else:
            print(f"  Window {win}: no forward transitions found (too few steps?)")

    print(f"  ──────────────────────────────────────────")
    print(f"  TOTAL dG ({leg}) = {total_dG:+.5f} kcal/mol")
    return total_dG


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculate BAR free energy from CHARMM-GUI ABFE REMD output."
    )
    parser.add_argument("--leg", type=str, required=True, choices=["site", "solv"],
                        help="Simulation leg: 'site' (complex) or 'solv' (ligand)")
    parser.add_argument("--nreplicas", type=int, default=32,
                        help="Number of replicas (default: 32)")
    parser.add_argument("--step", type=int, default=0,
                        help="Job step number (default: 0)")
    parser.add_argument("--outdir", type=str, default="output_off",
                        help="Sorted output directory (default: output_off)")
    args = parser.parse_args()

    dG = calc_bar(args.outdir, args.leg, args.nreplicas, args.step)

    print(f"\n  Run with --leg site and --leg solv, then compute:")
    print(f"  ΔG_bind = ΔG_site - ΔG_solv")
