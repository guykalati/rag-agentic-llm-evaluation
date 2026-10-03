"""Audit retrieved candidate and record its bounded keep/discard decision."""
import hashlib
import json
from pathlib import Path
from experiment_ledger import record, records, summary

BASE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    root=BASE/'data/agent_pilot_retrieved_20260930'
    local=BASE/'autoresearch_agent_pilot_20260930'
    manifest=json.loads((root/'batch_manifest.json').read_text())
    assert sha(root/'batch_manifest.json')==sha(local/'batch_manifest.json')
    for name,digest in manifest['source_sha256'].items():assert sha(root/name)==digest
    for split in ['train','val']:
        assert sha(root/'data'/f'{split}.bin')==manifest['fixed_data'][split+'_sha256']
    cell=manifest['cells'][0]
    out=root/Path(cell['candidate_file']).parent/'output'
    result=json.loads((out/'result.json').read_text())
    verified=json.loads((out/'verified.json').read_text())
    assert result['status']=='success' and verified['verified'] is True
    assert sha(root/cell['candidate_file'])==sha(local/cell['candidate_file'])==cell['train_sha256']==result['train_sha256']
    assert sha(out/'model.pt')==result['checkpoint_sha256']==verified['checkpoint_sha256']
    assert sha(root/'prepare.py')==manifest['prepare_sha256']==result['prepare_sha256']
    assert sha(root/'data/data_manifest.json')==manifest['data_manifest_sha256']==result['data_manifest_sha256']
    assert result['seed']==20260929 and 1200<=result['training_seconds']<=1210
    assert result['validation_bytes_scored']==verified['validation_bytes_scored']==2097152
    assert abs(result['val_bpb']-verified['independent_val_bpb'])<1e-5
    reference=json.loads((BASE/'data/longruns_20260930/language_model/cells/larger_20260929/output/result.json').read_text())
    assert reference['seed']==result['seed'] and reference['data_manifest_sha256']==result['data_manifest_sha256']
    assert reference['prepare_sha256']==result['prepare_sha256']
    assert reference['val_bpb']==0.9121882523777711
    keep=result['val_bpb']<reference['val_bpb']
    proposal=json.loads((BASE/'data/agent_pilot_20260930/proposal_2/proposal.json').read_text())
    ledger=records(local)
    if len(ledger)==1:
        record(local,{'status':'success','metric_value':result['val_bpb'],'training_seconds':result['training_seconds'],
                      'candidate_file':cell['candidate_file'],'hypothesis':proposal['hypothesis'],
                      'notes':f'Independently verified. Decision: {"keep" if keep else "discard"}; frozen same-seed reference {reference["val_bpb"]}. Width480 candidate, not unchanged larger reference despite inherited configuration label. Memory benefit unmeasured.'})
    ledger=records(local)
    assert len(ledger)==2 and ledger[1]['train_sha256']==result['train_sha256']
    audit={'status':'passed','job':21894420,'candidate_id':cell['id'],'candidate':result,
           'independent_verifier':verified,'reference_val_bpb':reference['val_bpb'],
           'delta_bpb':result['val_bpb']-reference['val_bpb'],'decision':'keep' if keep else 'discard',
           'ledger':summary(local),'gpu_allocation_seconds':1219,
           'limits':'Single adaptive development seed. Independent scoring by pinned GPU verifier; local audit checks records and hashes. Retrieval benefit unmeasured. Failed first architecture consumed zero GPU allocation.'}
    (BASE/'agent_pilot_audit_2026-09-30.json').write_text(json.dumps(audit,indent=2)+'\n')
    (BASE/'agent_pilot_retrieval_hashes_2026-09-30.json').write_text(json.dumps({str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()},indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ['status','reference_val_bpb','delta_bpb','decision','ledger']},indent=2))

if __name__=='__main__':run()
