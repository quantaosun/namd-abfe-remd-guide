#!/usr/bin/env python3
"""
sort_replicas.py — Adapted CHARMM-GUI ABFE replica sort script.

Sorts NAMD REMD history files from physical-replica order (output_site/ or
output_solv/) into lambda-window order (output_off/), enabling BAR analysis.

This is a Python 3-compatible, configurable adaptation of the original
CHARMM-GUI sort.py (which used Python 2 and hardcoded 32 replicas).

Usage:
    python3 sort_replicas.py --step <job_step> --leg <site|solv> --nreplicas <N>

Example (4-replica test, complex leg, job step 0):
    python3 sort_replicas.py --step 0 --leg site --nreplicas 4
"""

import sys
import os
import argparse


def sort_replicas(step, leg, num_replica):
    prefix = "fep"

    if leg == "site":
        in_dir = "output_site"
        out_dir = "output_off"
    elif leg == "solv":
        in_dir = "output_solv"
        out_dir = "output_off"
    else:
        raise ValueError(f"Unknown leg '{leg}'. Use 'site' or 'solv'.")

    # Open input history files (one per physical replica)
    history_fps = []
    for i in range(num_replica):
        path = f"{in_dir}/{i}/{prefix}.job{step}.{i}.history"
        history_fps.append(open(path))

    # Open output sorted history files (one per lambda window)
    os.makedirs(out_dir, exist_ok=True)
    sorted_history_fps = []
    for i in range(num_replica):
        os.makedirs(f"{out_dir}/{i}", exist_ok=True)
        path = f"{out_dir}/{i}/{prefix}.job{step}.{i}.sort.history"
        sorted_history_fps.append(open(path, "w"))

    timestamp = [0] * num_replica
    rep = list(range(num_replica))
    final_step = -1

    while True:
        all_done = True
        _timestamp = list(timestamp)

        for i in range(num_replica):
            try:
                if timestamp[i] > 0 and timestamp[i] > min(_timestamp):
                    continue  # wait if this replica is ahead of others
                line = history_fps[i].readline()
                if not line.strip():
                    raise EOFError
                parts = line.split()
                time = int(parts[0])
                rep[i] = int(parts[1])
                next_rep = int(parts[2])
                doswap = int(parts[-1])
                timestamp[i] = time
                all_done = False
            except Exception:
                time = max(timestamp) if any(t > 0 for t in timestamp) else 0
                timestamp[i] = time
                final_step = time
                continue

            sorted_history_fps[rep[i]].write(line)
            if doswap:
                rep[i] = next_rep

        _timestamp = list(timestamp)
        time = min(_timestamp)
        if all_done or (final_step > 0 and time >= final_step):
            break
        print(time)

    for f in history_fps + sorted_history_fps:
        f.close()

    print(f"Sort complete: job{step}, leg={leg}, replicas={num_replica}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sort NAMD REMD replica histories by lambda window.")
    parser.add_argument("--step", type=int, default=0, help="Job step number (default: 0)")
    parser.add_argument("--leg", type=str, default="site", choices=["site", "solv"],
                        help="Simulation leg: 'site' (complex) or 'solv' (ligand)")
    parser.add_argument("--nreplicas", type=int, default=32,
                        help="Number of replicas (default: 32)")
    args = parser.parse_args()
    sort_replicas(args.step, args.leg, args.nreplicas)
