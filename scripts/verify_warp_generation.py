"""Independent byte-contract and graph-phase verifier for retained DOS controls."""
import argparse
from collections import Counter, deque
import gzip
import hashlib
import json
import re
from pathlib import Path
import struct
from verify_port_generation import get

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
INIT_SHA = "601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2"
RUNTIME_SHA = "3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8"
# Deliberately independent of the capture runner's recipe implementation.
CONTRACTS = {
    "original": [],
    "no-repair": [("skip-repair-shortcuts", 0x1420, "bf50a6", "e91404")],
    "local-only": [("skip-repair-shortcuts", 0x1420, "bf50a6", "e91404"),
                   ("disable-random-wormholes", 0x2f4c, "f6287c80", "00000081")],
    "repair-only": [("skip-shortcuts", 0x1557, "cd3fbc", "e9dd02")],
}
FILES = {"before-maint.dat.gz", "INIT.LOG", "INITRET.LOG", "ANSWERS.TXT", "init-dosbox.log"}

def verify_native(directory):
    binary=(ROOT/"archive/dos-original/YT-INIT.EXE").read_bytes()
    assert SHA(binary)==INIT_SHA
    header=struct.unpack_from("<H",binary,8)[0]*16
    image=bytearray(binary[header:])
    relocation=struct.unpack_from("<H",binary,24)[0]
    for i in range(struct.unpack_from("<H",binary,6)[0]):
        offset,segment=struct.unpack_from("<HH",binary,relocation+4*i)
        at=segment*16+offset
        struct.pack_into("<H",image,at,(struct.unpack_from("<H",image,at)[0]+0x1000)&0xffff)
    required={"0x1004f":30,"0x10d11":1300,"0x11220":1050,"0x11637":384,
              "0x12f44":12,"0x12ff6":4,"0x12d44":12,"0x12df6":4}
    records=json.loads((Path(directory)/"rea.json").read_text())["records"]
    assert len(records)==len(required),"native observation coverage"
    observed=set()
    for record in records:
        value=record["normalized_result"];address=value["address"]
        assert record["operation"]=="read_bytes" and record["subject"]["digest"]["sha256"]==INIT_SHA,"native target"
        assert address in required and address not in observed,"unexpected native range"
        size=required[address]
        assert record["parameters"]=={"address":address,"length":size},"native read contract"
        assert value["complete"] and value["requested_bytes"]==value["returned_bytes"]==size,"incomplete native read"
        at=int(address,16)-0x10000
        assert bytes.fromhex(value["bytes_hex"])==image[at:at+size],"native byte mismatch"
        observed.add(address)
    assert observed==set(required),"native required ranges"

def rows(world):
    assert len(world) == 4151 * 137, "complete world size"
    assert get(world, 1, 53) == 51 and get(world, 1, 57) == 3051, "sector record bases"
    graph = []
    for sector in range(1, 3001):
        row = [get(world, 51 + sector, 41 + 4 * column) for column in range(6)]
        assert all(d == int(d) and 0 <= d <= 3000 for d in row), "noninteger or invalid destination"
        row = list(map(int, row))
        assert len([d for d in row if d]) == len(set(row) - {0}), "duplicate destination"
        assert all(d != sector or sector == 1 for d in row), "unexpected self link"
        graph.append(row)
    assert graph[0] == [1, 2, 3, 4, 5, 6], "Earth slot order"
    for sector, row in enumerate(graph, 1):
        for column, dest in enumerate(row[:5]):
            if dest:
                assert abs(dest - sector) <= 10, "nonlocal first-five link"
                assert graph[dest - 1][column] == sector, "first-five reciprocity"
    return graph

def reachable(graph, reverse=False):
    links = {s: [d for d in row if d] for s, row in enumerate(graph, 1)}
    if reverse:
        rev = {s: [] for s in links}
        for source, ds in links.items():
            for dest in ds:
                rev[dest].append(source)
        links = rev
    distances = {1: 0}
    queue = deque([1])
    while queue:
        source = queue.popleft()
        for dest in links[source]:
            if dest not in distances:
                distances[dest] = distances[source] + 1
                queue.append(dest)
    return distances

