"""Verify DOS navigation snapshots, transcripts, routes, and Go fixture provenance."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import re

root = Path(__file__).resolve().parents[1]
evidence = root / "research/yt-navigation/dos"
manifest = json.loads((evidence / "results.json").read_text())
golden = json.loads((root / "internal/game/testdata/dos-navigation.json").read_text())
assert manifest == golden, "Go fixture differs from evidence manifest"


def number(data, record, offset):
    raw = data[(record-1)*137+offset:(record-1)*137+offset+4]
    mantissa = int.from_bytes(raw[:3], "little")
    return 0 if raw[3] == 0 else math.copysign(1 + (mantissa & 0x7fffff)/2**23,
                                              -1 if mantissa & 0x800000 else 1) * 2.0**(raw[3]-129)


expected = {"sensors": (100,500), "sensors-zero": (100,0), "move": (101,499),
            "move-invalid": (100,500), "move-last": (101,0), "move-zero": (100,0),
            "path": (100,500), "path-reverse": (100,500), "path-same": (100,500),
            "path-unreachable": (100,500), "autopilot": (110,496),
            "autopilot-cancel": (100,500), "autopilot-short": (100,3)}
assert {r["name"] for r in manifest["scenarios"]} == set(expected)
for case in manifest["scenarios"]:
    directory = evidence / case["name"]
    assert case["executable_sha256"] == "c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037"
    for label in ("before", "after"):
        raw = gzip.decompress((directory / (label + ".dat.gz")).read_bytes())
        assert len(raw) == 568687
        assert hashlib.sha256(raw).hexdigest() == case[label + "_sha256"]
        assert number(raw,2,49) == case["turns_" + label]
        assert number(raw,2,57) == case["sector_" + label]
    assert (case["sector_after"],case["turns_after"]) == expected[case["name"]]
    text = (directory / "transcript.txt").read_text()
    assert "Returning to Yankee Trader Local Logon Program" in text, case["name"]
    if case["name"].startswith("sensors"):
        scan = text.split("[ Sensors Activated ]")[1].split("[ End Sensor Scan ]")[0]
        assert re.findall(r"Sector: (\d+)",scan) == [str(n) for n in range(101,107)]
        for part in ("Port: Test Port, Selling: Org", "Planet: Test Planet * Forces: 12",
                     "Enemy  - Fighters: 42 - Shields: 7"):
            assert part in scan
    if "route" in case:
        route = case["route"]
        assert case["course_turns"] == len(route)-1
        assert all(b in manifest["graph"][str(a)] for a,b in zip(route,route[1:]))
        assert route == ([101,107,109,110,100] if case["name"] == "path-reverse" else [100,101,107,109,110])

print("Verified 13 DOS sessions, 26 save snapshots, scan transcripts, directed routes and Go fixture provenance.")
