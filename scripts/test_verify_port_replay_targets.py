"""Semantic tests for complete pre-maintenance replay inputs and comparisons."""
import copy
import gzip
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_port_replay_targets import ROOT, SHA, compare_targets, parse_target, verify

CLOCK = ROOT / "research/yt-rng-seeding/clock-dos"
PORTS = ROOT / "research/yt-port-generation/dos"


def encode(value):
    if value == 0:
        return bytes(4)
    fraction, exponent = math.frexp(abs(value))
    mantissa = int((fraction * 2 - 1) * 2**23)
    if value < 0:
        mantissa |= 0x800000
    return mantissa.to_bytes(3, "little") + bytes([exponent + 128])


class PortReplayTargetTests(unittest.TestCase):
    def raw(self, name="midnight"):
        return gzip.decompress((CLOCK / name / "before-maint.dat.gz").read_bytes())

    def put(self, world, port, offset, value):
        at = (3050 + port) * 137 + offset
        world[at:at + len(value)] = value

    def test_all_retained_records_and_collision(self):
        targets = verify()
        self.assertEqual(len(targets), 6)
        self.assertTrue(all(len(t["records"]) == 1000 for t in targets.values()))
        self.assertTrue(all(len(t["sector_links"]) == 3000 for t in targets.values()))
        self.assertEqual(targets["second-two"]["collisions"], [dict(sector=7, overwritten=4, winner=274)])
        self.assertEqual(targets["second-two"]["sector_links"][6], 274)
        self.assertEqual(targets["second-two"]["records"][3]["sector"], 7)
        self.assertEqual(targets["second-two"]["records"][273]["sector"], 7)
        self.assertEqual(targets["midnight"]["records"][0]["opaque"][117], 849)

    def test_semantic_parser_corruptions_without_hash_guard(self):
        modes = ("fractional", "class", "name-length", "date", "rate", "coefficient", "stock", "owner",
                 "normalize-zero", "ordinary-tail", "earth-tail", "unmapped-tail", "padded-name", "wrong-sector-link")
        for mode in modes:
            with self.subTest(mode=mode):
                world = bytearray(self.raw())
                if mode == "fractional": self.put(world, 2, 61, encode(1000.5))
                elif mode == "class": self.put(world, 2, 41, encode(1))
                elif mode == "name-length": self.put(world, 2, 85, encode(10))
                elif mode == "date": self.put(world, 2, 45, encode(297))
                elif mode == "rate": self.put(world, 2, 61, encode(999))
                elif mode == "coefficient": self.put(world, 2, 73, encode(-6))
                elif mode == "stock": self.put(world, 2, 49, encode(1))
                elif mode == "owner": self.put(world, 2, 97, encode(1))
                elif mode == "normalize-zero": self.put(world, 2, 49, bytes(4))
                elif mode == "ordinary-tail": self.put(world, 2, 117, encode(849))
                elif mode == "earth-tail": self.put(world, 1, 117, encode(848))
                elif mode == "unmapped-tail": self.put(world, 2, 133, b"\x01")
                elif mode == "padded-name": self.put(world, 2, 0, b"\x00")
                else:
                    at = (50 + 3) * 137 + 65
                    world[at:at + 4] = encode(3)  # sector3 must link port2
                with self.assertRaises(AssertionError): parse_target(world, 306)

    def test_zero_residue_preserved_in_complete_records(self):
        target = parse_target(self.raw(), 306)
        raw = bytes.fromhex(target["records"][1]["raw_hex"])
        self.assertEqual(raw[49:53], bytes.fromhex("0000a000"))
        self.assertEqual(target["records"][1]["stock"], [0, 0, 0])
        self.assertNotEqual(raw[49:53], bytes(4))

    def test_valid_semantic_changes_are_compared_byte_exactly(self):
        original = parse_target(self.raw(), 306)
        for mode in ("valid-rate", "valid-name", "opaque-shared-tail"):
            with self.subTest(mode=mode):
                world = bytearray(self.raw())
                if mode == "valid-rate":
                    current = original["records"][16]["production"][0]
                    self.put(world, 17, 61, encode(current + 1))
                elif mode == "valid-name":
                    self.put(world, 17, 0, b"X" if original["records"][16]["name"][0] != "X" else b"Y")
                else:
                    self.put(world, 1, 117, encode(848))
                    world[117:121] = encode(848)
                changed = parse_target(world, 306)
                diff = compare_targets(original, changed)
                self.assertEqual(len(diff["port_differences"]), 1)
                self.assertFalse(diff["sector_link_differences"])
                self.assertTrue(diff["port_differences"][0]["offsets"])

    def test_rehashed_valid_change_cannot_redefine_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            clock = Path(tmp) / "clock-dos"
            shutil.copytree(CLOCK, clock)
            folder = clock / "second-one"
            p = folder / "before-maint.dat.gz"
            world = bytearray(gzip.decompress(p.read_bytes()))
            parsed = parse_target(world, 306)
            self.put(world, 17, 61, encode(parsed["records"][16]["production"][0] + 1))
            p.write_bytes(gzip.compress(world, mtime=0))
            metadata_path = folder / "result.json"
            metadata = json.loads(metadata_path.read_text())
            metadata["files"][p.name] = SHA(p.read_bytes())
            metadata_path.write_text(json.dumps(metadata))
            with self.assertRaisesRegex(AssertionError, "pinned replay target"):
                verify(clock, PORTS, check_source_verifiers=False)

    def test_compare_does_not_hide_sector_link_changes(self):
        original = parse_target(self.raw(), 306)
        changed = copy.deepcopy(original)
        changed["sector_links"][2] = 3
        self.assertEqual(compare_targets(original, changed)["sector_link_differences"], [3])

if __name__ == "__main__":
    unittest.main()
