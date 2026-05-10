#!/usr/bin/env python3
"""
namd_cpu_advisor.py — NAMD ABFE REMD CPU Configuration Advisor

Parses `lscpu` output to determine the true physical core count (ignoring
hyperthreading) and recommends the optimal +replicas / +p configuration
for NAMD replica exchange simulations.

WHY PHYSICAL CORES ONLY?
  `lscpu` reports logical CPUs = physical cores × threads_per_core.
  Hyperthreaded "virtual" CPUs share the same floating-point execution units,
  so they provide no real speedup for compute-intensive MD workloads and can
  actually increase memory bandwidth contention. Always use physical cores only.

Usage:
    python3 namd_cpu_advisor.py                  # auto-detect via lscpu
    python3 namd_cpu_advisor.py --lscpu-file <file>  # parse saved lscpu output
    python3 namd_cpu_advisor.py --physical-cores 14  # override manually

Output:
    Ranked table of valid +replicas / +p combinations with recommendations.
"""

import subprocess
import argparse
import sys


# ---------------------------------------------------------------------------
# Preferred replica counts for ABFE (in order of scientific preference).
# These are the values CHARMM-GUI supports and that give good lambda spacing.
PREFERRED_REPLICA_COUNTS = [32, 16, 8, 4, 2]
# ---------------------------------------------------------------------------


def parse_lscpu(text: str) -> dict:
    """Parse lscpu text output into a key→value dictionary."""
    info = {}
    for line in text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            info[key.strip()] = val.strip()
    return info


def get_lscpu_info(lscpu_file: str = None) -> dict:
    """Obtain lscpu info either from a file or by running lscpu."""
    if lscpu_file:
        with open(lscpu_file) as f:
            text = f.read()
    else:
        try:
            result = subprocess.run(["lscpu"], capture_output=True, text=True, check=True)
            text = result.stdout
        except FileNotFoundError:
            print("ERROR: `lscpu` not found. Use --physical-cores to specify manually.")
            sys.exit(1)
    return parse_lscpu(text)


def extract_physical_cores(info: dict) -> tuple[int, int, int, int]:
    """
    Extract physical core count from lscpu info dictionary.

    Returns:
        (physical_cores, logical_cpus, threads_per_core, sockets)
    """
    try:
        logical_cpus    = int(info.get("CPU(s)", 0))
        threads_per_core = int(info.get("Thread(s) per core", 1))
        cores_per_socket = int(info.get("Core(s) per socket", logical_cpus))
        sockets          = int(info.get("Socket(s)", 1))
        physical_cores   = cores_per_socket * sockets
    except (ValueError, TypeError) as e:
        print(f"ERROR: Could not parse lscpu output: {e}")
        sys.exit(1)

    return physical_cores, logical_cpus, threads_per_core, sockets


def get_divisors(n: int) -> list[int]:
    """Return all divisors of n in ascending order."""
    return sorted(d for d in range(1, n + 1) if n % d == 0)


def recommend_configurations(physical_cores: int, max_replicas: int = 32) -> list[dict]:
    """
    Generate all valid +replicas / +p combinations for the given physical core count.

    Rules:
      1. +p must equal physical_cores (use all cores)
      2. +replicas must divide +p evenly
      3. +replicas <= max_replicas (CHARMM-GUI default maximum)
      4. +replicas >= 2 (need at least 2 windows for FEP)

    Returns a list of config dicts sorted by scientific preference.
    """
    configs = []
    divisors = get_divisors(physical_cores)

    for nrep in divisors:
        if nrep < 2 or nrep > max_replicas:
            continue
        pe_per_replica = physical_cores // nrep
        configs.append({
            "replicas":       nrep,
            "total_p":        physical_cores,
            "pe_per_replica": pe_per_replica,
        })

    # Sort priority:
    #   1. Prefer pe_per_replica >= 2 (fast per-window MD) over 1 PE (slow)
    #   2. Among configs with pe >= 2, prefer MORE replicas (better accuracy)
    #   3. Among configs with pe == 1, prefer more replicas over fewer
    def score(c):
        rep = c["replicas"]
        pe  = c["pe_per_replica"]
        # Group 0 = pe>=2 (good), Group 1 = pe==1 (slow)
        pe_group = 0 if pe >= 2 else 1
        # Within each group, higher replica count = better (use negative for ascending sort)
        return (pe_group, -rep)

    configs.sort(key=score)
    return configs


