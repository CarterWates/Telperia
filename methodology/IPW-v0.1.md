# IPW v0.1

## Status

Draft scaffold with the formulas provided in the Telperia MVP roadmap.

## Purpose

IPW measures capability delivered per watt-hour for a completed evaluation run on specific hardware.

## Formula

```text
IPW = TCI * Completion Ratio / GPU Energy in Wh
Displayed IPW = 1000 * TCI * Completion Ratio / GPU Energy in Wh
```

## Implementation Rule

Always preserve the unscaled IPW result. If a scaled display score is shown, store or expose it separately from the unscaled value.

GPU energy must be calculated from raw power samples and preserved with those samples for verification.
