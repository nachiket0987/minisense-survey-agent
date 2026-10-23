# Requirements coverage

Authority: supplied Assignment(1).docx, including both appendices. The user's
mission adds engineering and delivery requirements beyond the original assessment.
Implemented means code exists; verified means the listed runtime evidence exists.
No live LLM success or training run is implied by a unit test.

Windows continuation: live/evaluation.json passed all three required Groq questions
and 58 independent checks; live/probes.json records passing paraphrase, exact-date
and empty-business checks. The complete Windows suite passed 48 tests including
real embeddings. Historical demo evidence is preserved. No training claim is made.
Publication target is now nachiket0987/minisense-survey-agent, explicitly authorized
by the user instead of the handoff's original owner.

| Expectation | Implementation | Source or artifact | Verification | Status |
|---|---|---|---|---|
| Runnable small AI analysis system | CLI and optional compatible LLM | minisense/cli.py, provider.py | CLI commands; provider unit tests | Live verified on Windows; live/evaluation.json |
| Two-level architecture | Orchestrator and four specialists | minisense/agents.py | test_agents.py; evaluation plans | Verified in demo |
| Natural-language planning | Validated LLM JSON plan; limited offline grammar | agents.py, provider.py | plan and unsupported-scope tests | Live planning and validation verified |
| Structured task input | Pydantic Task and Period | contracts.py | agent/operation, dependency and scope tests | Verified |
| Structured sub-agent output | Metrics, Comparison, Retrieval, Summary | contracts.py, agents.py | validation plus JSON traces | Verified |
| At least two sub-agents | Data, Comparison, RAG, Summary | agents.py | actual invocation lists | Verified |
| Actual routing rather than fixed sequence | Dependency scheduler; per-question tasks | agents.py | single/comparison/FAQ routing tests | Verified |
| Tool call from inside agent | compute_metrics dispatcher and compute_csat inside analytics | agents.py, analytics.py | function traces and scope tests | Actual API calls and Python execution verified in live traces |
| Coherent business narrative | Evidence-preserving summary and recommendation | agents.py | actual evaluation answers | Live constrained evidence synthesis verified |
| Generate 50k–100k rows | Exactly 100,000; seed 42 | dataset.py | validate command, dataset_validation.json | Verified |
| Required schema and dates | IDs, business/survey fields, channels, text, rating; May/June 2026 | contracts.py, dataset.py | uniqueness/schema/count/month tests | Verified |
| CSAT ambiguity resolved | rating is observation; mean and satisfied percentage separate | README, analytics.py | known-value and empty-input tests | Verified |
| Realistic feedback variation | Four sentiments, multi-theme mixed text, varied contexts, monthly distributions | dataset.py | 65,458 distinct texts; sentiment counts | Verified; synthetic templates remain a limitation |
| Main business consistency | GreenLeaf Bistro/b01 only | dataset.py | contamination and filter checks | Verified |
| Efficient repeated operations | Shared once-loaded validated store | analytics.py | code review; agents share instance | Implemented and reviewed |
| FAQ roughly 500 words and preserved facts | Seven complete Q/A sections | data/faq.txt | word count = 500; manual source comparison | Verified |
| Justified chunking | Complete short Q/A sections | retrieval.py, design.md | chunking and length tests | Verified |
| Real embeddings | all-MiniLM-L6-v2 on CPU | retrieval.py | real-model integration test | Verified |
| Local vector store and top-k | Persisted normalized NumPy vectors, exact cosine search | retrieval.py | actual index and semantic retrieval | Verified |
| Repeatable ingestion | Model/FAQ signature and no-op reuse | retrieval.py | cache/stale-index/reingestion tests | Verified |
| Attributed retrieval and absent-context handling | IDs, source, content, score; threshold limitation | contracts.py, retrieval.py | empty-context and source tests | Verified |
| Inject context and metrics into final prompt | structured_results plus evidence sent to provider | agents.py, provider.py | mocked provider path; code review | Live synthesis prompt and result verified |
| Three questions with chunks and answers | Evaluation CLI with independent correctness checks | docs/evaluation.json, rag_evaluation.md | 33 checks across 3 executed questions | Verified with real embeddings and demo planning |
| Comment on retrieval strengths/shortfalls | Per-question observations and report | rag_evaluation.md | inspected actual ranked chunks | Verified |
| 300–500-word fine-tuning proposal, all six aspects | 424-word proposal embedded in README | README.md, docs/fine_tuning.md | word count and scope review | Verified |
| Optional fine-tuning code | Not necessary for required assessment | docs/fine_tuning.md | explicitly no training claims | Deferred optional bonus |
| Tests and errors | pytest; clear missing-data/index/provider failures | tests/, __main__.py | full suite and failure-path tests | See verification.md |
| Reference implementation audit | Five snapshot reviews, real implementation files | reference_review.md | clone SHAs and inspected modules | Complete |
| Personalization and attribution | Nachiket maintainer, no copied configuration or source | README, pyproject.toml, LICENSE | identity and secret scan | Complete |
| GitHub repository and incremental commits | Local implementation branch with staged commits | Git history; supplied bundle | git log and git bundle verify | Local history complete; publication tracked in verification.md |
| Windows VS Code reproduction | PowerShell commands without activation requirement | README.md | Actual Windows commands, 48 tests and live evaluation | Windows verified; clean-checkout evidence in verification.md |

## Assumptions

The original example contains a missing comma and JSON comments; the generated
file uses valid JSON. Its QuickFit Gym identity conflicts with the bistro FAQ;
GreenLeaf Bistro is used consistently. The introduction says supplied 100,000
records while Appendix A asks the candidate to generate them: the appendix and
user request are satisfied by a seeded 100,000-record generator. No independent
CSAT field is supplied, so rating represents satisfaction. Relative periods use
the dataset's latest month. Synthetic theme labels are declared additional fields,
not undisclosed semantic inference. The eight fine-tuning categories are a proposed
single-label taxonomy, with a documented mixed-feedback rule. No paid API access
or GPU rental has been authorized or used.
