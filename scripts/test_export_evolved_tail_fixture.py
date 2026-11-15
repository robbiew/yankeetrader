import base64,copy,gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import export_evolved_tail_fixture as e

class EvolvedTailFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.expected=e.check()
    def reject(self,change):
        d=copy.deepcopy(self.expected);change(d)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def audits_off(self):
        stack=ExitStack()
        for module in (e.convergence,e.native,e.occupied_evidence,e.placement):stack.enter_context(patch.object(module,'verify'))
        return stack
    def test_phase_inventory_and_receipt_corruption(self):
        self.assertEqual([c['mercenary']['force']for c in self.expected['cases']],[0]*9+[97525]*3+[37]*3)
        self.assertEqual([len(c['mercenary']['activations'])for c in self.expected['cases']],[0]*9+[1]*3+[2]*3)
        self.reject(lambda d:d['cases'].pop())
        for field,value in [('initial_state',1<<24),('final_state',0),('expected_sha256','0'*64),('draws',0),('lottery','00000000')]:
            self.reject(lambda d,f=field,v=value:d['cases'][0].__setitem__(f,v))
        self.reject(lambda d:d['cases'][9]['helpers'][0].__setitem__('caller',0x437a))
        self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
    def test_recompression_and_changed_before_bytes(self):
        d=copy.deepcopy(self.expected);key=next(iter(d['worlds']));raw=gzip.decompress(base64.b64decode(d['worlds'][key]))
        d['worlds'][key]=base64.b64encode(gzip.compress(raw,mtime=17)).decode();e.validate(d,self.expected)
        raw=bytearray(raw);raw[-1]^=1;d['worlds'][key]=e.PACK(raw)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_models_precede_native_oracles_without_child_world_inputs(self):
        read=Path.read_bytes;calls=[];targets=[[],[],[]];probes=[]
        roots=(e.convergence.DEFAULT,e.occupied.DEFAULT,e.collision.DEFAULT)
        def wrap(real):
            def phase(*args):calls.append(1);return real(*args)
            return phase
        def guarded(path):
            for i,root in enumerate(roots):
                if root not in path.parents:continue
                self.assertFalse(path.name.startswith('before-'),'native child worlds forbidden')
                if path.name.startswith('after-'):
                    want=3*(len(targets[0])//108+1)if i==0 else(10 if i==1 else 13)+len(targets[i])//36
                    self.assertEqual(len(calls),want);targets[i].append(path)
                elif path.name=='TRACE.BIN':probes.append(path)
            return read(path)
        with self.audits_off(),patch.object(e.large,'maintain',wrap(e.large.maintain)),patch.object(e.small,'maintain',wrap(e.small.maintain)),patch.object(Path,'read_bytes',guarded):
            e.validate(e.build(),self.expected)
        self.assertEqual((len(calls),sum(map(len,targets)),len(probes)),(15,540,36))
    def test_native_outputs_and_cache_probes_do_not_correct_synthesis(self):
        read=Path.read_bytes
        for kind in ('world','cache'):
            def changed(path):
                raw=read(path)
                if e.convergence.DEFAULT in path.parents:
                    if kind=='world'and path.name=='after-YTDATA.DAT.gz':
                        world=bytearray(gzip.decompress(raw));world[-1]^=1;return gzip.compress(world,mtime=0)
                    if kind=='cache'and path.name=='TRACE.BIN'and path.parent.name.startswith('cache-'):
                        data=bytearray(raw);data[-164]^=1;return bytes(data)
                return raw
            with self.audits_off(),patch.object(Path,'read_bytes',changed):
                with self.assertRaises((AssertionError,ValueError)):e.build()
    def test_poisoned_rng_witnesses_are_not_model_inputs(self):
        read=Path.read_bytes;extract=e.chain.inputs_from_observation;inputs=[]
        def capture(ob):v=extract(ob);inputs.append(v);return v
        def changed(path):
            raw=read(path)
            if e.convergence.DEFAULT in path.parents and path.name=='host-time.json.gz':
                ob=json.loads(gzip.decompress(raw))
                for row in ob['events']:
                    for side in ('before','after'):row[side]['rng_raw']='00000000'
                return gzip.compress(json.dumps(ob).encode(),mtime=0)
            return raw
        with self.audits_off(),patch.object(Path,'read_bytes',changed),patch.object(e.chain,'inputs_from_observation',capture):
            with self.assertRaises((AssertionError,ValueError)):e.build()
        self.assertEqual(len(inputs),3,'clock extraction succeeds before independent witness audit fails')

if __name__=='__main__':unittest.main()
