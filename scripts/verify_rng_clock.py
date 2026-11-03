"""Independently verify bounded original-initializer clock correlation controls.

No seed formula is inferred. Startup clock logs precede the initializer's seed
operation and therefore do not reveal its exact TIMER value or internal state.
"""
import argparse
from collections import deque
import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
INIT_SHA = "601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2"
RUNTIME_SHA = "3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8"
CASES = {
    "midnight": ("11/02/2026", "00:00:00"),
    "repeat": ("11/02/2026", "00:00:00"),
    "second-one": ("11/02/2026", "00:00:01"),
    "second-two": ("11/02/2026", "00:00:02"),
    "later": ("11/02/2026", "12:34:00"),
    "next-date": ("11/03/2026", "00:00:00"),
}
FILES = {"before-maint.dat.gz", "INIT.LOG", "INITRET.LOG", "ANSWERS.TXT", "COMMANDS.TXT",
         "DOSDATE.LOG", "DOSTIME.LOG", "ENDDATE.LOG", "ENDTIME.LOG", "dosbox.log"}

def get(world, record, offset):
    raw = world[(record - 1) * 137 + offset:(record - 1) * 137 + offset + 4]
    assert len(raw) == 4
    if raw[3] == 0:
        return 0
    mantissa = int.from_bytes(raw[:3], "little")
    return (-1 if mantissa & 0x800000 else 1) * math.ldexp(1 + (mantissa & 0x7fffff) / 2**23, raw[3] - 129)

def fingerprints(world):
    # Reconstruct slices independently; do not import the runner's fingerprinting.
    warp_bytes = bytearray()
    port_bytes = bytearray()
    for sector in range(1, 3001):
        start = (51 + sector - 1) * 137
        warp_bytes.extend(world[start + 41:start + 65])
    for port in range(1, 1001):
        start = (3051 + port - 1) * 137
        for left, right in ((0, 45), (61, 85), (93, 97)):
            port_bytes.extend(world[start + left:start + right])
    return dict(world_sha256=SHA(world), warp_slots_sha256=SHA(warp_bytes), generated_ports_sha256=SHA(port_bytes))

def read_date(raw):
    match = re.search(rb"^Current date: (Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{2}/\d{2}/\d{4})\r?\n", raw)
    assert match, "raw DOS date display"
    result = datetime.datetime.strptime(match[2].decode(), "%m/%d/%Y").date()
    assert result.strftime("%a").encode() == match[1], "DOS weekday/date mismatch"
    return result

def read_time(raw):
    match = re.search(rb"^Current time: (\d{1,2}):(\d{2}):(\d{2})\.(\d{2})(am|pm)\r?\n", raw)
    assert match, "raw DOS time display"
    hour, minute, second, centisecond = map(int, match.groups()[:4])
    assert 0 <= hour <= 12 and 0 <= minute < 60 and 0 <= second < 60
    hour %= 12
    if match[5] == b"pm":
        hour += 12
    return hour * 3600 + minute * 60 + second + centisecond / 100

def validate_world(world, date):
    assert len(world) == 4151 * 137, "whole raw world size"
    assert get(world, 1, 53) == 51 and get(world, 1, 57) == 3051 and get(world, 1, 61) == 4051, "record layout"
    day = date.timetuple().tm_yday
    assert get(world, 1, 81) == day - 1, "configuration generation date"
    for record in range(4052, 4152):
        assert get(world, record, 81) == day - 1, "planet generation date"
    graph = {}
    for sector in range(1, 3001):
        values = [get(world, 51 + sector, 41 + 4 * i) for i in range(6)]
        assert all(v == int(v) and 0 <= v <= 3000 for v in values), "invalid warp destination"
        slots = list(map(int, values))
        assert len([v for v in slots if v]) == len(set(slots) - {0}), "duplicate warp destination"
        assert all(v != sector or sector == 1 for v in slots), "self warp outside Earth"
        graph[sector] = slots
    assert graph[1] == [1, 2, 3, 4, 5, 6], "Earth slots"
    for sector, slots in graph.items():
        for column, dest in enumerate(slots):
            if not dest:
                continue
            if column < 5:
                assert abs(dest - sector) <= 10 and graph[dest][column] == sector, "local warp structure"
            elif graph[dest][5] != sector:
                assert dest == 1 and sector > 6, "non-Earth one-way warp"
    def visit(reverse=False):
        links = {s: [v for v in slots if v] for s, slots in graph.items()}
        if reverse:
            rev = {s: [] for s in links}
            for source, dests in links.items():
                for dest in dests:
                    rev[dest].append(source)
            links = rev
        queue = deque([1])
        seen = {1}
        while queue:
            for dest in links[queue.popleft()]:
                if dest not in seen:
                    seen.add(dest)
                    queue.append(dest)
        return len(seen)
    assert visit() == visit(True) == 3000, "generated graph reachability"
    for port in range(1, 1001):
        record = 3051 + port
        start = (record - 1) * 137
        name = world[start:start + 41].rstrip(b" ")
        assert name and all(32 <= byte <= 126 for byte in name), "port name"
        assert port != 1 or name == b"Earth", "Earth name"
        assert get(world, record, 45) == day - 10, "port backdated generation date"
        location = get(world, record, 93)
        assert location == int(location) and 1 <= location <= 3000, "port location"
        coefficients = [get(world, record, at) for at in (73, 77, 81)]
        assert all(c == int(c) and 1 <= abs(c) <= 100 for c in coefficients) and sum(c > 0 for c in coefficients) == 1, "port coefficients"
        klass = get(world, record, 41)
        assert klass in (1, 2, 3) and coefficients[3 - int(klass)] > 0, "port class"
        for offset in (49, 53, 57):
            assert get(world, record, offset) == 0, "pre-maintenance port stock"
            production = get(world, record, offset + 12)
            assert production == int(production) and 1000 <= production <= 32766, "port production"

