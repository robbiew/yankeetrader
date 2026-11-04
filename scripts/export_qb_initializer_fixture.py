"""Export/check portable Go golden hashes against independently verified native worlds."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
from verify_initializer_targets import verify as verify_targets, verify_fresh_controls
from verify_initializer_native import verify as verify_native
from replay_qb_initializer import controlled_cases

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'internal/qbinit/testdata/native_initializer.json'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def document():
    verify_native(); verify_targets(); verify_fresh_controls()
    # The complete replay report is checked afresh, but golden byte hashes below
    # are always read from pinned observed DOS worlds, not synthesized outputs.
    report = controlled_cases()
    assert report == json.loads((ROOT / 'research/yt-initializer-replay/replay-results.json').read_text())
    from replay_qb_ports import syllables
    tokens = ','.join(syllables())
    go = (ROOT / 'internal/qbinit/syllables.go').read_text()
    assert re.search(r'const syllableData = `([^`]+)`', go)[1] == tokens, 'Go DATA pool differs from original'
    from replay_qb_ports import controlled_cases as port_cases
    endpoints = {c['seed_trace']['world_seed']: c for c in port_cases()['cases']}
    cases = []
    for case in report['cases']:
        raw = gzip.decompress((ROOT / case['world']).read_bytes())
        assert SHA(raw) == case['observed_world_sha256']
        stats = dict(case['statistics'])
        for field in ('final_state', 'placement_final_state'): stats[field] = int(stats[field], 16)
        stats['graph_draws'] = endpoints[case['seed_trace']['world_seed']]['graph_draws']
        stats['graph_state'] = int(endpoints[case['seed_trace']['world_seed']]['graph_final_state'], 16)
        cases.append(dict(name=case['clock_case'], state=case['seed_trace']['world_seed'],
                          date=case['date'], scoreboard=case['scoreboard'], world_sha256=SHA(raw),
                          blocks={name: case['blocks'][name]['observed_sha256'] for name in case['blocks']},
                          stats=stats, source_world=case['world'],
                          source_compressed_sha256=SHA((ROOT / case['world']).read_bytes()),
                          source_seed_trace_sha256=case['seed_trace']['trace_sha256']))
    return dict(format='qb-initializer-native-hashes-v1',record_size=137,record_count=4151,
                syllables_sha256=SHA(tokens.encode()),
                authority='Byte hashes are observed DOS outputs; draw counts are verified replay bookkeeping. Native phase states are independently checked by the parent port replay.',
                cases=cases)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', type=Path, nargs='?', const=DEFAULT)
    args = parser.parse_args()
    result = document()
    if args.output: args.output.write_text(json.dumps(result, indent=2) + '\n')
    if args.check: assert json.loads(args.check.read_text()) == result, 'portable Go fixture differs from verified native evidence'
    if not args.output and not args.check: parser.error('choose --output or --check')
    print('Verified twenty complete native initializer golden cases and original weighted DATA.')
