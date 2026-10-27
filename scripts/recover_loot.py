"""Run isolated original-DOS loot and estate probes; never mount the archive."""
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


def prepare_baseline(source, mbf):
    baseline = bytearray((source/'YTDATA.DAT').read_bytes())
    for record in range(52, 3052):
        for offset in (81, 85, 129):
            mbf.put(baseline, record, offset, 0)
    for record in range(3052, 4052):
        for offset in (89, 97):
            mbf.put(baseline, record, offset, 0)
    for record in range(4052, 4152):
        for offset in (73, 117):
            mbf.put(baseline, record, offset, 0)
    for record in range(52, 102):
        for offset in (73, 77, 109, 117, 121, 125):
            mbf.put(baseline, record, offset, 0)
        baseline[(record-1)*137+113:(record-1)*137+117] = b'    '
    for player in (2, 3):
        fields = {45: 0, 49: 500, 53: 1000000 if player == 2 else 0,
                  57: 100, 61: 1000000 if player == 2 else 0,
                  65: 1000 if player == 2 else 100, 69: 0, 73: 0, 77: 0,
                  81: 1005 if player == 2 else 10000, 89: 0, 93: 0, 97: 0,
                  105: 0, 109: 0, 113: 0, 117: 0, 121: 0, 125: 0, 129: 0}
        for offset, value in fields.items():
            mbf.put(baseline, player, offset, value)
    # A distinct third account supplies unrelated-ownership controls.
    baseline[3*137:4*137] = baseline[2*137:3*137]
    baseline[3*137:3*137+41] = b'Third '.ljust(41, b' ')
    for offset, value in {57: 200, 81: 3000, 85: 6, 125: 1}.items():
        mbf.put(baseline, 4, offset, value)
    return baseline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--only', nargs='+')
    args = parser.parse_args()
    dest = args.destination.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    archive = ROOT/'archive'
    source = archive/'analysis/yt-combat/experiments/fixture-ship-kill'
    spec = importlib.util.spec_from_file_location('mbf', archive/'analysis/yt-maint/experiments.py')
    mbf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mbf)
    baseline = prepare_baseline(source, mbf)
    (dest/'baseline.dat.gz').write_bytes(gzip.compress(baseline, mtime=0))
    items = {(3, 69): 11, (3, 73): 23, (3, 77): 37, (3, 97): 41,
             (3, 113): 43, (3, 121): 47, (3, 129): 5}
    estate = {(3053, 97): 3, (3053, 89): 777, (3054, 97): 3, (3054, 89): 333,
              (3055, 97): 4, (3055, 89): 555, (3, 117): 2,
              (4053, 73): 3, (4053, 117): 1000, (4053, 77): 100,
              (4054, 73): 2, (4054, 117): 2000,
              (4055, 73): 4, (4055, 117): 3000,
              (161, 81): 123, (161, 85): 3,
              (162, 81): 234, (162, 85): 4, (163, 81): 345, (163, 85): 2}
    team = {(3, 89): 1, (4, 89): 1, (52, 73): 5, (52, 77): 3,
            (52, 109): 3, (52, 117): 4}
    cases = [(f'loot-credit-{n}', {(3, 81): n}) for n in (0, 1, 2, 3, 10, 100, 10000)]
    cases += [('loot-items', items), ('loot-holds-empty', {**items, (2, 65): 10}),
              ('loot-holds-full', {**items, (2, 65): 10, (2, 69): 10}),
              ('loot-estate', estate), ('loot-estate-stale-count', {**estate, (3, 117): 0}),
              ('loot-team-captain', {**estate, **team}),
              ('loot-team-last', {**estate, **team, (4, 89): 0, (52, 117): 0})]
    cases += [(f'loot-clock-{hour:02d}', items) for hour in (1, 2, 3, 4)]
    cases += [('loot-weapons-100', {(3, o):100 for o in (97,113,121,129)}),
              ('loot-cargo-ore', {(2,65):10,(3,65):100,(3,69):100}),
              ('loot-cargo-org', {(2,65):10,(3,65):100,(3,73):100}),
              ('loot-cargo-equip', {(2,65):10,(3,65):100,(3,77):100}),
              ('loot-cargo-empty', {(2,65):10,(3,65):100}),
              ('loot-holds-990', {**items,(2,65):990}),
              ('loot-holds-999', {**items,(2,65):999}),
              ('loot-credit-large', {(3,81):100000000,(2,81):100000000}),
              ('loot-own-prior-port', {**estate,(3055,97):2,(2,117):1}),
              ('loot-estate-collect', estate)]
    self_estate = {**estate, (2,53):0,(2,61):0,(2,97):1,(2,117):2,(3,117):0,(3,57):200,
                   (3053,97):2,(3054,97):2,(4053,73):2,(4054,73):3,(161,85):2}
    cases += [('loot-self-estate',self_estate),
              ('loot-self-stale-count',{**self_estate,(2,117):0})]
    live_links = {(161,93):2,(162,93):3,(163,93):4}
    cases += [('loot-live-estate',{**estate,**live_links}),
              ('loot-live-stale-count',{**estate,**live_links,(3,117):0}),
              ('loot-live-team-captain',{**estate,**team,**live_links}),
              ('loot-live-self-estate',{**self_estate,**live_links}),
              ('loot-live-mine-death',{**self_estate,**live_links,(2,53):1,(2,61):1,(2,65):10,(151,129):100}),
              ('loot-live-mine-fatal',{**self_estate,**live_links,(2,53):1,(2,61):1,(2,65):10,(151,129):10000})]
    chain_source = (archive/'analysis/yt-combat/experiments/ship-earthdeath/before.dat').read_bytes()
    chain_players = {(r,o):mbf.get(chain_source,r,o) for r in (2,3) for o in range(41,130,4)}
    cases += [('loot-live-chain-death',{**self_estate,**live_links,**chain_players,(2,117):2,(3,117):0})]
    if args.only:
        assert set(args.only) <= {name for name, _ in cases}, 'unknown scenario'
        cases = [case for case in cases if case[0] in args.only]

    def run(case):
        name, patches = case
        directory = dest/name
        directory.mkdir()
        for path in source.iterdir():
            if path.suffix.upper() in ('.DAT', '.EXE', '.DOC', '.DEF', '.ASC', '.ANS'):
                shutil.copy2(path, directory/path.name)
        feeder = archive/'analysis/yt-combat/KEYFEED.COM'
        shutil.copy2(feeder, directory/'KEYFEED.COM')
        data = bytearray(baseline)
        template_hash = None
        if name.startswith('loot-live-'):
            template_source = archive/'analysis/yt-combat/experiments/fixture-planet-foreign/YTDATA.DAT'
            template_bytes = template_source.read_bytes()
            template_hash = hashlib.sha256(template_bytes).hexdigest()
            for record in (4053,4054,4055):
                data[(record-1)*137:record*137] = template_bytes[4052*137:4053*137]
        for (record, offset), value in patches.items():
            mbf.put(data, record, offset, value)
        before = bytes(data)
        (directory/'YTDATA.DAT').write_bytes(before)
        command = b'A\r~~Y\r~~1000'
        if name.startswith('loot-self-') or name == 'loot-live-self-estate': command = b'!;100;1'
        if name.startswith('loot-live-mine-'): command = b'Q;Y'
        if name == 'loot-live-chain-death': command = b'A\r~~Y\r~100'
        if name == 'loot-estate-collect': command += b'\r~~~~$'
        keys = b'\r~~~~~\r~' + command + b'\r~~~~' + b'\rQ;Y\r~~'*24
        dos_time = f"{int(name[-2:]):02d}:00:00" if name.startswith('loot-clock-') else '00:00:00'
        (directory/'KEYS.TXT').write_bytes(keys)
        completed = True
        try:
            with (directory/'dosbox.log').open('w') as log:
                subprocess.run(['dosbox-staging', '--noprimaryconf', '--nolocalconf',
                                '--set', 'cpu_cycles=200000', '--set', 'nosound=true',
                                '-c', f'mount c {directory}', '-c', 'c:', '-c', 'date 10/24/2026',
                                '-c', 'time '+dos_time, '-c', 'keyfeed',
                                '-c', 'local TESTER > game.log', '-c', 'exit'],
                               env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'},
                               stdout=log, stderr=subprocess.STDOUT, timeout=130, check=True)
        except subprocess.TimeoutExpired:
            completed = False
        after = (directory/'YTDATA.DAT').read_bytes()
        transcript = (directory/'GAME.LOG').read_bytes().decode('cp437').replace('\\r\\n', '\n')
        (directory/'transcript.txt').write_text(transcript)
        for label, payload in [('before', before), ('after', after)]:
            (directory/(label+'.dat.gz')).write_bytes(gzip.compress(payload, mtime=0))
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        result = dict(name=name, complete=completed and 'Returning to Yankee Trader Local Logon Program' in transcript,
                      planet_template_sha256=template_hash,
                      source_sha256=digest(source/'YTDATA.DAT'), baseline_sha256=hashlib.sha256(baseline).hexdigest(),
                      before_sha256=hashlib.sha256(before).hexdigest(), after_sha256=hashlib.sha256(after).hexdigest(),
                      executable_sha256=digest(directory/'YT.EXE'), keyfeed_sha256=digest(feeder),
                      keys_sha256=digest(directory/'KEYS.TXT'), transcript_sha256=digest(directory/'transcript.txt'),
                      dosbox_log_sha256=digest(directory/'dosbox.log'), dos_date='10/24/2026', dos_time=dos_time,
                      patches=[dict(record=r, offset=o, value=v) for (r, o), v in sorted(patches.items())])
        (directory/'result.json').write_text(json.dumps(result, indent=2)+'\n')
        print(name, 'complete='+str(result['complete']), flush=True)
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, cases))
    (dest/'results.json').write_text(json.dumps(dict(scenarios=results), indent=2)+'\n')


if __name__ == '__main__':
    main()
