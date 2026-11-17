import copy,gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
import export_occupied_records_fixture as e
class OccupiedRecordsFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.expected=e.check()
    def reject(self,change):
        d=copy.deepcopy(self.expected);change(d)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_complete_clock_and_output_inventory(self):
        self.assertEqual(len(self.expected['cases']),30)
        self.assertEqual(sum(len(c['mercenary']['activations'])for c in self.expected['cases']),3)
        self.reject(lambda d:d['cases'].pop())
        self.reject(lambda d:d['cases'][0]['expected_files'].__setitem__('YTDATA.DAT','0'*64))
        self.reject(lambda d:d['cases'][0].__setitem__('startup_state',0))
        self.reject(lambda d:d['cases'][0]['tail'].__setitem__('initial_state',0))
        self.reject(lambda d:d['cases'][0].__setitem__('final_state',0))
        self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
    def test_complete_synthesis_precedes_native_targets(self):
        real=e.chain.synthesize;read=Path.read_bytes;completed=[];targets=[]
        def synth(*args):value=real(*args);completed.append(1);return value
        def guarded(path):
            if e.chain.DEFAULT in path.parents:
                self.assertFalse(path.name.startswith('before-'),'native case before-world is not a synthesis input')
                if path.name.startswith('after-'):
                    self.assertEqual(len(completed),len(targets)//36+1);targets.append(path)
            return read(path)
        with patch.object(e.native,'verify'),patch.object(e.source,'verify'),patch.object(e.chain,'synthesize',synth),patch.object(Path,'read_bytes',guarded):e.validate(e.build(),self.expected)
        self.assertEqual((len(completed),len(targets)),(30,1080))
    def test_corrupt_native_outputs_fail_without_correction(self):
        read=Path.read_bytes
        def changed(path):
            raw=read(path)
            if e.chain.DEFAULT in path.parents and path.name=='after-YTDATA.DAT.gz':
                world=bytearray(gzip.decompress(raw));world[-1]^=1;return gzip.compress(world,mtime=0)
            return raw
        with patch.object(e.native,'verify'),patch.object(e.source,'verify'),patch.object(Path,'read_bytes',changed):
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
        with patch.object(e.native,'verify'),patch.object(e.source,'verify'),patch.object(Path,'read_bytes',changed),patch.object(e.chain,'inputs_from_observation',capture):
            with self.assertRaises((AssertionError,ValueError)):e.build()
        self.assertEqual(len(inputs),1)
if __name__=='__main__':unittest.main()
