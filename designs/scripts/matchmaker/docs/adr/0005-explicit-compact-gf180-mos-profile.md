# ADR 0005: Generated GF180 MOS cells use an explicit compact profile

Status: Accepted

## Context

The first family-composable vertical B0 selector reached a DRC-clean extracted
layout but still produced only four of the five required shared child nets. The
child-interface report showed that the intended PMOS `vdd_*` connection had
merged into `VSUBS` rather than remaining an independent VDD net.

Inspection of the generated geometry identified the physical cause. The MOS
primitive call requested conductive body ties but left substrate taps, deep
wells, guard rings, and dummies unspecified. Those `None` values inherited the
installed gLayout defaults. The PMOS VDD escape crossed an inherited outer
substrate ring, so the selector supply failure was a short to substrate rather
than a missing route.

A reusable generator cannot treat a PDK primitive's version-dependent defaults
as harmless. Primitive-envelope policy affects placement, legal escapes,
connectivity, and every composite route derived from the resulting bounding box.

## Decision

Transmission-gate MOS children use one explicit compact GF180 primitive profile:

```text
conductive body ties: on
substrate taps: off
deep wells: off
guard rings: off
dummies: off
```

All five safety-critical fields are concrete booleans. `None` is not accepted,
because it means that geometry is inherited from the installed primitive rather
than selected by MatchMaker. A conflicting value is also rejected before any
component is generated.

The restriction is enforced at `TransmissionGateLayoutIntent`, not hidden in the
placement algorithm. Other explicit routing or layer options may still be
supplied, but they do not relax the compact-profile requirements.

The primitive diagnostic prints the selected profile and a normalized bounding
box with width and height. This makes changes in inherited or unexpected
primitive envelopes visible before a composite-cell validation run.

## Invariants

1. Generated transmission-gate children never rely on gLayout defaults for
   substrate taps, body ties, deep wells, guard rings, or dummies.
2. The body-tie ring remains present because its measured cardinal metal exports
   are the VSS/VDD access contract.
3. Substrate taps, deep wells, guard rings, and dummies remain absent from this
   compact leaf profile unless a later ADR defines a different device family and
   its complete routing contract.
4. Unsafe, expansive, or partially inherited profiles fail during intent
   construction, before placement or routing.
5. Runtime bounding boxes remain the geometry source of truth, but diagnostics
   must identify the profile that produced them.
6. The profile correction does not by itself validate B0. The selector must be
   regenerated in `/foss` and pass DRC, extraction, exact five-net connectivity,
   visual inspection, and independent LVS.

## Consequences

Positive:

- the PMOS VDD escape is no longer planned across an unrequested outer substrate
  ring;
- composite placement and corridor geometry derive from a deliberately compact
  leaf envelope;
- installed-version changes cannot silently re-enable expansive MOS features;
- profile and bounding-box evidence are visible in the standard diagnostic;
- one focused regression rejects both inherited and explicitly unsafe profiles.

Costs and limitations:

- transmission-gate callers can no longer provide partial MOS options;
- any future guard-ring, deep-well, substrate-tap, or dummy-enabled family needs
  its own explicit profile, access contract, placement policy, and validation;
- the prior base-TG signal-net evidence remains useful, but supply correctness
  under the compact profile must be rerun;
- the former local commit `b7d80a6` was not published, so the recovered change
  may receive a different Git SHA even though this decision is equivalent.
