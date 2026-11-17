import base64,copy,gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
import export_occupied_report_fixture as e
class OccupiedReportFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.expected=e.check()
    def reject(self,change):
        d=copy.deepcopy(self.expected);change(d)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_complete_report_inputs_events_and_outputs(self):
        self.assertEqual(len(self.expected['cases']),30)
        self.assertEqual(sum(len(c['events'])for c in self.expected['cases']),120)
        self.reject(lambda d:d['cases'].pop())
        self.reject(lambda d:d['cases'][0]['expected_files'].__setitem__('YTNEWS.DAT','0'*64))
        self.reject(lambda d:d['cases'][0].__setitem__('news_clock','00:00:02'))
        self.reject(lambda d:d['cases'][0]['statistics']['scores'].__setitem__('-1',0))
        self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
    def test_portable_recompression_and_changed_before(self):
        d=copy.deepcopy(self.expected);key=next(iter(d['blobs']));raw=gzip.decompress(base64.b64decode(d['blobs'][key]))
        d['blobs'][key]=base64.b64encode(gzip.compress(raw,mtime=17)).decode();e.validate(d,self.expected)
        raw=bytearray(raw);raw[-1]^=1;d['blobs'][key]=e.PACK(raw)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
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
