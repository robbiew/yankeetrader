"""Complete initializer replay and independent byte-level negative controls."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import replay_qb_initializer as model

ROOT=model.ROOT


class InitializerReplayTests(unittest.TestCase):
    def test_all_ten_complete_worlds(self):
        result=model.controlled_cases()
        retained=json.loads((ROOT/'research/yt-initializer-replay/replay-results.json').read_text())
        self.assertEqual(result,retained)
        self.assertEqual(len(result['cases']),10)
        expected=dict(model.ports.WORLD_HASHES,**{
            'fresh-baseline':'0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d',
            'fresh-score-path':'d4efcd1d3f4c2401e4e3c53345d67af72665b1027de56d289810c88e66fc1f5e',
            'fresh-new-year':'e6d5ab5b3fab7563b279e976cdde3c4e6e494c2dffd5c35a74a60fac38fdf328',
            'fresh-leap-day':'523bfb954a8588285d6606cbdbfaa11dbccede964b512ad23bea13b496ed3d18',
        })
        for case in result['cases']:
            with self.subTest(case=case['clock_case']):
                self.assertEqual(case['compared_records'],4151)
                self.assertEqual(case['matching_bytes'],568687)
                self.assertEqual(case['byte_mismatches'],0)
                self.assertEqual(case['replayed_world_sha256'],expected[case['clock_case']])
                self.assertEqual(case['observed_world_sha256'],expected[case['clock_case']])
                self.assertEqual(set(case['blocks']),{'configuration','players','sectors','ports','planets'})
                self.assertTrue(all(block['byte_mismatches']==0 for block in case['blocks'].values()))

    def test_synthesis_reads_only_original_data_not_target_templates(self):
        original=Path.read_bytes
        def restricted(path):
            self.assertEqual(path,ROOT/'archive/dos-original/YT-INIT.EXE')
            return original(path)
        with patch.object(Path,'read_bytes',restricted):
            raw,_=model.synthesize(0xc805,datetime.date(2026,11,2))
        self.assertEqual(model.SHA(raw),'0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d')

    def test_sector_residue_is_compared_as_bytes(self):
        raw,_=model.synthesize(0xc805,'2026-11-02')
        changed=bytearray(raw);at=52*137+41
        self.assertEqual(raw[at:at+4],bytes.fromhex('02005400'))
        self.assertEqual(model.graph.mbf.dec(raw[at:at+4]),0)
        changed[at:at+4]=bytes(4)
        result=model.compare(raw,changed)
        self.assertEqual(result['byte_mismatches'],2)
        self.assertEqual(result['blocks']['sectors']['byte_mismatches'],2)

    def test_planets_inherit_configuration_except_display_flag(self):
        raw,_=model.synthesize(0xc805,'2026-11-02','SCORES.TXT')
        config=bytearray(raw[:137]);config[85:89]=bytes(4)
        self.assertEqual(raw[4051*137:],bytes(config)*100)
        changed=bytearray(raw);changed[4051*137:4052*137]=bytes(137)
        result=model.compare(raw,changed)
        self.assertGreater(result['blocks']['planets']['byte_mismatches'],0)
        self.assertEqual(result['blocks']['configuration']['byte_mismatches'],0)

    def test_calendar_and_scoreboard_inputs(self):
        jan,_=model.synthesize(0xc805,'2027-01-01')
        self.assertEqual(jan[45:49],model.graph.mbf.enc(27))
        self.assertEqual(jan[81:85],bytes.fromhex('00004000'))
        self.assertEqual(jan[3051*137+45:3051*137+49],model.graph.mbf.enc(-9))
        leap,_=model.synthesize(0xc805,'2028-02-29')
        self.assertEqual(leap[81:85],model.graph.mbf.enc(59))
        score,_=model.synthesize(0xc805,'2026-11-02','SCORES.TXT')
        self.assertEqual(score[:41],b'SCORES.TXT'+b' '*31)
        self.assertEqual(score[41:45],model.graph.mbf.enc(10))

    def test_verification_does_not_rewrite_report(self):
        report=ROOT/'research/yt-initializer-replay/replay-results.json';before=report.read_bytes()
        checked=subprocess.run([sys.executable,str(ROOT/'scripts/replay_qb_initializer.py'),'--check'],cwd=ROOT,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        self.assertEqual(report.read_bytes(),before)
        self.assertEqual(json.loads(checked.stdout),json.loads(before))

    def test_bounded_inputs_and_length(self):
        for scoreboard in ('','x'*42):
            with self.assertRaises(ValueError):model.synthesize(0xc805,'2026-11-02',scoreboard)
        with self.assertRaises(ValueError):model.synthesize(0xc805,'1999-12-31')
        with self.assertRaisesRegex(AssertionError,'complete world length'):model.compare(bytes(10),bytes(10))


if __name__=='__main__':unittest.main()
