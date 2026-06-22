def abba_pattern(rows: int, cols: int) -> list[list[str]]:
    """
    Generate an AB/BA common-centroid pattern.

    Example for 2x4:
        A B B A
        B A A B
    """
    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive")

    if cols % 2 != 0:
        raise ValueError("ABBA pattern currently expects an even number of columns")

    base = ["A", "B", "B", "A"]

    pattern = []
    for r in range(rows):
        row = []
        while len(row) < cols:
            row.extend(base)

        row = row[:cols]

        if r % 2 == 1:
            row = ["B" if x == "A" else "A" for x in row]

        pattern.append(row)

    return pattern


def print_pattern(pattern: list[list[str]]) -> None:
    for row in pattern:
        print(" ".join(row))