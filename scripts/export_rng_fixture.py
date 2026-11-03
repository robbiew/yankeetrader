"""Export independently validated raw native RNG controls for portable tests."""
import argparse
import json
from pathlib import Path
from verify_rng_trace import ROOT, fixture_document, verify

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', nargs='?', type=Path, default=ROOT / 'internal/qbrng/testdata/native_rng.json')
    parser.add_argument('--source', type=Path, default=ROOT / 'research/yt-rng-seeding/trace-dos')
    args = parser.parse_args()
    verify(args.source)
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(json.dumps(fixture_document(args.source), indent=2) + '\n')
    print(args.destination)
