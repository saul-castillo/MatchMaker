import unittest

from matchmaker.placement.core.reference_orientation import orient_reference


class _FakeReference:
    def __init__(self):
        self.operations = []

    def mirror_y(self):
        self.operations.append(("mirror_y", None))

    def mirror_x(self):
        self.operations.append(("mirror_x", None))

    def rotate(self, degrees):
        self.operations.append(("rotate", degrees))


class ReferenceOrientationTests(unittest.TestCase):
    def test_supported_orientations_apply_one_transform(self):
        expectations = {
            "R0": [],
            "MY": [("mirror_y", None)],
            "MX": [("mirror_x", None)],
            "R180": [("rotate", 180)],
        }
        for orientation, expected in expectations.items():
            with self.subTest(orientation=orientation):
                reference = _FakeReference()
                returned = orient_reference(reference, orientation)
                self.assertIs(returned, reference)
                self.assertEqual(reference.operations, expected)

    def test_unknown_orientation_fails_explicitly(self):
        with self.assertRaises(NotImplementedError):
            orient_reference(_FakeReference(), "R90")


if __name__ == "__main__":
    unittest.main()
