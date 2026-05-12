#!/usr/bin/env bash
# =============================================================================
# compile_namd.sh — Compile NAMD 3.0.2 from source (CPU, single-node REMD)
#
# PREREQUISITES:
#   1. Extract the NAMD source tarball first:
#        tar xf NAMD_3.0.2_Source.tar
#   2. cd into the extracted directory:
#        cd NAMD_3.0.2_Source
#   3. Run this script:
#        bash /path/to/compile_namd.sh
#
# Tested on: Ubuntu 20.04 / 22.04 LTS (x86_64)
# Output:    ./Linux-x86_64-g++-netlrts/namd3
# =============================================================================

set -e
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Sanity check: must be run from inside the NAMD source directory ──────────
[[ -f "config" && -d "src" && -d "arch" ]] || \
    error "Run this script from inside the NAMD source directory.
  Example:  cd NAMD_3.0.2_Source && bash /path/to/compile_namd.sh"

NAMD_SRC=$(pwd)
NCORES=$(nproc)
info "NAMD source : $NAMD_SRC"
info "Build cores : $NCORES"

# ── Step 1: Install system dependencies ─────────────────────────────────────
# The UIUC-bundled FFTW2 and TCL8.5 libraries were compiled without -fPIC
# and fail to link on modern Ubuntu with a relocation error.
# We use system libfftw3-dev and tcl8.6-dev instead.
info "Step 1/4: Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y g++ make libfftw3-dev tcl8.6-dev
info "Dependencies ready."

# ── Step 2: Build Charm++ with netlrts backend ───────────────────────────────
# The 'multicore' Charm++ build does NOT support +replicas (replica exchange).
# 'netlrts-linux-x86_64' is required for multi-copy / REMD simulations.
CHARM_TAR=$(ls charm-*.tar 2>/dev/null | head -n 1)
[[ -n "$CHARM_TAR" ]] || error "Charm++ tarball (charm-*.tar) not found in $NAMD_SRC"
CHARM_DIR="${CHARM_TAR%.tar}"

if [[ -x "$CHARM_DIR/netlrts-linux-x86_64/bin/charmrun" ]]; then
    info "Step 2/4: Charm++ netlrts already built — skipping."
else
    info "Step 2/4: Extracting and building Charm++ ($CHARM_TAR) — ~5 minutes..."
    [[ -d "$CHARM_DIR" ]] || tar xf "$CHARM_TAR"
    cd "$CHARM_DIR"
    ./build charm++ netlrts-linux-x86_64 --with-production -j"$NCORES"
    cd "$NAMD_SRC"
    info "Charm++ built: $CHARM_DIR/netlrts-linux-x86_64"
fi

# ── Step 3: Patch arch files and configure NAMD ──────────────────────────────
info "Step 3/4: Configuring NAMD..."

# Write TCL arch file pointing to system tcl8.6
cat > arch/Linux-x86_64.tcl << 'EOF'
TCLDIR=/usr
TCLINCL=-I$(TCLDIR)/include/tcl8.6
TCLLIB=-L$(TCLDIR)/lib/x86_64-linux-gnu -ltcl8.6 -ldl -lpthread
TCLFLAGS=-DNAMD_TCL
TCL=$(TCLINCL) $(TCLFLAGS)
EOF

# Write FFTW3 arch file pointing to system fftw3
# The default arch uses FFTW2 API (-DNAMD_FFTW); FFTW3 needs -DNAMD_FFTW_3
cat > arch/Linux-x86_64.fftw3 << 'EOF'
FFTDIR=/usr
FFTINCL=-I$(FFTDIR)/include
FFTLIB=-L$(FFTDIR)/lib/x86_64-linux-gnu -lfftw3f
FFTFLAGS=-DNAMD_FFTW -DNAMD_FFTW_3
FFT=$(FFTINCL) $(FFTFLAGS)
EOF

# Write the netlrts arch file
cat > arch/Linux-x86_64-g++-netlrts.arch << EOF
NAMD_ARCH = Linux-x86_64
CHARMARCH = netlrts-linux-x86_64
CXX = g++ -m64 -std=c++11
CXXOPTS = -O3 -fexpensive-optimizations -ffast-math
CC = gcc -m64
COPTS = -O3 -fexpensive-optimizations -ffast-math
EOF

# Run the NAMD config script
./config Linux-x86_64-g++-netlrts --charm-arch netlrts-linux-x86_64 --with-fftw3

# Patch Make.config to override any remaining references to the UIUC bundle paths
MAKE_CONFIG="Linux-x86_64-g++-netlrts/Make.config"
sed -i "s|^TCLDIR.*|TCLDIR = /usr|"                                    "$MAKE_CONFIG"
sed -i "s|^TCLINCL.*|TCLINCL = -I/usr/include/tcl8.6|"                "$MAKE_CONFIG"
sed -i "s|^TCLLIB.*|TCLLIB = -L/usr/lib/x86_64-linux-gnu -ltcl8.6|"   "$MAKE_CONFIG"
sed -i "s|^FFTDIR.*|FFTDIR = /usr|"                                    "$MAKE_CONFIG"
sed -i "s|^FFTINCL.*|FFTINCL = -I/usr/include|"                       "$MAKE_CONFIG"
sed -i "s|^FFTLIB.*|FFTLIB = -L/usr/lib/x86_64-linux-gnu -lfftw3f|"   "$MAKE_CONFIG"
info "NAMD configured."

# ── Step 4: Compile NAMD ─────────────────────────────────────────────────────
info "Step 4/4: Compiling NAMD — ~15 minutes..."
cd Linux-x86_64-g++-netlrts
make -j"$NCORES"
cd "$NAMD_SRC"

# ── Verify ───────────────────────────────────────────────────────────────────
NAMD_BIN="$NAMD_SRC/Linux-x86_64-g++-netlrts/namd3"
CHARMRUN="$NAMD_SRC/$CHARM_DIR/netlrts-linux-x86_64/bin/charmrun"
[[ -x "$NAMD_BIN" ]] || error "namd3 binary not found after build."

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN} NAMD 3.0.2 compiled successfully!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "  namd3    : $NAMD_BIN"
echo "  charmrun : $CHARMRUN"
echo ""
echo "Quick test:"
echo "  $NAMD_BIN +p1 2>&1 | head -3"
echo ""
echo "For replica exchange, launch with charmrun:"
echo "  $CHARMRUN ++local +p<N> $NAMD_BIN +replicas <N> fep_site.conf \\"
echo "    --source FEP_remd_softcore.namd +stdout output_site/%d/job0.%d.log"
