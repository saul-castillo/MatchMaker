import unittest

from matchmaker.verification.drc.magic_drc import _parse_drc_count
from matchmaker.verification.lvs.magic_netgen_lvs import _netgen_output_passed


class VerificationParserTests(unittest.TestCase):
    def test_drc_count_uses_last_marker(self):
        output = "MATCHMAKER_DRC_COUNT=3\nMATCHMAKER_DRC_COUNT=0\n"
        self.assertEqual(_parse_drc_count(output), 0)

    def test_drc_count_returns_none_without_marker(self):
        self.assertIsNone(_parse_drc_count("magic completed without count marker"))

    def test_netgen_unique_match_passes(self):
        self.assertTrue(_netgen_output_passed("Circuits match uniquely.\n.\n"))

    def test_netgen_mismatch_fails(self):
        self.assertFalse(_netgen_output_passed("Netlists do not match.\n"))

    def test_netgen_property_error_fails(self):
        output = "Circuits match uniquely.\nProperty errors were found.\n"
        self.assertFalse(_netgen_output_passed(output))

    def test_netgen_port_error_fails(self):
        output = "Circuits match uniquely with port errors.\n"
        self.assertFalse(_netgen_output_passed(output))


if __name__ == "__main__":
    unittest.main()
