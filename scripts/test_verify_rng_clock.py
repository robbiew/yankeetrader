"""Rehashed semantic corruption controls for the independent clock verifier."""
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_rng_clock import ROOT, SHA, fingerprints, verify

SOURCE = ROOT / "research/yt-rng-seeding/clock-dos"

class RNGClockEvidenceTests(unittest.TestCase):
    def copy(self, tmp):
        root = Path(tmp) / "clock-dos"
        shutil.copytree(SOURCE, root)
        return root

    def rehash(self, directory, filename, world=False):
        metadata_path = directory / "result.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["files"][filename] = SHA((directory / filename).read_bytes())
        if world:
            metadata["fingerprints"] = fingerprints(gzip.decompress((directory / filename).read_bytes()))
        metadata_path.write_text(json.dumps(metadata))

    def test_retained_correlations(self):
        results = verify(SOURCE)
        self.assertEqual(results["midnight"]["world_sha256"], results["repeat"]["world_sha256"])
        self.assertNotEqual(results["midnight"]["world_sha256"], results["next-date"]["world_sha256"])
        self.assertEqual(results["midnight"]["warp_slots_sha256"], results["next-date"]["warp_slots_sha256"])
        self.assertEqual(results["second-one"]["observed_start_seconds"], .98)
        self.assertEqual(results["second-two"]["observed_start_seconds"], 1.97)
        self.assertAlmostEqual(results["later"]["observed_start_seconds"], 45239.91)

    def test_fixed_case_coverage(self):
        for mode in ("missing", "extra"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = self.copy(tmp)
                if mode == "missing": shutil.rmtree(root / "repeat")
                else: (root / "unexpected").mkdir()
                with self.assertRaises(AssertionError): verify(root)

    def test_rehashed_raw_clock_and_return_corruptions(self):
        cases = (
            ("midnight", "DOSDATE.LOG", b"Mon 11/02/2026", b"Tue 11/03/2026"),
            ("midnight", "ENDDATE.LOG", b"Mon 11/02/2026", b"Tue 11/03/2026"),
            ("midnight", "DOSDATE.LOG", b"Mon 11/02/2026", b"Tue 11/02/2026"),
            ("second-one", "DOSTIME.LOG", b"0:00:00.98am", b"0:00:00.00am"),
            ("second-two", "DOSTIME.LOG", b"0:00:01.97am", b"0:00:02.50am"),
            ("midnight", "ENDTIME.LOG", b"0:00:06.81am", b"0:00:00.00am"),
            ("later", "DOSTIME.LOG", b"12:33:59.91pm", b"12:33:59.91am"),
            ("repeat", "INITRET.LOG", b"INITIALIZER_RETURNED", b"NOT_RETURNED"),
            ("repeat", "INIT.LOG", b"<YT-INIT Normal Termination>", b"<abnormal process>"),
            ("repeat", "COMMANDS.TXT", b"time 00:00:00", b"time 00:00:01"),
        )
        for name, filename, before, after in cases:
            with self.subTest(name=name, filename=filename, after=after), tempfile.TemporaryDirectory() as tmp:
                root = self.copy(tmp)
                d = root / name
                p = d / filename
                raw = p.read_bytes()
                self.assertIn(before, raw)
                p.write_bytes(raw.replace(before, after))
                self.rehash(d, filename)
                with self.assertRaises(AssertionError): verify(root)

    def test_rehashed_world_corruptions(self):
        for mode in ("fractional-warp", "missing-link", "port-coefficient", "port-production", "port-stock", "next-date-raw-field", "next-date-port-date"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = self.copy(tmp)
                name = "next-date" if mode.startswith("next-date") else "second-one"
                d = root / name
                p = d / "before-maint.dat.gz"
                world = bytearray(gzip.decompress(p.read_bytes()))
                if mode == "fractional-warp": record, offset, value = 52, 41, bytes.fromhex("00004081")
                elif mode == "missing-link": record, offset, value = 52, 45, bytes(4)
                elif mode == "port-coefficient": record, offset, value = 3052, 73, bytes(4)
                elif mode == "port-production": record, offset, value = 3052, 61, bytes(4)
                elif mode == "port-stock": record, offset, value = 3052, 49, bytes.fromhex("00000081")
                elif mode == "next-date-port-date":
                    baseline = gzip.decompress((root / "midnight/before-maint.dat.gz").read_bytes())
                    record, offset = 3052, 45
                    at = (record - 1) * 137 + offset
                    value = baseline[at:at + 4]
                else: record, offset, value = 1, 0, b"X"
                at = (record - 1) * 137 + offset
                self.assertNotEqual(world[at:at + len(value)], value)
                world[at:at + len(value)] = value
                p.write_bytes(gzip.compress(world, mtime=0))
                self.rehash(d, p.name, world=True)
                with self.assertRaises(AssertionError): verify(root)

    def test_rehashed_repeat_world_substitution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.copy(tmp)
            d = root / "repeat"
            shutil.copyfile(root / "second-one/before-maint.dat.gz", d / "before-maint.dat.gz")
            self.rehash(d, "before-maint.dat.gz", world=True)
            with self.assertRaises(AssertionError): verify(root)

    def test_false_attribution_and_fingerprints(self):
        for mode in ("initializer", "runtime", "child", "clock", "date", "cycles", "fingerprint"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = self.copy(tmp)
                p = root / "second-one/result.json"
                metadata = json.loads(p.read_text())
                if mode == "initializer": metadata["binaries"]["YT-INIT.EXE"] = "0" * 64
                elif mode == "runtime": metadata["binaries"]["BRUN30.EXE"] = "0" * 64
                elif mode == "child": metadata["binaries"]["YTMAINT.EXE"] = "0" * 64
                elif mode == "clock": metadata["time"] = "00:00:02"
                elif mode == "date": metadata["date"] = "11/03/2026"
                elif mode == "cycles": metadata["cpu_cycles"] = 2000
                else: metadata["fingerprints"]["generated_ports_sha256"] = "0" * 64
                p.write_text(json.dumps(metadata))
                with self.assertRaises(AssertionError): verify(root)

if __name__ == "__main__":
    unittest.main()
