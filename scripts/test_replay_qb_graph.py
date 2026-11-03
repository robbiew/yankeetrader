"""Regressions and causal negative controls for fixed-clock graph research replay."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('graph_research',ROOT/'scripts/replay_qb_graph.py')
model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)


class FixedClockGraphReplayTests(unittest.TestCase):
    def test_all_retained_replay_results(self):
        retained=json.loads((ROOT/'research/yt-rng-seeding/replay-results.json').read_text())
        self.assertEqual(retained['recipe'],'qb3-fixed-clock-graph-comparison-v1')
        self.assertEqual(len(retained['cases']),4)
        pins=[('base',0xc805,27734,'0xf5b72b',0,0),
              ('repair',0xc805,27754,'0xdaa8af',19,0),
              ('full',0xc805,27770,'0xc3cfff',19,15),
              ('full',0x275905,27927,'0xd1df02',19,13)]
        checked=model.controlled_cases()
        self.assertEqual(checked,retained)
        for recorded,(phase,state,draws,final,repairs,shortcuts)in zip(checked['cases'],pins):
            with self.subTest(phase=phase,state=state):
                observed=model.run_case(ROOT/recorded['world'],state,1,phase)
                self.assertEqual(observed,{key:value for key,value in recorded.items()if key not in ('native_init_log_sha256','seed_trace')})
                self.assertEqual(recorded['seed_trace']['world_seed'],state)
                self.assertEqual(len(recorded['native_init_log_sha256']),64)
                self.assertEqual(observed['matching_cells'],18000)
                self.assertEqual(observed['mismatch_count'],0)
                self.assertEqual(observed['draws'],draws)
                self.assertEqual(observed['final_state'],final)
                self.assertEqual(len(observed['repair_pairs']),repairs)
                self.assertEqual(len(observed['shortcut_writes']),shortcuts)

    def test_raw_seed_provenance(self):
        seeds=model.native_seeds()
        for name,fac,negative,state in (
            ('timer-midnight','00004800','0000c800',0xc805),
            ('timer-noon','e9b73090','e9b7b090',0x275905),
        ):
            with self.subTest(name=name):
                self.assertEqual(seeds[name]['fac'],fac)
                self.assertEqual(seeds[name]['negative_fac'],negative)
                self.assertEqual(seeds[name]['world_seed'],state)
                raw=(ROOT/seeds[name]['trace']).read_bytes()
                self.assertEqual(seeds[name]['trace_sha256'],hashlib.sha256(raw).hexdigest())

    def test_rehashed_wrong_raw_seed_trace_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            target=Path(tmp)/'trace'
            shutil.copytree(ROOT/'research/yt-rng-seeding/trace-dos',target)
            trace=target/'timer-noon/TRACE.BIN'
            raw=bytearray(trace.read_bytes());raw[16]^=1;trace.write_bytes(raw)
            meta_path=trace.parent/'result.json'
            meta=json.loads(meta_path.read_text())
            meta['files']['TRACE.BIN']=hashlib.sha256(raw).hexdigest()
            meta_path.write_text(json.dumps(meta))
            with self.assertRaises(AssertionError):model.native_seeds(target)

    def test_changed_target_rejected_despite_rehashed_metadata(self):
        source=ROOT/'research/yt-warp-generation/dos/no-repair/before-maint.dat.gz'
        expected='c19362ee2f6dd8e0c2dc6d869daf9cbdafb27ca5247ba7a145e6ad2dfd44ab35'
        raw=bytearray(gzip.decompress(source.read_bytes()))
        # Change a warp cell, then supply plausible freshly computed metadata.
        model.mbf.put(raw,51+3,41,2999)
        with tempfile.TemporaryDirectory()as tmp:
            target=Path(tmp)/'changed.dat.gz';target.write_bytes(gzip.compress(raw))
            metadata={'world_sha256':hashlib.sha256(raw).hexdigest()}
            self.assertNotEqual(metadata['world_sha256'],expected)
            with self.assertRaisesRegex(AssertionError,'changed fixed observed target'):
                model.run_case(target,0xc805,1,'base',expected_world_sha=expected)
            # Without an identity pin, direct cell comparison still reports it.
            comparison=model.run_case(target,0xc805,1,'base')
            self.assertGreater(comparison['mismatch_count'],0)

    def test_wrong_seed_does_not_match(self):
        observed=model.run_case(ROOT/'research/yt-warp-generation/dos/no-repair/before-maint.dat.gz',0xc806,1,'base')
        self.assertGreater(observed['mismatch_count'],0)
        self.assertIsNotNone(observed['first_difference'])

    def test_graph_alone_cannot_identify_the_hq_prefix(self):
        # The first occupied Earth slot consumes an unused offset and can make
        # the zero-prefix stream catch up. Native HQ evidence is still required.
        observed=model.run_case(ROOT/'research/yt-warp-generation/dos/no-repair/before-maint.dat.gz',0xc805,0,'base')
        self.assertEqual(observed['mismatch_count'],0)
        self.assertEqual(observed['draws'],27734)
        self.assertEqual(observed['final_state'],'0xf5b72b')

    def test_duplicated_pregraph_hq_draw_does_not_match(self):
        observed=model.run_case(ROOT/'research/yt-warp-generation/dos/no-repair/before-maint.dat.gz',0xc805,2,'base')
        self.assertGreater(observed['mismatch_count'],0)
        self.assertIsNotNone(observed['first_difference'])


class TargetCellTests(unittest.TestCase):
    def test_unpinned_custom_world_rejects_fractional_and_out_of_range_cells(self):
        import gzip
        import tempfile
        source=ROOT/'research/yt-warp-generation/dos/no-repair/before-maint.dat.gz'
        for value in (1.5,3001):
            with self.subTest(value=value),tempfile.TemporaryDirectory() as tmp:
                raw=bytearray(gzip.decompress(source.read_bytes()))
                model.mbf.put(raw,52,41,value)
                path=Path(tmp)/'world.dat.gz';path.write_bytes(gzip.compress(raw,mtime=0))
                with self.assertRaisesRegex(AssertionError,'invalid target warp cell'):model.read_table(path)

if __name__=='__main__':unittest.main()
