# Classifier shadow-safety implementation plan

Goal: prevent the unvalidated synthetic classifier from making automatic decisions.
Use the existing CPU model and dependencies. No hosted service or paid resource.

Design: confidence-only acceptance failed the frozen challenge audit. Raising a
threshold cannot reliably reject confident errors; adding keyword rules would
overfit the audit. Keep candidate predictions for human review and withhold the
final label for every unvalidated checkpoint. There is no flag to bypass this.
Reuse a loaded model through an explicit runtime object, enforce the trained
128-token input boundary without truncation, and validate confidence policy.
This is safe shadow operation, not a claim of production accuracy.

- [x] Add regression tests for invalid input/config and mandatory review.
- [x] Verify tests fail, implement isolated runtime, route CLI inference through it.
- [x] Run full suite and frozen challenge in a separate new artifact.
- [x] Document limits and verify independent checkout; ready for publication.

Production validation remains blocked on independently labeled representative
real feedback and an operational deployment context. No synthetic report can
authorize automatic use. Original benchmark and challenge artifacts stay intact.
