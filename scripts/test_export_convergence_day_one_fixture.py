import base64,copy,gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
import export_convergence_day_one_fixture as e

class ConvergenceDayOneFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.expected=e.check()
    def reject(self,change):
        d=copy.deepcopy(self.expected);change(d)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_complete_phase_inputs_and_calculated_receipts(self):
        self.assertEqual(len(self.expected['cases']),3)
        self.assertTrue(all(c['created']==['wanderer','xannoron','base']for c in self.expected['cases']))
        self.reject(lambda d:d['cases'].pop())
        for field,value in [('expected_sha256','0'*64),('initial_state',0),('final_state',0),('draws',0)]:
            self.reject(lambda d,f=field,v=value:d['cases'][0].__setitem__(f,v))
        self.reject(lambda d:d['cases'][0]['helpers'][0].__setitem__('caller',0x437a))
        self.reject(lambda d:d['cases'][0]['seeds'][0].__setitem__('old_state',0))
        self.reject(lambda d:d['cases'][0].__setitem__('wanderer_day',0))
        self.reject(lambda d:d['cases'][0].__setitem__('xannoron_timer','00000000'))
        self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
    def test_portable_recompression_and_changed_before(self):
        d=copy.deepcopy(self.expected);key=next(iter(d['worlds']));raw=gzip.decompress(base64.b64decode(d['worlds'][key]))
        d['worlds'][key]=base64.b64encode(gzip.compress(raw,mtime=17)).decode();e.validate(d,self.expected)
        raw=bytearray(raw);raw[-1]^=1;d['worlds'][key]=e.PACK(raw)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_entire_chain_precedes_targets_and_cache_probes(self):
        real=e.planets.maintain;read=Path.read_bytes;phases=[];targets=[];probes=[]
        def phase(*args):phases.append(1);return real(*args)
        def guarded(path):
            if e.convergence.DEFAULT in path.parents:
                self.assertFalse(path.name.startswith('before-'),'native child before input is forbidden')
                if path.name.startswith('after-')or path.name=='TRACE.BIN':
                    self.assertEqual(len(phases),3*(len(targets)//108+1))
                    if path.name.startswith('after-'):targets.append(path)
                    else:probes.append(path)
            return read(path)
        with patch.object(e.convergence,'verify'),patch.object(e.native,'verify'),patch.object(e.planets,'maintain',phase),patch.object(Path,'read_bytes',guarded):
            e.validate(e.build(),self.expected)
        self.assertEqual((len(phases),len(targets),len(probes)),(9,324,36))
    def test_native_files_and_cache_probes_cannot_correct_the_model(self):
        read=Path.read_bytes
        for kind in ('world','cache'):
            def changed(path):
                raw=read(path)
                if e.convergence.DEFAULT in path.parents:
                    if kind=='world'and path.name=='after-YTDATA.DAT.gz':
                        world=bytearray(gzip.decompress(raw));world[-1]^=1;return gzip.compress(world,mtime=0)
                    if kind=='cache'and path.name=='TRACE.BIN'and path.parent.name.startswith('cache-'):
                        data=bytearray(raw);data[-168+4]^=1;return bytes(data)
                return raw
            with patch.object(e.convergence,'verify'),patch.object(e.native,'verify'),patch.object(Path,'read_bytes',changed):
                with self.assertRaises((AssertionError,ValueError)):e.build()
    def test_poisoned_rng_witnesses_are_not_synthesis_inputs(self):
        read=Path.read_bytes;extract=e.chain.inputs_from_observation;inputs=[]
        def capture(ob):value=extract(ob);inputs.append(value);return value
        def changed(path):
            raw=read(path)
            if e.convergence.DEFAULT in path.parents and path.name=='host-time.json.gz':
                ob=json.loads(gzip.decompress(raw))
                for row in ob['events']:
                    for side in ('before','after'):row[side]['rng_raw']='00000000'
                return gzip.compress(json.dumps(ob).encode(),mtime=0)
            return raw
        with patch.object(e.convergence,'verify'),patch.object(e.native,'verify'),patch.object(Path,'read_bytes',changed),patch.object(e.chain,'inputs_from_observation',capture):
            with self.assertRaises((AssertionError,ValueError)):e.build()
        self.assertEqual(len(inputs),3,'clock extraction succeeds before independent witness audit rejects corruption')

if __name__=='__main__':unittest.main()