def print_report(physical_cores: int, logical_cpus: int,
                 threads_per_core: int, sockets: int,
                 configs: list[dict]) -> None:
    """Print a formatted recommendation report."""
    ht_status = "enabled" if threads_per_core > 1 else "not present"

    print()
    print("=" * 65)
    print("  NAMD ABFE REMD — CPU Configuration Advisor")
    print("=" * 65)
    print(f"  Logical CPUs (lscpu)   : {logical_cpus}")
    print(f"  Threads per core       : {threads_per_core}  (hyperthreading {ht_status})")
    print(f"  Sockets                : {sockets}")
    print(f"  *** Physical cores     : {physical_cores}  ← use this for NAMD ***")
    print()

    if threads_per_core > 1:
        print(f"  NOTE: lscpu reports {logical_cpus} logical CPUs, but only {physical_cores}")
        print(f"  are real physical cores. Using all {logical_cpus} logical CPUs would")
        print(f"  NOT speed up NAMD and may slow it down due to cache contention.")
        print(f"  Always set +p{physical_cores} (physical cores only).")
        print()

    if not configs:
        print(f"  No valid replica configurations found for {physical_cores} physical cores.")
        print(f"  (Need at least 2 replicas; cores must be divisible by replica count.)")
        print()
        return

    print(f"  Valid configurations for +p{physical_cores}:")
    print()
    print(f"  {'Rank':<5} {'+replicas':<12} {'+p':<8} {'PE/replica':<14} {'Recommendation'}")
    print(f"  {'-'*4} {'-'*11} {'-'*7} {'-'*13} {'-'*35}")

    for rank, cfg in enumerate(configs, 1):
        nrep = cfg["replicas"]
        pe   = cfg["pe_per_replica"]
        p    = cfg["total_p"]

        if rank == 1:
            tag = "<-- BEST (most accurate + fast)"
        elif rank == 2:
            tag = "<-- Good alternative"
        elif nrep in PREFERRED_REPLICA_COUNTS and pe >= 2:
            tag = "Acceptable"
        elif pe == 1:
            tag = "Works; each replica single-threaded (slow)"
        else:
            tag = ""

        print(f"  {rank:<5} {nrep:<12} {p:<8} {pe:<14} {tag}")

    print()
    best = configs[0]
    print(f"  RECOMMENDED LAUNCH COMMAND:")
    print(f"    charmrun ++local +p{best['total_p']} namd3 \\")
    print(f"      +replicas {best['replicas']} fep_site.conf \\")
    print(f"      --source FEP_remd_softcore.namd \\")
    print(f"      +stdout output_site/%d/job0.%d.log")
    print()
    print(f"  SCRIPTS TO UPDATE (change 32 → {best['replicas']}):")
    print(f"    fep_site.conf / fep_solv.conf : set num_replicas {best['replicas']}")
    print(f"                                    set num_replicasb {best['replicas']}")
    print(f"    1_mkdir.pl                    : loop upper bound → {best['replicas']}")
    print(f"    3_job_run.pbs                 : +replicas {best['replicas']}")
    print(f"    sort.py                       : num_replica = {best['replicas']}")
    print(f"    calc_fe.pl                    : $fep_win_num = {best['replicas']}")
    print("=" * 65)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Recommend NAMD +replicas / +p settings from lscpu output."
    )
    parser.add_argument(
        "--lscpu-file", type=str, default=None,
        help="Path to a saved `lscpu` output file (optional; runs lscpu if omitted)"
    )
    parser.add_argument(
        "--physical-cores", type=int, default=None,
        help="Override: specify physical core count directly (skips lscpu parsing)"
    )
    parser.add_argument(
        "--max-replicas", type=int, default=32,
        help="Maximum replica count to consider (default: 32)"
    )
    args = parser.parse_args()

    if args.physical_cores:
        # Manual override — assume no hyperthreading info available
        physical_cores = args.physical_cores
        logical_cpus = physical_cores
        threads_per_core = 1
        sockets = 1
    else:
        info = get_lscpu_info(args.lscpu_file)
        physical_cores, logical_cpus, threads_per_core, sockets = extract_physical_cores(info)

    configs = recommend_configurations(physical_cores, args.max_replicas)
    print_report(physical_cores, logical_cpus, threads_per_core, sockets, configs)


if __name__ == "__main__":
    main()
