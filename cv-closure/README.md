# Coding agent and real RAG evaluation

## What is implemented

The coding controller already has real multi-step model traces: list/read files, apply an exact edit, execute an isolated target test, and independently verify target plus regression tests. The preserved PySnooper3 trace passes both checks. Eleven existing controller/gateway tests passed again during CV closure. Evidence is in `agent_evidence_audit.json`, `agent_unit_audit.json`, and `../research-workbench/implementation/repair_agent_success_pysnooper3_2026-09-29.json`. The real agent is in `../research-workbench/implementation/repair_agent.py`; isolated Slurm execution is in `repair_eval_bridge.py` and `run_repair_candidate_eval.sbatch` beside it. The earlier four-attempt report includes unsuccessful cases and does not establish a retrieval benefit for coding repairs.

The missing RAG component is now executable: eight official Python documentation snapshots, 581 chunks, actual pinned MiniLM embeddings, BM25/dense/hybrid retrieval, cited local-model answers, and the real RAGAS ContextPrecision, ContextRecall and Faithfulness classes. Twelve source-checked references and 13 evidence anchors are frozen before evaluation. The retrieval benchmark is separate from the coding repair benchmark; it does not prove that RAG improves repair success.

## Reproduce

Python3.12; install `environment.lock.txt` in an isolated environment. The initial unconstrained dependency install failed because current LangChain removed a RAGAS import; compatible versions are pinned in the lock, and `dependency_audit.txt` confirms no broken requirements. Local Ollama with the cached model in `runtime_manifest.json` must run at127.0.0.1:11434.

```sh
cd cv-closure  # from the repository root
python -m venv .venv
.venv/bin/python -m pip install -r environment.lock.txt
# Corpus/embeddings are already frozen in Git. Acquire the pinned encoder cache:
# Run prepare.py in a clean copy without corpus/ to rebuild the whole index.
.venv/bin/python query.py 'How does Path.mkdir create missing parents?' --strategy hybrid
.venv/bin/python evaluate.py --output new-output --cap-seconds 10800
.venv/bin/python verify_results.py --output new-output
```

The encoder cache is excluded from Git. For a fresh clone with the included corpus, download `sentence-transformers/all-MiniLM-L6-v2` at revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41 into `cache/` using SentenceTransformer with the same revision/cache_folder arguments as `prepare.py`, then use the frozen index. Corpus rebuilding requires network access; answer/judge inference is local. Source licenses and attribution are in `SOURCE_CREDITS.md`.

## Verified results — 4 October 2026

The frozen campaign completed all **12 questions × 3 strategies** in **7,486 seconds (2 h 4 min 46 s)** on the local Mac, within its three-hour cap. All **108 metric executions** succeeded; all 216 raw judge calls are retained. `verify_results.py` independently recomputed every metric from judge verdicts, checked frozen inputs/contexts and raw prompt hashes, and recalculated latency summaries. No failed or undefined scores were excluded.

| Strategy | Context precision | Context recall | Faithfulness | Retrieval median / p95 (s) | Full answer median / p95 (s) |
|---|---:|---:|---:|---:|---:|
| BM25 | 0.8194 | 0.9167 | 0.8611 | 0.046 / 0.056 | 21.392 / 24.702 |
| Dense | 0.7639 | 0.9583 | 0.8417 | 0.354 / 0.443 | 21.623 / 24.614 |
| Hybrid RRF | 0.8889 | 0.9583 | 0.8681 | 0.343 / 0.452 | 21.029 / 24.547 |

Each mean includes all12questions for that strategy. These are model-judged RAGAS metrics on a small fixed documentation benchmark. Hybrid has the highest observed mean precision and faithfulness, and ties dense recall. This is descriptive evidence from one campaign, without a statistical superiority claim.

**The old CV values0.94/0.92/0.95 are not reproduced.** Retrieval is subsecond on this machine; complete uncached answers are approximately21seconds at the median. A subsecond query-to-answer claim is unsupported. Evaluation overhead is excluded from application latency; embedding time is included in retrieval. Offline retriever startup is reported separately in the result. Benchmark queries run in fixed order with warmed models; these timings do not measure cold starts or concurrent load.

## Error analysis and limits

Read [the preserved interpretation review](judge_interpretation_review.json). All36responses were inspected against the questions and saved references; this is a Codex review, not expert gold. Raw RAGAS scores remain unchanged.

- **Wrong API despite faithfulness1:** BM25 answers a `subprocess.run` timeout question using retrieved `Popen.communicate` behavior. It says the child is not killed, which is wrong for `run`. Precision/recall0 flag the missing relevant evidence.
- **Wrong composition despite high scores:** on the two-source read-text/JSON question, BM25 names `json.load` after `Path.read_text`, though the resulting string needs `json.loads`. Dense omits the function, and hybrid names `JSONDecoder` without the requested usable interface. None provides the complete requested pipeline.
- **Missed distinctions:** dense/hybrid `assertRaises` answers merge failed assertion and unexpected-exception error outcomes; the faithfulness judge returns1.
- **Judge false negatives:** all three correct mkdir-option answers receive faithfulness0 because the judge objects to “should” wording. Other verdicts reject a two-item list by treating each item as an exclusive claim.
- **Citation metadata mismatch:** generated answers cite real chunk IDs, but RAGAS receives text-only contexts. Some extracted statements treat those IDs as unsupported facts or even error codes. This depresses faithfulness for otherwise supported answers.

Faithfulness checks support from retrieved text; it does not establish answer correctness, API identity, completeness or executable code. Reference-based recall also has judge errors. Shared answer/judge Gemma weights introduce correlated errors. The benchmark has12questions, not enough to claim general RAG reliability. Dense chunk encoding can truncate beyond256tokens. Source-checked references and their13anchors are preserved in `reference_audit.json`; no anchor labels enter retrieval or generation.

## Evidence files

- [Final scores and runtime/source hashes](output/result.json)
- [Every answer, retrieved context, score and latency](output/rows.jsonl)
- [Raw judge prompts, schemas, verdicts and call timings](output/judge_calls.jsonl)
- [Independent result audit](output/result_audit.json)
- [Execution log](full-campaign.log)
- [Model digest and runtime](runtime_manifest.json)
- [Frozen experimental protocol](PROTOCOL.md)

## Preserved execution repairs

The initial smoke exposed empty model answer content and truncated judge JSON; it remains in `smoke-output/`. Explicit `think=false` fixed the output-budget problem. The repaired smoke executed all nine metrics across the three strategies, before the full campaign began. Its answers took16–22seconds with retrieval below0.43seconds. Preflight source history is explained in `preflight_source_audit.json`; the full campaign captures its source hash at import and binds each metric to raw judge call IDs.

The CV implementation gaps are closed with measured evidence and documented limitations. Larger benchmarks, improved chunk metadata/scoring, independent judges and generator improvements belong to subsequent expansion; they were not introduced midway through this comparison.
