"""Verify packaged DOS avoid-list results and compact Go fixture provenance."""
from pathlib import Path
import gzip
import hashlib
import json
import re

root = Path(__file__).resolve().parents[1]
evidence = root / "research/yt-navigation/avoid-dos"
manifest = json.loads((evidence / "results.json").read_text())
assert manifest == json.loads((root / "internal/game/testdata/dos-avoid.json").read_text())
assert len(manifest["scenarios"]) == 10
cases = {case["name"]:case for case in manifest["scenarios"]}


def number(data, offset):
    raw = data[137+offset:137+offset+4]
    mantissa = int.from_bytes(raw[:3], "little")
    return 0 if not raw[3] else (-1 if mantissa & 0x800000 else 1) * (1+(mantissa & 0x7fffff)/2**23)*2.0**(raw[3]-129)


for case in manifest["scenarios"]:
    directory = evidence / case["name"]
    for label in ("before","after"):
        payload = gzip.decompress((directory / (label+".dat.gz")).read_bytes())
        assert len(payload) == 568687
        assert hashlib.sha256(payload).hexdigest() == case[label+"_sha256"]
        assert number(payload,49) == case["turns_"+label]
        assert number(payload,57) == case["sector_"+label]
    assert case["executable_sha256"] == "c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037"
    assert (case["sector_before"],case["turns_before"]) == (100,500)
    assert (case["sector_after"],case["turns_after"]) == ((101,499) if case["name"]=="avoid-manual" else (100,500))
    text = (directory / "transcript.txt").read_text()
    assert "Returning to Yankee Trader Local Logon Program" in text
    if case["name"] in ("avoid-block","avoid-start","avoid-destination"):
        assert "can't get there without going someplace you dont want to" in text
        assert not case.get("route")
    elif case["name"]!="avoid-manual":
        route = case["route"]
        expected = [100,102,108,109,110] if case["name"] in ("avoid-reroute","avoid-slot30") else [100,101,107,109,110]
        assert route == expected
        assert all(b in manifest["graph"][str(a)] for a,b in zip(route,route[1:]))
    if case["name"]=="avoid-reconnect":
        # The source world is the actual previous session's saved output.
        before = gzip.decompress((directory / "before.dat.gz").read_bytes())
        source = gzip.decompress((evidence / "avoid-reroute/after.dat.gz").read_bytes())
        # Fixture normalization restores the controlled graph/player fields;
        # all other DOS files were copied from that completed session.
        assert case["source_session"] == "avoid-reroute"
        assert before == source, "reconnect changed the source fixture"
        slots = dict((int(a),int(b)) for a,b in re.findall(r"\[\s*(\d+)\s*\]\s*-=>\s*(\d+)",text))
        assert slots == dict.fromkeys(range(1,31),0), "DOS did not reset avoid list"

print("Verified 10 DOS avoid-list sessions, 20 save snapshots, routes, slot boundaries and reconnect reset.")
