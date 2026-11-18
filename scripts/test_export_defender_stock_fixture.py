import base64,copy,gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
import export_defender_stock_fixture as e
class DefenderStockFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.expected=e.check()
    def reject(self,change):
        d=copy.deepcopy(self.expected);change(d)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_complete_inventory_receipts_and_portable_bytes(self):
        self.assertEqual(len(self.expected['cases']),24)
        self.reject(lambda d:d['cases'].pop())
        self.reject(lambda d:d['cases'][0].__setitem__('initial_state',0))
        self.reject(lambda d:d['cases'][0].__setitem__('expected_sha256','0'*64))
        self.reject(lambda d:d['cases'][0]['statistics']['events'][0].__setitem__('defenders',0))
        self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
        d=copy.deepcopy(self.expected);key=next(iter(d['worlds']));raw=gzip.decompress(base64.b64decode(d['worlds'][key]))
        d['worlds'][key]=base64.b64encode(gzip.compress(raw,mtime=17)).decode();e.validate(d,self.expected)
        b=bytearray(raw);b[-1]^=1;d['worlds'][key]=e.PACK(b)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_five_day_synthesis_precedes_native_targets(self):
        real=e.chain.synthesize_chain;read=Path.read_bytes;completed=[];targets=[]
        def synth(*args):v=real(*args);completed.append(1);return v
        def guarded(path):
            if e.chain.DEFAULT in path.parents:
                self.assertFalse(path.name.startswith('before-'),'native child before world is not a synthesis input')
                if path.name.startswith('after-'):
                    self.assertEqual(len(completed),len(targets)//72+1);targets.append(path)
            return read(path)
        with patch.object(e.native,'verify'),patch.object(e.chain,'synthesize_chain',synth),patch.object(Path,'read_bytes',guarded):e.validate(e.build(),self.expected)
        self.assertEqual((len(completed),len(targets)),(12,864))
    def test_corrupted_native_world_is_not_a_correction(self):
        read=Path.read_bytes
        def changed(path):
            raw=read(path)
            if e.chain.DEFAULT in path.parents and path.name=='after-YTDATA.DAT.gz':
                b=bytearray(gzip.decompress(raw));b[-1]^=1;return gzip.compress(b,mtime=0)
            return raw
        with patch.object(e.native,'verify'),patch.object(Path,'read_bytes',changed):
            with self.assertRaises((ValueError,AssertionError)):e.build()
    def test_poisoned_rng_witnesses_cannot_seed_synthesis(self):
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
            with self.assertRaises((ValueError,AssertionError)):e.build()
        self.assertEqual(len(inputs),2)
if __name__=='__main__':unittest.main()
