# Execution and review evidence

Executed on Linux, Python 3.12, 23 October 2026. Final commands use `.venv-clean`
because the initial environment was replaced after a dependency-install conflict.
The README uses the conventional `.venv` directory for a clean user installation.

## Commands executed

- Read all paragraphs and tables of the supplied DOCX with python-docx.
- Shallow-cloned all five supplied GitHub repositories and inspected source,
  dependency manifests, and available licenses; recorded snapshot SHAs.
- Created isolated environment; installed CPU PyTorch 2.6.0 and requirements.
- `python -m minisense generate`
- `python -m minisense validate`
- `python -m minisense ingest`
- `python -m minisense --help`
- `python -m minisense ask ... --json` (see final verification below)
- `python -m minisense evaluate`
- `python -m pytest -m "not integration" -q`
- `python -m pytest tests/test_retrieval.py -m integration -q`
- `python -m pytest -q`
- `python -m pip check`
- `python -m minisense --provider llm ask "CSAT in June 2026"`
- Git commits, diff whitespace check, tracked-source identity and secret scans.

## Results

Dataset: exactly 100,000 unique IDs, 47,000 May and 53,000 June responses,
all b01/GreenLeaf Bistro. Four sentiment classes; 65,458 unique feedback strings.
Full schema validation passed; hash and counts are in dataset_validation.json.
FAQ: exactly 500 whitespace-delimited words, seven Q/A sections. Ingestion used
the actual all-MiniLM-L6-v2 model and wrote seven 384-dimensional normalized
vectors. Repeat ingestion returned `rebuilt: false`.

Real-model integration test passed. Three assessment questions ran with real
embeddings, exact analytics and deterministic demo planning/synthesis. All 33
explicit evaluation checks passed, including expected periods/business, specialist
routing, independent complaint/mean calculations, comparison changes and relevant
FAQ section retrieval. They are not live generative-LLM integration results.

Final full suite: **29 passed**, with the real embedding integration test included.
`python -m pip check` reported no broken requirements; `compileall` and Git
whitespace checks passed. The final active-source scan checked 17 source/config
files and found no secret/contact matches or old developer branding.

## Failures observed and resolved

Initial test collection failed before retrieval/agent/CLI modules existed, then
passed after implementation. The earliest analytics test attempt could not run
because pytest installation had not finished; it is not presented as a red test.

An initial unconstrained ML install and overlapping downgrade attempts produced
mixed PyTorch files and Transformers/tokenizers incompatibilities. The concrete
errors included a missing SerializationFormat import and invalid tokenizers
metadata. A fresh environment, CPU PyTorch 2.6.0, sentence-transformers 3.4.1,
Transformers 4.48.3 and tokenizers 0.21 resolved them. Future installations should
follow the documented sequential commands, not concurrent dependency mutations.

A unit test encountered the host's SOCKS proxy without socksio; httpx[socks] now
includes the required transport support. Independent review reproduced six failing
scope/summary/empty-data cases and a stale-vector-cache bug. Regression tests were
written before the fixes and passed afterwards. Evaluation rendering initially
formatted an optional absent score as a float; it now displays `unavailable`.

## Independent review

A separate reviewer inspected source, contracts, tests and design. Fixed its
important findings: unsupported demo scopes, undefined empty prevalence,
missing rating/volume comparison statements, evaluator scope blindness, and
cached vectors paired with newly ingested metadata. Full FAQ answers retain
qualifying language. The reviewer did not rerun after fixes; regression tests and
the final full suite verify the changes. No claim of a second review is made.

## Identity and secret audit

The four reference application sources were not copied. Active application
configuration contains no original developer names, unrelated contact addresses,
or old branding. Reference URLs remain intentionally in README and reference_review.
No account email is embedded as an application contact. `.env`, environments,
generated survey JSON and vector caches are ignored. Git uses a GitHub noreply
identity. Package/model dependencies retain their upstream licenses.

## Explicit blockers and unverified behavior

No LLM endpoint/model credentials are configured. LLM mode exits with a clear
configuration error. Provider transport, plan validation and function-call guards
are unit-tested with labeled mocks; real LLM task planning, API function calling
and synthesis remain unverified. A tool-capable compatible endpoint is required
before calling the entire AI assessment integration complete. No training occurred.

The connected GitHub profile is psychochan. The connector exposes repository
reads and file/commit mutations, but no repository-creation operation; no target
MiniSense repository was found, and no authenticated Git CLI is configured.
No remote repository was created or overwritten. A local Git bundle and clean
source archive preserve the work for importing into an empty user-owned repo.
Windows instructions were written but runtime checks occurred on Linux only.
