# Choose Champion Hex With Occupancy

The user clarified the next rule for large champions: keep hex occupancy as the first signal and
champion detection as the second signal, but when a champion box covers multiple occupied hexes,
assign the champion signal to the occupied hex nearest the champion box bottom-center point.

If no occupied hex exists under the champion box, the champion detector should still be trusted as a
fallback by assigning the champion to the nearest hex by bottom-center distance.
