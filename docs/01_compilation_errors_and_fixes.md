# NAMD 3.0.2 Compilation: Errors Encountered and Fixes

This document records the exact compilation errors encountered when building NAMD 3.0.2 from source on **Ubuntu 22.04 (x86_64)** and the steps taken to resolve each one.

---

## Error 1: Pre-built FFTW Library Not Position-Independent

### Symptom
When using the UIUC-provided pre-built FFTW library (`FFTW_NAMD_3.0.2_Linux-x86_64-multicore_FFTW3.tar.gz`), the linker fails with:

```
/usr/bin/ld: /path/to/fftw3/lib/libfftw3f.a(fftw3f.o): relocation R_X86_64_32
against `.rodata' can not be used when making a PIE object; recompile with -fPIC
/usr/bin/ld: cannot find : No such file or directory
collect2: error: ld returned 1 exit status
```

### Root Cause
The UIUC-provided FFTW3 library was compiled circa 2009 without the `-fPIC` (Position-Independent Code) flag. Modern Ubuntu 22.04 compiles all executables as Position-Independent Executables (PIE) by default, which requires all linked static libraries to also be compiled with `-fPIC`.

### Fix
Replace the pre-built UIUC FFTW library with the system's `libfftw3-dev` package, which is compiled correctly for modern systems:

```bash
sudo apt-get install -y libfftw3-dev
```

Then update the NAMD arch file (`arch/Linux-x86_64.fftw`) to use the system library:
```text
FFTDIR=/usr
FFTINCL=-I/usr/include
FFTLIB=-L/usr/lib/x86_64-linux-gnu -lfftw3f
```

---

## Error 2: Wrong FFTW3 Preprocessor Flag

### Symptom
After switching to the system FFTW3 library, the build fails with a compilation error in `ComputePme.C`:

```
ComputePme.C:XX:YY: error: 'fftwf_plan_dft_r2c_3d' was not declared in this scope
```

### Root Cause
The NAMD source uses the preprocessor flag `NAMD_FFTW_3` (with an underscore before the `3`) to enable FFTW3 API calls. The arch file was incorrectly set to `NAMD_FFTW3` (without the underscore), so the FFTW3 code path was never compiled.

### Fix
Edit `arch/Linux-x86_64.fftw` and ensure the flag is spelled correctly:
```text
# WRONG:
FFTFLAGS=-DNAMD_FFTW3

# CORRECT:
FFTFLAGS=-DNAMD_FFTW_3
```

---

## Error 3: Multicore Build Does Not Support Replica Exchange

### Symptom
Running the CHARMM-GUI ABFE scripts with the `multicore` NAMD binary:

```bash
namd3 +replicas 32 fep_site.conf --source FEP_remd_softcore.namd ...
```

Produces an immediate abort:

```
FATAL ERROR: Replicas not supported in this build.
```

### Root Cause
The NAMD `multicore` build uses a simplified Charm++ backend that does not support the partition-based multi-copy framework required by `+replicas`. The NAMD documentation explicitly states:

> "NET, IBVERBS, AND MULTICORE BUILDS ARE NOT SUPPORTED" for replica exchange.

### Fix
Recompile NAMD using the `netlrts-linux-x86_64` Charm++ backend, which supports the full multi-partition framework:

```bash
cd charm-8.0.0
./build charm++ netlrts-linux-x86_64 --with-production -j4
```

Then configure NAMD with the new backend:
```bash
# Create a new arch file for netlrts
cp arch/Linux-x86_64-g++.arch arch/Linux-x86_64-g++-netlrts.arch
# Edit the CHARMARCH line:
# CHARMARCH = netlrts-linux-x86_64

./config Linux-x86_64-g++-netlrts --with-fftw3 --with-tcl
cd Linux-x86_64-g++-netlrts
make -j4
```

Launch the simulation using `charmrun ++local` to run the network backend locally without requiring SSH or an MPI cluster:
```bash
/path/to/charmrun ++local +p4 /path/to/namd3 +replicas 4 fep_site.conf ...
```

---

## Summary of Build Configuration

The final working build configuration for Ubuntu 22.04 is:

| Component | Value |
| :--- | :--- |
| **OS** | Ubuntu 22.04 LTS (x86_64) |
| **Charm++ version** | 8.0.0 |
| **Charm++ backend** | `netlrts-linux-x86_64` |
| **TCL** | System `tcl8.6-dev` (`/usr/include/tcl8.6`) |
| **FFTW** | System `libfftw3-dev` (single-precision: `-lfftw3f`) |
| **NAMD FFTW flag** | `-DNAMD_FFTW_3` |
| **Launch method** | `charmrun ++local +pN namd3 +replicas N ...` |
