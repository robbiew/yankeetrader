"""Verify committed DOS mine-placement snapshots and expected outcomes."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "archive"
MBF_SPEC = importlib.util.spec_from_file_location("mbf", ARCHIVE / "analysis/yt-maint/experiments.py")
mbf = importlib.util.module_from_spec(MBF_SPEC)
MBF_SPEC.loader.exec_module(mbf)


def load_results(path):
    data = json.loads((path / "results.json").read_text())
    return {scenario["name"]: scenario for scenario in data["scenarios"]}


def check_set(path, expected):
    scenarios = load_results(path)
    assert set(scenarios) == set(expected), (path, set(scenarios))
    for name, (stock, field, turns, marker) in expected.items():
        directory = path / name
        result = scenarios[name]
        assert result["complete"], (name, "incomplete DOS session")
        assert result["executable_sha256"] == "c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037"
        before_bytes = gzip.decompress((directory / "before.dat.gz").read_bytes())
        after_bytes = gzip.decompress((directory / "after.dat.gz").read_bytes())
        transcript = (directory / "transcript.txt").read_text()
        assert hashlib.sha256(before_bytes).hexdigest() == result["before_sha256"]
        assert hashlib.sha256(after_bytes).hexdigest() == result["after_sha256"]
        assert hashlib.sha256((directory / "transcript.txt").read_bytes()).hexdigest() == result["transcript_sha256"]
        sector = result["sector"]
        record = 52 + sector - 1
        assert mbf.get(after_bytes, 2, 129) == stock, (name, "player stock")
        assert mbf.get(after_bytes, record, 129) == field, (name, "sector field")
        assert mbf.get(after_bytes, 2, 49) == turns, (name, "daily turns")
        assert marker in transcript, (name, "transcript marker", marker)
    print(f"verified {len(scenarios)} DOS scenarios in {path.relative_to(ROOT)}")


def main():
    check_set(ROOT / "research/yt-ships/mine-placement-dos", {
        "drop-five": (5, 5, 500, "Sector 100 is now mined!"),
        "drop-default": (10, 0, 500, "Drop how many? [0]"),
        "drop-zero": (10, 0, 500, "Drop how many? [0]"),
        "drop-over-stock": (10, 0, 500, "Drop how many? [0]"),
        "drop-negative": (10, 0, 500, "Drop how many? [0]"),
        "drop-onto-existing": (5, 5, 500, "Sector 100 is now mined!"),
        "drop-without-stock": (0, 0, 500, "You don't HAVE any!"),
        "drop-at-earth": (10, 0, 500, "home 7 sectors mined"),
    })
    check_set(ROOT / "research/yt-ships/mine-placement-home-boundaries", {
        "drop-at-earth": (10, 0, 500, "home 7 sectors mined"),
        "drop-at-home-sector-2": (10, 0, 500, "home 7 sectors mined"),
        "drop-at-home-sector-7": (10, 0, 500, "home 7 sectors mined"),
        "drop-outside-home-sector-8": (5, 5, 500, "Sector 8 is now mined!"),
    })


if __name__ == "__main__":
    main()
