#!/usr/bin/env bash
# =============================================================================
# compile_namd.sh — Automated NAMD 3.0.2 compilation for replica exchange
#
# This script compiles NAMD 3.0.2 from source with the netlrts-linux-x86_64
# Charm++ backend, which is required for replica exchange (+replicas) support.
# It automatically handles all known compilation errors on Ubuntu 20.04/22.04.
#
# Usage:
#   bash compile_namd.sh <path/to/NAMD_3.0.2_Source.tar.gz>
#
# Output:
#   A compiled namd3 binary at:
#   NAMD_3.0.2_Source/Linux-x86_64-g++-netlrts/namd3
#
# Tested on: Ubuntu 22.04 LTS (x86_64)
# =============================================================================

set -e

# ---- Colour helpers ----------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ---- Argument check ----------------------------------------------------------
TARBALL="${1}"
if [[ -z "$TARBALL" ]]; then
    echo "Usage: bash compile_namd.sh <path/to/NAMD_3.0.2_Source.tar.gz>"
    echo ""
    echo "Download the source tarball from:"
    echo "  https://www.ks.uiuc.edu/Development/Download/download.cgi?PackageName=NAMD"
    echo "  (free registration required)"
    exit 1
fi
[[ -f "$TARBALL" ]] || error "File not found: $TARBALL"

# ---- Detect number of CPU cores for parallel build ---------------------------
NCORES=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || echo 4)
info "Building with $NCORES parallel jobs"

# =============================================================================
# STEP 1: Install system dependencies
# -----------------------------------------------------------------------------
# ERROR FIXED: The pre-built UIUC FFTW2 and TCL libraries distributed with
# NAMD were compiled without -fPIC and fail to link on modern Ubuntu with:
#   "relocation R_X86_64_32 against ... can not be used when making a PIE"
# FIX: Use system libfftw3-dev and tcl8.6-dev instead of the UIUC bundles.
# =============================================================================
info "Step 1/5: Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y \
    build-essential \
    csh \
    tcl-dev \
    tcl8.6-dev \
    libfftw3-dev \
    wget \
    tar \
    2>&1 | grep -E "^(Get|Setting|Unpacking|Selecting)" || true
info "Dependencies installed."

# =============================================================================
# STEP 2: Extract NAMD source
# =============================================================================
info "Step 2/5: Extracting NAMD source..."
WORKDIR="$(pwd)/namd_build"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

tar xf "$TARBALL"
NAMD_SRC="$WORKDIR/NAMD_3.0.2_Source"
[[ -d "$NAMD_SRC" ]] || error "Expected directory $NAMD_SRC not found after extraction."
info "Extracted to: $NAMD_SRC"

# =============================================================================
# STEP 3: Build Charm++ with netlrts backend
# -----------------------------------------------------------------------------
# ERROR FIXED: The standard 'multicore' Charm++ build does NOT support
# partition-based replica exchange (+replicas). The NAMD source notes.txt
# explicitly states: "NET, IBVERBS, AND MULTICORE BUILDS ARE NOT SUPPORTED"
# for multi-copy algorithms.
# FIX: Build with 'netlrts-linux-x86_64' which uses the LRTS machine layer
# required for +replicas. Uses charmrun ++local for single-node execution.
# =============================================================================
info "Step 3/5: Building Charm++ (netlrts-linux-x86_64)..."
cd "$NAMD_SRC"
tar xf charm-8.0.0.tar
cd charm-8.0.0
./build charm++ netlrts-linux-x86_64 --with-production -j"$NCORES" \
    > "$WORKDIR/charm_build.log" 2>&1 || {
    error "Charm++ build failed. Check $WORKDIR/charm_build.log"
}
CHARM_BUILD="$NAMD_SRC/charm-8.0.0/netlrts-linux-x86_64"
[[ -d "$CHARM_BUILD" ]] || error "Charm++ build directory not found: $CHARM_BUILD"
info "Charm++ built successfully: $CHARM_BUILD"

# =============================================================================
# STEP 4: Configure NAMD with netlrts backend and system libraries
# =============================================================================
info "Step 4/5: Configuring NAMD..."
cd "$NAMD_SRC"

