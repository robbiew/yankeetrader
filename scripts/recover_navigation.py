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
    parser.add_argument("--followup", action="store_true", help="Run the cloak/team/varied-warp follow-up suite")
    parser.add_argument("--hazards", action="store_true", help="Run disruption/scanner-damage/automatic-escape probes")
    parser.add_argument("--utilities", action="store_true", help="Run computer-report and fighter/NPC encounter probes")
    parser.add_argument("--bribes", action="store_true", help="Run mercenary offer-boundary and faction refusal probes")
    parser.add_argument("--commerce", action="store_true", help="Run route-commerce, spy-hiring and radio probes")
    parser.add_argument("--ownership", action="store_true", help="Run port acquisition, buyout and treasury probes")
    parser.add_argument("--dosbox", default="dosbox-staging", help="DOSBox Staging command or executable path")
    args = parser.parse_args()
    if sum((args.followup, args.hazards, args.utilities, args.bribes, args.commerce, args.ownership, args.only is not None)) > 1:
        parser.error("choose a suite or --only")
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

        ("danger-clear", 500, "M;101", {(2,93):-1}),
        ("danger-mines-no", 500, "M;101\r~~N", {(2,93):-1,(152,129):10}),
        ("danger-mines-yes", 500, "M;101\r~~Y", {(2,93):-1,(152,129):1}),
        ("danger-stacked-yes", 500, "M;101;Y", {(2,93):-1,(152,129):10}),
        ("danger-fighters-no", 500, "M;101\r~~N", {(2,93):-1,(152,81):100,(152,85):3}),
        ("danger-own-fighters", 500, "M;101", {(2,93):-1,(152,81):100,(152,85):2}),
        ("danger-no-scanner", 500, "M;101", {(2,93):0,(152,129):1}),
        ("danger-autopilot-no", 500, "C;3;110;Y\r~~N", {(2,93):-1,(152,129):10}),
        ("warp-cancel", 500, "W;N", {}),
        ("warp-default", 500, "W;", {}),
        ("warp-yes", 500, "W;Y", {}),
        ("warp-one", 1, "W;Y", {}),
        ("warp-zero", 0, "W;Y", {}),

        ("danger-team", 500, "M;101", {(2,93):-1,(2,89):1,(3,89):1,
            (52,77):2,(52,109):2,(52,117):3,(152,81):100,(152,85):3}),
        ("danger-other-team", 500, "M;101\r~~N", {(2,93):-1,(2,89):1,(3,89):2,
            (52,77):2,(52,109):2,(52,117):0,(53,77):3,(53,109):3,
            (152,81):100,(152,85):3}),
        ("cloak-none", 500, "S", {(3,125):0}),
        ("cloak-full", 500, "S", {(3,125):1}),
        ("cloak-weak", 500, "S;S", {(3,125):0.000001}),
        ("cloak-half", 500, "S;S;S", {(3,125):0.5}),

    ]
    # Scan a visible adjacent ship to advance the normal game's RNG, without
    # patching executable code or forcing a random return value.
    scenarios += [(f"warp-scan-{n:02d}", 500, "S;" * n + "W;Y", {})
                  for n in range(1, 17)]
    scenarios += [(f"warp-clock-{hour:02d}", 500, "W;Y", {})
                  for hour in range(1, 13)]
    scenarios += [(f"warp-look-{n:02d}", 500, "\r" * n + "W;Y", {(3,57):100})
                  for n in (0, 1, 2, 4, 8, 16, 24, 32)]
    # Two sectors force both session-generated disruption locations to sector 2:
    # INT(RND * (sector_count - 2)) + 2. No executable patch is involved.
    disruption = {(1,57):53,(1,61):53,(1,93):53,(2,57):1,(3,57):1,(3,125):1,
                  (52,65):0,(52,93):0,(53,65):0,(53,93):0,(2,93):-1}
    scenarios += [
        ("hazard-disrupt-scan",500,"S",disruption),
        ("hazard-disrupt-no",500,"M;2\r~~N",disruption),
        ("hazard-disrupt-yes",500,"M;2\r~~Y",disruption),
        ("hazard-disrupt-bare",500,"M;2",{**disruption,(2,93):0}),
        ("hazard-disrupt-last",1,"M;2\r~~Y",disruption),
    ]
    scenarios += [(f"hazard-shield-clock-{hour:02d}",500,"M;101\r~~Y",
                   {(2,93):-1,(152,129):1}) for hour in range(1,13)]
    scenarios += [(f"hazard-bare-clock-{hour:02d}",500,"M;101\r~~Y",
                   {(2,93):-1,(2,53):0,(2,113):0,(152,129):1}) for hour in range(1,13)]
    scenarios += [(f"hazard-small-clock-{hour:02d}",500,"M;101\r~~Y",
                   {(2,93):-1,(2,53):0,(2,65):9,(2,69):9,(2,73):0,(2,77):0,
                    (152,129):1}) for hour in range(1,13)]
    scenarios += [(f"hazard-burst-clock-{hour:02d}",500,"M;101\r~~Y",
                   {(2,93):-1,(2,53):1000000,(152,129):20}) for hour in range(1,5)]
    scenarios.append(("hazard-ten-holds",500,"M;101\r~~Y",
                      {(2,93):-1,(2,53):0,(2,65):10,(2,69):10,(2,73):0,(2,77):0,(152,129):1}))
    defenders = {(2,93):0,(2,61):2000,(152,81):100,(152,85):-2}
    scenarios += [
        ("utility-menu",500,"C;?;1",{}),
        ("utility-fighters",500,"C;11;1",{(152,81):123,(152,85):2,(153,81):456,(153,85):3,(157,81):789,(157,85):2}),
        ("utility-planets",500,"C;13;1",{(4053,73):2}),
        ("utility-planets-foreign",500,"C;13;1",{(4053,73):3}),
        ("utility-port-known",500,"C;2;101;1",{}),
        ("utility-port-empty",500,"C;2;104;1",{}),
        ("utility-port-guarded",500,"C;2;101;1",{(152,81):100,(152,85):3}),
        ("utility-planet-report",500,"C;9;102;1",{}),
        ("utility-planet-private",500,"C;9;102;1",{(4053,73):3}),
        ("utility-planet-owned",500,"C;9;102;1",{(4053,73):2}),
        ("utility-planet-unguarded",500,"C;9;102;1",{(4053,73):3,(4053,77):0}),
        ("utility-planet-guarded",500,"C;9;102;1",{(4053,73):3,(153,81):100,(153,85):3}),
        ("utility-treasury",500,"C;12;1",{}),
        ("utility-spies",500,"C;15;1",{}),
        ("npc-merc-attack",500,"M;101\r~~A;1001",defenders),
        ("npc-xannor-attack",500,"M;101\r~~A;1001",{**defenders,(152,85):-1}),
        ("npc-human-surrender",500,"M;101\r~~A;1001\r~~~~Y",{**defenders,(152,85):3}),
        ("npc-merc-bribe",500,"M;101\r~~B\r~~50000",defenders),
        ("npc-merc-cancel",500,"M;101\r~~B\r~~",defenders),
        ("npc-human-bribe",500,"M;101\r~~B",{**defenders,(152,85):3}),
        ("npc-xannor-bribe",500,"M;101\r~~B",{**defenders,(152,85):-1}),
        ("npc-warp-cancel",500,"M;101\r~~W;N",defenders),
        ("npc-warp-escape",500,"M;101\r~~W;Y",defenders),
    ]
    bribes = [
        ("blank", "", {}), ("zero", "0", {}), ("negative", "-1", {}),
        ("one", "1", {}), ("hundred", "100", {}), ("thousand", "1000", {}),
        ("two-hundred", "200", {}), ("three-hundred", "300", {}),
        ("ten-thousand", "10000", {}), ("fifty-thousand", "50000", {}),
        ("all-credits", "100000", {}), ("over-budget", "100001", {}),
        ("fraction", "50000.5", {}), ("text", "abc", {}),
        ("planet", "50000", {(152,93):2,(4053,73):-2}),
        ("merc-weak", "50000", {(2,61):10}),
        ("merc-zero-force", "50000", {(2,61):0}),
        ("human-weak", "", {(152,85):3,(2,61):10}),
        ("xannor", "", {(152,85):-1}),
    ]
    scenarios += [("npc-bribe-"+name,500,"M;101\r~~B\r~~"+offer,
                   {**defenders,**patches}) for name,offer,patches in bribes]
    ports = {(158,65):3,(3054,41):3,(3054,45):297,(3054,49):1000,(3054,53):1000,
             (3054,57):1000,(3054,61):100,(3054,65):100,(3054,69):100,
             (3054,73):-50,(3054,77):50,(3054,81):-50,(3054,89):0,(3054,93):107,(3054,97):0}
    spies = {(2,57):1,(2,81):2000000,(52,65):1}
    scenarios += [
        ("commerce-nearest-all",500,"C;14;A;1",ports),
        ("commerce-nearest-ore",500,"C;14;3;S;1",ports),
        ("commerce-nearest-team",500,"C;14;T;1",ports),
        ("commerce-pairs-oneway",500,"C;16;1",ports),
        ("commerce-pairs-twoway",500,"C;16;1",{**ports,(158,45):101}),
        ("commerce-profit-empty",500,"C;17;1",ports),
        ("commerce-profit-ports",500,"C;17;1",{**ports,(2,57):101,(158,45):101}),
        ("commerce-profit-small",500,"C;17;1",{**ports,(2,57):101,(2,65):10,
            (2,69):0,(2,73):0,(2,77):0,(158,45):101}),
        ("intel-hire-one",500,"P;9;1;101\r~~~~\r~~0;C;15;1",spies),
        ("intel-hire-three",500,"P;9;3;101;102;103\r~~~~\r~~0;C;15;1",spies),
        ("intel-limit-four",500,"P;9;4\r~~0;0;C;15;1",spies),
        ("intel-reconnect",500,"C;15;1",{}),
        ("radio-send",500,"C;5;Enemy;Y\r~~YT RADIO PROBE\r\r~~S\r~~~~6;1",{}),
        ("radio-abort",500,"C;5;Enemy;Y\r~~YT ABORT PROBE\r\r~~A;Y",{}),
        ("radio-log-empty",500,"C;6;1",{}),
        ("radio-team-denied",500,"C;5;TEAM;1",{}),
        ("radio-read",500,"\r~~~~C;6;1",{}),
        ("radio-read-again",500,"\r~~~~C;6;1",{}),
    ]
    ownership = {(2,57):101,(2,81):100000,(2,117):0,(3,81):2000,(3,117):1,
                 (3053,97):3,(3053,89):777,(3053,61):100,(3053,65):100,(3053,69):100}
    scenarios += [
        ("ownership-buyout",500,"B\r~~Y",ownership),
        ("ownership-cancel",500,"B\r~~N",ownership),
        ("ownership-default",500,"B\r~~",ownership),
        ("ownership-poor",500,"B",{**ownership,(2,81):30}),
        ("ownership-unowned",500,"B\r~~Y",{**ownership,(3053,97):0,(3053,89):0}),
        ("ownership-self",500,"B",{**ownership,(3053,97):2,(2,117):1}),
        ("ownership-collect",500,"$",{**ownership,(2,57):100,(3053,97):2,(2,117):1}),
        ("ownership-report",500,"C;12;1",{**ownership,(2,57):100,(3053,97):2,(2,117):1}),
        ("ownership-buy-collect",500,"B\r~~Y\r~~$",ownership),
    ]
    if args.ownership:
        scenarios = [s for s in scenarios if s[0].startswith("ownership-")]
    elif args.commerce:
        scenarios = [s for s in scenarios if s[0].startswith(("commerce-", "intel-", "radio-"))
                     and s[0] not in ("intel-reconnect", "radio-read", "radio-read-again")]
    elif args.bribes:
        scenarios = [s for s in scenarios if s[0].startswith("npc-bribe-")]
    elif args.utilities:
        scenarios = [s for s in scenarios if s[0].startswith(("utility-", "npc-")) and not s[0].startswith("npc-bribe-")]
    elif args.hazards:
        scenarios = [s for s in scenarios if s[0].startswith("hazard-")]
    elif args.followup:
        scenarios = [s for s in scenarios if s[0].startswith(("cloak-", "warp-scan-", "warp-clock-", "warp-look-"))
                     or s[0] in ("danger-team", "danger-other-team")]
    elif not args.only:
        scenarios = [s for s in scenarios if not s[0].startswith(("avoid-", "danger-", "warp-", "cloak-", "hazard-", "utility-", "npc-", "commerce-", "intel-", "radio-", "ownership-"))]
    if args.only:
        scenarios = [s for s in scenarios if s[0] in args.only]
        if len(scenarios) != len(set(args.only)):
            parser.error("unknown or repeated probe name")

    def run(scenario):
        name, turns, command, overrides = scenario
        actor = "ENEMY" if name.startswith("radio-read") else "TESTER"
        player_record = 3 if actor == "ENEMY" else 2
        varied_warp = name.startswith(("warp-scan-", "warp-clock-", "warp-look-", "hazard-", "utility-", "npc-", "commerce-", "intel-", "radio-", "ownership-"))
        dos_time = f"{int(name[-2:]):02d}:00:00" if "clock-" in name else "00:00:00"
        case_graph = {1:[2],2:[1]} if name.startswith("hazard-disrupt-") else graph
        dest = args.destination / name
        dest.mkdir()
        for p in source.iterdir():
            if p.suffix.upper() in (".DAT", ".EXE", ".DOC", ".DEF", ".ASC", ".ANS"):
                shutil.copy2(p, dest / p.name)
        shutil.copy2(archive / "analysis/yt-combat/KEYFEED.COM", dest / "KEYFEED.COM")
        data = bytearray((dest / "YTDATA.DAT").read_bytes())
        if name.startswith("commerce-"):
            for sector in range(1,3001):
                mbf.put(data,51+sector,65,0)
        for sector, warps in case_graph.items():
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
        if name in ("intel-reconnect", "radio-read", "radio-read-again"):
            # Linked-session probes reopen the exact committed world, including
            # spent turns and position, instead of resetting the base fixture.
            data = bytearray((dest / "YTDATA.DAT").read_bytes())
        before = bytes(data)
        (dest / "YTDATA.DAT").write_bytes(before)
        auxiliary_before = {p.name:p.read_bytes() for p in dest.glob('*.DAT') if p.name != 'YTDATA.DAT'}
        # Display/temperature routines consume typeahead. Retry the ordinary
        # quit command after delays until an actual main prompt can read it.
        tail = "\r~~~~" + "\rQ;Y\r~~" * 24 if varied_warp else "\r~~~~" + "\r" * 8 + "Q;Y\r"
        keys = ("\r~~~~~\r~" + command + tail).encode()
        (dest / "KEYS.TXT").write_bytes(keys)
        with (dest / "dosbox.log").open("w") as log:
            subprocess.run([dosbox, "--noprimaryconf", "--nolocalconf",
                            "--set", "cpu_cycles=200000", "--set", "nosound=true",
                            "-c", f"mount c {dest.resolve()}", "-c", "c:",
                            "-c", "date 10/24/2026", "-c", f"time {dos_time}",
                            "-c", "keyfeed", "-c", f"local {actor} > game.log", "-c", "exit"],
                           env={**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"},
                           stdout=log, stderr=subprocess.STDOUT,
                           timeout=150 if varied_warp else 55,
                           check=True)
        after = (dest / "YTDATA.DAT").read_bytes()
        transcript = (dest / "GAME.LOG").read_bytes().decode("cp437").replace("\\r\\n", "\n")
        (dest / "transcript.txt").write_text(transcript)
        for label, payload in [("before", before), ("after", after)]:
            (dest / (label + ".dat.gz")).write_bytes(gzip.compress(payload, mtime=0))
        result = {"name": name, "command": command, "before_sha256": hashlib.sha256(before).hexdigest(),
                  "after_sha256": hashlib.sha256(after).hexdigest(),
                  "turns_before": int(mbf.get(before, player_record, 49)), "turns_after": int(mbf.get(after, player_record, 49)),
                  "sector_before": int(mbf.get(before, player_record, 57)), "sector_after": int(mbf.get(after, player_record, 57)),
                  "executable_sha256": hashlib.sha256((dest / "YT.EXE").read_bytes()).hexdigest()}
        if name.startswith(("danger-", "warp-", "cloak-", "hazard-", "utility-", "npc-", "commerce-", "intel-", "radio-", "ownership-")):
            if "Returning to Yankee Trader Local Logon Program" not in transcript:
                raise RuntimeError(f"{name}: session did not finish; inspect {dest}")
            result.update({
                "dos_time": dos_time,
                "graph": case_graph,
                "patches": [{"record": r, "offset": o, "value": v}
                            for (r, o), v in sorted(overrides.items())],
                "source_sha256": hashlib.sha256((source / "YTDATA.DAT").read_bytes()).hexdigest(),
                "keys_sha256": hashlib.sha256(keys).hexdigest(),
                "transcript_sha256": hashlib.sha256((dest / "transcript.txt").read_bytes()).hexdigest(),
                "dosbox_log_sha256": hashlib.sha256((dest / "dosbox.log").read_bytes()).hexdigest(),
                "keyfeed_sha256": hashlib.sha256((dest / "KEYFEED.COM").read_bytes()).hexdigest(),
            })
        if name.startswith(("commerce-", "intel-", "radio-")):
            result['actor'] = actor
            result['player_record'] = player_record
            result['auxiliary'] = {}
            for filename,payload in auxiliary_before.items():
                final = (dest/filename).read_bytes()
                for label,raw in [('before',payload),('after',final)]:
                    (dest/f'{filename}.{label}.gz').write_bytes(gzip.compress(raw,mtime=0))
                result['auxiliary'][filename] = {'before_sha256':hashlib.sha256(payload).hexdigest(),
                                                 'after_sha256':hashlib.sha256(final).hexdigest()}
        (dest / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, scenarios))
    (args.destination / "results.json").write_text(json.dumps({"graph": graph, "scenarios": results}, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
