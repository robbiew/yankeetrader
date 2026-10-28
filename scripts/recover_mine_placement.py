"""Run isolated original-DOS mine placement probes; never mount the archive."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--only", nargs="+")
    parser.add_argument("--dosbox", default="dosbox-staging")
    args = parser.parse_args()
    dest = args.destination.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    archive = ROOT / "archive"
    source = archive / "analysis/yt-combat/experiments/fixture-mines"
    source_data = source / "before.dat"
    mbf_spec = importlib.util.spec_from_file_location("mbf", archive / "analysis/yt-maint/experiments.py")
    mbf = importlib.util.module_from_spec(mbf_spec)
    mbf_spec.loader.exec_module(mbf)
    base = bytearray(source_data.read_bytes())
    # Player 2 is alive in sector 100 with 10 carried mines. Sector records
    # start at 52, so sector 100 is record 151.
    for record, offset, value in ((2, 45, 0), (2, 49, 500), (2, 57, 100),
                                  (2, 129, 10), (52, 129, 0), (151, 129, 0)):
        mbf.put(base, record, offset, value)
    base_bytes = bytes(base)

    cases = [
        ("drop-five", 100, 10, 0, b"D;5"),
        ("drop-default", 100, 10, 0, b"D;\r"),
        ("drop-zero", 100, 10, 0, b"D;0"),
        ("drop-over-stock", 100, 10, 0, b"D;11"),
        ("drop-negative", 100, 10, 0, b"D;-1"),
        ("drop-onto-existing", 100, 10, 3, b"D;5"),
        ("drop-without-stock", 100, 0, 0, b"D;5"),
        ("drop-at-earth", 1, 10, 0, b"D;5"),
        ("drop-at-home-sector-2", 2, 10, 0, b"D;5"),
        ("drop-at-home-sector-7", 7, 10, 0, b"D;5"),
        ("drop-outside-home-sector-8", 8, 10, 0, b"D;5"),
    ]
    if args.only:
        names = {case[0] for case in cases}
        if set(args.only) - names:
            parser.error("unknown probe name")
        cases = [case for case in cases if case[0] in args.only]
    dosbox = shutil.which(args.dosbox)
    if dosbox is None:
        parser.error("DOSBox Staging not found")

    def run(case):
        name, sector, stock, existing, command = case
        directory = dest / name
        directory.mkdir()
        for path in source.iterdir():
            if path.name.lower() != "before.dat" and path.suffix.upper() in (".DAT", ".EXE", ".DOC", ".DEF", ".ASC", ".ANS"):
                shutil.copy2(path, directory / path.name)
        feeder = archive / "analysis/yt-combat/KEYFEED.COM"
        shutil.copy2(feeder, directory / "KEYFEED.COM")
        data = bytearray(base_bytes)
        mbf.put(data, 2, 57, sector)
        mbf.put(data, 2, 129, stock)
        mbf.put(data, 52 + sector - 1, 129, existing)
        before = bytes(data)
        (directory / "YTDATA.DAT").write_bytes(before)
        (directory / "KEYS.TXT").write_bytes(b"\r~~~~~\r~" + command + b"\r~~~~Q;Y\r~~~~" * 5)
        completed = True
        try:
            with (directory / "dosbox.log").open("w") as log:
                subprocess.run(
                    [dosbox, "--noprimaryconf", "--nolocalconf", "--set", "cpu_cycles=200000",
                     "--set", "nosound=true", "-c", f"mount c {directory}", "-c", "c:",
                     "-c", "date 10/24/2026", "-c", "time 00:00:00", "-c", "keyfeed",
                     "-c", "local TESTER > game.log", "-c", "exit"],
                    env={**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"},
                    stdout=log, stderr=subprocess.STDOUT, timeout=130, check=True)
        except subprocess.TimeoutExpired:
            completed = False
        after = (directory / "YTDATA.DAT").read_bytes()
        transcript = (directory / "GAME.LOG").read_bytes().decode("cp437").replace("\r\n", "\n")
        (directory / "transcript.txt").write_text(transcript)
        for label, payload in (("before", before), ("after", after)):
            (directory / (label + ".dat.gz")).write_bytes(gzip.compress(payload, mtime=0))
        digest = lambda payload: hashlib.sha256(payload).hexdigest()
        result = {
            "name": name,
            "complete": completed and "Generating ScoreBoard" in transcript,
            "source_sha256": hashlib.sha256(source_data.read_bytes()).hexdigest(),
            "baseline_sha256": digest(base_bytes),
            "before_sha256": digest(before),
            "after_sha256": digest(after),
            "executable_sha256": hashlib.sha256((directory / "YT.EXE").read_bytes()).hexdigest(),
            "keyfeed_sha256": hashlib.sha256(feeder.read_bytes()).hexdigest(),
            "keys_sha256": hashlib.sha256((directory / "KEYS.TXT").read_bytes()).hexdigest(),
            "transcript_sha256": hashlib.sha256((directory / "transcript.txt").read_bytes()).hexdigest(),
            "dosbox_log_sha256": hashlib.sha256((directory / "dosbox.log").read_bytes()).hexdigest(),
            "dos_date": "10/24/2026",
            "dos_time": "00:00:00",
            "sector": sector,
            "starting_stock": stock,
            "existing_field": existing,
            "command": command.decode("ascii"),
        }
        (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        retained = {"KEYS.TXT", "before.dat.gz", "after.dat.gz", "transcript.txt", "result.json", "dosbox.log"}
        for path in directory.iterdir():
            if path.is_file() and path.name not in retained:
                path.unlink()
        print(name, "complete=" + str(result["complete"]), flush=True)
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, cases))
    (dest / "results.json").write_text(json.dumps({"scenarios": results}, indent=2) + "\n")


if __name__ == "__main__":
    main()
