#!/usr/bin/env bash
# =============================================================================
# run_abfe_remd.sh — Run CHARMM-GUI ABFE Replica Exchange with scaled replicas
#
# Usage:
#   bash run_abfe_remd.sh <leg> <nreplicas> <ncpus> <num_runs> <steps_per_run>
#
# Arguments:
#   leg          : 'site' (complex) or 'solv' (ligand)
#   nreplicas    : Number of replicas (must divide ncpus evenly)
#   ncpus        : Total number of CPUs to use
#   num_runs     : Number of REMD exchange cycles
#   steps_per_run: MD steps per exchange cycle
#
# Example (4 replicas, 4 CPUs, 2 runs x 100 steps):
#   bash run_abfe_remd.sh site 4 4 2 100
#
# Prerequisites:
#   - NAMD 3.0.2 compiled with netlrts backend (see docs/01_compilation_errors_and_fixes.md)
#   - CHARMM-GUI ABFE input files in the current directory
#   - Equilibration already completed (complex_eq.coor / ligand_eq.coor exist)
# =============================================================================

set -e

LEG="${1:-site}"
NREPLICAS="${2:-4}"
NCPUS="${3:-4}"
NUM_RUNS="${4:-2}"
STEPS_PER_RUN="${5:-100}"

# ---- Paths (edit these to match your installation) ----
NAMD_BIN="${NAMD_BIN:-/path/to/namd3}"
CHARMRUN="${CHARMRUN:-/path/to/charmrun}"
# -------------------------------------------------------

if [ "$LEG" = "site" ]; then
    CONF_FILE="fep_site.conf"
    OUTPUT_DIR="output_site"
elif [ "$LEG" = "solv" ]; then
    CONF_FILE="fep_solv.conf"
    OUTPUT_DIR="output_solv"
else
    echo "ERROR: leg must be 'site' or 'solv'" && exit 1
fi

# Validate that ncpus is a multiple of nreplicas
if (( NCPUS % NREPLICAS != 0 )); then
    echo "ERROR: ncpus ($NCPUS) must be a multiple of nreplicas ($NREPLICAS)"
    exit 1
fi

echo "========================================"
echo " NAMD ABFE REMD Configuration"
echo "========================================"
echo "  Leg              : $LEG"
echo "  Replicas         : $NREPLICAS"
echo "  CPUs             : $NCPUS ($(( NCPUS / NREPLICAS )) PE per replica)"
echo "  Runs             : $NUM_RUNS x $STEPS_PER_RUN steps"
echo "  Config file      : $CONF_FILE"
echo "========================================"

# Create output directories
for i in $(seq 0 $(( NREPLICAS - 1 ))); do
    mkdir -p "${OUTPUT_DIR}/${i}" "output_off/${i}"
done

# Generate a temporary conf file with the scaled parameters
TMP_CONF="fep_${LEG}_scaled.conf"
cat > "$TMP_CONF" << EOF
# Auto-generated scaled conf for $NREPLICAS replicas
source $CONF_FILE
set num_replicas $NREPLICAS
set num_replicasb $NREPLICAS
set num_runs $NUM_RUNS
set steps_per_run $STEPS_PER_RUN
set runs_per_frame $NUM_RUNS
set output_root "${OUTPUT_DIR}/%s/fep"
EOF

echo "Generated: $TMP_CONF"
echo "Launching REMD..."

"$CHARMRUN" ++local "+p${NCPUS}" "$NAMD_BIN" "+replicas" "$NREPLICAS" \
    "$TMP_CONF" --source FEP_remd_softcore.namd \
    "+stdout" "${OUTPUT_DIR}/%d/job0.%d.log" \
    > "remd_${LEG}.log" 2>&1

echo "REMD complete. Log: remd_${LEG}.log"
echo ""
echo "Next steps:"
echo "  1. Sort trajectories:  python3 sort_replicas.py --step 0 --leg $LEG --nreplicas $NREPLICAS"
echo "  2. Calculate dG:       python3 calc_bar_fe.py --leg $LEG --nreplicas $NREPLICAS"
