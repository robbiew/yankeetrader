"""Capture original DOS initializer repeatability under bounded clock changes.

Only disposable maintenance children are replaced. Original initializer/runtime
bytes are verified and copied unchanged. World comparisons establish observed
clock correlations, not a general RANDOMIZE seed formula.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
INIT_SHA = "601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2"
RUNTIME_SHA = "3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8"
EXIT_STUB = bytes.fromhex("b8004ccd21")
CASES = (
    ("midnight", "11/02/2026", "00:00:00"),
    ("repeat", "11/02/2026", "00:00:00"),
    ("second-one", "11/02/2026", "00:00:01"),
    ("second-two", "11/02/2026", "00:00:02"),
    ("later", "11/02/2026", "12:34:00"),
    ("next-date", "11/03/2026", "00:00:00"),
)

def fingerprints(world):
    # Raw packed bytes avoid a decoder/rounding dependency in correlation results.
    assert len(world) == 4151 * 137
    warps = b"".join(world[(50 + sector) * 137 + 41:(50 + sector) * 137 + 65]
                     for sector in range(1, 3001))
    # Exclude per-port date offset45; names/class, production, coefficients and
    # locations remain direct observations of generated outcomes.
    ports = b"".join(world[(3050 + port) * 137:(3050 + port) * 137 + 45] +
                     world[(3050 + port) * 137 + 61:(3050 + port) * 137 + 85] +
                     world[(3050 + port) * 137 + 93:(3050 + port) * 137 + 97]
                     for port in range(1, 1001))
    return dict(world_sha256=SHA(world), warp_slots_sha256=SHA(warps), generated_ports_sha256=SHA(ports))

def run(destination):
    original = (ROOT / "archive/dos-original/YT-INIT.EXE").read_bytes()
    runtime = (ROOT / "archive/dos-original/BRUN30.EXE").read_bytes()
    assert SHA(original) == INIT_SHA and SHA(runtime) == RUNTIME_SHA
    executable = shutil.which("dosbox-staging")
    if executable is None:
        raise RuntimeError("DOSBox Staging is required")
    destination.mkdir(parents=True, exist_ok=False)
    for name, date, clock in CASES:
        directory = destination / name
        directory.mkdir()
        (directory / "YT-INIT.EXE").write_bytes(original)
        (directory / "BRUN30.EXE").write_bytes(runtime)
        (directory / "YTMAINT.EXE").write_bytes(EXIT_STUB)
        (directory / "ANSWERS.TXT").write_bytes(b"Y\r\n\r\n")
        commands = ["date " + date, "time " + clock, "date > DOSDATE.LOG", "time > DOSTIME.LOG",
                    "yt-init < answers.txt > init.log", "echo INITIALIZER_RETURNED > INITRET.LOG",
                    "date > ENDDATE.LOG", "time > ENDTIME.LOG"]
        (directory / "COMMANDS.TXT").write_text("\n".join(commands) + "\n")
        with (directory / "dosbox.log").open("w") as output:
            subprocess.run([executable, "--noprimaryconf", "--nolocalconf", "--set", "cpu_cycles=200000",
                            "--set", "nosound=true"] +
                           [part for command in ["mount c " + str(directory), "c:"] + commands + ["exit"]
                            for part in ("-c", command)],
                           env={**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"},
                           stdout=output, stderr=subprocess.STDOUT, check=True, timeout=120)
        assert b"<YT-INIT Normal Termination>" in (directory / "INIT.LOG").read_bytes()
        assert b"INITIALIZER_RETURNED" in (directory / "INITRET.LOG").read_bytes()
        world = (directory / "YTDATA.DAT").read_bytes()
        assert len(world) == 4151 * 137
        (directory / "before-maint.dat.gz").write_bytes(gzip.compress(world, mtime=0))
        keep = ("before-maint.dat.gz", "INIT.LOG", "INITRET.LOG", "ANSWERS.TXT", "COMMANDS.TXT",
                "DOSDATE.LOG", "DOSTIME.LOG", "ENDDATE.LOG", "ENDTIME.LOG", "dosbox.log")
        metadata = dict(name=name, recipe="dos-rng-clock-v1", date=date, time=clock,
                        cpu_cycles=200000, maintenance_child="declared-exit-stub",
                        binaries={"YT-INIT.EXE": INIT_SHA, "BRUN30.EXE": RUNTIME_SHA, "YTMAINT.EXE": SHA(EXIT_STUB)},
                        fingerprints=fingerprints(world), files={filename: SHA((directory / filename).read_bytes()) for filename in keep})
        (directory / "result.json").write_text(json.dumps(metadata, indent=2) + "\n")
        for p in directory.iterdir():
            if p.name not in keep + ("result.json",):
                p.unlink()
        print(name, json.dumps(metadata["fingerprints"]), flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    run(parser.parse_args().destination.resolve())
