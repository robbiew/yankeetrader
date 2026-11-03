"""Independent complete pre-maintenance DOS port replay target parser.

This anchors target inputs, not a Go or Python generation model. Every retained
137-byte port record and all sector->port links remain available to comparators;
unknown/reused fields are not silently normalized away.
"""
import argparse
from collections import Counter
import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
CLOCK_CASES = ("midnight", "repeat", "second-one", "second-two", "later", "next-date")
PORT_CASES = ("midnight", "repeat", "later")
TARGET_WORLD_SHA256 = {
    "midnight": "0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d",
    "repeat": "0ee47eae7975827f11636c18887cc9475af3085e62c0f9f5ff98f50eaab3af0d",
    "second-one": "6cccb3fe676d40016b553e3ee7ea6d1a0d44dff0f029550602f44e88ecfda5db",
    "second-two": "6fce61a33be6090dfa681c97f0873b1de926215f727dac1d87be4279c02e2fd7",
    "later": "b2db0e8bc4f0c1ababaaf46d4db7144e7c8fee7afa28c3b76e2c7328cc2ceb7f",
    "next-date": "042fdce8f48d40c5292eebc676a11b7f9f9725537fc98066a178aa394bef1b0c",
}
# Zero-based offsets in record 3051 + portID. Every numeric field is MBF single.
LAYOUT = {
    "class": 41, "production_day": 45, "stock": [49, 53, 57],
    "production": [61, 65, 69], "coefficient": [73, 77, 81],
    "name_length": 85, "treasury": 89, "sector": 93, "owner": 97,
    "opaque": [101, 105, 109, 113, 117, 121, 125, 129],
}


def number(raw):
    assert len(raw) == 4
    if raw[3] == 0:
        return 0
    mantissa = int.from_bytes(raw[:3], "little")
    value = (-1 if mantissa & 0x800000 else 1) * math.ldexp(1 + (mantissa & 0x7fffff) / 2**23, raw[3] - 129)
    assert math.isfinite(value) and value == int(value), "noninteger pre-maintenance port field"
    return int(value)


def field(world, record, offset):
    at = (record - 1) * 137 + offset
    return number(world[at:at + 4])


def parse_target(world, expected_day):
    """Parse/check all 1,000 original port records, preserving complete bytes."""
    assert len(world) == 4151 * 137, "complete target world"
    assert field(world, 1, 53) == 51 and field(world, 1, 57) == 3051 and field(world, 1, 61) == 4051, "target record bases"
    records = []
    expected_sector_links = {}
    collisions = []
    for port in range(1, 1001):
        start = (3050 + port) * 137
        raw = world[start:start + 137]
        name = raw[:41].rstrip(b" ")
        assert name and all(32 <= char <= 126 for char in name) and raw[:41] == name.ljust(41, b" "), "padded port name"
        values = {offset: number(raw[offset:offset + 4]) for offset in range(41, 133, 4)}
        assert values[85] == len(name), "saved port name length"
        assert values[41] in (1, 2, 3), "port class"
        assert values[45] == expected_day - 10, "pre-maintenance production day"
        assert all(raw[offset:offset + 4] == bytes.fromhex("0000a000") for offset in (49, 53, 57, 89, 97, 101, 105, 109, 129)), "fresh zero residue encoding"
        assert raw[113:117] == bytes(4), "opaque field113 encoding"
        rates = [values[offset] for offset in (61, 65, 69)]
        assert all(1000 <= rate <= 32766 for rate in rates), "production range"
        coefficients = [values[offset] for offset in (73, 77, 81)]
        assert all(1 <= abs(c) <= 100 for c in coefficients) and sum(c > 0 for c in coefficients) == 1, "coefficient ranges/signs"
        assert coefficients[3 - values[41]] > 0, "class-to-seller mapping"
        sector = values[93]
        assert 1 <= sector <= 3000, "port sector"
        if port <= 4:
            assert sector == (1, 3, 5, 7)[port - 1], "first port placement"
        if port == 1:
            assert name == b"Earth", "first port name"
            # Earth retains these three shared configuration-buffer values.
            # Preserve exact bytes without inventing normal port-field semantics.
            for offset in (117, 121, 125):
                assert raw[offset:offset + 4] == world[offset:offset + 4], "Earth shared-buffer tail"
        else:
            assert raw[117:129] == bytes(12), "ordinary port opaque tail"
        assert raw[133:137] == bytes(4), "unmapped record tail"
        if sector in expected_sector_links:
            collisions.append(dict(sector=sector, overwritten=expected_sector_links[sector], winner=port))
        expected_sector_links[sector] = port
        records.append(dict(id=port, name=name.decode("ascii"), raw_hex=raw.hex(), numeric_fields=values,
                            klass=values[41], production_day=values[45], stock=[values[o] for o in (49, 53, 57)],
                            production=rates, coefficient=coefficients, name_length=values[85], treasury=values[89],
                            sector=sector, owner=values[97], opaque={o: values[o] for o in range(101, 133, 4)}))
    sector_links = []
    for sector in range(1, 3001):
        link = field(world, 51 + sector, 65)
        assert link == expected_sector_links.get(sector, 0), "last-writer-wins sector port link"
        sector_links.append(link)
    block = world[3051 * 137:4051 * 137]
    return dict(source_world_sha256=SHA(world), complete_port_block_sha256=SHA(block), records=records,
                sector_links=sector_links, collisions=collisions)


