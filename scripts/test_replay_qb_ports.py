"""Exact record replay and negative controls; expected observations are fixed."""
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import replay_qb_ports as model

ROOT=model.ROOT


class PortReplayTests(unittest.TestCase):
    def test_all_six_observed_worlds(self):
        result=model.controlled_cases()
        retained=json.loads((ROOT/'research/yt-port-replay/replay-results.json').read_text())
        self.assertEqual(result,retained)
        pins={
            'midnight':(1217,221,'0x54bf86',11333,40320,'0x1ca785'),
            'repeat':(1217,221,'0x54bf86',11333,40320,'0x1ca785'),
            'second-one':(1222,226,'0x451a25',11344,40176,'0xbcd835'),
            'second-two':(1198,202,'0x1ae0f8',11332,40329,'0x79697c'),
            'later':(1197,201,'0x6c4e19',11333,40457,'0x34b8fc'),
            'next-date':(1217,221,'0x54bf86',11333,40320,'0x1ca785'),
        }
        for case in result['cases']:
            with self.subTest(clock=case['clock_case']):
                self.assertEqual(case['matching_port_bytes'],137000)
                self.assertEqual(case['byte_mismatches'],0)
                self.assertEqual(case['matching_ports'],1000)
                self.assertEqual(case['sector_link_mismatches'],0)
                self.assertEqual(case['graph_comparison']['matching_cells'],18000)
                self.assertEqual(tuple(case[key]for key in ('placement_draws','placement_rejections','placement_final_state','economy_draws','draws','final_state')),pins[case['clock_case']])

    def test_checking_never_rewrites_retained_report(self):
        report=ROOT/'research/yt-port-replay/replay-results.json'
        before=report.read_bytes()
        result=subprocess.run([sys.executable,str(ROOT/'scripts/replay_qb_ports.py'),'--check'],
                              cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        self.assertEqual(report.read_bytes(),before)
        self.assertEqual(json.loads(result.stdout),json.loads(before))

    def test_original_overwrite_is_preserved(self):
        table,rng=model.graph.replay(state=0xa90a05)
        model.graph.repair(table,rng);model.graph.shortcuts(table,rng)
        ports=model.replay_ports(rng)
        self.assertEqual([(p['id'],p['sector'])for p in ports if p['sector']==7],[(4,7),(274,7)])
        self.assertEqual(len(set(p['sector']for p in ports)),999)

    def test_wrong_seed_diverges(self):
        path=ROOT/'research/yt-rng-seeding/clock-dos/midnight/before-maint.dat.gz'
        case=model.run_case(path,0xc806,expected_sha=model.WORLD_HASHES['midnight'])
        self.assertGreater(case['byte_mismatches'],0)
        self.assertGreater(case['sector_link_mismatches'],0)

    def test_rehashed_numeric_zero_residue_change_is_detected(self):
        path=ROOT/'research/yt-rng-seeding/clock-dos/midnight/before-maint.dat.gz'
        raw=bytearray(gzip.decompress(path.read_bytes()))
        at=3051*137+49
        self.assertEqual(raw[at:at+4],bytes.fromhex('0000a000'))
        raw[at:at+4]=bytes(4) # Same numeric supply; different original bytes.
        with tempfile.TemporaryDirectory()as tmp:
            target=Path(tmp)/'world.gz';target.write_bytes(gzip.compress(raw))
            with self.assertRaisesRegex(AssertionError,'changed observed world'):
                model.run_case(target,0xc805,expected_sha=model.WORLD_HASHES['midnight'])
            result=model.run_case(target,0xc805,expected_sha=model.SHA(raw))
            self.assertEqual(result['mismatch_fields'],0)
            self.assertEqual(result['byte_mismatches'],1)
            self.assertEqual(result['first_byte_differences'],[dict(port=1,offset=51,observed=0,replayed=160)])

    def test_raw_record_template_covers_earth_tail_and_name_length(self):
        port=dict(id=1,name='Earth',sector=1,trade_class=3,production=[1,2,3],coefficients=[4,-5,-6])
        raw=model.port_bytes(port,296,849)
        self.assertEqual(len(raw),137)
        self.assertEqual(raw[:41],b'Earth'+b' '*36)
        self.assertEqual(raw[85:89],bytes.fromhex('00002083'))
        self.assertEqual(raw[117:129],bytes.fromhex('0040548a00007a8a00a0458d'))
        for offset in (49,53,57,89,97,101,105,109,129):self.assertEqual(raw[offset:offset+4],bytes.fromhex('0000a000'))
        for offset in (113,133):self.assertEqual(raw[offset:offset+4],bytes(4))
        port['id']=2
        self.assertEqual(model.port_bytes(port,296,849)[117:129],bytes(12))


if __name__=='__main__':unittest.main()
