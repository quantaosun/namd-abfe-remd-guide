#!/usr/bin/env bash
# =============================================================================
# run_abfe_remd.sh — Run CHARMM-GUI ABFE Replica Exchange with scaled replicas
#
# This script is the ONLY file users need to modify to adapt a CHARMM-GUI
# ABFE job to their available CPU count. All simulation parameters
# (steps_per_run, num_runs, lambda windows, force field, etc.) are read
# directly from the CHARMM-GUI generated conf files and are NOT changed.
#
# Usage:
#   bash run_abfe_remd.sh <leg> <nreplicas> <ncpus>
#
# Arguments:
#   leg        : 'site' (complex leg) or 'solv' (ligand solvation leg)
#   nreplicas  : Number of replicas to run simultaneously.
#                Must divide ncpus evenly. Must also divide the total number
#                of lambda windows (32 by default) evenly.
#   ncpus      : Total number of PHYSICAL CPU cores to use.
#                Use 'python3 scripts/namd_cpu_advisor.py' to find the right value.
#
# Example (14 physical cores, 7 replicas):
#   bash run_abfe_remd.sh site 7 14
#   bash run_abfe_remd.sh solv 7 14
#
# Prerequisites:
#   - NAMD 3.0.2 compiled with netlrts backend (see docs/01_compilation_errors_and_fixes.md)
#   - CHARMM-GUI ABFE input files in the current directory
#   - Equilibration already completed (complex_eq.coor / ligand_eq.coor exist)
#   - Set NAMD_BIN and CHARMRUN below to point to your compiled binaries
# =============================================================================

set -e

# ---- Set these two paths to your compiled NAMD binaries ----------------------
NAMD_BIN="${NAMD_BIN:-/path/to/namd3}"
CHARMRUN="${CHARMRUN:-/path/to/charmrun}"
# ------------------------------------------------------------------------------

LEG="${1}"
NREPLICAS="${2}"
NCPUS="${3}"

# ---- Validate arguments -------------------------------------------------------
if [[ -z "$LEG" || -z "$NREPLICAS" || -z "$NCPUS" ]]; then
    echo "Usage: bash run_abfe_remd.sh <leg> <nreplicas> <ncpus>"
    echo "  leg       : 'site' or 'solv'"
    echo "  nreplicas : number of replicas (must divide ncpus evenly)"
    echo "  ncpus     : total physical CPU cores"
    echo ""
    echo "Example: bash run_abfe_remd.sh site 7 14"
    exit 1
fi

if [[ "$LEG" != "site" && "$LEG" != "solv" ]]; then
    echo "ERROR: leg must be 'site' or 'solv'" && exit 1
fi

if (( NCPUS % NREPLICAS != 0 )); then
    echo "ERROR: ncpus ($NCPUS) must be a multiple of nreplicas ($NREPLICAS)"
    echo "       Valid replica counts for $NCPUS CPUs:"
    for n in $(seq 1 $NCPUS); do
        if (( NCPUS % n == 0 && n >= 2 )); then printf "         +replicas %d  (%d PE/replica)\n" $n $((NCPUS/n)); fi
    done
    exit 1
fi

# ---- Select the CHARMM-GUI conf file (unchanged) -----------------------------
if [ "$LEG" = "site" ]; then
    CONF_FILE="fep_site.conf"
    OUTPUT_DIR="output_site"
else
    CONF_FILE="fep_solv.conf"
    OUTPUT_DIR="output_solv"
fi

if [[ ! -f "$CONF_FILE" ]]; then
    echo "ERROR: Cannot find $CONF_FILE in the current directory."
    echo "       Run this script from inside the complex/ or ligand/ directory."
    exit 1
fi

# ---- Read simulation parameters directly from the CHARMM-GUI conf file ------
# These values are set by CHARMM-GUI and should NOT be changed by the user.
STEPS_PER_RUN=$(grep -E "^set steps_per_run" "$CONF_FILE" | awk '{print $3}')
NUM_RUNS=$(grep -E "^set num_runs" "$CONF_FILE" | awk '{print $3}')
RUNS_PER_FRAME=$(grep -E "^set runs_per_frame" "$CONF_FILE" | awk '{print $3}')
TOTAL_LAMBDA=$(grep -E "^set num_replicas " "$CONF_FILE" | awk '{print $3}' | tr -d ' ')

echo "========================================"
echo " NAMD ABFE REMD — Configuration Summary"
echo "========================================"
echo "  Leg              : $LEG"
echo "  Replicas         : $NREPLICAS  (of $TOTAL_LAMBDA total lambda windows)"
echo "  CPUs             : $NCPUS  ($(( NCPUS / NREPLICAS )) PE per replica)"
echo "  Steps per run    : $STEPS_PER_RUN  [from CHARMM-GUI, not modified]"
echo "  Number of runs   : $NUM_RUNS  [from CHARMM-GUI, not modified]"
echo "  Runs per frame   : $RUNS_PER_FRAME  [from CHARMM-GUI, not modified]"
echo "  Total MD steps   : $(( STEPS_PER_RUN * NUM_RUNS )) per replica"
echo "  Config file      : $CONF_FILE  [CHARMM-GUI generated, not modified]"
echo "========================================"

# ---- Create output directories -----------------------------------------------
for i in $(seq 0 $(( NREPLICAS - 1 ))); do
    mkdir -p "${OUTPUT_DIR}/${i}" "output_off/${i}"
done

# ---- Patch ONLY num_replicas in a temporary copy of the conf file ------------
# All other parameters (steps, runs, lambda values, etc.) are preserved exactly.
TMP_CONF=$(mktemp fep_${LEG}_scaled_XXXXXX.conf)
sed "s/^set num_replicas .*/set num_replicas $NREPLICAS/" \
    "$CONF_FILE" | \
sed "s/^set num_replicasb .*/set num_replicasb $NREPLICAS/" \
    > "$TMP_CONF"

echo "Temporary scaled conf: $TMP_CONF  (only num_replicas changed)"
echo "Launching REMD..."

"$CHARMRUN" ++local "+p${NCPUS}" "$NAMD_BIN" "+replicas" "$NREPLICAS" \
    "$TMP_CONF" --source FEP_remd_softcore.namd \
    "+stdout" "${OUTPUT_DIR}/%d/job0.%d.log" \
    > "remd_${LEG}.log" 2>&1

# Clean up temp file
rm -f "$TMP_CONF"

echo ""
echo "========================================"
echo " REMD complete. Log: remd_${LEG}.log"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Sort trajectories:  python3 scripts/sort_replicas.py --leg $LEG --nreplicas $NREPLICAS"
echo "  2. Calculate dG:       python3 scripts/calc_bar_fe.py   --leg $LEG --nreplicas $NREPLICAS"
