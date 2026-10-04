# Understanding the agent and RAG project

A study guide for Guy Kalati. This repository contains two evaluated systems: a bounded repository-repair agent and a documentation RAG benchmark. They share an interest in tool use and evidence, but the RAG results do not measure coding repair success.

## 1. The explanation you should start with

I built a Python controller that lets a language model inspect candidate code, edit it and request isolated tests. I also built a retrieval pipeline over Python documentation and compared keyword search, dense embeddings and a hybrid ranking. I saved the answers and raw evaluation verdicts so I could check both the scores and the mistakes behind them.

The repair trace demonstrates actual tool execution and a verified fix. The RAG comparison demonstrates retrieval and evaluation. Neither establishes a general autonomous coding success rate or reliable answer correctness.

**First exercise:** say what each system takes as input, what it can do, what it returns, and who verifies the result. Avoid library names until the flow is clear.

## 2. Foundations: model, agent, tool and RAG

A language model normally outputs text or structured messages. A **tool** is an application-defined function with an accepted input schema and an observable result. An **agent controller** repeatedly asks the model for an action, validates the request, executes an allowed tool and returns the observation to the model.

A tool-call message does not itself run code. The Python application owns execution and permissions. A model claiming a test passed is weaker evidence than a saved exit code from the test runner.

