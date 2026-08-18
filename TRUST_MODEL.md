# Trust model

Factur-X Engine separates execution, validation, extraction, and client business
decisions. No single `valid` or `success` boolean proves that an invoice should
be booked, paid, reported, or accepted.

## Endpoint semantics

### `/v1/validate`

This endpoint reports the checks that actually ran.

- Read `valid` together with `validation_completeness`.
- `validation_completeness=partial` means that at least one applicable layer did
  not run; inspect `layers_skipped` for the reason.
- `pdfa_valid=true` means VeraPDF ran and accepted the configured PDF/A profile.
- `pdfa_valid=false` means VeraPDF ran and rejected it.
- `pdfa_valid=null` means no PDF/A verdict exists.

Validation is evidence about configured technical rules, not tax or legal advice.

### `/v1/extract`

This endpoint is a heuristic preview. Every response declares:

```json
{
  "mode": "preview",
  "suitable_for_automatic_import": false
}
```

The preview may contain absent, coerced, truncated, or fallback values. Its
`invoice_json._meta.limitations` list records known limitations. Use it for
inspection and troubleshooting, not automatic accounting import.

### `/v1/serialize`

This endpoint implements schema version `2.0.0` as a strict contract.

HTTP 200 requires all of the following:

1. well-formed CII or UBL XML;
2. complete configured validation with no rejection;
3. no parser recovery;
4. no invented defaults or placeholders;
5. no silently skipped line or tax entry;
6. no material source group that the schema does not map;
7. mapped totals satisfying the declared invariant.

Unsupported or incomplete input returns HTTP 422 with stable diagnostics. A
successful response uses `suggested_route=continue_client_checks`, never an
automatic-booking decision. The caller remains responsible for supplier,
duplicate, order, tax-policy, and payment controls.

### `/v1/xml`, `/v1/convert`, and `/v1/merge`

Generation and verification are separate jobs. These endpoints create an
artifact but do not, by themselves, prove that every applicable validation layer
or PDF/A check passed. Run `/v1/validate` on generated output when evidence is
required.

## Operational endpoints

`/health` is a liveness probe. `/healthz` exposes readiness and runs a minimal
Saxon transform that also checks temporary input/output I/O. `/diagnostics` and
`/metrics` disclose operational information and are disabled or protected by
tokens in production configurations.

## Common integration mistakes this model prevents

- treating `not checked` as `failed` or `passed`;
- treating heuristic extraction as a strict mapping;
- treating generated output as proof of technical validity;
- mistaking successful normalization for permission to book or pay;
- hiding skipped validation layers from downstream logic.
