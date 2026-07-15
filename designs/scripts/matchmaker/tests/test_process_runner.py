import sys
import unittest

from matchmaker.verification.process_runner import run_process


class ProcessRunnerTests(unittest.TestCase):
    def test_missing_executable_returns_structured_failure(self):
        result = run_process(["matchmaker-command-that-does-not-exist"])
        self.assertEqual(result.returncode, 127)
        self.assertIn("Executable not found", result.stderr)

    def test_timeout_returns_structured_failure(self):
        result = run_process(
            [sys.executable, "-c", "import time; time.sleep(1)"],
            timeout_s=0.01,
        )
        self.assertEqual(result.returncode, 124)
        self.assertIn("timed out", result.stderr)


if __name__ == "__main__":
    unittest.main()
