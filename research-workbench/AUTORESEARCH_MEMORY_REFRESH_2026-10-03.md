# Completed feedback added to a new bounded snapshot

The verified eight-head run is now stored as completed development feedback: 0.9169007335 validation bits per byte versus the retained incumbent 0.9121882524. Its source hash, optimizer steps, fixed-time duration, parameter count and independent reload provenance are retained. Completion does not mean model improvement.

A new snapshot contains 18 records: all 17 prior records unchanged plus this single outcome. The previous SQLite snapshot and every historical proposal ledger remain unchanged. The default 17-record reader rejects the grown index, preventing silent use under the old bound.

The proposer now accepts an explicit `--history-limit 18` for a future separately frozen campaign, with a maximum of 18 and default 17. Its result records the declared cap and SQLite hash. No-history continues to read no database. Five meaningful tests pass, including default-cap rejection, explicit18 inclusion,19 rejection, source-edit protections and no-history isolation. No new generation or GPU training accompanies this refresh.

Use the new snapshot only with a fresh protocol that freezes the 18-record database/input-ledger/source hashes and sampling/training caps. Do not overwrite the old index, regenerate historical proposals or claim a memory benefit from one unsuccessful candidate. Existing evaluator, training-data and edit boundaries remain enforced.

Evidence: implementation/experiment_memory_refresh_audit_2026-10-03.json; autoresearch_completed_feedback_2026-10-03.jsonl; experiment_proposer.py; test_experiment_proposer.py.
