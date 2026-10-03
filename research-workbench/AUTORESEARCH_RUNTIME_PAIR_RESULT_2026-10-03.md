# Runtime-feedback continuation — repairs verified, candidate submitted

The first frozen runtime pair used two local generation calls. Both outputs were statically valid but reproduced the already completed feed-forward1920 and six-layer source hashes. No GPU was spent on them. Prompt inspection found that keyword selection supplied11older records from the17record index and omitted every paired runtime result.

The second, separately frozen campaign supplied the complete bounded17record read-only snapshot. Four calls exhausted its finite ledger:the no-history arm repeated the same two completed candidates;the memory arm twice proposed eight attention heads but failed exact string matching because the original assignment was line-wrapped. All four original invalid outcomes and raw requests/responses remain recorded. No benefit of training or retrieval was measured by those failures.

Two repairs passed five tests:complete-history selection includes feedback missed by keyword search while preserving no-history isolation and a17record cap;the source edit gate can resolve a unique identical complete AST statement when only whitespace differs, while wrong-source/ambiguous/protected-code changes remain rejected. Existing numeric edit, evaluator protection and attention divisibility checks remain in force.

A separately reported saved-response replay recovers one unique candidate from the two memory proposals:four layers,width384,feed-forward1536,**eight heads**,7,295,232parameters. It uses zero new generation calls. Request inspection confirms17history records including all four paired runtime entries. The original failures are not relabeled.

**Slurm job22001602 submitted:**one candidate only,1200second training budget/22minute allocation cap, no requeue/restart; protected existing TinyStories data/evaluator, restricted Bubblewrap and independent checkpoint verification. Candidate SHA-256:`09009f8379bc211c415bf72b867a9ef0ec908b40a135e6a4dd50ad7df15fd53e`. Results are pending. No no-history candidate is eligible, so this cannot establish paired retrieval superiority even if it improves the historical incumbent. Original experiment ledgers remain exhausted and unchanged.

[History-selection repair](AUTORESEARCH_RUNTIME_PAIR_REPAIR_2026-10-03.md) · [Saved-response protocol](AUTORESEARCH_STATEMENT_REPLAY_PROTOCOL_2026-10-03.md) · [Replay audit](implementation/runtime_statement_replay_audit_2026-10-03.json) · [GPU manifest](implementation/runtime_statement_gpu_manifest_2026-10-03.json).
