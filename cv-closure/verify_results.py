"""Audit RAG evidence against frozen inputs and actual raw judge verdicts."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify(out):
    r=json.loads((out/'result.json').read_text());rows=[json.loads(s) for s in (out/'rows.jsonl').read_text().splitlines()];calls={x['call']:x for x in map(json.loads,(out/'judge_calls.jsonl').read_text().splitlines())}
    assert r['status']=='completed' and not r['smoke'] and len(rows)==36
    questions={q['id']:q for q in json.loads((ROOT/'questions.json').read_text())['questions']};chunks={c['id']:c for c in json.loads((ROOT/'corpus/chunks.json').read_text())}
    assert {(x['id'],x['strategy']) for x in rows}=={(q,s) for q in questions for s in ['bm25','dense','hybrid']}
    assert r['sources_sha256']['evaluate.py']==sha(ROOT/'evaluate.py');assert r['sources_sha256']['questions.json']==sha(ROOT/'questions.json');assert r['sources_sha256']['manifest.json']==sha(ROOT/'corpus/manifest.json')
    manifest=json.loads((ROOT/'corpus/manifest.json').read_text())
    for n,h in manifest['files_sha256'].items():assert sha(ROOT/'corpus'/n)==h,n
    ordered_calls=[calls[i] for i in sorted(calls)]
    assert sorted(calls)==list(range(1,r['judge_calls']+1))
    for call in ordered_calls:
        assert hashlib.sha256(call['prompt'].encode()).hexdigest()==call['prompt_sha256']
    runtime=json.loads((ROOT/'runtime_manifest.json').read_text())
    assert runtime['full_campaign_source_sha256']==r['sources_sha256']['evaluate.py']
    assert runtime['questions_sha256']==r['sources_sha256']['questions.json']
    assert runtime['model']['name']==r['model'] and runtime['think']==r['think']==False
    checked=0;failures=[]
    for row in rows:
        assert row['question']==questions[row['id']]['question'] and row['reference']==questions[row['id']]['reference']
        assert len(row['contexts'])==3 and all(c==chunks[c['id']] for c in row['contexts'])
        assert row['response'].strip(),'No empty model answers allowed in a completed CV result'
        latency=row['latency']
        assert all(math.isfinite(x) and x>=0 for x in latency.values())
        assert latency['retrieval_seconds']>=latency['embedding_seconds']
        assert latency['query_to_answer_seconds']>=latency['generation_seconds']+latency['retrieval_seconds']
        for metric,m in row['ragas'].items():
            start,end=m['judge_call_range'];events=[calls[i] for i in range(start,end+1)]
            if m['status']!='ok':failures.append({'id':row['id'],'strategy':row['strategy'],'metric':metric,'status':m['status']});continue
            assert all(e['status']=='ok' for e in events)
            outputs=[json.loads(e['raw']) for e in events]
            if metric=='context_precision':
                verdicts=[o['verdict'] for o in outputs];positive=sum(verdicts);expected=sum(sum(verdicts[:i+1])/(i+1)*v for i,v in enumerate(verdicts))/(positive+1e-10)
            elif metric=='context_recall':
                verdicts=[o['attributed'] for o in outputs[-1]['classifications']];expected=sum(verdicts)/len(verdicts)
            elif metric=='faithfulness':
                verdicts=[o['verdict'] for o in outputs[-1]['statements']];expected=sum(verdicts)/len(verdicts)
            else:raise AssertionError(metric)
            assert math.isclose(expected,m['value'],abs_tol=1e-8),(row['id'],metric,expected,m['value']);checked+=1
    for strategy,s in r['summary'].items():
        selected=[x for x in rows if x['strategy']==strategy]
        for name,stats in s['latency'].items():
            times=[x['latency'][name] for x in selected]
            assert math.isclose(float(np.median(times)),stats['median_seconds'],abs_tol=1e-10)
            assert math.isclose(float(np.percentile(times,95)),stats['p95_seconds'],abs_tol=1e-10)
        for metric,m in s['ragas'].items():
            values=[x['ragas'][metric]['value'] for x in selected if x['ragas'][metric]['status']=='ok'];assert len(values)==m['valid_n']
            if values:assert math.isclose(float(np.mean(values)),m['mean'],abs_tol=1e-10)
    audit={'status':'passed','rows':len(rows),'metrics_recomputed_from_raw_judge_verdicts':checked,'raw_prompt_hashes_and_runtime_binding_verified':True,'latency_summaries_recomputed':True,'failures_or_undefined':failures,'result_sha256':sha(out/'result.json'),'limits':'Verifies provenance and calculations, not judge correctness. Judge false negatives need manual review.'}
    (out/'result_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'output');verify(p.parse_args().output)