def compare_targets(expected, actual):
    """Return explicit first differences without throwing away unknown bytes."""
    differences = []
    assert len(expected["records"]) == len(actual["records"]) == 1000
    for left, right in zip(expected["records"], actual["records"]):
        if left["raw_hex"] == right["raw_hex"]:
            continue
        a, b = bytes.fromhex(left["raw_hex"]), bytes.fromhex(right["raw_hex"])
        differences.append(dict(port=left["id"], offsets=[i for i, (x, y) in enumerate(zip(a, b)) if x != y],
                                expected_name=left["name"], actual_name=right["name"]))
    link_differences = [s + 1 for s, (left, right) in enumerate(zip(expected["sector_links"], actual["sector_links"])) if left != right]
    return dict(port_differences=differences, sector_link_differences=link_differences)


def verify(clock_directory=None, port_directory=None, check_source_verifiers=True):
    clock_directory = clock_directory or ROOT / "research/yt-rng-seeding/clock-dos"
    port_directory = port_directory or ROOT / "research/yt-port-generation/dos"
    if check_source_verifiers:
        # Existing source-specific verifiers validate the original binary/recipe,
        # normal-return/clock files and complete retained hashes as a separate layer.
        from verify_rng_clock import verify as verify_clock
        from verify_port_generation import verify as verify_ports
        verify_clock(clock_directory)
        verify_ports(port_directory)
    targets = {}
    for name in CLOCK_CASES:
        directory = clock_directory / name
        metadata = json.loads((directory / "result.json").read_text())
        date = datetime.datetime.strptime(metadata["date"], "%m/%d/%Y").date()
        world = gzip.decompress((directory / "before-maint.dat.gz").read_bytes())
        assert SHA((directory / "before-maint.dat.gz").read_bytes()) == metadata["files"]["before-maint.dat.gz"], "target capture hash"
        targets[name] = parse_target(world, date.timetuple().tm_yday)
        assert SHA(world) == TARGET_WORLD_SHA256[name], "pinned replay target world"
    for name in PORT_CASES:
        directory = port_directory / name
        metadata = json.loads((directory / "result.json").read_text())
        date = datetime.datetime.strptime(metadata["date"], "%m/%d/%Y").date()
        world = gzip.decompress((directory / "before-maint.dat.gz").read_bytes())
        assert SHA((directory / "before-maint.dat.gz").read_bytes()) == metadata["files"]["before-maint.dat.gz"], "prior target capture hash"
        old = parse_target(world, date.timetuple().tm_yday)
        assert compare_targets(old, targets[name]) == dict(port_differences=[], sector_link_differences=[]), "all prior pre-maintenance port records/links"
    assert compare_targets(targets["midnight"], targets["repeat"]) == dict(port_differences=[], sector_link_differences=[]), "repeat port records/links"
    date_compare = compare_targets(targets["midnight"], targets["next-date"])
    assert len(date_compare["port_differences"]) == 1000 and not date_compare["sector_link_differences"], "next-date record coverage"
    for left, right in zip(targets["midnight"]["records"], targets["next-date"]["records"]):
        a, b = bytearray.fromhex(left["raw_hex"]), bytearray.fromhex(right["raw_hex"])
        assert left["production_day"] + 1 == right["production_day"]
        b[45:49] = a[45:49]
        assert a == b, "next-date exact port difference is production day only"
    assert targets["second-two"]["collisions"] == [dict(sector=7, overwritten=4, winner=274)], "retained duplicate-location counterexample"
    for name in ("midnight", "repeat", "second-one", "later", "next-date"):
        assert not targets[name]["collisions"], "selected unique-location control"
    return targets


def summary(target):
    records = target["records"]
    return dict(source_world_sha256=target["source_world_sha256"], complete_port_block_sha256=target["complete_port_block_sha256"],
                ports=len(records), distinct_locations=len(set(p["sector"] for p in records)), collisions=target["collisions"],
                classes=dict(sorted(Counter(p["klass"] for p in records).items())),
                name_length_range=[min(p["name_length"] for p in records), max(p["name_length"] for p in records)],
                production_range=[min(min(p["production"]) for p in records), max(max(p["production"]) for p in records)])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clock-directory", type=Path)
    parser.add_argument("--port-directory", type=Path)
    args = parser.parse_args()
    print(json.dumps({name: summary(target) for name, target in verify(args.clock_directory, args.port_directory).items()}, indent=2))
