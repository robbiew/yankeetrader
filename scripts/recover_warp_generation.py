"""Capture declared copied-initializer controls for DOS warp-generation phases."""
import argparse
import gzip
import hashlib
import json
import os
import math
import re
from pathlib import Path
import shutil
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
ORIGINAL_SHA = "601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2"
RUNTIME_SHA = "3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8"
EXIT_STUB = bytes.fromhex("b8004ccd21")
# Original file bytes pinned before applying patches to disposable copies only.
PATCHES = {
    "skip-repair-shortcuts": (0x1420, "bf50a6", "e91404"),
    "disable-random-wormholes": (0x2F4C, "f6287c80", "00000081"),
    "skip-shortcuts": (0x1557, "cd3fbc", "e9dd02"),
}
CASES = {
    "original": [],
    "no-repair": ["skip-repair-shortcuts"],
    "local-only": ["skip-repair-shortcuts", "disable-random-wormholes"],
    "repair-only": ["skip-shortcuts"],
}

def run(destination):
    original = (ROOT / "archive/dos-original/YT-INIT.EXE").read_bytes()
    runtime = (ROOT / "archive/dos-original/BRUN30.EXE").read_bytes()
    assert SHA(original) == ORIGINAL_SHA and SHA(runtime) == RUNTIME_SHA
    assert struct.unpack_from("<H", original, 8)[0] * 16 == 512
    for at, before, after in PATCHES.values():
        assert original[at:at + len(bytes.fromhex(before))].hex() == before
        assert len(before) == len(after)
    destination.mkdir(parents=True, exist_ok=False)
    for name, names in CASES.items():
        d = destination / name
        d.mkdir()
        binary = bytearray(original)
        patches = []
        for patchname in names:
            at, before, after = PATCHES[patchname]
            binary[at:at + len(bytes.fromhex(after))] = bytes.fromhex(after)
            patches.append(dict(name=patchname, offset=at, before=before, after=after))
        (d / "YT-INIT.EXE").write_bytes(binary)
        (d / "BRUN30.EXE").write_bytes(runtime)
        (d / "YTMAINT.EXE").write_bytes(EXIT_STUB)
        (d / "ANSWERS.TXT").write_bytes(b"Y\r\n\r\n")
        metadata = dict(name=name, recipe="dos-warp-generation-v1", date="11/02/2026", time="00:00:00",
                        initializer_original_sha256=ORIGINAL_SHA, initializer_copied_sha256=SHA(binary),
                        patches=patches, maintenance_child="declared-exit-stub",
                        binaries={"YT-INIT.EXE": SHA(binary), "BRUN30.EXE": RUNTIME_SHA, "YTMAINT.EXE": SHA(EXIT_STUB)})
        commands = ["mount c " + str(d), "c:", "date 11/02/2026", "time 00:00:00",
                    "yt-init < answers.txt > init.log", "echo INITIALIZER_RETURNED > INITRET.LOG", "exit"]
        with (d / "init-dosbox.log").open("w") as output:
            subprocess.run([shutil.which("dosbox-staging"), "--noprimaryconf", "--nolocalconf",
                            "--set", "cpu_cycles=200000", "--set", "nosound=true"] +
                           [x for command in commands for x in ("-c", command)],
                           env={**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"},
                           stdout=output, stderr=subprocess.STDOUT, check=True, timeout=120)
        world = (d / "YTDATA.DAT").read_bytes()
        assert b"<YT-INIT Normal Termination>" in (d / "INIT.LOG").read_bytes()
        assert b"INITIALIZER_RETURNED" in (d / "INITRET.LOG").read_bytes()
        assert len(world) == 4151 * 137
        (d / "before-maint.dat.gz").write_bytes(gzip.compress(world, mtime=0))
        keep = ["before-maint.dat.gz", "INIT.LOG", "INITRET.LOG", "ANSWERS.TXT", "init-dosbox.log"]
        metadata["files"] = {n: SHA((d / n).read_bytes()) for n in keep}
        (d / "result.json").write_text(json.dumps(metadata, indent=2) + "\n")
        for p in d.iterdir():
            if p.name not in keep + ["result.json"]:
                p.unlink()
        print(name, len(world), metadata["initializer_copied_sha256"], flush=True)

def export_fixture(directory, fixture):
    # Writer-side decoder intentionally independent from the verifier.
    def decode(raw):
        if raw[3] == 0: return 0
        mantissa = int.from_bytes(raw[:3], "little")
        value = (-1 if mantissa & 0x800000 else 1) * math.ldexp(1 + (mantissa & 0x7fffff) / 2**23, raw[3] - 129)
        assert value == int(value)
        return int(value)
    cases = {}
    for name in ("no-repair", "repair-only", "original"):
        d = directory / name
        world = gzip.decompress((d / "before-maint.dat.gz").read_bytes())
        metadata = json.loads((d / "result.json").read_text())
        slots = [[0] * 6]
        for sector in range(1, 3001):
            at = (50 + sector) * 137 + 41
            slots.append([decode(world[at + 4*i:at + 4*i + 4]) for i in range(6)])
        cases[name] = dict(source_world_sha256=SHA(world), initializer_original_sha256=ORIGINAL_SHA,
                           initializer_copied_sha256=metadata["initializer_copied_sha256"], slots=slots)
    pairs = [[int(a), int(b)] for a, b in re.findall(rb"Sector (\d+) has been linked to sector (\d+)",
             (directory / "repair-only/INIT.LOG").read_bytes())]
    payload = dict(format=1, cases=cases, repair_pairs=pairs)
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_bytes(gzip.compress(json.dumps(payload, separators=(",", ":")).encode() + b"\n", mtime=0))
    print("fixture", fixture, "repair pairs", len(pairs), flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    run(args.destination.resolve())
    if args.fixture:
        export_fixture(args.destination.resolve(), args.fixture.resolve())
