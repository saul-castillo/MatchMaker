from pathlib import Path
from typing import Mapping


def build_magic_environment(
    pdk_name: str | None = "gf180mcuD",
    pdk_root: Path | None = Path("/foss/pdks"),
    extra_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return explicit environment overrides for headless Magic/Netgen runs."""
    environment: dict[str, str] = {}

    if pdk_name is not None:
        environment["PDK"] = pdk_name
    if pdk_root is not None:
        environment["PDK_ROOT"] = str(Path(pdk_root))
    if extra_env is not None:
        environment.update({str(key): str(value) for key, value in extra_env.items()})

    return environment


def build_magic_argv(
    magic_bin: str,
    startup_file: Path | None = None,
) -> list[str]:
    argv = [magic_bin, "-dnull", "-noconsole"]
    if startup_file is not None:
        argv.extend(["-r", str(Path(startup_file).resolve())])
    return argv


def magic_loaded_target_cell(output: str, cell_name: str) -> bool:
    """Conservatively confirm that Magic read the requested GDS top cell."""
    if f'Reading "{cell_name}".' not in output:
        return False

    fatal_fragments = (
        "Don't know how to read GDS-II",
        f"Cell {cell_name} couldn't be read",
        'Using technology "minimum"',
    )
    return not any(fragment in output for fragment in fatal_fragments)


def resolve_netgen_setup_file(
    explicit_path: Path | None = None,
    pdk_name: str = "gf180mcuD",
    pdk_root: Path = Path("/foss/pdks"),
) -> Path:
    """Resolve the GF180 Netgen setup file across direct and CIEL PDK layouts."""
    if explicit_path is not None:
        resolved = Path(explicit_path).resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Netgen setup file not found: {resolved}")
        return resolved

    pdk_root = Path(pdk_root)
    filename = f"{pdk_name}_setup.tcl"
    direct = pdk_root / pdk_name / "libs.tech" / "netgen" / filename
    if direct.is_file():
        return direct.resolve()

    ciel_candidates = sorted(
        pdk_root.glob(
            f"ciel/gf180mcu/versions/*/{pdk_name}/libs.tech/netgen/{filename}"
        )
    )
    for candidate in reversed(ciel_candidates):
        if candidate.is_file():
            return candidate.resolve()

    searched = [str(direct), *(str(path) for path in ciel_candidates)]
    raise FileNotFoundError(
        "Could not resolve the Netgen setup file. Searched: " + ", ".join(searched)
    )
