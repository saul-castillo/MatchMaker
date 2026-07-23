from matchmaker.placement.core.tile_plan import Orientation


def orient_reference(reference, orientation: Orientation):
    """Apply one supported geometric orientation to a placed reference."""

    if orientation == "R0":
        return reference
    if orientation == "MY":
        reference.mirror_y()
        return reference
    if orientation == "MX":
        reference.mirror_x()
        return reference
    if orientation == "R180":
        reference.rotate(180)
        return reference
    raise NotImplementedError(f"Unsupported reference orientation: {orientation!r}")
