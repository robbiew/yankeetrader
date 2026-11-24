import base64,copy,gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
import export_evolved_occupied_tail_fixture as e
class EvolvedOccupiedTailFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.expected=e.check()
    def reject(self,change):
        d=copy.deepcopy(self.expected);change(d)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_complete_phase_worlds_clocks_routes_events(self):
        self.assertEqual(len(self.expected['cases']),24)
        self.assertEqual(sum(len(c['events'])for c in self.expected['cases']),108)
        self.reject(lambda d:d['cases'].pop())
        for key,value in [('expected_sha256','0'*64),('initial_state',0),('final_state',0),('draws',0)]:
            self.reject(lambda d,k=key,v=value:d['cases'][0].__setitem__(k,v))
        self.reject(lambda d:d['cases'][0]['helpers'][0].__setitem__('caller',0x437a))
        self.reject(lambda d:d['cases'][0]['seeds'][0].__setitem__('old_state',0))
        self.reject(lambda d:d['cases'][0]['report_sha256'].__setitem__('YTNEWS.DAT','0'*64))
        self.reject(lambda d:d['cases'][0]['report_clock'].__setitem__('news_clock','12:00:00'))
        self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
    def test_portable_recompression_and_changed_before(self):
        d=copy.deepcopy(self.expected);key=next(iter(d['worlds']));raw=gzip.decompress(base64.b64decode(d['worlds'][key]))
        d['worlds'][key]=base64.b64encode(gzip.compress(raw,mtime=17)).decode();e.validate(d,self.expected)
        raw=bytearray(raw);raw[-1]^=1;d['worlds'][key]=e.PACK(raw)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_complete_synthesis_precedes_native_targets(self):
        real=e.chain.synthesize_chain;read=Path.read_bytes;completed=[];targets=[]
        def synth(*args):value=real(*args);completed.append(1);return value
        def guarded(path):
            if e.chain.DEFAULT in path.parents:
                self.assertFalse(path.name.startswith('before-'),'native case before-world is not a synthesis input')
                if path.name.startswith('after-'):
                    self.assertEqual(len(completed),len(targets)//72+1);targets.append(path)
            return read(path)
        with patch.object(e.native,'verify'),patch.object(e.chain,'synthesize_chain',synth),patch.object(Path,'read_bytes',guarded):e.validate(e.build(),self.expected)
        self.assertEqual((len(completed),len(targets)),(12,864))
    def test_corrupt_native_outputs_fail_without_correction(self):
        read=Path.read_bytes
        def changed(path):
            raw=read(path)
            if e.chain.DEFAULT in path.parents and path.name=='after-YTDATA.DAT.gz':
                world=bytearray(gzip.decompress(raw));world[-1]^=1;return gzip.compress(world,mtime=0)
            return raw
        with patch.object(e.native,'verify'),patch.object(Path,'read_bytes',changed):
            with self.assertRaises(AssertionError):e.build()
    def test_rng_witnesses_are_not_synthesis_seeds(self):
        read=Path.read_bytes;extract=e.chain.inputs_from_observation;inputs=[]
        def capture(ob):v=extract(ob);inputs.append(v);return v
        def changed(path):
            raw=read(path)
            if e.chain.DEFAULT in path.parents and path.name=='host-time.json.gz':
                ob=json.loads(gzip.decompress(raw))
                for row in ob['events']:
                    for side in ('before','after'):row[side]['rng_raw']='00000000'
                return gzip.compress(json.dumps(ob).encode(),mtime=0)
            return raw
        with patch.object(e.native,'verify'),patch.object(Path,'read_bytes',changed),patch.object(e.chain,'inputs_from_observation',capture):
            with self.assertRaises((AssertionError,ValueError)):e.build()
        self.assertEqual(len(inputs),3)
if __name__=='__main__':unittest.main()