def verify(directory):
    assert SHA((ROOT / "archive/dos-original/YT-INIT.EXE").read_bytes()) == INIT_SHA
    assert SHA((ROOT / "archive/dos-original/BRUN30.EXE").read_bytes()) == RUNTIME_SHA
    assert {p.name for p in directory.iterdir()} == set(CASES), "fixed six-case coverage"
    worlds = {}
    observed = {}
    for name, (date_text, clock) in CASES.items():
        folder = directory / name
        metadata = json.loads((folder / "result.json").read_text())
        assert metadata["name"] == name and metadata["recipe"] == "dos-rng-clock-v1"
        assert metadata["date"] == date_text and metadata["time"] == clock and metadata["cpu_cycles"] == 200000, "declared clock recipe"
        assert metadata["maintenance_child"] == "declared-exit-stub"
        assert metadata["binaries"] == {"YT-INIT.EXE": INIT_SHA, "BRUN30.EXE": RUNTIME_SHA,
                                         "YTMAINT.EXE": SHA(bytes.fromhex("b8004ccd21"))}, "unmodified initializer/runtime attribution"
        assert set(metadata["files"]) == FILES and {p.name for p in folder.iterdir()} == FILES | {"result.json"}, "retained files"
        for filename, digest in metadata["files"].items():
            assert SHA((folder / filename).read_bytes()) == digest, (name, filename, "retained hash")
        expected_commands = ["date " + date_text, "time " + clock, "date > DOSDATE.LOG", "time > DOSTIME.LOG",
                             "yt-init < answers.txt > init.log", "echo INITIALIZER_RETURNED > INITRET.LOG",
                             "date > ENDDATE.LOG", "time > ENDTIME.LOG"]
        assert (folder / "COMMANDS.TXT").read_text() == "\n".join(expected_commands) + "\n", "launch command recipe"
        assert (folder / "ANSWERS.TXT").read_bytes() == b"Y\r\n\r\n"
        assert b"<YT-INIT Normal Termination>" in (folder / "INIT.LOG").read_bytes(), "normal initializer termination"
        assert b"INITIALIZER_RETURNED" in (folder / "INITRET.LOG").read_bytes(), "normal shell return"
        date = datetime.datetime.strptime(date_text, "%m/%d/%Y").date()
        assert read_date((folder / "DOSDATE.LOG").read_bytes()) == date, "start date"
        assert read_date((folder / "ENDDATE.LOG").read_bytes()) == date, "end date"
        start, end = (read_time((folder / filename).read_bytes()) for filename in ("DOSTIME.LOG", "ENDTIME.LOG"))
        hh, mm, ss = map(int, clock.split(":"))
        requested = hh * 3600 + mm * 60 + ss
        # DOSBox's clock setter displays a nearby lower BIOS-tick value in these
        # controls. Do not relabel .98/1.97/12:33:59.91 as exact requested seconds.
        assert -0.0001 <= requested - start <= 0.12, "observed start clock differs from requested bound"
        assert 0 < end - start < 120, "start/end clock interval"
        world = gzip.decompress((folder / "before-maint.dat.gz").read_bytes())
        validate_world(world, date)
        values = fingerprints(world)
        assert metadata["fingerprints"] == values, "independent fingerprint reconstruction"
        worlds[name] = world
        observed[name] = dict(requested_time=clock, observed_start_seconds=start, observed_end_seconds=end, **values)
    assert worlds["midnight"] == worlds["repeat"], "fixed-clock repeatability"
    for field in ("warp_slots_sha256", "generated_ports_sha256"):
        assert len({observed[name][field] for name in ("midnight", "second-one", "second-two", "later")}) == 4, "distinct observed clock correlations"
        assert observed["next-date"][field] == observed["midnight"][field], "date-independent generated fields in selected controls"
    # Same clock on Nov3 reproduces generated fields, but routine generation dates
    # change. Pin the complete difference rather than discarding every date-like
    # field or using the whole-world hash as a seed identity.
    normalized = bytearray(worlds["next-date"])
    allowed = [(1, 81)] + [(record, 81) for record in range(4052, 4152)] + [(record, 45) for record in range(3052, 4052)]
    for record, offset in allowed:
        at = (record - 1) * 137 + offset
        normalized[at:at + 4] = worlds["midnight"][at:at + 4]
    assert normalized == worlds["midnight"] and worlds["next-date"] != worlds["midnight"], "only declared date fields differ"
    for name, old in (("midnight", "midnight"), ("later", "later")):
        anchor = gzip.decompress((ROOT / "research/yt-port-generation/dos" / old / "before-maint.dat.gz").read_bytes())
        assert worlds[name] == anchor, "independent prior initializer capture"
    return observed

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "research/yt-rng-seeding/clock-dos")
    print(json.dumps(verify(parser.parse_args().directory), indent=2))
