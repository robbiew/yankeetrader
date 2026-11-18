import base64,copy,gzip,json,unittest
from pathlib import Path
from unittest.mock import patch
import export_evolved_occupied_planet_fixture as e

class EvolvedOccupiedPlanetFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.expected=e.check()
    def reject(self,change):
        d=copy.deepcopy(self.expected);change(d)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_phase_inventory_clock_state_and_oracle_corruption(self):
        self.assertEqual(sum(len(c['clocks'])for c in self.expected['cases']),78)
        self.reject(lambda d:d['cases'].pop())
        for field,value in [('expected_sha256','0'*64),('initial_state',1<<24),('final_state',0),('draws',0)]:
            self.reject(lambda d,f=field,v=value:d['cases'][1].__setitem__(f,v))
        self.reject(lambda d:d['cases'][1]['clocks'][0].__setitem__('record',4054))
        self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
    def test_container_recompression_and_before_bytes(self):
        d=copy.deepcopy(self.expected);key=next(iter(d['worlds']));raw=gzip.decompress(base64.b64decode(d['worlds'][key]))
        d['worlds'][key]=base64.b64encode(gzip.compress(raw,mtime=17)).decode();e.validate(d,self.expected)
        raw=bytearray(raw);raw[-1]^=1;d['worlds'][key]=e.PACK(raw)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_complete_chains_precede_native_targets(self):
        real=e.planets.maintain;read=Path.read_bytes;phases=[];targets=[]
        def phase(*args):phases.append(1);return real(*args)
        def guarded(path):
            if e.chain.DEFAULT in path.parents:
                self.assertFalse(path.name.startswith('before-'),'native child before world must not enter export')
                if path.name.startswith('after-'):
                    self.assertEqual(len(phases),2*(len(targets)//72+1));targets.append(path)
            return read(path)
        with patch.object(e.native,'verify'),patch.object(e.planets,'maintain',phase),patch.object(Path,'read_bytes',guarded):
            e.validate(e.build(),self.expected)
        self.assertEqual((len(phases),len(targets)),(24,864))
    def test_changed_native_output_and_rng_witness_fail(self):
        read=Path.read_bytes
        def changed(path):
            raw=read(path)
            if e.chain.DEFAULT in path.parents and path.name=='after-YTDATA.DAT.gz':
                world=bytearray(gzip.decompress(raw));world[-1]^=1;return gzip.compress(world,mtime=0)
            return raw
        with patch.object(e.native,'verify'),patch.object(Path,'read_bytes',changed):
            with self.assertRaises(AssertionError):e.build()
        extract=e.chain.inputs_from_observation;inputs=[]
        def original_inputs(ob):
            value=extract(ob);inputs.append(value);return value
        def poison(path):
            raw=read(path)
            if e.chain.DEFAULT in path.parents and path.name=='host-time.json.gz':
                ob=json.loads(gzip.decompress(raw))
                for row in ob['events']:
                    for side in ('before','after'):row[side]['rng_raw']='00000000'
                return gzip.compress(json.dumps(ob).encode(),mtime=0)
            return raw
        with patch.object(e.native,'verify'),patch.object(Path,'read_bytes',poison),patch.object(e.chain,'inputs_from_observation',original_inputs):
            with self.assertRaises((AssertionError,ValueError)):e.build()
        self.assertEqual(len(inputs),3,'clock extraction succeeds; independent RNG audit rejects poisoned witnesses')

if __name__=='__main__':unittest.main()
