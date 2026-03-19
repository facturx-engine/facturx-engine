# Trust Model

Factur-X Engine is built around explicit evidence and explicit uncertainty.

This document explains what each core endpoint proves, what stays heuristic, and how an integrator should interpret the output.

## The short version

- `/v1/validate` is the proof endpoint.
- `/v1/extract` is heuristic best-effort extraction.
- `/v1/serialize` is the ERP-oriented contract with fallback transparency.
- `/v1/convert` and `/v1/merge` generate files, but they do not prove final PDF/A compliance on their own.
- `Community` is not the same thing as `invalid`.

## Core principles

### 1. Verification and generation are different jobs

Generation endpoints create an invoice artifact.
Validation endpoints tell you what was actually checked.

That is why outbound workflows should use this sequence when evidence matters:
1. Generate with `/v1/xml`, `/v1/convert`, or `/v1/merge`.
2. Verify with `/v1/validate`.

### 2. Missing proof must not be reported as failure

`pdfa_valid` uses tri-state semantics:
- `true`: VeraPDF ran and the document passed.
- `false`: VeraPDF ran and the document failed.
- `null`: PDF/A was not checked or did not apply.

`null` means "not verified", not "invalid".

### 3. Partial validation must stay visible

`validation_completeness` tells you whether all applicable layers actually ran.
- `full`: all applicable layers ran.
- `partial`: one or more applicable layers were skipped.

Applications should inspect `layers_executed` and `layers_skipped` instead of assuming a single boolean covers everything.

## Endpoint semantics

## `/v1/validate`

Use this endpoint when you need evidence.

It can report:
- structural or business-rule validity
- `validation_completeness`
- `pdfa_valid`
- executed and skipped layers

Recommended interpretation:
- trust `valid` only together with `validation_completeness`
- trust `pdfa_valid=true` only when it is explicitly `true`
- treat `pdfa_valid=null` as "no PDF/A verdict"

## `/v1/extract`

This is a heuristic extraction endpoint for reception workflows.

It is useful when you need quick access to embedded invoice data, but it is not the strongest integration contract.

Look at:
- `invoice_json._meta.limitations`

Typical limitation codes include:
- `heuristic_mapping`
- `fallback_values_used`
- `missing_line_items`
- `max_20_lines_cii`

Recommended interpretation:
- good for exploration, routing, and basic downstream flows
- not the best contract when your ERP needs typed, explicit normalization guarantees

## `/v1/serialize`

This is the ERP-oriented endpoint.

It keeps the payload stable and explicit by exposing:
- a versioned schema
- `fallbacks_applied`
- `xml_recovery_applied`

Interpretation rules:
- `fallbacks_applied = []` means no fallback was needed
- non-empty `fallbacks_applied` means the invoice was normalized with explicit repairs, defaults, or truncation decisions
- `xml_recovery_applied = true` means malformed XML had to be recovered before normalization

This endpoint is designed so integrators can decide what is acceptable in their own pipeline.

## `/v1/convert` and `/v1/merge`

These endpoints generate output files.

They should be read as production endpoints, not proof endpoints.

Interpretation rules:
- they can produce an output that is intended for Factur-X workflows
- they do not, by themselves, assert final PDF/A compliance unless a verification step runs afterward
- if you need evidence, run `/v1/validate` on the generated output

## Community vs Pro

License tier changes feature availability, not truth.

That means:
- `Community` should not be interpreted as `invalid`
- lack of Pro features should not be reported as a failed compliance verdict
- lack of VeraPDF execution should keep `pdfa_valid = null`, not `false`

## Recommended patterns

### Outbound compliance

1. Generate with `/v1/xml`, `/v1/convert`, or `/v1/merge`.
2. Validate the result with `/v1/validate`.
3. Read `validation_completeness` and `pdfa_valid` before making a compliance claim.

### Inbound ERP ingestion

1. Validate with `/v1/validate`.
2. Use `/v1/extract` for heuristic inspection or lightweight routing.
3. Use `/v1/serialize` when you need typed ERP JSON and explicit fallback transparency.

## What this model avoids

This trust model is meant to avoid the most common integration failures:
- treating "not verified" as "failed"
- treating heuristic extraction as a strict contract
- treating generated output as proof of PDF/A compliance
- hiding normalization fallbacks from downstream ERP logic

If you are evaluating the engine, the fastest hands-on path is:
- `examples/send-invoice/`
- `examples/receive-invoice/`