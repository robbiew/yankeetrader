"""Run isolated DOS navigation probes. Never mount or write the archive itself."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--archive", type=Path, default=Path(__file__).resolve().parents[1] / "archive")
    parser.add_argument("--source", type=Path, help="Use a completed disposable session as the fixture source")
    parser.add_argument("--only", nargs="*", help="Run only named probes")
    parser.add_argument("--dosbox", default="dosbox-staging", help="DOSBox Staging command or executable path")
    args = parser.parse_args()
    dosbox = shutil.which(args.dosbox)
    if dosbox is None:
        parser.error("DOSBox Staging not found; install dosbox-staging on PATH or pass --dosbox /path/to/executable")
    archive = args.archive.resolve()
    args.destination.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location("mbf", archive / "analysis/yt-maint/experiments.py")
    mbf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mbf)
    source = args.source or archive / "analysis/yt-combat/experiments/fixture-team-captain"
    graph = {100: [101, 102, 103, 104, 105, 106], 101: [107], 102: [108],
             103: [100], 104: [100], 105: [100], 106: [100], 107: [109],
             108: [109], 109: [110], 110: [100]}
    scenarios = [
        ("sensors", 500, "S", {}),
        ("sensors-zero", 0, "S", {}),
        ("move", 500, "M;101", {}),
        ("move-invalid", 500, "M;110", {}),
        ("move-last", 1, "M;101", {}),
        ("path", 500, "C;10;100;110;1", {}),
        ("path-reverse", 500, "C;10;101;100;1", {}),
        ("autopilot", 500, "C;3;110;Y", {}),
        ("autopilot-cancel", 500, "C;3;110;N;1", {}),
        ("autopilot-short", 3, "C;3;110\r~~\r~1", {}),
        ("move-zero", 0, "M;101", {}),
        ("path-same", 500, "C;10;100;100\r~~\r~1", {}),
        ("path-unreachable", 500, "C;10;100;111\r~~\r~1", {}),
        ("avoid-reroute", 500, "C;7;1;101;10;100;110;1", {}),
        ("avoid-block", 500, "C;7;1;101;7;2;102;10;100;110\r~~\r~1", {}),
        ("avoid-destination", 500, "C;7;1;110;10;100;110\r~~\r~1", {}),
        ("avoid-start", 500, "C;7;1;100;10;100;110\r~~\r~1", {}),
        ("avoid-manual", 500, "C;7;1;101;1;M;101", {}),
        ("avoid-clear", 500, "C;7;1;101;7;1;0;10;100;110;1", {}),
        ("avoid-slot30", 500, "C;7;30;101;10;100;110;1", {}),
        ("avoid-slot31", 500, "C;7;31;10;100;110;1", {}),
        ("avoid-invalid-sector", 500, "C;7;1;3001;10;100;110;1", {}),
        ("avoid-reconnect", 500, "C;7;0;10;100;110;1", {}),

    ]
    if not args.only:
        scenarios = [s for s in scenarios if not s[0].startswith("avoid-")]
    if args.only:
        scenarios = [s for s in scenarios if s[0] in args.only]
        if len(scenarios) != len(set(args.only)):
            parser.error("unknown or repeated probe name")

    def run(scenario):
        name, turns, command, overrides = scenario
        dest = args.destination / name
        dest.mkdir()
        for p in source.iterdir():
            if p.suffix.upper() in (".DAT", ".EXE", ".DOC", ".DEF", ".ASC", ".ANS"):
                shutil.copy2(p, dest / p.name)
        shutil.copy2(archive / "analysis/yt-combat/KEYFEED.COM", dest / "KEYFEED.COM")
        data = bytearray((dest / "YTDATA.DAT").read_bytes())
        for sector, warps in graph.items():
            record = 51 + sector
            data[(record-1)*137:record*137] = bytes(137)
            for offset, target in zip(range(41, 65, 4), warps):
                mbf.put(data, record, offset, target)
        # Visible ship and named port/planet in three distinct adjacent sectors.
        for offset, value in {45: 0, 49: turns, 57: 100, 89: 0, 105: 0, 125: 0}.items():
            mbf.put(data, 2, offset, value)
        for offset, value in {45: 0, 57: 103, 61: 42, 53: 7, 89: 0, 125: 0}.items():
            mbf.put(data, 3, offset, value)
        mbf.put(data, 152, 65, 2)
        mbf.put(data, 3053, 93, 101)
        mbf.put(data, 153, 93, 2)
        mbf.put(data, 4053, 73, 0)
        mbf.put(data, 4053, 77, 12)
        for (record, offset), value in overrides.items():
            mbf.put(data, record, offset, value)
        before = bytes(data)
        (dest / "YTDATA.DAT").write_bytes(before)
        keys = ("\r~~~~~\r~" + command + "\r~~~~" + "\r" * 8 + "Q;Y\r").encode()
        (dest / "KEYS.TXT").write_bytes(keys)
        with (dest / "dosbox.log").open("w") as log:
            subprocess.run([dosbox, "--noprimaryconf", "--nolocalconf",
                            "--set", "cpu_cycles=200000", "--set", "nosound=true",
                            "-c", f"mount c {dest.resolve()}", "-c", "c:",
                            "-c", "date 10/24/2026", "-c", "time 00:00:00",
                            "-c", "keyfeed", "-c", "local TESTER > game.log", "-c", "exit"],
                           env={**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"},
                           stdout=log, stderr=subprocess.STDOUT, timeout=55, check=True)
        after = (dest / "YTDATA.DAT").read_bytes()
        transcript = (dest / "GAME.LOG").read_bytes().decode("cp437").replace("\\r\\n", "\n")
        (dest / "transcript.txt").write_text(transcript)
        for label, payload in [("before", before), ("after", after)]:
            (dest / (label + ".dat.gz")).write_bytes(gzip.compress(payload, mtime=0))
        result = {"name": name, "command": command, "before_sha256": hashlib.sha256(before).hexdigest(),
                  "after_sha256": hashlib.sha256(after).hexdigest(),
                  "turns_before": int(mbf.get(before, 2, 49)), "turns_after": int(mbf.get(after, 2, 49)),
                  "sector_before": int(mbf.get(before, 2, 57)), "sector_after": int(mbf.get(after, 2, 57)),
                  "executable_sha256": hashlib.sha256((dest / "YT.EXE").read_bytes()).hexdigest()}
        (dest / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, scenarios))
    (args.destination / "results.json").write_text(json.dumps({"graph": graph, "scenarios": results}, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
