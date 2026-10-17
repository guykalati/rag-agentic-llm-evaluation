# Bounded coding agent, RAG evaluation and ML experiment loop

Build testable repository repair and bounded ML experimentation, and measure retrieval separately from answer generation and repair success.

[Project page](showcase/index.html) · [Technical study guide](showcase/guide.html) · [Current status](PROJECT_STATUS.md) · [Decisions](DECISIONS.md) · [Research archive](research-workbench/INDEX.md)

## Verified implementation

A real multi-step repair trace with independent target/regression checks; an eight-page, 581-chunk retrieval corpus; 12 source-checked questions and 36 evaluated answers; all 108 RAGAS metric executions preserved. A bounded autoresearch-inspired loop and verified TinyStories candidate experiment also exist.

## What changed on 17 October

Added deterministic source/anchor coverage and citation-ID diagnostics for every saved answer. Hybrid covers 11/13 required anchors at top 3; BM25 and dense each cover 8/13. Ten of twelve answers per strategy contain a valid retrieved-chunk citation. A one-command verifier recomputes raw judge arithmetic and runs controller, gateway and proposer checks.

## Verify locally

Use Python 3.10 or newer in an isolated environment. Saved-evidence verification needs NumPy; it does not need a GPU, model server or downloaded base model.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-verify.txt
.venv/bin/python verify_project.py
```

The command checks saved source/data/output hashes, recomputes scores, checks derived analysis, runs offline regression tests and validates both page link sets. It runs no training or network requests. To save a fresh report, add `--report verification/<new-name>.json`; existing report files are protected from overwrite. Large ignored weights/data may remain external; the report states when optional adapter verification is unavailable.

[Verification snapshot](verification/2026-10-17-final.json) · [Training/inference instructions](cv-closure/README.md) · [CV claim register](cv-closure/CLAIM_REGISTER.md)

## Repository layout

| Location | Purpose |
|---|---|
| `cv-closure/` | Frozen benchmark implementation, source data instructions and saved outputs |
| `cv-closure/analyze_results.py` | Reproducible analysis; `--check` compares against the saved derived report |
| `research-workbench/` | Historical expansion code, protocols, reports and results |
| `DECISIONS.md` | Accepted, rejected and pending choices with source links |
| `PROJECT_STATUS.md` / `.json` | Current completion boundaries and next work |
| `showcase/` | Self-contained landing page and 20-question study guide |
| `verification/` | Dated verification reports |
| `LEGACY_README.md` | Original claims, retained for history |

The workbench preserves shared/cross-project foundation files. It is an archive, not a second current entry point. Read the root status first; older pending statements describe their original dates.

## Remaining work

The original 12-question set is small development evidence. Citation presence does not prove entailment. A paired retrieval/no-retrieval benefit for repairs or new experiment proposals is not established. New isolated cluster evaluations are blocked by the SSH timeout on 17 October.

Prepare an independent, source-checked development extension, retaining the original benchmark. Preserve chunk IDs in future judge inputs and add executable API-composition checks. For repair and experiment memory, freeze a paired task/candidate ledger with identical budgets before new isolated runs. Do not tune on sealed outcomes. No new campaign was submitted.

## Open the pages

Download and open `showcase/index.html` in a browser. GitHub displays HTML source; these files are not a public deployment. Page controls explore saved outputs. The ECG replay server, where applicable, is a separate executable model interface.
