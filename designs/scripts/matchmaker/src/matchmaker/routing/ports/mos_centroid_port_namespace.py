from matchmaker.placement.core.tile_plan import PlacementPlan


def _get_component_references(component) -> list:
    """Handle the reference container names used across gdsfactory generations."""
    references = getattr(component, "references", None)
    if references is not None:
        return list(references)

    instances = getattr(component, "insts", None)
    if instances is not None:
        if hasattr(instances, "values"):
            return list(instances.values())
        return list(instances)

    raise TypeError("Component does not expose references or instances")


def expose_mos_centroid_tile_ports(
    component,
    plan: PlacementPlan,
    separator: str = "__",
):
    """
    Promote each placed MOS tile reference port into a stable top-level namespace.

    Example:
        A0 + gate_E -> A0__gate_E

    The current MOS placement builder adds exactly one top-level reference for each
    non-empty placement tile, in plan order. This adapter validates that invariant
    before promoting ports.
    """
    placeable_tiles = [tile for tile in plan.tiles if tile.role != "empty"]
    references = _get_component_references(component)

    if len(references) != len(placeable_tiles):
        raise ValueError(
            "MOS centroid component/reference count does not match the placement plan: "
            f"references={len(references)}, tiles={len(placeable_tiles)}"
        )

    for tile, reference in zip(placeable_tiles, references):
        prefix = f"{tile.name}{separator}"
        component.add_ports(reference.get_ports_list(), prefix=prefix)

    component.info["matchmaker_port_separator"] = separator
    component.info["matchmaker_routing_instances"] = tuple(
        tile.name for tile in placeable_tiles
    )
    return component
