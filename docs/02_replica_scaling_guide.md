# Scaling CHARMM-GUI ABFE Replicas for Limited CPU Resources

## Background

The CHARMM-GUI ABFE workflow generates scripts configured for **32 replicas** (lambda windows), which requires at least 32 CPUs to run efficiently. The NAMD `+replicas N` flag requires that the total number of Processing Elements (PEs, specified by `+pX`) is a **multiple of N**. Specifically:

- Each replica receives `X / N` PEs
- For 32 replicas with 1 PE each, you need `+p32` (32 CPUs minimum)
- For 32 replicas with 2 PEs each, you need `+p64` (64 CPUs)

On a workstation with 4–16 CPUs, running 32 replicas is either impossible or extremely slow. The solution is to **reduce the number of replicas** to match the available CPU count.

## Scientific Impact of Reducing Replicas

A common question is: **If I reduce the number of simultaneous replicas from 32 to 7 or 14, does it reduce the accuracy of the final free energy?**

The short answer is: **No, the theoretical accuracy remains exactly the same, but the *rate of convergence* decreases.**

### The Difference Between $\lambda$ Windows and Replicas
It is crucial to distinguish between the two:
- **$\lambda$ Windows:** The discrete states along the alchemical pathway (e.g., $\lambda = 0.00, 0.03, \dots, 1.00$). The CHARMM-GUI scripts define 32 fixed $\lambda$ windows. **This repository does not change the number of $\lambda$ windows.**
- **Replicas:** The number of independent MD simulations running simultaneously and exchanging states.

### How Fewer Replicas Affects the Simulation
When you run `+replicas 7` on a system with 32 $\lambda$ windows, NAMD uses a technique called **sparse replica exchange** or **window hopping**. Instead of having one replica sitting at every single $\lambda$ window simultaneously, you have 7 replicas moving up and down the 32-window ladder.

According to the literature on Hamiltonian Replica Exchange Molecular Dynamics (H-REMD) and FEP [1, 2]:
1. **Thermodynamic Accuracy:** The Bennett Acceptance Ratio (BAR) calculation relies on the phase space overlap between adjacent $\lambda$ windows. Because all 32 $\lambda$ windows are still sampled (just sequentially rather than simultaneously), the phase space overlap is preserved. The final $\Delta G$ will converge to the exact same value.
2. **Convergence Rate:** The primary benefit of having 32 replicas is that a conformation can "travel" from $\lambda=0$ to $\lambda=1$ very quickly via rapid exchanges, helping the system escape kinetic traps (e.g., a buried water molecule or a trapped sidechain rotamer) [1]. With fewer replicas, the "round-trip time" for a replica to traverse the entire $\lambda$ space increases.
3. **Sampling Efficiency:** To achieve the same level of statistical convergence (i.e., the same error bar in kcal/mol) with fewer replicas, you generally need to run the simulation for **more MD steps per replica**.

**Recommendation:** If you reduce the replica count significantly (e.g., from 32 to 4 or 7), you should compensate by increasing the simulation time. In the `FEP_remd_softcore.namd` script, increase `num_runs` or `steps_per_run` to ensure each replica spends enough time sampling the $\lambda$ space.

---

## References

[1] Jiang, W., & Roux, B. (2010). Free Energy Perturbation Hamiltonian Replica-Exchange Molecular Dynamics (FEP/H-REMD) for Absolute Ligand Binding Free Energy Calculations. *Journal of Chemical Theory and Computation*, 6(9), 2559–2565. https://doi.org/10.1021/ct1001768

[2] Jiang, W., Thirman, J., Jo, S., & Roux, B. (2018). Reduced Free Energy Perturbation/Hamiltonian Replica Exchange Molecular Dynamics Method with Unbiased Alchemical Thermodynamic Axis. *The Journal of Physical Chemistry B*, 122(41), 9435–9442. https://doi.org/10.1021/acs.jpcb.8b03277

## Complete List of Files to Modify

When changing from 32 replicas to `N` replicas, update the following files in **both** the `complex/` and `ligand/` directories:

