"""Audit retrieval anchor coverage and citation IDs without an LLM judge."""
import argparse,hashlib,json,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text):
    return ' '.join(text.casefold().split())

def anchor_coverage(evidence, contexts):
    return [any(c['source_url']==e['source_url'] and normalize(e['anchor_phrase']) in normalize(c['text']) for c in contexts) for e in evidence]

def citation_ids(response):
    # Only chunk-shaped identifiers inside square brackets count as citations.
    return sorted({m for group in re.findall(r'\[([^]\n]+)\]',response) for m in re.findall(r'\b[a-z_]+:\d{6}\b',group)})

def analyze():
    paths=[ROOT/'questions.json',ROOT/'corpus/chunks.json',ROOT/'output/rows.jsonl']
    questions={q['id']:q for q in read(paths[0])['questions']};chunks={c['id']:c for c in read(paths[1])}
    rows=[json.loads(line) for line in paths[2].read_text().splitlines()];diagnostics=[]
    assert len(rows)==36 and len({(r['id'],r['strategy']) for r in rows})==36
    for row in rows:
        q=questions[row['id']];contexts=row['contexts']
        for c in contexts:assert c==chunks[c['id']]
        evidence=q.get('evidence_sources') or [q]
        covered=anchor_coverage(evidence,contexts);cited=citation_ids(row['response']);allowed={c['id'] for c in contexts}
        # Boundary-spanning anchors cannot be recovered whole by the frozen chunker.
        index_available=anchor_coverage(evidence,list(chunks.values()))
        diagnostics.append({'id':row['id'],'strategy':row['strategy'],'required_anchors':len(evidence),'anchors_present_in_index':sum(index_available),'anchors_found_at_3':sum(covered),'all_anchors_found_at_3':all(covered),'cited_ids':cited,'unknown_or_unretrieved_ids':sorted(set(cited)-allowed),'has_valid_citation':bool(set(cited)&allowed)})
    summary={}
    for strategy in ['bm25','dense','hybrid']:
        cases=[r for r in diagnostics if r['strategy']==strategy]
        summary[strategy]={'questions':len(cases),'anchor_hits':sum(r['anchors_found_at_3'] for r in cases),'required_anchors':sum(r['required_anchors'] for r in cases),'questions_with_all_anchors_at_3':sum(r['all_anchors_found_at_3'] for r in cases),'answers_with_valid_citation':sum(r['has_valid_citation'] for r in cases),'answers_with_unknown_or_unretrieved_id':sum(bool(r['unknown_or_unretrieved_ids']) for r in cases)}
    return {'kind':'deterministic_retrieval_and_citation_diagnostics','inputs':{str(p.relative_to(ROOT)):digest(p) for p in paths},'script_sha256':digest(Path(__file__)),'summary':summary,'cases':diagnostics,
            'limits':['Exact source/phrase coverage is a retrieval diagnostic, not semantic relevance or answer correctness.','Citation existence does not establish that the cited passage entails the answer.','The 12 original questions are development evidence; this is not a new benchmark or an independent model judge.','Frozen RAGAS scores and original answers are unchanged.']}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'output/analysis.json');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    report=analyze()
    if args.check:
        assert read(args.output)==report,'Saved derived analysis differs; regenerate explicitly after reviewing source/input changes.'
    else:
        args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['cases','paired_questions','inputs']},indent=2))
