"""Query the frozen documentation corpus using the same evaluated RAG path."""
import argparse,json,time
from evaluate import Retriever,answer
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('question');p.add_argument('--strategy',choices=['bm25','dense','hybrid'],default='hybrid');a=p.parse_args()
    r=Retriever();start=time.perf_counter();contexts,latency=r.retrieve(a.question,a.strategy);begin=time.perf_counter();response,generation=answer(a.question,contexts)
    latency['generation_seconds']=time.perf_counter()-begin;latency['query_to_answer_seconds']=time.perf_counter()-start
    print(json.dumps({'question':a.question,'strategy':a.strategy,'response':response,'contexts':contexts,'latency':latency,'generation':generation},indent=2))