def components(graph):
    links = {s: set(d for d in row if d) for s, row in enumerate(graph, 1)}
    for source, ds in list(links.items()):
        for dest in tuple(ds):
            links[dest].add(source)
    seen = set()
    sizes = []
    for source in links:
        if source in seen:
            continue
        queue = [source]
        seen.add(source)
        size = 0
        while queue:
            node = queue.pop()
            size += 1
            for dest in links[node]:
                if dest not in seen:
                    seen.add(dest)
                    queue.append(dest)
        sizes.append(size)
    return sorted(sizes, reverse=True)

def verify(directory, fixture=None):
    original = (ROOT / "archive/dos-original/YT-INIT.EXE").read_bytes()
    assert SHA(original) == INIT_SHA
    assert SHA((ROOT / "archive/dos-original/BRUN30.EXE").read_bytes()) == RUNTIME_SHA
    assert struct.unpack_from("<H", original, 8)[0] * 16 == 512, "MZ header"
    graphs = {}
    worlds = {}
    copied_hashes = {}
    for name, patches in CONTRACTS.items():
        d = directory / name
        metadata = json.loads((d / "result.json").read_text())
        assert metadata["name"] == name and metadata["recipe"] == "dos-warp-generation-v1"
        assert metadata["date"] == "11/02/2026" and metadata["time"] == "00:00:00"
        assert metadata["maintenance_child"] == "declared-exit-stub"
        patched = bytearray(original)
        contract = []
        for tag, offset, before, after in patches:
            assert original[offset:offset + len(bytes.fromhex(before))].hex() == before, "original patch bytes"
            assert len(before) == len(after)
            if tag.startswith("skip-"):
                assert bytes.fromhex(after)[0] == 0xe9
                logical = offset - 512
                assert logical + 3 + struct.unpack("<h", bytes.fromhex(after)[1:])[0] == 0x1637, "patch jump target"
            patched[offset:offset + len(bytes.fromhex(after))] = bytes.fromhex(after)
            contract.append(dict(name=tag, offset=offset, before=before, after=after))
        assert metadata["patches"] == contract, "patch contract"
        assert metadata["initializer_original_sha256"] == INIT_SHA
        assert metadata["initializer_copied_sha256"] == SHA(patched), "complete copied initializer"
        assert metadata["binaries"] == {"YT-INIT.EXE": SHA(patched), "BRUN30.EXE": RUNTIME_SHA,
                                         "YTMAINT.EXE": SHA(bytes.fromhex("b8004ccd21"))}
        assert set(metadata["files"]) == FILES
        assert {p.name for p in d.iterdir()} == FILES | {"result.json"}, "retained file inventory"
        for filename, digest in metadata["files"].items():
            assert SHA((d / filename).read_bytes()) == digest, (name, filename, "retained hash")
        assert (d / "ANSWERS.TXT").read_bytes() == b"Y\r\n\r\n"
        assert b"INITIALIZER_RETURNED" in (d / "INITRET.LOG").read_bytes(), "normal shell return"
        log = (d / "INIT.LOG").read_bytes()
        assert b"<YT-INIT Normal Termination>" in log, "normal initializer termination"
        assert (b"Verifying warps" in log) == (name in ("original", "repair-only")), "phase transcript"
        assert (b"Building shortcuts" in log) == (name == "original"), "shortcut transcript"
        worlds[name] = gzip.decompress((d / "before-maint.dat.gz").read_bytes())
        copied_hashes[name] = SHA(patched)
        graphs[name] = rows(worlds[name])
    # Earlier unpatched fixed-clock capture independently anchors this whole graph.
    anchor = gzip.decompress((ROOT / "research/yt-port-generation/dos/midnight/before-maint.dat.gz").read_bytes())
    assert graphs["original"] == rows(anchor), "unpatched graph differs from independent capture"
    for name in ("original", "no-repair", "repair-only"):
        graph = graphs[name]
        assert [r[:5] for r in graph] == [r[:5] for r in graphs["original"]], "first-five phase preservation"
    local = graphs["local-only"]
    assert all(r[5] == (6 if s == 1 else 1 if s == 6 else 0) for s, r in enumerate(local, 1)), "local-only sixth column"
    assert len(components(local)) > 1, "local-only graph unexpectedly connected"
    # Suppression changes RNG consumption during the interleaved generation loop;
    # this diagnostic is not an otherwise identical graph with sixth links erased.
    assert any(a[:5] != b[:5] for a, b in zip(local, graphs["no-repair"])), "wormhole suppression did not alter subsequent local draws"
    raw = graphs["no-repair"]
    for source, row in enumerate(raw, 1):
        if row[5]:
            assert raw[row[5] - 1][5] == source, "unrepaired sixth reciprocity"
    assert len(components(raw)) > 1, "unrepaired graph unexpectedly connected"
    repair = graphs["repair-only"]
    repair_changes = []
    for source, (before, after) in enumerate(zip(raw, repair), 1):
        if before[5] != after[5]:
            assert before[5] == 0 and after[5] != 0, "repair overwrote existing sixth link"
            repair_changes.append(source)
    assert repair_changes, "missing repair transition"
    assert len(reachable(repair)) == len(reachable(repair, True)) == 3000, "repair did not connect directed graph"
    final = graphs["original"]
    shortcuts = []
    for source, (before, after) in enumerate(zip(repair, final), 1):
        if before[5] != after[5]:
            assert before[5] == 0 and after[5] == 1 and source > 6, "invalid Earth shortcut transition"
            shortcuts.append(source)
    assert shortcuts, "missing Earth shortcuts"
    assert len(reachable(final)) == len(reachable(final, True)) == 3000
    original_pairs = [[int(a), int(b)] for a, b in re.findall(rb"Sector (\d+) has been linked to sector (\d+)", (directory / "original/INIT.LOG").read_bytes())]
    repair_pairs = [[int(a), int(b)] for a, b in re.findall(rb"Sector (\d+) has been linked to sector (\d+)", (directory / "repair-only/INIT.LOG").read_bytes())]
    assert original_pairs == repair_pairs and len(repair_pairs) * 2 == len(repair_changes), "exact repair transcript"
    replay = [row[:] for row in raw]
    for source, dest in repair_pairs:
        assert 1 <= source <= 3000 and 1 <= dest <= 3000 and source != dest
        assert replay[source - 1][5] == replay[dest - 1][5] == 0, "repair transcript occupied slot"
        replay[source - 1][5] = dest
        replay[dest - 1][5] = source
    assert replay == repair, "repair transcript does not reproduce saved graph"
    fixture_path = fixture or ROOT / "internal/game/testdata/dos_warps.json.gz"
    golden = json.loads(gzip.decompress(fixture_path.read_bytes()))
    assert set(golden) == {"format", "cases", "repair_pairs"} and golden["format"] == 1, "golden format"
    assert set(golden["cases"]) == {"no-repair", "repair-only", "original"}, "golden case inventory"
    assert golden["repair_pairs"] == repair_pairs, "golden repair transcript"
    for name, case in golden["cases"].items():
        assert set(case) == {"source_world_sha256", "initializer_original_sha256", "initializer_copied_sha256", "slots"}
        assert case["source_world_sha256"] == SHA(worlds[name]), "golden world provenance"
        assert case["initializer_original_sha256"] == INIT_SHA and case["initializer_copied_sha256"] == copied_hashes[name], "golden initializer provenance"
        assert len(case["slots"]) == 3001 and all(len(row) == 6 and all(type(v) is int for v in row) for row in case["slots"]), "golden slot encoding"
        assert case["slots"] == [[0] * 6] + graphs[name], "golden full six-column table"
    summaries = {}
    for name, graph in graphs.items():
        forward, back = reachable(graph), reachable(graph, True)
        summaries[name] = dict(edges=sum(bool(d) for r in graph for d in r),
                              degree_histogram=dict(sorted(Counter(sum(bool(d) for d in r) for r in graph).items())),
                              weak_components=components(graph), reachable_from_earth=len(forward), can_reach_earth=len(back),
                              max_distance_from_earth=max(forward.values()), max_distance_to_earth=max(back.values()))
    return dict(cases=summaries, repair_changed_sources=repair_changes, shortcut_sources=shortcuts)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "research/yt-warp-generation/dos")
    args=parser.parse_args()
    verify_native(args.directory.parent)
    print(json.dumps(verify(args.directory), indent=2))