**ReAct** describes interleaving reasoning and actions, using observations to inform later actions. This implementation is ReAct-style through an observable tool loop. It does not reproduce the paper's benchmark or expose a faithful transcript of the model's internal reasoning. [ReAct paper](https://arxiv.org/abs/2210.03629).

**Retrieval augmented generation**, or RAG, first selects external text and then asks a model to answer using it. Retrieval changes the prompt, not the model weights. An answer can cite a source and still misread it. A retrieved passage can be accurate but describe the wrong API.

## 3. Walk through the coding controller

The candidate repository is a copy where edits are allowed. The controller supplies a task and four function schemas:

| Function | Purpose | Boundary |
|---|---|---|
| list_files | Discover readable candidate files | Gateway limits accessible files |
| read_file | Read a bounded line window | Path and range checks |
| replace_text | Make an exact implementation edit | Exactly one match required |
| run_test | Request target or regression test | Fixed stages, at most three model-requested calls |

The loop receives a model message. If it contains tool calls, the application validates them and dispatches sequentially. It stores arguments and observations, appends tool messages to the conversation, and asks the model again. A normal final message ends the loop. Budget exhaustion and transport errors produce explicit statuses.

The local Ollama mode has a 24-turn cap, a 900-second controller budget and a 20,000-token usage cap checked between turns. It uses `think=false`. This budget is not a hard interruption inside an already-running network call; transport timeouts also matter. The controller supports another API transport, but that capability is not evidence that every transport was used in the saved successful trace.

`replace_text` rejects absent or repeated matches. That makes edits inspectable and prevents an ambiguous replacement from changing unrelated locations. Malformed arguments, rejected paths and invalid stages return error observations. The model may use those observations to try another allowed action.

The gateway restricts candidate paths and implementation edits. The trusted evaluation bridge runs fixed tests in isolated CPU Slurm jobs with Bubblewrap. The model does not receive an unrestricted shell, cluster credential or network tool. These are application enforcement rules; a prompt saying "be safe" would not provide the same boundary.

## 4. What proves the agent worked?

The preserved PySnooper3 trace contains eight calls using all four tools. Independent final target and regression jobs both completed with exit 0. The final verifier reruns those checks after the model stops, independently of its written conclusion.

Eleven controller/gateway unit tests also pass. Those tests use controlled transports and evaluators to exercise error handling. They do not substitute for the real model-driven trace. Earlier repair attempts include failures, and retrieval-assisted repair benefit remains unproven.

A passing target test verifies the intended local behavior under that test. Regression tests reduce the chance of breaking covered behavior. Neither proves all possible behavior is correct. Small test suites can miss a wrong patch, and a model can overfit visible tests. Broader hidden tests and a larger task suite would support stronger claims.

[Agent code](../research-workbench/implementation/repair_agent.py) · [Gateway](../research-workbench/implementation/repair_gateway.py) · [Trace](../research-workbench/implementation/repair_agent_success_pysnooper3_2026-09-29.json) · [Independent trace audit](../cv-closure/agent_evidence_audit.json).

## 5. Build the RAG index from the source

The frozen corpus contains eight Python 3.12 documentation pages: pathlib, json, subprocess, unittest, venv, logging, sqlite3 and shutil. The index has 581 chunks from 63,575 words. Original HTML, source links and SHA256 hashes preserve the source snapshot.

The builder extracts body text and creates 140-word chunks with stride 110. Neighboring chunks overlap by 30 words before adding the module prefix. The last short chunk is discarded when it has fewer than 15 words. The chunk ID identifies module and start-word offset; it is not a semantic relevance label.

Word boundaries are simple to audit, but can cut through an API section or code example. Flattened HTML loses some hierarchy. One consequence is confusion between `subprocess.run` and `Popen.communicate`. Section-aware chunks are a proposed improvement, not the method used in this run.

Dense vectors come from pinned `sentence-transformers/all-MiniLM-L6-v2`. Each is a normalized 384-dimensional vector. The encoder is reused, not fine-tuned. It has a 256-token input limit, so a 140-word chunk plus metadata can still be truncated. The source word length and encoder token limit are different units. [Encoder model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).

## 6. Understand the three retrievers

**BM25** ranks chunks using word matches, document frequency and length-normalized term frequency. Exact API names can be useful signals. This implementation tokenizes case-folded text with a regular expression and uses rank-bm25's BM25 Okapi defaults. It does not train a lexical retriever.

A common form is:

<div class="formula">score(d,q) = Σ IDF(t) × tf(t,d)(k₁+1) / [tf(t,d)+k₁(1−b+b·|d|/avgdl)]</div>

Implementation details matter, including the package's handling of negative IDF values. The defaults are k₁=1.5 and b=0.75. High term overlap can rank a related but wrong API above the relevant section.

**Dense retrieval** encodes the query with the same MiniLM encoder and ranks the stored vectors by dot product. Since query and document vectors have unit length, dot product equals cosine similarity. Dense similarity can recover paraphrases, but does not guarantee precise API distinctions.

**Hybrid RRF** combines rankings rather than raw scores:

<div class="formula">RRF(d) = Σretrievers 1 / (60 + rankretriever(d))</div>

Ranks start at 1. A chunk ranked first in one list and tenth in the other scores 1/61+1/70≈0.03068. A chunk ranked third in both scores 2/63≈0.03175 and wins that example. RRF does not assume BM25 scores and cosine scores are comparable. The constant 60 and top 3 were frozen before evaluation.

All three methods return the top three chunks. Dense similarity uses exact matrix multiplication over 581 vectors. There is no vector database or approximate nearest-neighbor index. At this size, a plain NumPy matrix is sufficient. Large-scale indexing would introduce different memory and recall tradeoffs.

## 7. Generation and evaluation are separate calls

The answer model is cached Gemma 4 12B QAT served locally by Ollama. The prompt asks for at most three factual sentences using supplied documentation and chunk citations. Temperature 0, seed 20261003, context 8192 and output 192 tokens are fixed. Temperature 0 reduces sampling variation; it is not a proof of identical behavior across runtime or hardware changes.

The same model acts as a RAGAS judge. Native Ollama schema-constrained JSON implements the RAGAS LLM interface. The campaign uses the real RAGAS 0.4.3 ContextPrecision, ContextRecall and Faithfulness classes. Raw prompts, schemas, outputs, token counts and failures are saved. The answer and judge share weights, so their errors can correlate.

The first smoke failed: model thinking used the answer budget and the recall JSON truncated. Explicit `think=false` repaired execution before the full benchmark. Both original and repaired smoke outputs remain saved. The full campaign kept the repaired settings and performed no automatic retry that manufactured a score.

## 8. What each RAGAS score means

The selected **context precision** implementation asks the judge which ranked chunks are useful relative to the question/reference. It averages precision at ranks containing relevant chunks. If relevance verdicts are [1,0,1], the score is (1+2/3)/2≈0.8333. It is not simply two relevant chunks divided by three. [Context precision documentation](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/).

**Context recall** asks how many statements in the reference answer are attributable to the retrieved text. Three supported statements out of four give 0.75. It does not measure whether the generated answer includes those statements. The source-checked reference is an input, not a relevance hint given to retrieval. [Context recall documentation](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/).

**Faithfulness** decomposes the generated answer into statements and judges whether the retrieved contexts support them. Three supported statements out of four give 0.75. It does not establish that the answer addresses the question correctly. A faithful answer to the wrong API can be wrong for the task. [Faithfulness documentation](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/).

A successful metric call means a value was returned and parsed. It does not mean the verdict is correct. The independent audit recomputes the arithmetic from verdicts; it does not turn the judge into human gold. [RAGAS paper](https://arxiv.org/abs/2309.15217).

## 9. Design, results and latency

Twelve questions and references were checked against 13 source anchors before comparison. Every question is run with all three strategies, using the same corpus, generator and top 3 budget. That gives 36 cases and 108 metric executions, with 216 judge calls. All calls complete within the three-hour campaign cap; actual runtime is 2 h 4 m 46 s.

| Strategy | Context precision | Context recall | Faithfulness | Full answer median / p95 seconds |
|---|---:|---:|---:|---:|
| BM25 | 0.8194 | 0.9167 | 0.8611 | 21.392 / 24.702 |
| Dense | 0.7639 | 0.9583 | 0.8417 | 21.623 / 24.614 |
| Hybrid | 0.8889 | 0.9583 | 0.8681 | 21.029 / 24.547 |

Each metric includes all 12 cases for its strategy. There are no failed or undefined values to discard. Hybrid has the best observed precision and faithfulness and ties dense recall. With 12 questions and one shared judge, this does not prove statistical or general superiority.

Retrieval median/p95 seconds: BM25 0.046/0.056; dense 0.354/0.443; hybrid 0.343/0.452. Query embedding is included in retrieval. Full-answer time starts before retrieval and ends after uncached generation. Offline index/model initialization and RAGAS evaluation overhead are measured separately. Warm models and fixed strategy order limit a hardware latency comparison.

The old CV's "sub-second query latency" could describe retrieval only, but it cannot describe complete answers here. The measured 21-second latency should not be silently converted into a production response-time claim.

## 10. Learn the failures by their case IDs

**py312_05/BM25:** the question asks what `subprocess.run` does after a timeout. The retriever supplies `Popen.communicate` instructions. The answer says the child is not killed, which is wrong for `run`. Precision/recall are 0, while faithfulness is 1. The answer follows the wrong retrieved evidence.

**py312_12/BM25:** `Path.read_text` returns a string. The answer then names `json.load`, which accepts a file-like input, rather than `json.loads`. Faithfulness and recall both score 1. The composed interface is wrong even though both named functions exist. Dense omits the needed JSON function; hybrid names `JSONDecoder` without the requested usable handoff.

**py312_01/all strategies:** the correct mkdir options receive faithfulness 0 because the judge rejects "should use" wording. Another failure treats a valid chunk citation as an unsupported error code because RAGAS receives text without chunk IDs. Dense/hybrid unittest answers also merge test failures and errors while receiving faithfulness 1.

These cases justify a future evaluation repair: preserve chunk metadata, review extracted statements, add API/composition checks and calibrate judgments against independent annotations. They do not justify changing the completed scores. [Saved review](../cv-closure/judge_interpretation_review.json).

## 11. The autoresearch extension

A separate experiment loop follows the idea of a fixed training/evaluation contract with candidate proposals, finite budgets and a results ledger. The additional work includes history retrieval, candidate validation and independently reloaded checkpoint evaluation. It is inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch), not a claim to have invented that approach.

One completed eight-head TinyStories candidate scored 0.9169007335 validation bits per byte, worse than the same-seed incumbent 0.9121882524 (lower is better). The verified decision was to retain the incumbent. Proposal failures and duplicate/invalid outcomes remain in the record. There was no complete paired new-candidate training comparison proving history retrieval helps.

Bits per byte divides negative log probability in base 2 by source bytes, which helps compare compression quality across tokenizations when text/encoding are held fixed. It is a language-model metric, not coding-task accuracy. Do not mix this result into the documentation RAGAS table. [Completed experiment report](../research-workbench/AUTORESEARCH_STATEMENT_REPLAY_RESULT_2026-10-03.md).

## 12. Reproduce and navigate

From the repository root, `cd cv-closure`. Follow [README.md](../cv-closure/README.md) to create the isolated Python 3.12 environment from `environment.lock.txt`, acquire the pinned encoder cache, and run the cached local Ollama model. The frozen corpus/index are already included.

```sh
.venv/bin/python query.py 'How does Path.mkdir create missing parents?' --strategy hybrid
.venv/bin/python evaluate.py --output new-output --cap-seconds 10800
.venv/bin/python verify_results.py --output new-output
```

`prepare.py` builds sources/index; `evaluate.py` contains retrieval, generation, judging and timing; `query.py` calls the same retrieval/answer path without benchmark scoring. `output/rows.jsonl` binds each answer to contexts and scores. `judge_calls.jsonl` saves evidence for every verdict. `verify_results.py` checks inputs, arithmetic and timings. Rebuilding into an existing corpus/output directory is refused to protect previous evidence.

For controller tests, change to `research-workbench/implementation` and run `python3 -m unittest test_repair_agent test_repair_gateway`. Real repair execution additionally requires the candidate fixtures and the isolated cluster evaluation environment. Unit tests alone do not recreate the successful model trace.

## 13. Interview drill

<details><summary>Is the agent the same thing as the RAG system?</summary>

No. The agent chooses and executes restricted code tools. RAG retrieves text for documentation answers. They have separate evaluations. Connecting them later would require matched coding-task tests; the current RAG score does not prove better repair success.

</details>

<details><summary>Why use a controller instead of giving the model a shell?</summary>

The controller enforces paths, allowed edits, test stages and budgets. It makes actions inspectable and limits the tool surface. A shell would expose broader operations that the current task does not need. A prompt cannot enforce these restrictions by itself.

</details>

<details><summary>How do you handle malformed calls or repeated edits?</summary>

Validate function name and argument keys, reject unsafe inputs through the gateway and return explicit errors. Exact replacement requires one match. A failed call is an observation the model can react to, not permission to bypass the check.

</details>

<details><summary>How do you know a repair succeeded?</summary>

Read the target and regression exit codes from independently completed final jobs, plus the patch and trace. The model's final message is not the acceptance criterion. The preserved successful case has both exit 0 results, but a single case is not a general success rate.

</details>

<details><summary>What is an embedding, and did you train one?</summary>

It is a learned vector representation. I reused a pinned MiniLM encoder and built normalized chunk vectors. I did not fine-tune it. Cosine similarity ranks vector directions, not verified factual relevance.

</details>

<details><summary>Why hybrid ranking? Why not average the scores?</summary>

BM25 and dense search can retrieve different useful passages. Their scores have different scales. RRF combines positions in the ranked lists, using a fixed constant. The observed hybrid result is descriptive evidence, not a promise that hybrid always wins.

</details>

<details><summary>Why no vector database?</summary>

The index is 581×384. Exact NumPy ranking is simple and adequate. A larger corpus might need approximate search, persistence and incremental indexing. Those changes require recall, memory and latency checks rather than adding a database for its own sake.

</details>

<details><summary>Can faithfulness 1 mean the answer is wrong?</summary>

Yes. The timeout answer follows a passage about the wrong API. The JSON answer mixes incompatible interfaces. Faithfulness checks support in the supplied contexts, and the judge also makes errors. Task correctness needs a separate check.

</details>

<details><summary>Why do some correct answers score 0?</summary>

The judge rejects prescriptive "should" language despite correct API semantics. Statement extraction can also misread citations. I preserved the original verdicts and recorded concrete examples rather than adjusting scores to fit the old CV.

</details>

<details><summary>Is this reference-free evaluation?</summary>

That depends on the metric variant. The selected precision and recall calls use the source-checked reference. Faithfulness uses the generated response and contexts. The library's general description does not override the actual arguments used here.

</details>

<details><summary>Why use the same model for answers and judging?</summary>

It allowed local, finite evaluation with the available cached model. It introduces correlated errors and judge bias. An independent judge and reviewed annotations would test robustness. Those comparisons were not run.

</details>

<details><summary>What does subsecond mean in your results?</summary>

Retrieval, including query embedding, is below one second at the measured median/p95. Complete generated answers take about 21 seconds. RAGAS grading is additional offline evaluation time. I should specify which interval I measured.

</details>

<details><summary>How did you avoid tuning against the benchmark?</summary>

Freeze sources, questions/references, chunking, top 3, RRF constant and generation settings before the comparison. Repair the smoke execution before starting. Report all strategies and errors. Repeated future use of these 12 questions would make them development data, requiring a fresh test set.

</details>

<details><summary>How would you test retrieval independently of generation?</summary>

Use reviewed relevance labels to compute metrics such as recall@k or nDCG, and inspect wrong-API retrieval. Then evaluate answer correctness separately under the same retrieved contexts. This campaign uses model-judged reference metrics; it has no full human relevance annotation.

</details>

<details><summary>What would you cache? How would you measure the benefit?</summary>

Document embeddings are already precomputed. Query embeddings or results could be cached for repeated identical/versioned requests. The benchmark uses uncached answers. A cache evaluation must separate warm hits from misses and include invalidation when sources or models change.

</details>

<details><summary>How would you handle prompt injection in documents?</summary>

Treat retrieved text as data and keep tool permissions outside the prompt. The answer prompt states that boundary, but there is no adversarial injection benchmark here. For a connected agent, gateway restrictions and independent acceptance checks still need to hold if model behavior changes.

</details>

<details><summary>What is the original personal contribution?</summary>

The project began as joint coursework. The current successor adds bounded candidate tools, real isolated verification, source/version checks, the retrieval benchmark and raw-verdict auditing. I should distinguish reused models/libraries, team foundations and the new work I can explain. The extension used AI coding assistance.

</details>

<details><summary>Did autoresearch discover a better model?</summary>

The latest eight-head candidate was worse than the incumbent on the fixed validation bytes. The system correctly retained the incumbent. I can show a completed proposed experiment and rejection decision, but cannot claim history retrieval or autonomous search superiority.

</details>

<details><summary>What would you improve first for a user-facing system?</summary>

Fix API-aware chunk structure and missing metadata, add answer-composition tests, calibrate judge verdicts, then measure faster generation under a quality constraint. These are proposed experiments. A larger index alone would not fix the demonstrated load/loads error.

</details>

<details><summary>How would this change at a million chunks?</summary>

A million 384-dimensional float32 vectors require about 1.54 GB before index overhead. Exact scanning also scales with corpus size. I would evaluate approximate indexing, candidate reranking, versioned updates and concurrency, while measuring retrieval recall against an exact reference. These capabilities are not required or demonstrated by the 581-chunk run.

</details>

## 14. Whiteboard exercises and readiness check

1. Draw both paths: model→tool controller→isolated test→observation, and question→retriever→contexts→answer→judge.
2. Compute RRF for ranks 1/10 and 3/3. Explain why the latter wins.
3. Calculate average precision for relevance [0,1,1]. Answer: (1/2+2/3)/2≈0.5833.
4. Describe a case with high context recall and an incomplete answer. Use the JSON example.
5. A manager asks for subsecond responses. Explain what you measured, where generation dominates, and how to test a smaller model without sacrificing correctness.

You are ready when you can trace an action or answer to its raw evidence, derive the selected metrics, and explain at least one real failure in each system. For a question outside the measured scope, propose a test rather than inventing a result.
