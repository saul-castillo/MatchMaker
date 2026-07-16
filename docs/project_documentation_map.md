# Project documentation map

MatchMaker keeps documentation beside the part of the repository that it governs. The multiple `docs/` directories are intentional and have different scopes.

| Location | Scope |
| --- | --- |
| `docs/` | Chipathon container, team, schematic, layout, and repository workflow documentation inherited from the project template |
| `designs/libs/core_matchmaker/` | Hand-authored reference-circuit documentation and reusable Xschem cells |
| `designs/libs/tb_matchmaker/` | Xschem/ngspice testbenches for the reference circuits |
| `designs/scripts/matchmaker/docs/` | MatchMaker layout-engine architecture, ADRs, and physical-validation evidence |

Reference-circuit simulation results are not physical-layout signoff. DRC, extraction, connectivity, and LVS evidence for generated layouts belongs in `designs/scripts/matchmaker/docs/VALIDATION_STATUS.md` only after it has been demonstrated in the Chipathon `/foss` environment.

## Design-library convention

The repository follows the Chipathon project-template convention:

```text
designs/libs/
  core_matchmaker/
    <cell_name>/
      <cell_name>.sch
      <cell_name>.sym
      <cell_name>_README.md  # optional cell-specific documentation

  tb_matchmaker/
    <testbench_name>/
      <testbench_name>.sch
```

Each reusable circuit cell has its own directory. Core-cell filenames match the directory name. MatchMaker cell names use the team prefix `7D_`; testbench names place the identifier after the testbench prefix as `tb_7D_`. Testbench files remain in the `tb_matchmaker` library.

See [the core reference-library index](../designs/libs/core_matchmaker/README.md) for available cells.
