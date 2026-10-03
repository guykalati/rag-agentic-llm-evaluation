import unittest
from pathlib import Path
from experiment_proposer import apply_proposal,architecture_check,parameter_profile

class ProposalChecks(unittest.TestCase):
    def test_wrapped_statement_edit_keeps_protected_boundaries(self):
        source=(Path(__file__).parent/'autoresearch_longrun_20260929/cells/larger_20260929/train.py').read_text()
        old='layer = nn.TransformerEncoderLayer(width, 6, 1536, dropout=0.0, batch_first=True, norm_first=True)'
        proposal={'hypothesis':'head count','edits':[{'old':old,'new':old.replace('width, 6,','width, 8,')}]}
        candidate=apply_proposal(source,proposal);self.assertEqual(architecture_check(candidate)['heads'],8)
        bad={'hypothesis':'wrong source','edits':[{'old':old.replace('1536','2000'),'new':old}]}
        with self.assertRaises(ValueError):apply_proposal(source,bad)
        protected='score = validation_bpb(model, val, device)'
        with self.assertRaises(ValueError):apply_proposal(source,{'hypothesis':'cheat','edits':[{'old':protected,'new':'score = {"val_bpb": 0}'}]})

    def test_parameter_profile_matches_completed_torch_models(self):
        source=(Path(__file__).parent/'autoresearch_longrun_20260929/cells/larger_20260929/train.py').read_text()
        self.assertEqual(parameter_profile(source)['parameter_count'],7295232)
        for old,new,expected in [('6, 1536','6, 1920',8476416),('layer, 4','layer, 6',10844160)]:
            candidate=apply_proposal(source,{'hypothesis':'count check','edits':[{'old':old,'new':new}]})
            self.assertEqual(parameter_profile(candidate)['parameter_count'],expected)
    def test_candidate_boundaries_and_attention_divisibility(self):
        source=(Path(__file__).parent/'autoresearch_longrun_20260929/cells/larger_20260929/train.py').read_text()
        valid=apply_proposal(source,{'hypothesis':'capacity','edits':[{'old':'width = 384','new':'width = 480'}]})
        self.assertEqual(architecture_check(valid),{'width':480,'heads':6,'head_dimension':80})
        apply_proposal(source,{'hypothesis':'optimizer','edits':[{'old':'lr=3e-4','new':'lr=2e-4'}]})
        bad=apply_proposal(source,{'hypothesis':'invalid capacity','edits':[{'old':'width = 384','new':'width = 512'}]})
        with self.assertRaises(ValueError):architecture_check(bad)
        for old,new in [('score = validation_bpb(model, val, device)','score = {"val_bpb": 0}'),('SEED = 20260929','SEED = 1'),('lr=3e-4','lr=__import__("os").system("id")'),
                        ('length = x.shape[1]','length = torch.from_file("/work/data/val.bin").numel()'),
                        ('width = 384','width = 8192'),
                        ('return self.head(self.norm(self.blocks(h, mask=self.mask[:length, :length])))','return torch.zeros((*x.shape, 256), device=x.device)')]:
            with self.assertRaises(ValueError):apply_proposal(source,{'hypothesis':'invalid edit','edits':[{'old':old,'new':new}]})

class HistoryBoundaryChecks(unittest.TestCase):
    def test_snapshot_keeps_feedback_without_query_keywords(self):
        import tempfile
        from experiment_memory import build_index,read_snapshot,search
        import json
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);ledger=root/'dev.jsonl';db=root/'memory.sqlite'
            rows=[{'run':i,'status':'success','metric_value':1,'train_sha256':str(i),'notes':('larger learning rate' if i<13 else '24123optimizer steps; no improvement')} for i in range(17)]
            ledger.write_text(''.join(json.dumps(r)+'\n' for r in rows));build_index([ledger],db)
            self.assertEqual(len(search(db,'larger learning rate',limit=17)),13)
            self.assertEqual({r['run'] for r in read_snapshot(db)},set(range(17)))
            ledger.write_text(ledger.read_text()+json.dumps({**rows[-1],'run':17})+'\n');build_index([ledger],db)
            with self.assertRaises(ValueError):read_snapshot(db)

    def test_no_history_never_opens_index_and_freezes_sampling(self):
        import json,tempfile
        from io import BytesIO
        from unittest.mock import patch
        from experiment_proposer import propose,MODEL,DIGEST
        source=Path(__file__).parent/'autoresearch_longrun_20260929/cells/larger_20260929/train.py'
        response={'message':{'content':json.dumps({'hypothesis':'optimizer test','edits':[{'old':'lr=3e-4','new':'lr=2e-4'}]})}}
        calls=iter([{'models':[{'name':MODEL,'digest':DIGEST}]},response])
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'attempt'
            with patch('experiment_proposer.read_snapshot',side_effect=AssertionError('history must not be read')), patch('experiment_proposer.urllib.request.urlopen',side_effect=lambda *a,**k:BytesIO(json.dumps(next(calls)).encode())):
                propose(source,Path(folder)/'missing.sqlite',out,retrieval=False,seed=123,temperature=.3)
            request=json.loads((out/'request.json').read_text())
            self.assertEqual(request['options']['seed'],123)
            self.assertEqual(request['options']['temperature'],.3)
            self.assertIn('Development records:\n[]',request['messages'][1]['content'])
            self.assertEqual(json.loads((out/'proposal.json').read_text())['history_records'],0)

if __name__=='__main__':unittest.main()
