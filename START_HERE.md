# Continue MiniSense in VS Code

Open this folder in VS Code: the one containing this file, README.md, minisense,
tests and requirements.txt. The archive includes a local Git repository with the
implementation history. The continuation is now published at
https://github.com/nachiket0987/minisense-survey-agent on `implementation`. Do not initialize a
second repository or copy files over an existing project.

Open the Codex extension in this folder and paste:

> Read START_HERE.md, docs/CODEX_HANDOFF.md, and docs/Assignment.docx. Continue the existing MiniSense implementation from its current state. Complete live LLM evaluation, fix confirmed problems, update evidence and documentation, publish to my GitHub repository when available, and verify a fresh checkout. Do not restart or regenerate the project from scratch. Never print or commit API keys. Execute all work that is possible; ask me only for missing local credentials, permissions, paid-service approval, or a required repository choice.

The detailed handoff contains the scope, current implementation, test evidence,
remaining work, known weak points, commands and reference projects. It can be
used without access to the previous ChatGPT conversation.

## What is included

- Complete Python source, tests, requirements, README and .env.example.
- Original assignment at docs/Assignment.docx.
- Actual demo evaluation JSON, retrieved passages, numerical checks and reports.
- Requirements matrix, architecture, reference audits and fine-tuning proposal.
- 100,000 generated survey records in data/responses.json, matching the recorded
  evaluation hash. The dataset remains ignored by Git.
- Local .git history with the prior implementation milestones and this handoff.

Python environments, installed libraries and model caches are machine-specific
and are not included. Recreate the environment and run ingestion locally.
The original reference repositories were reviewed but their source is not bundled;
links and inspected commits are in docs/reference_review.md.

## First local commands

Open a PowerShell terminal in this folder:

```powershell
py -3.12 -m venv .venv
$py = ".\.venv\Scripts\python.exe"
uv pip install --python $py torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
uv pip install --python $py -r requirements.txt
& $py -m minisense validate
& $py -m minisense ingest
& $py -m pytest -q
```

The dataset is already included; `python -m minisense generate` can recreate it.
If Python 3.12 is unavailable, README documents the tested workspace-local uv
bootstrap. Windows continuation passed 47 tests, real model ingestion and all
three live Groq questions (58 checks). See docs/verification.md for evidence and
docs/live for actual traces. Historical demo artifacts remain unchanged.

## LLM credentials

Signing in to Codex in VS Code does not configure MiniSense's own LLM provider.
MiniSense needs MINISENSE_BASE_URL, MINISENSE_MODEL and, for authenticated hosted
services, MINISENSE_API_KEY. Current code reads environment variables and does
not automatically load .env. Values set in an integrated terminal apply to that
terminal and its child processes; a separate Codex execution shell may not inherit
them. Run the credential-dependent commands in the configured terminal or have
Codex implement explicit local .env loading without exposing the key.

A previously proposed starting provider is Groq with base URL
https://api.groq.com/openai/v1 and model openai/gpt-oss-20b. Confirm the account's
available model and free quota before use; this project's live compatibility has
not yet been tested. Do not activate paid billing without approval.

```powershell
$env:MINISENSE_BASE_URL = "https://api.groq.com/openai/v1"
$env:MINISENSE_MODEL = "openai/gpt-oss-20b"
$secureKey = Read-Host "Paste your provider API key" -AsSecureString
$env:MINISENSE_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
Remove-Variable secureKey
& $py -m minisense --provider llm ask "What are the top three customer complaints in June 2026?" --json
& $py -m minisense --provider llm evaluate --output docs/live/evaluation.json
```

Do not change a failed check to a passing claim. Fix the underlying defect or
record the actual blocker. Complete the rest using docs/CODEX_HANDOFF.md.
