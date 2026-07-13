from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from matchmaker.outputs.core_analog_cell_paths import create_core_analog_cell_paths


class GeneratedCellPathsTests(unittest.TestCase):
    def test_standard_artifact_directories_are_created(self):
        with TemporaryDirectory() as directory:
            paths = create_core_analog_cell_paths(Path(directory), "demo")

            self.assertTrue(paths.gds_dir.is_dir())
            self.assertTrue(paths.netlist_dir.is_dir())
            self.assertTrue(paths.drc_report_dir.is_dir())
            self.assertTrue(paths.extraction_report_dir.is_dir())
            self.assertTrue(paths.lvs_report_dir.is_dir())
            self.assertEqual(paths.final_gds.name, "demo.gds")
            self.assertEqual(paths.extracted_netlist.name, "demo.spice")
            self.assertEqual(paths.extraction_report.name, "demo_extraction.rpt")


if __name__ == "__main__":
    unittest.main()
