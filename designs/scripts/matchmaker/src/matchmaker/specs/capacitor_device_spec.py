from dataclasses import dataclass


@dataclass(frozen=True)
class MimCapacitorSpec:
    """Technology-facing MIM capacitor description used by MatchMaker.

    Concrete model and geometry values belong in a named preset or caller-owned
    configuration. Placement and routing algorithms must consume this object and
    must not contain hidden capacitor dimensions or model names.
    """

    name: str
    width: float
    length: float
    model: str | None = None
    multipliers: int = 1

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("MIM capacitor name must be non-empty")
        if self.width <= 0:
            raise ValueError("MIM capacitor width must be positive")
        if self.length <= 0:
            raise ValueError("MIM capacitor length must be positive")
        if self.model is not None and not self.model:
            raise ValueError("MIM capacitor model must be non-empty when provided")
        if self.multipliers <= 0:
            raise ValueError("MIM capacitor multipliers must be positive")

    @property
    def area(self) -> float:
        return float(self.width) * float(self.length) * self.multipliers

    @property
    def compatibility_key(self) -> tuple[str | None, float, float]:
        """Physical matching key for unit-array symmetry decisions."""
        return (self.model, float(self.width), float(self.length))
