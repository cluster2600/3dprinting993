# Repository instructions

This repository builds an evidence-backed catalogue of reproducible Porsche 993
parts for additive and conventional manufacturing.

## Working rules

- Treat `catalog/parts/*.json` as the catalogue source of truth.
- Prefer editable source geometry (`.FCStd`, `.scad`, `.step`) over derived
  meshes (`.3mf`, `.stl`).
- Preserve the original Porsche geometry from the best available scan or
  measured reference as the default design baseline. Do not globally smooth,
  regularize, rescale, or replace its silhouette with a convenient primitive
  unless that transformation is required and quantitatively justified.
- Every proposed geometry change must name a measurable engineering objective
  such as mass, heat rejection, flow, strength, fatigue, manufacturability, or
  packaging. Keep an unchanged-baseline variant, compare both variants under
  the same assumptions and solvers, and record gains, regressions, uncertainty,
  and local deviation from the baseline.
- Reject a geometry change when it provides no demonstrated material benefit.
  Aesthetic cleanup, easier modelling, or solver convenience alone are not
  engineering justifications. Prefer local changes around the affected feature
  over altering the complete part envelope.
- Never label a part as dimensionally accurate, fitted, tested, safe, or
  released without linked evidence in its catalogue record.
- A publicly visible model or photograph is not automatically reusable. Record
  its licence and provenance before adding it.
- Do not commit raw scans, proprietary manuals, supplier quotes, personal data,
  credentials, or vehicle identifiers.
- Do not release braking, steering, suspension, restraint, fuel-system, wheel,
  or highly loaded engine parts without documented professional engineering
  review and an approved validation plan.
- For titanium parts, document alloy, build process, orientation, heat
  treatment, machining, inspection, fatigue assumptions, and galvanic isolation.
- Keep changes surgical and run `make check` before proposing a merge.

## Repository language

Project documentation is written in French. Stable identifiers, schema field
names, filenames, and command-line messages remain in English.
