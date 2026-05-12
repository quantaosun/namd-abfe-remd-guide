#!/usr/bin/env bash
# =============================================================================
# scale_replicas.sh — Patch all CHARMM-GUI ABFE config files for a given
#                     replica count based on available CPU cores.
#
# This script is the ONLY modification needed to adapt a CHARMM-GUI ABFE
# job to your hardware. It patches exactly 5 files in both the complex/
# and ligand/ directories. All simulation parameters (steps, lambda values,
# force field, etc.) are left completely unchanged.
#
# Usage (run from inside the CHARMM-GUI namd/1/ directory):
#   bash /path/to/scale_replicas.sh <nreplicas>
#
# Arguments:
#   nreplicas : Number of replicas to use. Must divide your physical CPU count
#               evenly. Use 'python3 namd_cpu_advisor.py' to find the best value.
#
# Files patched in BOTH complex/ and ligand/ directories:
#   1. fep_site.conf / fep_solv.conf  — num_replicas, num_replicasb
#   2. 1_mkdir.pl                     — loop upper bound for output dirs
#   3. 3_job_run.pbs                  — +replicas N in the launch command
#   4. sort.py                        — num_replica = N  (+Python 2->3 fix)
#   5. calc_fe.pl                     — $fep_win_num = N
#
# Backups of all original files are saved as <filename>.orig before patching.
# To restore originals: bash scale_replicas.sh --restore
# =============================================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
patched() { echo -e "${CYAN}[PATCH]${NC} $*"; }

# ---- Restore mode ------------------------------------------------------------
if [[ "$1" == "--restore" ]]; then
    info "Restoring original CHARMM-GUI files from .orig backups..."
    for f in complex/fep_site.conf ligand/fep_solv.conf \
              complex/1_mkdir.pl ligand/1_mkdir.pl \
              complex/3_job_run.pbs ligand/3_job_run.pbs \
              complex/sort.py ligand/sort.py \
              complex/calc_fe.pl ligand/calc_fe.pl; do
        if [[ -f "${f}.orig" ]]; then
            cp "${f}.orig" "$f"
            info "Restored: $f"
        fi
    done
    info "Restore complete."
    exit 0
fi

# ---- Argument check ----------------------------------------------------------
N="${1}"
if [[ -z "$N" ]]; then
    echo "Usage: bash scale_replicas.sh <nreplicas>"
    echo "       bash scale_replicas.sh --restore"
    echo ""
    echo "  nreplicas : number of replicas (e.g. 4, 7, 14, 16)"
    echo "  Run 'python3 namd_cpu_advisor.py' to find the best value for your machine."
    exit 1
fi

[[ "$N" =~ ^[0-9]+$ ]] || error "nreplicas must be a positive integer, got: $N"
(( N >= 2 ))           || error "nreplicas must be at least 2, got: $N"

# ---- Check we are in the right directory -------------------------------------
if [[ ! -d "complex" || ! -d "ligand" ]]; then
    error "Cannot find 'complex/' and 'ligand/' directories here."
    error "Please run this script from inside the CHARMM-GUI namd/1/ directory."
fi

# ---- Read original replica count from fep_site.conf -------------------------
ORIG_N=$(grep -E "^set num_replicas " complex/fep_site.conf | awk '{print $3}' | tr -d ' ')
[[ -z "$ORIG_N" ]] && ORIG_N=32
info "Original replica count (from CHARMM-GUI): $ORIG_N"
info "Target  replica count                   : $N"

if [[ "$N" == "$ORIG_N" ]]; then
    warn "Target replica count ($N) equals the current value. No changes needed."
    exit 0
fi

# ---- Helper: backup a file before first patch --------------------------------
backup() {
    local f="$1"
    if [[ ! -f "${f}.orig" ]]; then
        cp "$f" "${f}.orig"
        info "Backup: ${f}.orig"
    fi
}

echo ""
echo "========================================"
echo " Patching CHARMM-GUI files: $ORIG_N -> $N replicas"
echo "========================================"

# FILE 1: fep_site.conf — num_replicas and num_replicasb only
# (num_replicasa and num_replicasc are restraint-window counts, left at 0)
F="complex/fep_site.conf"; backup "$F"
sed -i "s/^set num_replicas .*/set num_replicas $N /" "$F"
sed -i "s/^set num_replicasb .*/set num_replicasb $N /" "$F"
patched "$F  ->  num_replicas=$N, num_replicasb=$N"

# FILE 2: fep_solv.conf
F="ligand/fep_solv.conf"; backup "$F"
sed -i "s/^set num_replicas .*/set num_replicas $N /" "$F"
sed -i "s/^set num_replicasb .*/set num_replicasb $N /" "$F"
patched "$F  ->  num_replicas=$N, num_replicasb=$N"

# FILE 3+4: 1_mkdir.pl (both legs) — loop upper bound
for dir in complex ligand; do
    F="$dir/1_mkdir.pl"; backup "$F"
    sed -i "s/\$j < ${ORIG_N}/\$j < ${N}/g" "$F"
    patched "$F  ->  loop bound $ORIG_N -> $N"
done

# FILE 5+6: 3_job_run.pbs (both legs) — +replicas count
for dir in complex ligand; do
    F="$dir/3_job_run.pbs"; backup "$F"
    sed -i "s/+replicas ${ORIG_N}/+replicas ${N}/g" "$F"
    patched "$F  ->  +replicas $ORIG_N -> +replicas $N"
done

# FILE 7+8: sort.py (both legs) — num_replica count + Python 2->3 print fix
for dir in complex ligand; do
    F="$dir/sort.py"; backup "$F"
    sed -i "s/num_replica = ${ORIG_N}/num_replica = ${N}/g" "$F"
    # Fix Python 2 bare print statements if present (print x -> print(x))
    if grep -qP "^print [^(]" "$F" 2>/dev/null; then
        python3 -c "
import re, sys
txt = open('$F').read()
txt = re.sub(r'^(print )([^(].*)', lambda m: 'print(' + m.group(2).rstrip() + ')', txt, flags=re.MULTILINE)
open('$F','w').write(txt)
"
        patched "$F  ->  num_replica=$N  +  Python 2->3 print fix applied"
    else
        patched "$F  ->  num_replica=$N"
    fi
done

# FILE 9+10: calc_fe.pl (both legs) — fep_win_num
for dir in complex ligand; do
    F="$dir/calc_fe.pl"; backup "$F"
    sed -i "s/\$fep_win_num = ${ORIG_N}/\$fep_win_num = ${N}/" "$F"
    patched "$F  ->  fep_win_num=$N"
done

echo ""
echo -e "${GREEN}========================================"
echo " All files patched successfully!"
echo -e "========================================${NC}"
echo ""
echo "  Replica count : $ORIG_N -> $N"
echo "  Files patched : 10 files (5 per leg x 2 legs)"
echo "  Backups saved : <filename>.orig  (restore with: bash scale_replicas.sh --restore)"
echo ""
echo "Next step — run the REMD simulation:"
echo "  cd complex/ && bash /path/to/run_abfe_remd.sh site $N <ncpus>"
echo "  cd ../ligand/ && bash /path/to/run_abfe_remd.sh solv $N <ncpus>"
