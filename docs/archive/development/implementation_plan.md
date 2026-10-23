# MiniSense implementation plan

Goal: deliver the assessment as a reproducible CLI repository.
Spec: docs/design.md and the supplied assignment.

1. Contracts and analytics: write failing tests for schema, generation, filtering,
   CSAT, theme counts and comparison; implement and verify; commit.
2. Retrieval: test section chunking, persisted vectors, stale-index detection and
   semantic queries; implement and run a genuine model ingestion; commit.
3. Agents and provider: test plan dependencies, routing, structured tool dispatch,
   output validation and unsupported requests; implement provider and demo mode;
   run evaluation and CLI; commit.
4. Documentation and delivery: audit references, record actual evaluation and
   blockers, requirements, Windows commands, fine-tuning proposal; review the full
   repository, run suite and secret/identity scans; commit and deliver.

Review focus: empty business filters; zero denominators; unsupported dates or
questions; irrelevant FAQ retrieval; LLM output failing the tool/plan contract.
User authorizes autonomous routine decisions and execution, so no design approval
pause is needed. No pre-existing repository or worktree exists; work is isolated
on the new implementation branch. No public email is configured in the app.
