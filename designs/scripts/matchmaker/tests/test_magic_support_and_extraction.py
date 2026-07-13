from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from matchmaker.verification.extraction.magic_extraction import (
    _extraction_failure_reason,
)
from matchmaker.verification.magic_support import (
    build_magic_environment,
    resolve_netgen_setup_file,
)
from matchmaker.verification.process_runner import ProcessResult


class MagicSupportTests(unittest.TestCase):
    def test_magic_environment_sets_gf180_defaults(self):
        environment = build_magic_environment()
        self.assertEqual(environment["PDK"], "gf180mcuD")
        self.assertEqual(environment["PDK_ROOT"], "/foss/pdks")

    def test_magic_environment_allows_explicit_overrides(self):
        environment = build_magic_environment(
            extra_env={"PDK": "custom", "EXTRA": "1"}
        )
        self.assertEqual(environment["PDK"], "custom")
        self.assertEqual(environment["EXTRA"], "1")

    def test_netgen_setup_resolves_direct_pdk_layout(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            setup = (
                root
                / "gf180mcuD"
                / "libs.tech"
                / "netgen"
                / "gf180mcuD_setup.tcl"
            )
            setup.parent.mkdir(parents=True)
            setup.write_text("# test setup\n")

            resolved = resolve_netgen_setup_file(pdk_root=root)
            self.assertEqual(resolved, setup.resolve())

    def test_extraction_requires_nonempty_netlist_and_completion_marker(self):
        with TemporaryDirectory() as directory:
            netlist = Path(directory) / "demo.spice"
            netlist.write_text(".subckt demo\n.ends demo\n")
            process = ProcessResult(
                argv=("magic",),
                returncode=0,
                stdout=(
                    'Reading "demo".\n'
                    "MATCHMAKER_EXTRACTION_COMPLETED=1\n"
                ),
                stderr="",
            )

            reason = _extraction_failure_reason(
                process=process,
                output_netlist_path=netlist,
                cell_name="demo",
            )
            self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
