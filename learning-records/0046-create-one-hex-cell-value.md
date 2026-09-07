# Create One Hex Cell Value

## Date

2026-08-27

## Context

The user recreated `scripts/detect_hexes.py` with only the `HexCell` `TypedDict`.

## Learned

The next learning step is to create one real `HexCell` dictionary value. This separates a type
definition from runtime data and gives mypy something concrete to validate. The value now includes
`radius`, because center x/y tells where the hex is, while radius tells how large it is.

## Next Step

Have the user add `create_first_hex_cell() -> HexCell`, print it in a small `__main__` block, and
run the script plus mypy and ruff.
