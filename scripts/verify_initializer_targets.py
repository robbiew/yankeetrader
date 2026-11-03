"""Independently audit complete raw pre-maintenance initializer target worlds.

Expected nonrandom records are assembled from native writer rules, not copied
record templates. Random graph/port outcomes remain pinned source inputs; this
script does not claim to regenerate their RNG stream. Known FIELD/FAC residues
are verified byte-exactly rather than normalized as ordinary floating zero.
"""
import argparse
import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
from verify_port_replay_targets import TARGET_WORLD_SHA256, parse_target

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
CASES = ("midnight", "repeat", "second-one", "second-two", "later", "next-date")
# Fixed observed source identities, not a replacement for the native HQ RNG rule.
SOURCE_HQ = {"midnight": 849, "repeat": 849, "second-one": 911,
             "second-two": 2524, "later": 1040, "next-date": 849}
# Native configuration assignments main0720..0af2. Slots without an established
# gameplay semantic are named by byte offset and checked as writer defaults.
DEFAULTS = {41: 11, 49: 500, 53: 51, 57: 3051, 61: 4051, 65: 25,
            69: 1005, 73: 10, 77: 14, 85: -1, 89: 0, 93: 4151,
            97: 0, 101: 5, 105: 300, 109: 0, 113: 0, 121: 1000,
            125: 6324, 129: 0}


def mbf(value):
    """Canonical integer MBF single; residual zero is handled separately."""
    if value == 0:
        return bytes(4)
    assert type(value) is int and abs(value) < 2**24
    significand, exponent = math.frexp(abs(value))
    mantissa = int((significand * 2 - 1) * 2**23)
    if value < 0:
        mantissa |= 0x800000
    return mantissa.to_bytes(3, "little") + bytes([exponent + 128])


def decode(raw):
    assert len(raw) == 4
    if raw[3] == 0:
        return 0
    mantissa = int.from_bytes(raw[:3], "little")
    value = (-1 if mantissa & 0x800000 else 1) * math.ldexp(1 + (mantissa & 0x7fffff) / 2**23, raw[3] - 129)
    assert math.isfinite(value) and value == int(value), "nonintegral initializer numeric field"
    return int(value)


def fresh_record(name=b""):
    assert len(name) <= 41
    return bytearray(name.ljust(41, b" ") + bytes(96))


def write(record, offset, value):
    record[offset:offset + 4] = mbf(value)


