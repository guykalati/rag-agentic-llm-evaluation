"""Freeze official Python docs and a pinned MiniLM dense index."""
import hashlib,json,time,urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
import numpy as np,torch
from sentence_transformers import SentenceTransformer
ROOT=Path(__file__).resolve().parent
MODEL='sentence-transformers/all-MiniLM-L6-v2'
REVISION='1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
    out=ROOT/'corpus';out.mkdir(exist_ok=False);chunks=[];sources=[];start=time.monotonic()
    for module in ['pathlib','json','subprocess','unittest','venv','logging','sqlite3','shutil']:
        url=f'https://docs.python.org/3.12/library/{module}.html'
        with urllib.request.urlopen(url,timeout=60) as response:raw=response.read()
        (out/(module+'.html')).write_bytes(raw)
        soup=BeautifulSoup(raw,'html.parser');body=soup.select_one('div.body');assert body
        for e in body.select('script,style'):e.decompose()
        text=body.get_text(' ',strip=True);words=text.split()
        for i in range(0,len(words),110):
            content=' '.join(words[i:i+140]);
            if len(content.split())<15:continue
            chunks.append({'id':f'{module}:{i:06d}','source_url':url,'module':module,'text':f'Python 3.12 {module} documentation. '+content,'start_word':i})
        sources.append({'url':url,'html_sha256':hashlib.sha256(raw).hexdigest(),'word_count':len(words),'license':'Python Software Foundation documentation license; see https://docs.python.org/3.12/license.html'})
    (out/'chunks.json').write_text(json.dumps(chunks,ensure_ascii=False,indent=2))
    torch.set_num_threads(2);model=SentenceTransformer(MODEL,revision=REVISION,cache_folder=str(ROOT/'cache'),device='cpu')
    embeddings=model.encode([c['text'] for c in chunks],normalize_embeddings=True,batch_size=32,show_progress_bar=True)
    np.save(out/'embeddings.npy',embeddings)
    manifest={'sources':sources,'chunks':len(chunks),'chunk_words':140,'stride_words':110,'embedding_model':MODEL,'embedding_revision':REVISION,'embedding_license':'Apache-2.0','embedding_shape':list(embeddings.shape),'embedding_max_seq_length':model.max_seq_length,'files_sha256':{p.name:digest(p) for p in out.iterdir() if p.is_file()},'source_sha256':digest(__file__),'index_build_seconds':time.monotonic()-start}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest),flush=True)
if __name__=='__main__':run()
