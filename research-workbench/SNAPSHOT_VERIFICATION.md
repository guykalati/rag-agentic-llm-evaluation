# Snapshot verification — 3 October 2026

- Every exported source file matches its recorded SHA-256.
- All copied Python sources parse.
- Existing foundation suite: 14 tests passed in this checkout.
- Agent checkout: another 14 existing proposer/gateway/controller tests passed with mocked model responses. No live proposal or training occurred.
- Credential-pattern scan found no matching private-key or supported token patterns.
- Raw data directories, weights, virtual environments, caches, and SQLite indexes are excluded.

These checks verify packaging and existing local controls. They do not rerun historical GPU experiments or establish scientific model quality.

Historical logs and copied documents retain their original whitespace to preserve source hashes.
