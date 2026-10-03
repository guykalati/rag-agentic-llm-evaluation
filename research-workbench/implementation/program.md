# Bounded agent program for the new personal project

This is the project's instruction surface, following the role of `program.md` in [Karpathy's autoresearch](https://github.com/karpathy/autoresearch). It defines controls for bounded runs; it does not authorize a new batch by itself.

## Before either mode

1. Read the approved task and its evaluation contract. Record the source repository commit and an isolated worktree/container path. Never edit the old team assignment directly.
2. Fix the task set or dataset split, evaluation code, primary metric, cost ceiling, and run count **before** seeing candidate results. Ask Guy to approve that exact batch.
3. Keep hidden tests and final holdout labels outside the agent's searchable files. Index only the repository files and training/validation history approved for the batch.

## Repair mode

1. Read the issue and retrieve likely source, tests, and documentation with `repo_evidence.py`.
2. Propose one small patch in an isolated checkout. Preserve the original issue text and candidate diff.
3. Run the fixed visible test command in a container with no network or cluster credentials. Capture exit code, logs, time, and changed files.
4. Keep a patch only if the frozen evaluator says the issue is resolved and no existing tests regress. A final held-out task set is run after development, not used to guide each patch.
5. Record source citations, tool calls, failures, and the final patch for review. Compare a retrieval-enabled run with the same agent and budget without retrieval.

## Experiment mode

1. Use a project with immutable `prepare.py` and data manifest, one editable `train.py`, and a metric produced by `prepare.py`. This is the [autoresearch](https://github.com/karpathy/autoresearch) separation of evaluation from candidate training code.
2. Initialize `experiment_ledger.py` with the approved metric, direction, run count, and per-run training time. Run the unchanged baseline first.
3. For each candidate, state one hypothesis, change only `train.py`, run within the approved isolation and time limit, and save its output. Record success or failure and the measured metric. Never use `git reset` on a user checkout to discard a candidate.
4. A better single validation score is a candidate, not a confirmed discovery. Re-run the winner with the agreed seeds, compare variation, and open the held-out test only after selection.
5. Index only explicitly approved *development* experiment directories with `experiment_memory.py`. Search earlier hypotheses, failures, and notes before proposing a new candidate, then measure whether this retrieval improves useful progress against a no-retrieval control.

The current `experiment_proposer.py` profile allows only declared numeric architecture literals (width≤1024, attention heads≤16, feed-forward width≤4096, layers≤12, dropout≤.9) and literal AdamW hyperparameters. Model-forward behavior, imports, data, seed, time, preparation, evaluator and provenance are fixed. Width must be divisible by heads. This deliberately narrower profile differs from unrestricted upstream training-file editing. Static rejection consumes a candidate attempt; preserve the proposed source and failure. A different editable interface needs its own concrete frozen contract.

Stop when the approved budget or run count is exhausted. Do not expand the dataset, model family, method, split, or cost ceiling without a new concrete proposal.
