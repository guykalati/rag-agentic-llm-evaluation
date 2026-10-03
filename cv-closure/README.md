# Coding agent and real RAG evaluation

## What is implemented

The coding controller already has real multi-step model traces: list/read files, apply an exact edit, execute an isolated target test, and independently verify target plus regression tests. The preserved PySnooper3 trace passes both checks. Eleven existing controller/gateway tests passed again during CV closure. Evidence is in `agent_evidence_audit.json`, `agent_unit_audit.json`, and `../research-workbench/implementation/repair_agent_success_pysnooper3_2026-09-29.json`. The real agent is in `../research-workbench/implementation/repair_agent.py`; isolated Slurm execution is in `repair_eval_bridge.py` and `run_repair_candidate_eval.sbatch` beside it. The earlier four-attempt report includes unsuccessful cases and does not establish a retrieval benefit for coding repairs.

The missing RAG component is now executable: eight official Python documentation snapshots, 581 chunks, actual pinned MiniLM embeddings, BM25/dense/hybrid retrieval, cited local-model answers, and the real RAGAS ContextPrecision, ContextRecall and Faithfulness classes. Twelve source-checked references and 13 evidence anchors are frozen before evaluation. The retrieval benchmark is separate from the coding repair benchmark; it does not prove that RAG improves repair success.

## Reproduce

Python3.12; install `environment.lock.txt` in an isolated environment. The initial unconstrained dependency install failed because current LangChain removed a RAGAS import; compatible versions are pinned in the lock, and `dependency_audit.txt` confirms no broken requirements. Local Ollama with the cached model in `runtime_manifest.json` must run at127.0.0.1:11434.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r environment.lock.txt
# Corpus/embeddings are already frozen in Git. Acquire the pinned encoder cache:
# Run prepare.py in a clean copy without corpus/ to rebuild the whole index.
.venv/bin/python query.py 'How does Path.mkdir create missing parents?' --strategy hybrid
.venv/bin/python evaluate.py --output new-output --cap-seconds 10800
.venv/bin/python verify_results.py --output new-output
```

The encoder cache is excluded from Git. For a fresh clone with the included corpus, download `sentence-transformers/all-MiniLM-L6-v2` at revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41 into `cache/` using SentenceTransformer with the same revision/cache_folder arguments as `prepare.py`, then use the frozen index. Corpus rebuilding requires network access; answer/judge inference is local. Source licenses and attribution are in `SOURCE_CREDITS.md`.

## Current execution status

The initial smoke run exposed empty model answer content and truncated judge JSON. It is preserved in `smoke-output/`. Explicit `think=false` fixed the output-budget problem; the repaired smoke executed all nine metrics across the three retrieval strategies. Its answers took16–22seconds, with retrieval below0.43seconds. The full **12questions ×3strategies** campaign has started under a three-hour cap; final scores are pending. No original CV RAGAS numbers or subsecond end-to-end latency are asserted by this work.

The repaired smoke's faithfulness judge incorrectly rejected advice about documented behavior because the documentation describes behavior rather than saying a script “should” use it. Raw verdicts are preserved. This is a concrete judge false negative; numerical faithfulness scores need manual interpretation. The full benchmark keeps the same model/prompt/metric settings and reports all failures or undefined scores. Do not select examples to recover the old0.95score.

Preflight source history is explained in `preflight_source_audit.json`; the full campaign captures its source hash at import time and binds each metric to raw judge call IDs. `verify_results.py` independently recomputes successful metric values from judge verdicts and checks frozen question/context provenance. It validates calculations, not judge correctness.
