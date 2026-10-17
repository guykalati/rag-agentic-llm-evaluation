"""Verify saved project evidence, offline tests and page links; no model or network calls."""
import argparse,hashlib,json,subprocess,sys,tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parent
MODULES={
    'sherlock-llm-finetuning-lora':['test_scope_output_gate'],
    'rag-agentic-llm-evaluation':['test_repair_agent','test_repair_gateway','test_experiment_proposer'],
    'realtime-ecg-arrhythmia-classification':['test_ecg_waveform_transform'],
}
class Links(HTMLParser):
    def __init__(self,path):
        super().__init__();self.ids=[];self.links=[];self.scripts=[];self.in_script=False;self.feed(path.read_text())
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if tag=='script':self.in_script=True
    def handle_endtag(self,tag):
        if tag=='script':self.in_script=False

def pages():
    count=0
    for path in [ROOT/'showcase/index.html',ROOT/'showcase/guide.html']:
        doc=Links(path);assert len(doc.ids)==len(set(doc.ids)),f'duplicate HTML id: {path}'
        for href in doc.links:
            u=urlsplit(href)
            if u.scheme:
                prefix=f'https://github.com/guykalati/{ROOT.name}/blob/codex/project-review-2026-10-17/'
                if href.startswith(prefix):assert (ROOT/unquote(href[len(prefix):].split('#')[0])).is_file(),href
                continue
            target=path.parent/unquote(u.path) if u.path else path
            assert target.is_file(),href
            if u.fragment:assert unquote(u.fragment) in Links(target).ids,href
        count+=1
    return count

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path);args=parser.parse_args()
    def run(command,cwd=ROOT):
        result=subprocess.run([sys.executable,*command],cwd=cwd,text=True,capture_output=True)
        if result.returncode:raise RuntimeError(' '.join(command)+'\n'+result.stdout+'\n'+result.stderr)
        return result.stdout+result.stderr
    with tempfile.TemporaryDirectory() as temp:
        evidence=Path(temp)/'evidence.json'
        run(['cv-closure/verify_results.py','--report',str(evidence)])
        run(['cv-closure/analyze_results.py','--check'])
        tests=run(['-m','unittest','discover','-s','cv-closure','-p','test_analysis.py'])
        tests+=run(['-m','unittest',*MODULES[ROOT.name]],ROOT/'research-workbench/implementation')
        report={'status':'passed','repository':ROOT.name,'saved_evidence':json.loads(evidence.read_text()),'derived_analysis_matches_saved_report':True,'offline_tests':tests.strip(),'landing_and_guide_link_checks':pages(),'network_or_training_calls':False,'limits':'Verifies existing artifacts and implementation contracts; it does not rerun model training or establish scientific adequacy.'}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        with args.report.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
