# Detect Champion Stars

The user is ready to add star-level recognition after stabilizing champion boxes, champion identity,
Champion-to-Hex Evidence, and Board State JSON. The next learning step is to treat star level as a
separate crop classification problem with classes `1star`, `2star`, `3star`, and `unknown`, then
attach `star_level` and `star_confidence` back to each Board State unit.
