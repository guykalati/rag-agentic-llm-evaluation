# CV evidence closure

[Executable coding-agent and real RAG evaluation](cv-closure/README.md): pinned documentation corpus, BM25/dense/hybrid retrieval, local generated answers and actual RAGAS judging. Full benchmark is running; final scores are pending. Historical CV RAGAS numbers and subsecond end-to-end latency remain unverified.

# Bounded repository repair and ML experiment agent

This branch preserves the original course artifacts and adds the new personal research work through 3 October 2026.

- [Current status](research-workbench/CURRENT_STATUS_2026-10-03.md)
- [Plain-language HTML walkthrough](research-workbench/output/portfolio_progress_explained_2026-10-03.html) — download/open locally
- [Implementation and checks](research-workbench/implementation/README.md)
- [First audit](research-workbench/FIRST_SCAN_2026-09-27.md)
- [Original README](LEGACY_README.md) — historical claims, corrected by the audit

## Status

The completed eight-head candidate scored 0.9169007335 bits per byte versus incumbent 0.9121882524; retain the incumbent. A new bounded 18-record development snapshot adds that outcome and preserves the old17-record snapshot. The proposer requires explicit --history-limit18 to use it; default17 rejects growth. Five tests pass, and no-history reads no database. Retrieval benefit remains unproven.

Read [the completed result](research-workbench/AUTORESEARCH_STATEMENT_REPLAY_RESULT_2026-10-03.md) and [memory refresh](research-workbench/AUTORESEARCH_MEMORY_REFRESH_2026-10-03.md). All experiment calls/jobs are finished. Guy paused expansion to close actual RAG/RAGAS and coding-agent CV claims on another branch. Historical reports and HTML remain earlier snapshots.

## Snapshot layout

`research-workbench/implementation` holds project code and compact evidence. Shared foundation helpers and cross-project reports preserve dependencies and the original audit trail. Large raw datasets, checkpoints, model caches, and virtual environments remain external.

Historical reports record earlier stopping points. Read the current status before interpreting older pending statements. The new work does not establish clinical deployment, autonomous-research superiority, or unpublished benchmark claims.
