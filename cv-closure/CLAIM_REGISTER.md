# CV evidence closure

Branch: `codex/cv-evidence-closure-2026-10-03`. Expansion is paused until all three projects have executable code and verified results.

Source CV SHA256: `16ad4fb13ce8c4df0ae8b43061c30dd7def08f2d11d42d9242a4c46e0dfcc4b0`. No CV wording or numbers edited.

## Required evidence

- [x] Python ReAct coding agent: file operations, code execution, error handling, multi-step model trace.
- [x] Multiple retrieval strategies; actual RAGAS precision, recall, faithfulness; measured complete query latency.

Completion requires real execution, inspectable predictions/traces, data/config/source/artifact hashes, reproducible commands and honest limitations. Historical scores are not acceptance targets; measured scores may replace them.

Agent trace and11controller/gateway unit checks are verified. The full36-row RAG comparison completed; all108metrics independently recomputed with no failed/undefined values. Inspect `output/result.json`, `output/rows.jsonl`, `output/judge_calls.jsonl`, `output/result_audit.json` and `judge_interpretation_review.json`.

Hybrid precision0.8889, recall0.9583, faithfulness0.8681; full-query median21.029seconds, retrieval median0.343seconds. These measurements replace unsupported historical numeric targets; the CV itself remains unchanged. The implementation and measurement gaps are closed, but original scores and subsecond end-to-end latency are not backed. Real answer failures and judge errors are documented in `README.md`.
