# Decisions and evidence

Reviewed 17 October 2026. Historical protocols and results remain unchanged. A successful engineering check does not establish that a model is scientifically adequate.

## 1. Use a gateway with restricted file and test tools

**Decision/status:** Implemented.

The controller enforces exact edits, candidate paths and fixed tests; prompts alone do not enforce permissions.

[Evidence](research-workbench/implementation/repair_gateway.py)

## 2. Verify repairs after the model stops

**Decision/status:** Completed trace retained.

Independent target and regression checks are stronger evidence than a model claiming success. One trace is not a general solve rate.

[Evidence](cv-closure/agent_evidence_audit.json)

## 3. Compare BM25, dense and fixed RRF at identical top 3

**Decision/status:** Completed.

The corpus, answer model and context count remain fixed; raw sparse/dense scores are not directly averaged.

[Evidence](cv-closure/PROTOCOL.md)

## 4. Keep raw RAGAS verdicts and every observed failure

**Decision/status:** Preserved and recomputed.

A score is reproducible only when its inputs and judge decisions can be inspected.

[Evidence](cv-closure/output/judge_calls.jsonl)

## 5. Measure retrieval and complete-answer latency separately

**Decision/status:** Measured; scope corrected.

Hybrid median retrieval is 0.343 s; complete answers take 21.03 s. The old sub-second end-to-end claim is unsupported.

[Evidence](cv-closure/output/result.json)

## 6. Add exact anchor/citation diagnostics without changing scores

**Decision/status:** Implemented 17 October.

These checks catch missing source phrases and invalid chunk IDs without sharing the answer model judge. They are not semantic correctness judgments.

[Evidence](cv-closure/output/analysis.json)

## 7. Use Karpathy-inspired fixed experiment contracts

**Decision/status:** Implemented bounded adaptation.

Protected evaluation, finite budgets and a results ledger limit what proposals may change; the upstream concept remains attributed.

[Evidence](research-workbench/AUTORESEARCH_FIRST_RUN_PROTOCOL_2026-09-29.md)

## 8. Retain the TinyStories incumbent

**Decision/status:** Candidate rejected; incumbent retained.

The eight-head candidate scored worse, and there was no completed new paired training comparison proving retrieval benefit.

[Evidence](research-workbench/AUTORESEARCH_STATEMENT_REPLAY_RESULT_2026-10-03.md)

