"""Check the additional +2-second port replay seed with the independent raw verifier."""
from pathlib import Path
from verify_rng_trace import verify as verify_corpus

ROOT = Path(__file__).resolve().parents[1]
CASES = {'timer-plus-two': ('timer', 5, None, '11/02/2026', '00:00:02')}


def verify(destination=ROOT / 'research/yt-port-replay/seed-dos'):
    result = verify_corpus(destination, cases=CASES)['timer-plus-two']
    assert result['timer_or_input_fac'] == 'f6287c81', 'pinned observed TIMER FAC'
    assert result['seeded'] == 0xa90a05, 'pinned measured seed'
    return result


if __name__ == '__main__':
    import json
    print(json.dumps(verify(), indent=2))
