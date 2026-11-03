"""Rehashed semantic corruption controls for the DOS warp phase verifier."""
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_warp_generation import verify_native, ROOT, SHA, verify

SOURCE = ROOT / "research/yt-warp-generation/dos"

class WarpEvidenceTests(unittest.TestCase):
    def test_retained_phase_outcomes(self):
        result = verify(SOURCE)
        self.assertEqual(len(result["cases"]["no-repair"]["weak_components"]), 20)
        self.assertEqual(result["cases"]["no-repair"]["reachable_from_earth"], 2953)
        self.assertEqual(len(result["cases"]["local-only"]["weak_components"]), 28)
        self.assertEqual(result["cases"]["local-only"]["reachable_from_earth"], 322)
        self.assertEqual(result["cases"]["repair-only"]["reachable_from_earth"], 3000)
        self.assertEqual(result["cases"]["repair-only"]["can_reach_earth"], 3000)
        self.assertEqual(len(result["shortcut_sources"]), 15)

    def copied(self, directory):
        root = Path(directory) / "dos"
        shutil.copytree(SOURCE, root)
        return root

    def rehash(self, directory, filename):
        p = directory / "result.json"
        metadata = json.loads(p.read_text())
        metadata["files"][filename] = SHA((directory / filename).read_bytes())
        p.write_text(json.dumps(metadata))

    def test_rehashed_graph_corruptions(self):
        cases = {
            "missing-link": ("no-repair", 2, 1, "00000000"),
            "fractional-link": ("no-repair", 2, 1, "00004081"),
            "local-asymmetry": ("no-repair", 3, 0, "00004083"),  # 6 instead of 5
            "wrong-earth-order": ("original", 1, 0, "00000000"),
            "duplicate": ("original", 3, 1, "00002083"),  # another 5
            "unexpected-self": ("no-repair", 2, 0, "00000082"),  # 2 -> 2
            "invalid-target": ("no-repair", 2, 1, "ffff7fff"),
            "invalid-local-only-sixth": ("local-only", 2, 5, "00000081"),
        }
        for mode, (name, sector, column, value) in cases.items():
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = self.copied(tmp)
                d = root / name
                p = d / "before-maint.dat.gz"
                world = bytearray(gzip.decompress(p.read_bytes()))
                offset = (50 + sector) * 137 + 41 + 4 * column
                world[offset:offset + 4] = bytes.fromhex(value)
                p.write_bytes(gzip.compress(world, mtime=0))
                self.rehash(d, p.name)
                with self.assertRaises(AssertionError):
                    verify(root)

    def test_rehashed_phase_substitutions(self):
        for target, replacement in (("no-repair", "original"), ("repair-only", "no-repair"), ("original", "repair-only")):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                root = self.copied(tmp)
                d = root / target
                shutil.copyfile(root / replacement / "before-maint.dat.gz", d / "before-maint.dat.gz")
                self.rehash(d, "before-maint.dat.gz")
                with self.assertRaises(AssertionError):
                    verify(root)

    def test_rehashed_missing_returns_and_phase_claims(self):
        for filename in ("INITRET.LOG", "INIT.LOG"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                root = self.copied(tmp)
                d = root / "original"
                (d / filename).write_bytes(b"false report without normal return")
                self.rehash(d, filename)
                with self.assertRaises(AssertionError):
                    verify(root)
        with tempfile.TemporaryDirectory() as tmp:
            root = self.copied(tmp)
            d = root / "no-repair"
            p = d / "INIT.LOG"
            p.write_bytes(p.read_bytes() + b"Building shortcuts")
            self.rehash(d, p.name)
            with self.assertRaises(AssertionError):
                verify(root)

    def test_rehashed_false_repair_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.copied(tmp)
            for name in ("original", "repair-only"):
                d = root / name
                p = d / "INIT.LOG"
                raw = p.read_bytes()
                assert b"Sector 35 has been linked to sector 14" in raw
                p.write_bytes(raw.replace(b"Sector 35 has been linked to sector 14", b"Sector 36 has been linked to sector 14"))
                self.rehash(d, p.name)
            with self.assertRaises(AssertionError):
                verify(root)

    def test_false_golden_tables_and_provenance(self):
        source = ROOT / "internal/game/testdata/dos_warps.json.gz"
        for mode in ("slot", "fractional", "truncated", "world-provenance", "binary-provenance", "repair-pair"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                fixture = Path(tmp) / "fixture.gz"
                golden = json.loads(gzip.decompress(source.read_bytes()))
                case = golden["cases"]["no-repair"]
                if mode == "slot": case["slots"][2][1] = 0
                elif mode == "fractional": case["slots"][2][1] = 1.0
                elif mode == "truncated": case["slots"].pop()
                elif mode == "world-provenance": case["source_world_sha256"] = "0" * 64
                elif mode == "binary-provenance": case["initializer_copied_sha256"] = case["initializer_original_sha256"]
                elif mode == "repair-pair": golden["repair_pairs"][0][0] = 36
                fixture.write_bytes(gzip.compress(json.dumps(golden).encode(), mtime=0))
                with self.assertRaises(AssertionError):
                    verify(SOURCE, fixture=fixture)

    def test_false_patch_and_full_binary_attribution(self):
        for mode in ("patch-before", "patch-after", "copied-hash", "child", "clock"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = self.copied(tmp)
                p = root / "no-repair/result.json"
                metadata = json.loads(p.read_text())
                if mode == "patch-before": metadata["patches"][0]["before"] = "000000"
                elif mode == "patch-after": metadata["patches"][0]["after"] = "e90000"
                elif mode == "copied-hash": metadata["initializer_copied_sha256"] = metadata["initializer_original_sha256"]
                elif mode == "child": metadata["binaries"]["YTMAINT.EXE"] = "0" * 64
                elif mode == "clock": metadata["time"] = "12:34:00"
                p.write_text(json.dumps(metadata))
                with self.assertRaises(AssertionError):
                    verify(root)

class NativeEvidenceTests(unittest.TestCase):
    def test_retained_native_contract(self):
        verify_native(ROOT/"research/yt-warp-generation")

    def test_missing_truncated_or_false_native_reads(self):
        for mode in ("missing","empty","truncated","bytes"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                bundle=json.loads((ROOT/"research/yt-warp-generation/rea.json").read_text())
                if mode=="missing":bundle["records"].pop()
                else:
                    value=bundle["records"][0]["normalized_result"]
                    if mode=="bytes":value["bytes_hex"]="00"+value["bytes_hex"][2:]
                    else:
                        value["bytes_hex"]="" if mode=="empty" else value["bytes_hex"][:-2]
                        value["returned_bytes"]=len(value["bytes_hex"])//2
                (Path(tmp)/"rea.json").write_text(json.dumps(bundle))
                with self.assertRaises(AssertionError):verify_native(Path(tmp))

if __name__ == "__main__":
    unittest.main()
