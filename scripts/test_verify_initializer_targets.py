"""Complete-record semantic controls independent of hash rejection and model code."""
import datetime
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_initializer_targets import ROOT, SHA, audit_world, decode, mbf, verify, verify_fresh_controls

SOURCE = ROOT / "research/yt-rng-seeding/clock-dos"
DATE = datetime.date(2026, 11, 2)


class InitializerTargetTests(unittest.TestCase):
    def world(self, name="midnight"):
        return bytearray(gzip.decompress((SOURCE / name / "before-maint.dat.gz").read_bytes()))

    def put(self, world, record, offset, value):
        at = (record - 1) * 137 + offset
        world[at:at + len(value)] = value

    def test_all_complete_retained_worlds(self):
        result = verify()
        self.assertEqual(set(result), {"midnight", "repeat", "second-one", "second-two", "later", "next-date"})
        for case in result.values():
            self.assertEqual(case["records"], 4151)
            self.assertEqual(case["bytes"], 568687)
            self.assertEqual(case["inactive_players"], 50)
            self.assertEqual(case["complete_sectors"], 3000)
            self.assertEqual(case["inactive_planets"], 100)
        self.assertEqual(result["midnight"]["zero_first_warp_fields"], 1331)
        self.assertEqual(result["midnight"]["zero_later_warp_fields"], 8845)
        self.assertEqual(result["second-two"]["orphaned_ports"], [dict(sector=7, overwritten=4, winner=274)])

    def test_fresh_path_and_calendar_boundary_targets(self):
        results = verify_fresh_controls()
        self.assertEqual(set(results), {"baseline", "score-path", "new-year", "leap-day"})
        for result in results.values():
            self.assertEqual(result["records"], 4151)
            self.assertEqual(result["hq"], 849)
        from verify_initializer_controls import verify as source_controls
        controls = source_controls()
        january = controls["new-year"]["world"]
        self.assertEqual(decode(january[81:85]), 0)
        self.assertEqual(january[81:85], bytes.fromhex("00004000"))
        altered = bytearray(january)
        altered[81:85] = bytes(4)
        with self.assertRaisesRegex(AssertionError, "configuration"):
            audit_world(altered, controls["new-year"]["date"], 849)
        scored = controls["score-path"]["world"]
        self.assertTrue(scored[:41].startswith(b"SCORES.TXT"))
        self.assertEqual(decode(scored[41:45]), 10)
        with self.assertRaisesRegex(AssertionError, "configuration"):
            audit_world(scored, controls["score-path"]["date"], 849)  # wrong default path

    def test_config_semantics_without_hash_guard(self):
        for offset, value in ((41, mbf(10)), (45, mbf(27)), (49, mbf(501)), (81, mbf(306)),
                              (85, mbf(1)), (89, bytes.fromhex("0000a000")), (93, mbf(4150)),
                              (101, mbf(6)), (105, mbf(450)), (125, mbf(6325)), (129, mbf(1)), (133, b"\x01")):
            with self.subTest(offset=offset):
                world = self.world()
                self.put(world, 1, offset, value)
                with self.assertRaises(AssertionError): audit_world(world, DATE, 849)

    def test_all_inactive_player_records_are_checked(self):
        for record, offset, value in ((2, 0, b"X"), (26, 41, mbf(1)), (51, 129, bytes.fromhex("00008000")), (51, 136, b"\x01")):
            with self.subTest(record=record, offset=offset):
                world = self.world()
                self.put(world, record, offset, value)
                with self.assertRaisesRegex(AssertionError, "inactive player"): audit_world(world, DATE, 849)

    def test_complete_sector_residues_and_nonwarp_fields(self):
        cases = ((53, 41, bytes(4)),  # sector2 first slot is numeric zero with residue02005400
                 (54, 45, bytes(4)),  # sector3 later zero retains previous warp FAC mantissa
                 (52, 69, bytes.fromhex("00008000")), (152, 73, mbf(1)),
                 (52, 105, bytes(4)),  # remove Earth HQ reference
                 (900, 81, bytes(4)), (900, 85, bytes(4)),  # remove actual HQ defenses
                 (901, 81, mbf(10000)),  # invent another HQ
                 (3051, 0, b"X"), (3051, 133, b"\x01"))
        for record, offset, value in cases:
            with self.subTest(record=record, offset=offset):
                world = self.world()
                self.put(world, record, offset, value)
                if offset == 41 or (record == 54 and offset == 45):
                    self.assertEqual(decode(value), 0)  # corruption remains numerically indistinguishable
                with self.assertRaises(AssertionError): audit_world(world, DATE, 849)

    def test_inactive_planets_are_reused_fields_not_blank_templates(self):
        for record, offset, value in ((4052, 0, b" " * 41), (4102, 85, mbf(-1)), (4151, 117, bytes(4)),
                                      (4151, 125, bytes(4)), (4151, 133, b"\x01")):
            with self.subTest(record=record, offset=offset):
                world = self.world()
                self.put(world, record, offset, value)
                with self.assertRaisesRegex(AssertionError, "inactive planet"): audit_world(world, DATE, 849)

    def test_rehashed_semantic_residue_corruption_still_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "clock-dos"
            shutil.copytree(SOURCE, root)
            d = root / "midnight"
            p = d / "before-maint.dat.gz"
            world = self.world()
            self.put(world, 53, 41, bytes(4))
            p.write_bytes(gzip.compress(world, mtime=0))
            metadata_path = d / "result.json"
            metadata = json.loads(metadata_path.read_text())
            metadata["files"][p.name] = SHA(p.read_bytes())
            metadata_path.write_text(json.dumps(metadata))
            with self.assertRaisesRegex(AssertionError, "complete sector record"):
                verify(root, check_sources=False)

if __name__ == "__main__":
    unittest.main()
