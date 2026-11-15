import base64, copy, gzip, unittest
from unittest.mock import patch
from pathlib import Path
import export_evolved_port_fixture as e

class PortableEvolvedPorts(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.expected=e.check()
    def reject(self,change):
        d=copy.deepcopy(self.expected);change(d)
        with self.assertRaises(AssertionError):e.validate(d,self.expected)
    def test_complete_inventory_and_corruption(self):
        self.assertEqual(len(self.expected['cases']),9)
        self.assertEqual([c['rate_promotions'] for c in self.expected['cases']],[0,3000,3000]*3)
        self.reject(lambda d:d['cases'].pop())
        for field,value in [('expected_sha256','0'*64),('elapsed_min','00000000'),('rate_promotions',0)]:
            self.reject(lambda d,f=field,v=value:d['cases'][1].__setitem__(f,v))
        self.reject(lambda d:d['cases'][0]['timer_minutes'].__setitem__(999,'ffffffff'))
        self.reject(lambda d:d['sources'].pop(next(iter(d['sources']))))
    def test_all_days_precede_targets_and_mismatch_is_not_masked(self):
        real_read=Path.read_bytes;real_model=e.replay_ports;models=[];targets=[]
        def model(*args):
            models.append(args[1][0]);return real_model(*args)
        def read(path):
            if path.name=='after-YTDATA.DAT.gz' and e.convergence.DEFAULT in path.parents:
                self.assertEqual(len(models),3*(len(targets)//18+1))
                targets.append(path)
            return real_read(path)
        # Provenance audits read targets independently; isolate the exporter path.
        with patch.object(e.convergence,'verify'),patch.object(e.native,'verify'),patch.object(e,'replay_ports',model),patch.object(Path,'read_bytes',read):
            e.validate(e.build(),self.expected)
        self.assertEqual(len(models),9);self.assertEqual(len(targets),54)
        def corrupted(path):
            raw=real_read(path)
            if path.name=='after-YTDATA.DAT.gz' and e.convergence.DEFAULT in path.parents:
                world=bytearray(gzip.decompress(raw));world[e.START+136]^=1
                return gzip.compress(world,mtime=0)
            return raw
        with patch.object(e.convergence,'verify'),patch.object(e.native,'verify'),patch.object(Path,'read_bytes',corrupted):
            with self.assertRaises(AssertionError):e.build()

    def test_portable_container_and_changed_before(self):
        d=copy.deepcopy(self.expected);raw=gzip.decompress(base64.b64decode(d['initial_gzip']))
        d['initial_gzip']=base64.b64encode(gzip.compress(raw,mtime=17)).decode();e.validate(d,self.expected)
        changed=bytearray(raw);changed[-1]^=1
        d['initial_gzip']=base64.b64encode(gzip.compress(changed,mtime=0)).decode()
        with self.assertRaises(AssertionError):e.validate(d,self.expected)

if __name__=='__main__':unittest.main()
