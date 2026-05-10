# NAMD 3.0.2 ABFE Replica Exchange Guide

This repository provides a comprehensive guide for compiling NAMD 3.0.2 from source to support Replica Exchange Molecular Dynamics (REMD) and adapting CHARMM-GUI Absolute Binding Free Energy (ABFE) scripts to run on systems with limited CPU resources.

## Table of Contents
1. [Compiling NAMD 3.0.2 for Replica Exchange](#1-compiling-namd-302-for-replica-exchange)
2. [Adapting CHARMM-GUI ABFE Scripts for Fewer CPUs](#2-adapting-charmm-gui-abfe-scripts-for-fewer-cpus)
3. [Running the ABFE Workflow](#3-running-the-abfe-workflow)
4. [Analysis and Free Energy Calculation](#4-analysis-and-free-energy-calculation)

---

## 1. Compiling NAMD 3.0.2 for Replica Exchange

The standard `multicore` build of NAMD **does not support** partition-based replica exchange (`+replicas`). To run the CHARMM-GUI ABFE scripts, you must compile NAMD with a network-based Charm++ backend, such as `netlrts-linux-x86_64`.

### Prerequisites (Ubuntu 22.04)
Install the required build dependencies:
```bash
sudo apt-get update
sudo apt-get install -y build-essential csh tcl-dev tcl8.6-dev libfftw3-dev wget tar
```

### Step 1: Build Charm++ (netlrts backend)
Download the NAMD 3.0.2 source tarball and extract it. Then build the Charm++ backend:
```bash
cd NAMD_3.0.2_Source
tar xf charm-8.0.0.tar
cd charm-8.0.0
./build charm++ netlrts-linux-x86_64 --with-production -j4
```

### Step 2: Configure NAMD
Create an architecture file for the `netlrts` build by copying the standard `g++` file:
```bash
cd ../
cp arch/Linux-x86_64-g++.arch arch/Linux-x86_64-g++-netlrts.arch
```
Edit `arch/Linux-x86_64-g++-netlrts.arch` and update the `CHARMARCH` line:
```text
CHARMARCH = netlrts-linux-x86_64
```

Configure NAMD to use the system's FFTW3 and TCL libraries (the pre-built UIUC libraries often fail to link on modern Ubuntu due to missing `-fPIC` flags):
```bash
./config Linux-x86_64-g++-netlrts --with-fftw3 --with-tcl
```

### Step 3: Fix Make.config and Compile
Edit the generated `Linux-x86_64-g++-netlrts/Make.config` to point to the system libraries:
```text
TCLDIR = /usr
TCLINCL = -I/usr/include/tcl8.6
TCLLIB = -L/usr/lib/x86_64-linux-gnu -ltcl8.6

FFTDIR = /usr
FFTINCL = -I/usr/include
FFTLIB = -L/usr/lib/x86_64-linux-gnu -lfftw3f
```
*(Note: NAMD requires the single-precision FFTW3 library, `libfftw3f`)*

Compile NAMD:
```bash
cd Linux-x86_64-g++-netlrts
make -j4
```
The resulting binary `namd3` and the Charm++ launcher `charmrun` (located in `charm-8.0.0/netlrts-linux-x86_64/bin/charmrun`) will be used to run the REMD simulations.

---

## 2. Adapting CHARMM-GUI ABFE Scripts for Fewer CPUs

The default CHARMM-GUI ABFE workflow uses **32 replicas** (lambda windows). NAMD's `+replicas N` flag requires that the total number of Processing Elements (PEs) is a multiple of N. If you have fewer than 32 CPUs (e.g., a 4-core or 8-core workstation), you cannot run 32 replicas efficiently.

You can downgrade the number of replicas (e.g., to 4, 8, or 16) to match your CPU count. This sacrifices some accuracy and phase-space overlap but allows the simulation to run.

### Required Script Modifications

If you reduce the number of replicas from 32 to `N` (e.g., `N=4`), you must update the following files in both the `complex/` and `ligand/` directories:

#### 1. `fep_site.conf` / `fep_solv.conf`
Update the replica counts:
```tcl
set num_replicas 4      # Change from 32
set num_replicasb 4     # Change from 32
```

#### 2. `1_mkdir.pl`
Update the loop limits for directory creation:
```perl
for ($j = 0; $j < 4; $j++) {  # Change from 32
    system("mkdir output_site/$j");
}
for ($j = 0; $j < 4; $j++) {  # Change from 32
    system("mkdir output_off/$j");
}
```

#### 3. `3_job_run.pbs` (or your launch script)
Update the `+replicas` flag in the NAMD launch commands:
```bash
namd2 +replicas 4 fep_${system}.conf ...      # Change from 32
namd2 +replicas 4 restart_${cnt}.conf ...     # Change from 32
```

#### 4. `sort.py`
Update the hardcoded replica count:
```python
num_replica = 4  # Change from 32
```
*(Note: The default `sort.py` uses Python 2 syntax `print time`. If using Python 3, update it to `print(time)`).*

#### 5. `calc_fe.pl`
Update the FEP window number:
```perl
$fep_win_num = 4;  # Change from 32
```

---

## 3. Running the ABFE Workflow

With the scripts adapted, run the workflow using the `netlrts` NAMD build.

### Equilibration
Run the standard equilibration first (does not require `charmrun`):
```bash
/path/to/namd3 +p4 equ_site.namd > equ_site.log
```

### Replica Exchange (REMD)
Launch the REMD simulation using `charmrun ++local` (which runs the network backend locally without SSH):
```bash
/path/to/charmrun ++local +p4 /path/to/namd3 +replicas 4 fep_site.conf \
  --source FEP_remd_softcore.namd \
  +stdout output_site/%d/job0.%d.log > remd_site.log 2>&1
```
*(Replace `+p4` with your actual CPU count. Ensure `+p` is a multiple of `+replicas`).*

---

## 4. Analysis and Free Energy Calculation

After the REMD simulation completes, run the analysis scripts to calculate the Bennett Acceptance Ratio (BAR) free energy.

1. **Sort the trajectories by lambda window:**
   ```bash
   perl 4_sort.pl
   ```
   This runs `sort.py` to unshuffle the replica histories into the `output_off/` directories.

2. **Calculate Free Energy:**
   ```bash
   perl 5_fe.pl
   ```
   This runs `calc_fe.pl` across all runs and averages the ΔG values.

Repeat the entire process for both the `complex` (site) and `ligand` (solvation) legs. The Absolute Binding Free Energy is:
**ΔG_bind = ΔG_site - ΔG_solv**
