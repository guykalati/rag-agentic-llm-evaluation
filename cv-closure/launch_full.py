"""Start the finite full benchmark only after the repaired smoke has finished."""
import json,subprocess,sys,time
from pathlib import Path
p=Path(__file__).resolve().parent;deadline=time.monotonic()+600
while not (p/'smoke-fixed-output/result.json').exists():
    if time.monotonic()>deadline:raise TimeoutError('Smoke did not finish within launcher wait cap')
    time.sleep(2)
r=json.loads((p/'smoke-fixed-output/result.json').read_text())
assert r['status']=='completed' and r['smoke'] and r['rows']==3
assert all(m['valid_n']==m['total_n']==1 for strategy in r['summary'].values() for m in strategy['ragas'].values()),'Repair failed or undefined smoke metrics before full inference'
print('Repaired smoke passed all nine metric executions; starting frozen 36-row benchmark',flush=True)
subprocess.run([sys.executable,str(p/'evaluate.py'),'--output',str(p/'output'),'--cap-seconds','10800'],cwd=p,check=True,timeout=10830)
