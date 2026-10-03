# Runtime history selection repair

The first new pair generated two statically valid proposals in two local calls: feed-forward 1920 (no history) and six layers (memory). Both source hashes exactly matched earlier completed development candidates. No GPU run followed. Original manifests, prompts, responses and ledger remain intact.

Inspection found the frozen 17-record index was queried with `larger learning rate cosine` and limited to 11 matches. The actual 11 supplied records omitted all four paired runtime records, including the completed six-layer and wider-feed-forward failures. This is a selection defect, not evidence that correctly supplied runtime feedback failed.

Repair: use the whole explicitly bounded read-only 17-record development snapshot, ordered deterministically. Fail if the index exceeds 17 records. Keep no-history isolation. Four tests passed, including a fixture where keyword search misses the newest feedback and the complete snapshot includes it, plus an over-cap rejection. No claim of retrieval ranking quality follows; the next comparison tests development-memory context.

## Fresh finite v2 protocol

Same incumbent, protected source/evaluator, cached local model/digest, matched temperature0.3 and seed20261003, training seed20260929, fixed TinyStories files and prior 20-minute protocol. One pair, maximum two calls per arm (four total),300-second request cap, no transport retries. Freeze successful prior source hashes before sampling; duplicate proposals count as invalid outcomes and receive at most the second predeclared attempt, never GPU time. At most20M parameters per accepted candidate to fit the250MB output ceiling. Neither arm sees its peer's new proposals or results.

At most two22-minute GPU allocations (44 GPU-minutes), 1200 training seconds each, no requeue/restart, concurrency at most two. Only nonduplicate statically accepted code enters the existing Bubblewrap no-network read-only-data execution and independent checkpoint verification. Old ledgers stay exhausted; the unused GPU allowance of the first runtime pair is not spent on duplicate candidates. Generation waits for the article continuation and runs sequentially on the local model server. Report all sampled attempts and any missing/failed arm; one pair cannot establish general memory superiority.
