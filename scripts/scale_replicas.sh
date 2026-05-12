#!/usr/bin/env bash
# =============================================================================
# scale_replicas.sh — Patch all CHARMM-GUI ABFE config files for a given
#                     replica count based on available CPU cores.
#
# Works with any number of job directories (namd/1/, namd/2/, namd/3/, ...).
# Run this from the CHARMM-GUI namd/ directory (the one containing 1/, 2/, ...).
#
# Usage:
#   bash scale_replicas.sh <nreplicas>          # patch all jobs
#   bash scale_replicas.sh --restore            # restore all .orig backups
#
# Arguments:
#   nreplicas : Number of replicas to use. Must divide your physical CPU count
#               evenly. Run 'python3 namd_cpu_advisor.py' to find the best value.
#
# Files patched in EACH job's complex/ and ligand/ directories:
#   1. fep_site.conf / fep_solv.conf  — num_replicas, num_replicasb
#   2. 1_mkdir.pl                     — loop upper bound for output dirs
#   3. 3_job_run.pbs                  — +replicas N in the launch command
#   4. sort.py                        — num_replica = N  (+Python 2->3 fix)
#   5. calc_fe.pl                     — $fep_win_num = N
#
# All original files are backed up as <filename>.orig before patching.
# =============================================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
patched() { echo -e "${CYAN}[PATCH]${NC} $*"; }

# ---- Restore mode ------------------------------------------------------------
if [[ "$1" == "--restore" ]]; then
    info "Restoring original CHARMM-GUI files from .orig backups..."
    for jobdir in */; do
        jobdir="${jobdir%/}"
        [[ -d "${jobdir}/complex" || -d "${jobdir}/ligand" ]] || continue
        for f in "${jobdir}/complex/fep_site.conf" "${jobdir}/ligand/fep_solv.conf" \
                  "${jobdir}/complex/1_mkdir.pl"   "${jobdir}/ligand/1_mkdir.pl" \
                  "${jobdir}/complex/3_job_run.pbs" "${jobdir}/ligand/3_job_run.pbs" \
                  "${jobdir}/complex/sort.py"       "${jobdir}/ligand/sort.py" \
                  "${jobdir}/complex/calc_fe.pl"    "${jobdir}/ligand/calc_fe.pl"; do
            if [[ -f "${f}.orig" ]]; then
                cp "${f}.orig" "$f"
                info "Restored: $f"
            fi
        done
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

# ---- Discover all job directories (subdirs containing complex/ and ligand/) --
JOBS=()
for d in */; do
    d="${d%/}"
    if [[ -d "$d/complex" && -d "$d/ligand" ]]; then
        JOBS+=("$d")
    fi
done

if [[ ${#JOBS[@]} -eq 0 ]]; then
    error "No job directories found. Expected subdirectories each containing complex/ and ligand/."$'\n'"       Please run this script from inside the CHARMM-GUI namd/ directory (e.g., namd/)."
fi

info "Found ${#JOBS[@]} job(s): ${JOBS[*]}"

# ---- Helper: backup a file before first patch --------------------------------
backup() {
    local f="$1"
    if [[ ! -f "${f}.orig" ]]; then
        cp "$f" "${f}.orig"
    fi
}

# ---- Patch each job ----------------------------------------------------------
TOTAL_PATCHED=0
ORIG_N_LAST=32

for JOB in "${JOBS[@]}"; do

    CONF="$JOB/complex/fep_site.conf"
    [[ -f "$CONF" ]] || { warn "Skipping $JOB: fep_site.conf not found"; continue; }
    ORIG_N=$(grep -E "^set num_replicas " "$CONF" | awk '{print $3}' | tr -d ' ')
    [[ -z "$ORIG_N" ]] && ORIG_N=32
    ORIG_N_LAST=$ORIG_N

    echo ""
    echo "========================================"
    echo " Job: $JOB  ($ORIG_N -> $N replicas)"
    echo "========================================"

    if [[ "$N" == "$ORIG_N" ]]; then
        warn "Job $JOB: already set to $N replicas, skipping."
        continue
    fi

    # 1. fep_site.conf (complex leg)
    F="$JOB/complex/fep_site.conf"; backup "$F"
    sed -i "s/^set num_replicas .*/set num_replicas $N /" "$F"
    sed -i "s/^set num_replicasb .*/set num_replicasb $N /" "$F"
    patched "$F  ->  num_replicas=$N, num_replicasb=$N"

    # 2. fep_solv.conf (ligand leg)
    F="$JOB/ligand/fep_solv.conf"; backup "$F"
    sed -i "s/^set num_replicas .*/set num_replicas $N /" "$F"
    sed -i "s/^set num_replicasb .*/set num_replicasb $N /" "$F"
    patched "$F  ->  num_replicas=$N, num_replicasb=$N"

    # 3+4. 1_mkdir.pl (both legs)
    for dir in "$JOB/complex" "$JOB/ligand"; do
        F="$dir/1_mkdir.pl"; backup "$F"
        sed -i "s/\$j < ${ORIG_N}/\$j < ${N}/g" "$F"
        patched "$F  ->  loop bound $ORIG_N -> $N"
    done

    # 5+6. 3_job_run.pbs (both legs)
    for dir in "$JOB/complex" "$JOB/ligand"; do
        F="$dir/3_job_run.pbs"; backup "$F"
        sed -i "s/+replicas ${ORIG_N}/+replicas ${N}/g" "$F"
        patched "$F  ->  +replicas $ORIG_N -> +replicas $N"
    done

    # 7+8. sort.py (both legs) + Python 2->3 print fix
    for dir in "$JOB/complex" "$JOB/ligand"; do
        F="$dir/sort.py"; backup "$F"
        sed -i "s/num_replica = ${ORIG_N}/num_replica = ${N}/g" "$F"
        if grep -qP "^print [^(]" "$F" 2>/dev/null; then
            python3 -c "
import re
txt = open('${F}').read()
txt = re.sub(r'^(print )([^(].*)', lambda m: 'print(' + m.group(2).rstrip() + ')', txt, flags=re.MULTILINE)
open('${F}','w').write(txt)
"
            patched "$F  ->  num_replica=$N  +  Python 2->3 print fix"
        else
            patched "$F  ->  num_replica=$N"
        fi
    done

    # 9+10. calc_fe.pl (both legs)
    for dir in "$JOB/complex" "$JOB/ligand"; do
        F="$dir/calc_fe.pl"; backup "$F"
        sed -i "s/\$fep_win_num = ${ORIG_N}/\$fep_win_num = ${N}/" "$F"
        patched "$F  ->  fep_win_num=$N"
    done

    TOTAL_PATCHED=$(( TOTAL_PATCHED + 1 ))
done

# ---- Summary -----------------------------------------------------------------
echo ""
echo -e "${GREEN}========================================"
echo " Done! $TOTAL_PATCHED job(s) patched."
echo -e "========================================${NC}"
echo ""
echo "  Replica count : $ORIG_N_LAST -> $N"
echo "  Files patched : $(( TOTAL_PATCHED * 10 )) files (5 per leg x 2 legs x $TOTAL_PATCHED job(s))"
echo "  Backups saved : <filename>.orig  (restore with: bash scale_replicas.sh --restore)"
echo ""
echo "Next: run the CHARMM-GUI scripts for each job (see README for details)."