def configuration(date, hq, planet=False, scoreboard="YTSCORE.ASC"):
    """Native assignments plus the one cleared flag during planet allocation."""
    name = (scoreboard or "YTSCORE.ASC").encode("ascii")
    assert 1 <= len(name) <= 41 and all(32 <= byte <= 126 for byte in name), "bounded scoreboard path"
    record = fresh_record(name)
    for offset, value in DEFAULTS.items():
        write(record, offset, value)
    write(record, 41, len(name))
    write(record, 45, date.year % 100)  # DATE$ substring main0730..075c
    write(record, 81, date.timetuple().tm_yday - 1)
    if date.timetuple().tm_yday == 1:
        # Native date helper011d..016f computes INT(two-digit-year*.25).
        # In the retained Jan01/2027 subtraction path, exact cancellation
        # preserves that FAC mantissa while clearing the exponent.
        record[81:85] = mbf((date.year % 100) // 4)[:3] + b"\x00"
    write(record, 117, hq)
    if planet:
        write(record, 85, 0)
    return record


def audit_world(world, date, expected_hq=None, scoreboard="YTSCORE.ASC"):
    assert len(world) == 4151 * 137, "complete initializer target size"
    hq = decode(world[117:121])
    assert 1 <= hq <= 2993, "HQ candidate range in original initializer"
    if expected_hq is not None:
        assert hq == expected_hq, "fixed source HQ target"
    config = configuration(date, hq, scoreboard=scoreboard)
    assert world[:137] == config, "complete native configuration record"
    blank = fresh_record()
    for player in range(2, 52):
        assert world[(player - 1) * 137:player * 137] == blank, "complete inactive player record"
    # Port parser also proves last-writer-wins links including the sector7 orphan.
    ports = parse_target(world, date.timetuple().tm_yday)
    slot_values = []
    zero_first = zero_later = 0
    for sector in range(1, 3001):
        start = (50 + sector) * 137
        observed = world[start:start + 137]
        slots = [decode(observed[41 + 4 * i:45 + 4 * i]) for i in range(6)]
        assert all(0 <= dest <= 3000 for dest in slots), "warp destination range"
        expected = fresh_record()
        # Before the first INT->single warp conversion, the record-index path
        # 1672..16b6 leaves this FAC residue. A zero clears only its exponent.
        fac = sector.to_bytes(2, "little") + mbf(sector + 51)[2:3] + b"\x00"
        for column, dest in enumerate(slots):
            if dest:
                fac = mbf(dest)
            else:
                fac = fac[:3] + b"\x00"
                if column == 0:
                    zero_first += 1
                else:
                    zero_later += 1
            expected[41 + 4 * column:45 + 4 * column] = fac
        write(expected, 65, ports["sector_links"][sector - 1])
        if sector == hq:
            write(expected, 81, 10000)
            write(expected, 85, -1)
        if sector == 1:
            write(expected, 105, hq)
        assert observed == expected, (sector, "complete sector record and FAC residues")
        slot_values.append(slots)
    # Original GET configuration then clearing only A566 (offset85) causes all
    # inactive planet rows to retain config fields and scoreboard path.
    planet_record = configuration(date, hq, planet=True, scoreboard=scoreboard)
    for planet in range(4052, 4152):
        assert world[(planet - 1) * 137:planet * 137] == planet_record, "complete reused-FIELD inactive planet record"
    return dict(bytes=len(world), records=4151, configuration=1, inactive_players=50,
                complete_sectors=3000, complete_ports=1000, inactive_planets=100,
                hq=hq, zero_first_warp_fields=zero_first, zero_later_warp_fields=zero_later,
                orphaned_ports=ports["collisions"], source_world_sha256=SHA(world))


def verify(directory=None, check_sources=True):
    directory = directory or ROOT / "research/yt-rng-seeding/clock-dos"
    if check_sources:
        # Independently retained file/binary/clock and graph-validity contracts;
        # no capture-writer or Go model is imported by this target audit.
        from verify_rng_clock import verify as verify_clock
        verify_clock(directory)
    assert {p.name for p in directory.iterdir()} == set(CASES), "six initializer target cases"
    summaries = {}
    for name in CASES:
        folder = directory / name
        metadata = json.loads((folder / "result.json").read_text())
        date = datetime.datetime.strptime(metadata["date"], "%m/%d/%Y").date()
        world = gzip.decompress((folder / "before-maint.dat.gz").read_bytes())
        assert SHA((folder / "before-maint.dat.gz").read_bytes()) == metadata["files"]["before-maint.dat.gz"], "compressed target hash"
        summaries[name] = audit_world(world, date, SOURCE_HQ[name])
        assert SHA(world) == TARGET_WORLD_SHA256[name], "pinned complete initializer target"
    return summaries


def verify_fresh_controls(destination=None):
    """Apply the same complete-record semantics to independent path/date cases."""
    from verify_initializer_controls import verify as verify_controls
    controls = verify_controls() if destination is None else verify_controls(destination)
    assert set(controls) == {"baseline", "score-path", "new-year", "leap-day"}
    results = {}
    for name, control in controls.items():
        # Every independent raw-seed probe reports the same midnight state.
        # This is a bounded source assertion, not inference from an output hash.
        assert control["seed"] == 0xc805
        results[name] = audit_world(control["world"], control["date"], 849, control["scoreboard"])
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", type=Path)
    args = parser.parse_args()
    results = verify(args.directory)
    if args.directory is None:
        results.update({"boundary/" + name: result for name, result in verify_fresh_controls().items()})
    print(json.dumps(results, indent=2))
