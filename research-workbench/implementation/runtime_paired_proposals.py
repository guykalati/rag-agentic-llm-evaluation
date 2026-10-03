"""Run only the frozen, finite local proposal stage; never execute proposals."""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from experiment_proposer import propose


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root):
    manifest = json.loads((root / 'proposal_manifest.json').read_text())
    assert manifest['max_attempts_per_arm'] == 2 and manifest['seeds'] == [20261003]
    for name, expected in manifest['hashes'].items():
        assert digest(root / name) == expected, name
    # Check the service before spending proposal attempts.
    with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=10) as response:
        tags = json.load(response)
    assert any(m['name'] == manifest['model'] and m['digest'] == manifest['model_digest']
               for m in tags['models']), 'frozen local model unavailable'
    ledger = root / 'proposal_results.jsonl'
    if ledger.exists():
        raise FileExistsError('Already started; do not replay the finite campaign')
    ledger.touch(exist_ok=False)
    for pair, seed in enumerate(manifest['seeds']):
        arms = ['no_history', 'retrieval'] if pair == 0 else ['retrieval', 'no_history']
        for arm in arms:
            for attempt in range(2):
                name = f'pair{pair + 1}_{arm}_attempt{attempt + 1}'
                output = root / name
                row = {'id': name, 'pair': pair + 1, 'arm': arm, 'attempt': attempt + 1,
                       'proposal_seed': seed + attempt * 10000, 'status': 'invalid'}
                started = time.monotonic()
                try:
                    propose(root / 'incumbent.py', root / 'memory.sqlite', output,
                            retrieval=arm == 'retrieval', seed=row['proposal_seed'],
                            temperature=manifest['temperature'])
                    assert digest(output / 'train.py') != manifest['hashes']['incumbent.py'], 'unchanged incumbent'
                    row.update(status='valid', candidate_sha256=digest(output / 'train.py'))
                except urllib.error.URLError:
                    # Infrastructure outages require inspection, never a rapid retry loop.
                    raise
                except Exception as error:
                    row['failure_reason'] = f'{type(error).__name__}: {error}'
                row['elapsed_seconds'] = time.monotonic() - started
                with ledger.open('a') as handle:
                    handle.write(json.dumps(row) + '\n')
                print(json.dumps(row), flush=True)
                if row['status'] == 'valid':
                    break
    rows = [json.loads(line) for line in ledger.read_text().splitlines()]
    summary = {'status': 'complete', 'attempts': len(rows),
               'valid_candidates': sum(r['status'] == 'valid' for r in rows),
               'training_runs': 0, 'retrieval_benefit': 'unmeasured'}
    (root / 'proposal_summary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    run(parser.parse_args().root)