# Create the netlrts arch file by copying the g++ arch and patching CHARMARCH
cp arch/Linux-x86_64-g++.arch arch/Linux-x86_64-g++-netlrts.arch
sed -i 's/^CHARMARCH.*/CHARMARCH = netlrts-linux-x86_64/' \
    arch/Linux-x86_64-g++-netlrts.arch

# =============================================================================
# ERROR FIXED: The default NAMD FFTW arch file uses -DNAMD_FFTW (FFTW2 API).
# The system libfftw3-dev provides the FFTW3 API, which requires -DNAMD_FFTW_3.
# FIX: Write a corrected FFTW3 arch file pointing to system headers/libs.
# =============================================================================
cat > arch/Linux-x86_64.fftw << 'ARCHEOF'
FFTDIR=/usr
FFTINCL=-I$(FFTDIR)/include
FFTLIB=-L$(FFTDIR)/lib/x86_64-linux-gnu -lfftw3f
FFTFLAGS=-DNAMD_FFTW_3
FFT=$(FFTINCL) $(FFTFLAGS)
ARCHEOF

# Write TCL arch file pointing to system tcl8.6
cat > arch/Linux-x86_64.tcl << 'ARCHEOF'
TCLDIR=/usr
TCLINCL=-I$(TCLDIR)/include/tcl8.6
TCLLIB=-L$(TCLDIR)/lib/x86_64-linux-gnu -ltcl8.6
TCL=$(TCLINCL) -DNAMD_TCL
ARCHEOF

# Run the NAMD config script
./config Linux-x86_64-g++-netlrts \
    --charm-arch netlrts-linux-x86_64 \
    --with-fftw3 \
    --with-tcl \
    > "$WORKDIR/namd_config.log" 2>&1 || {
    error "NAMD config failed. Check $WORKDIR/namd_config.log"
}

BUILD_DIR="$NAMD_SRC/Linux-x86_64-g++-netlrts"
[[ -d "$BUILD_DIR" ]] || error "NAMD build directory not created: $BUILD_DIR"

# =============================================================================
# ERROR FIXED: The auto-generated Make.config still references the UIUC
# pre-built library paths (which lack -fPIC). Override them to use system libs.
# =============================================================================
MAKE_CONFIG="$BUILD_DIR/Make.config"
# Patch TCL paths
sed -i "s|^TCLDIR.*|TCLDIR = /usr|"                                    "$MAKE_CONFIG"
sed -i "s|^TCLINCL.*|TCLINCL = -I/usr/include/tcl8.6|"                "$MAKE_CONFIG"
sed -i "s|^TCLLIB.*|TCLLIB = -L/usr/lib/x86_64-linux-gnu -ltcl8.6|"   "$MAKE_CONFIG"
# Patch FFTW paths
sed -i "s|^FFTDIR.*|FFTDIR = /usr|"                                    "$MAKE_CONFIG"
sed -i "s|^FFTINCL.*|FFTINCL = -I/usr/include|"                       "$MAKE_CONFIG"
sed -i "s|^FFTLIB.*|FFTLIB = -L/usr/lib/x86_64-linux-gnu -lfftw3f|"   "$MAKE_CONFIG"

info "NAMD configured. Build directory: $BUILD_DIR"

# =============================================================================
# STEP 5: Compile NAMD
# =============================================================================
info "Step 5/5: Compiling NAMD (this takes 15–25 minutes)..."
cd "$BUILD_DIR"
make -j"$NCORES" > "$WORKDIR/namd_make.log" 2>&1 || {
    error "NAMD compilation failed. Check $WORKDIR/namd_make.log"
}

NAMD_BIN="$BUILD_DIR/namd3"
[[ -x "$NAMD_BIN" ]] || error "namd3 binary not found after build: $NAMD_BIN"

# =============================================================================
# Done
# =============================================================================
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN} NAMD 3.0.2 compiled successfully!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "  Binary  : $NAMD_BIN"
echo "  charmrun: $NAMD_SRC/charm-8.0.0/netlrts-linux-x86_64/bin/charmrun"
echo ""
echo "Quick test:"
echo "  $NAMD_BIN +p1 2>&1 | head -5"
echo ""
echo "Add these to your environment (or set in run_abfe_remd.sh):"
echo "  export NAMD_BIN=$NAMD_BIN"
echo "  export CHARMRUN=$NAMD_SRC/charm-8.0.0/netlrts-linux-x86_64/bin/charmrun"
