# NAMD ABFE Replica Exchange Guide

This repository provides automated tools to run CHARMM-GUI Absolute Binding Free Energy (ABFE) calculations using NAMD on hardware with limited CPU cores.

**Motivation:** The default CHARMM-GUI ABFE protocol requires 32 simultaneous replicas (meaning at least 32 physical CPU cores). If you have fewer cores, NAMD will fail to run. Additionally, compiling NAMD from source with the correct replica-exchange backend (`netlrts`) is complex and prone to errors on modern Linux systems. This repository solves both problems automatically.

---

## The 4-Step Workflow

### Step 1: Compile NAMD
NAMD must be compiled from source with the `netlrts` Charm++ backend to support replica exchange on a single node. We provide a fully automated script that handles all dependencies and known compilation errors.

```bash
# Download the NAMD 3.0.2 source tarball from UIUC (registration required)
bash scripts/compile_namd.sh /path/to/NAMD_3.0.2_Source.tar.gz
```
*The script will output the exact paths to your compiled `namd3` and `charmrun` binaries.*

### Step 2: Scale Replicas to Your Hardware
You must reduce the number of replicas to match your physical CPU cores. The number of replicas **must divide your physical CPU count evenly**. 

First, find the optimal replica count for your machine:
```bash
python3 scripts/namd_cpu_advisor.py
```

Then, run the scaling script from inside your CHARMM-GUI `namd/` directory (the folder containing `1/`, `2/`, etc.). It will automatically patch all configuration files across all jobs:
```bash
cd charmm-gui-XXXXXX/namd/
bash /path/to/scripts/scale_replicas.sh <nreplicas>
```
*Note: This script only changes the replica count. All other simulation parameters (steps, lambda windows, force fields) remain exactly as CHARMM-GUI generated them.*

### Step 3: Run the Simulation
Use the default CHARMM-GUI scripts to run the equilibration and replica exchange (REMD) simulations. You must do this for both the `complex` and `ligand` legs of each job.

```bash
# Example for Job 1 - Complex leg
cd 1/complex/
perl 1_mkdir.pl
/path/to/namd3 equ_site.namd > equ_site.log
/path/to/charmrun ++local +p<ncpus> /path/to/namd3 +replicas <nreplicas> fep_site.conf --source FEP_remd_softcore.namd +stdout output_site/%d/job0.%d.log
```
*(Repeat for `1/ligand/`, `2/complex/`, `2/ligand/`, etc.)*

### Step 4: Analyze the Results
Once the simulations finish, use the default CHARMM-GUI analysis scripts to calculate the free energies.

```bash
# Example for Job 1 - Complex leg
cd 1/complex/
python3 sort.py 0
perl calc_fe.pl > fe_site.txt
```
*(Repeat for all other legs and jobs)*

---

## Background: What is ABFE?

Absolute Binding Free Energy (ABFE) calculations compute the binding affinity ($\Delta G_{bind}$) of a ligand to a protein using a thermodynamic cycle. The ligand is alchemically decoupled (turned into a "ghost" molecule) in two environments: bound to the protein (complex/site) and free in water (solvation/ligand).

![ABFE Thermodynamic Cycle](docs/abfe_thermodynamic_cycle.png)
*Figure 1: The ABFE thermodynamic cycle and the corresponding NAMD workflow steps.*

To prevent the ligand from drifting away when it is decoupled in the binding site, distance-based restraints are applied. The free energy cost of these restraints must be corrected for:

![ABFE Restraint Correction](docs/abfe_restraint_correction.png)
*Figure 2: The restraint correction terms required for accurate ABFE calculation.*

**Accuracy Note:** Reducing the number of simultaneous replicas does not change the $\lambda$ window values themselves — all 32 $\lambda$ states are still sampled. However, fewer replicas means longer round-trip times across $\lambda$ space, which can slow statistical convergence. The default CHARMM-GUI step counts are generally sufficient, but you may observe slightly higher statistical error bars compared to a full 32-replica run [1] [2].

---

## References

[1] Kim, S., Oshima, H., Zhang, H., Kern, N. R., Re, S., Lee, J., ... & Im, W. (2020). CHARMM-GUI Free Energy Calculator for absolute and relative ligand binding free energy simulations. *Journal of Chemical Theory and Computation*, 16(12), 7207-7218. https://doi.org/10.1021/acs.jctc.0c00884

[2] Jiang, W., & Roux, B. (2010). Free energy perturbation Hamiltonian replica-exchange molecular dynamics (FEP/H-REMD) for absolute ligand binding free energy calculations. *Journal of Chemical Theory and Computation*, 6(9), 2559-2565. https://doi.org/10.1021/ct100177g

[3] Boresch, S., Tettinger, F., Leitgeb, M., & Karplus, M. (2003). Absolute binding free energies: a quantitative approach for their calculation. *The Journal of Physical Chemistry B*, 107(35), 9535-9551. https://doi.org/10.1021/jp0217839

[4] Boresch, S. (2024). Analytical corrections for the use of restraints in absolute binding free energy calculations. *Journal of Computer-Aided Molecular Design*, 38(1), 1-15. https://doi.org/10.1007/s10822-023-00545-x
