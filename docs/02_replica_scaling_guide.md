# Scaling CHARMM-GUI ABFE Replicas for Limited CPU Resources

## Background

The CHARMM-GUI ABFE workflow generates scripts configured for **32 replicas** (lambda windows), which requires at least 32 CPUs to run efficiently. The NAMD `+replicas N` flag requires that the total number of Processing Elements (PEs, specified by `+pX`) is a **multiple of N**. Specifically:

- Each replica receives `X / N` PEs
- For 32 replicas with 1 PE each, you need `+p32` (32 CPUs minimum)
- For 32 replicas with 2 PEs each, you need `+p64` (64 CPUs)

On a workstation with 4–16 CPUs, running 32 replicas is either impossible or extremely slow. The solution is to **reduce the number of replicas** to match the available CPU count.

## Scientific Impact of Reducing Replicas

Reducing the number of replicas (lambda windows) has the following effects:

| Aspect | Impact |
| :--- | :--- |
| **Phase-space overlap** | Fewer windows means larger gaps between adjacent lambda values, potentially reducing overlap and increasing statistical error |
| **Exchange acceptance ratio** | Wider lambda spacing typically lowers the probability of successful replica exchanges |
| **Convergence** | Fewer windows may require longer simulation time per window to achieve the same level of convergence |
| **Accuracy** | The free energy estimate may be less accurate, but the simulation remains physically valid |

For a quick test or a system with a small ligand (few rotatable bonds, low charge), 4–8 replicas can still produce qualitatively meaningful results. For production calculations, 16–32 replicas are recommended.

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