### File 1: `fep_site.conf` / `fep_solv.conf`
This is the primary configuration file. Update the replica counts:

```tcl
# ORIGINAL (32 replicas)
set num_replicas 32
set num_replicasb 32

# MODIFIED (e.g., 4 replicas)
set num_replicas 4
set num_replicasb 4
```

> **Note:** `num_replicasa` and `num_replicasc` are for restraint-only replicas (not FEP). Leave these at 0 unless you are using a staged restraint protocol.

### File 2: `1_mkdir.pl`
This script creates the output directories. Update the loop upper bound:

```perl
# ORIGINAL
for ($j = 0; $j < 32; $j++) {
    system("mkdir output_site/$j");
}
for ($j = 0; $j < 32; $j++) {
    system("mkdir output_off/$j");
}

# MODIFIED (N=4)
for ($j = 0; $j < 4; $j++) {
    system("mkdir output_site/$j");
}
for ($j = 0; $j < 4; $j++) {
    system("mkdir output_off/$j");
}
```

Or simply create the directories manually:
```bash
mkdir -p output_site/{0,1,2,3} output_off/{0,1,2,3}
```

### File 3: `3_job_run.pbs` (or your HPC/local launch script)
Update the `+replicas` argument and the `+p` (PE count) argument:

```bash
# ORIGINAL
namd2 +replicas 32 fep_site.conf --source FEP_remd_softcore.namd +stdout output_site/%d/job0.%d.log

# MODIFIED (N=4, local run with charmrun)
charmrun ++local +p4 namd3 +replicas 4 fep_site.conf --source FEP_remd_softcore.namd +stdout output_site/%d/job0.%d.log
```

> **Key rule:** `+p` must be a multiple of `+replicas`. For 4 replicas on 4 CPUs, use `+p4 +replicas 4` (1 PE per replica). For 4 replicas on 8 CPUs, use `+p8 +replicas 4` (2 PEs per replica, which is faster).

### File 4: `sort.py`
This Python 2 script sorts replica trajectories by lambda index. Update the hardcoded replica count, and fix the Python 2 `print` statement for Python 3:

```python
# ORIGINAL
num_replica = 32
...
print time  # Python 2 syntax

# MODIFIED (N=4, Python 3 compatible)
num_replica = 4
...
print(time)  # Python 3 syntax
```

### File 5: `calc_fe.pl`
This Perl script calculates the BAR free energy. Update the FEP window number:

```perl
# ORIGINAL
$fep_win_num = 32;

# MODIFIED (N=4)
$fep_win_num = 4;
```

### File 6: `5_fe.pl`
This script loops over all job runs. If you also changed `num_runs` in the conf file, update the loop limit here:

```perl
# ORIGINAL (100 runs)
$num_runs = 100;

# MODIFIED (e.g., 2 runs for a test)
$num_runs = 2;
```

### File 7: `4_sort.pl`
This script loops over all job runs to call `sort.py`. Update the loop limit to match `num_runs`:

```perl
# ORIGINAL (100 runs)
for ($j = 0; $j < 100; $j++) {

# MODIFIED (e.g., 2 runs)
for ($j = 0; $j < 2; $j++) {
```

## `FEP_remd_softcore.namd` — No Changes Needed

The core NAMD TCL replica exchange script `FEP_remd_softcore.namd` does **not** hardcode the replica count. It reads `$num_replicas` from the conf file at runtime and dynamically assigns lambda values. No changes are needed to this file.

## Recommended Replica Counts by CPU Availability

| Available CPUs | Recommended Replicas | PEs per Replica | Notes |
| :---: | :---: | :---: | :--- |
| 4 | 4 | 1 | Minimal test; qualitative results only |
| 8 | 4 or 8 | 2 or 1 | Suitable for small ligands |
| 16 | 8 or 16 | 2 or 1 | Reasonable accuracy |
| 32 | 16 or 32 | 2 or 1 | Approaching production quality |
| 64+ | 32 | 2 | Full production run as designed |
