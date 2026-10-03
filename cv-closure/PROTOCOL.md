# CV closure: retrieval and RAGAS

Frozen before inference on 2026-10-03. Official Python 3.12 documentation snapshots for pathlib/json/subprocess/unittest/venv/logging/sqlite3/shutil. Preserve source URLs and HTML hashes. 140 word chunks, 110 word stride. Dense encoder all-MiniLM-L6-v2, pinned revision1110a243fdf4706b3f48f1d95db1a4f5529b4d41, normalized embeddings, CPU. Some chunks may exceed the encoder's 256 token limit; record the limit and disclose truncation. Compare BM25, cosine dense, and fixed reciprocal rank fusion k60, at identical top3. No relevance labels enter retrieval.

Twelve independently source-checked questions and references are frozen before comparison. Cached Gemma4 12B QAT for answer and judge, temperature0, seed20261003, context8192. Answers192 output tokens, real RAGAS0.4.3 collections ContextPrecision/ContextRecall/Faithfulness with schema-constrained native Ollama outputs,1024 output tokens per judge call. Log raw judge outputs and every failure/undefined score. No retry/repair fabricates a verdict. First smoke query across three strategies verifies execution only; a fresh full campaign retains all12questions×3strategies. Three-hour finite local cap,420second per HTTP call. No paid/external inference.

Measure query embedding, retrieval, generation, complete query-to-answer time and offline startup separately. Uncached answers. RAGAS evaluation overhead is excluded from application query latency and recorded separately. Report measured median/p95; subsecond retrieval is not subsecond end-to-end latency. Metrics describe this small documentation benchmark and shared local judge, not general answer correctness.

## Preflight repair before full benchmark

The first smoke campaign exposed empty answer content: default thinking consumed the192output-token budget, and recall JSON truncated at1024tokens. Preserve all smoke failures. Set explicit `think=false` for both answer and judge, as supported by Ollama thinking controls (https://docs.ollama.com/capabilities/thinking). This is an execution repair before the full benchmark; references, retrieval and metric logic remain frozen. Recheck the same smoke query in a fresh output folder.
