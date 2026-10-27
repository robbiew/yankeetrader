"""Compare Go duel fixtures to the archived model; no DOS RNG parity claim."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[1]
source = root/'archive/analysis/yt-ships/recovered_rules.py'
assert hashlib.sha256(source.read_bytes()).hexdigest() == '51c4e625e6330bdb098f1103e7d429fe8c284bdc0b3318dda9ac3075cd75cb32'
spec = importlib.util.spec_from_file_location('rules', source)
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)

rows = []
for name, attackers, defenders, shields, cloak, draws in [
    ('fighter-win', 10, 10, 0, 1, [.5]),
    ('fighter-loss', 10, 10, 0, 0, [.1]),
    ('shield-large', 200, 0, 200, 0, [.1]),
    ('shield-small-loss', 100, 0, 10, 0, [.5]),
    ('shield-100-boundary', 101, 0, 101, 0, [.1, .9]),
    ('cloak-advantage', 5, 5, 5, 1, [.4, .1, .6, .8]),
    ('fighter-batch-boundary', 41, 40, 0, 0, [.45, .44, .9]),
    ('mixed', 1000, 1000, 10000, 0, [.2, .8, .7, .49, .45, .9, .5]),
    ('no-defenses', 7, 0, 0, 0, [.5]),
]:
    count = [0]

    def rng():
        index = count[0]
        count[0] += 1
        return draws[index % len(draws)]

    survivors, remaining, _, _ = rules.fighter_duel(attackers, defenders, cloak, rng)
    survivors, remaining_shields = rules.shield_duel(survivors, shields, rng) if remaining == 0 else (survivors, shields)
    rows.append(dict(
        Name=name, Committed=attackers, Defenders=defenders, Shields=shields,
        Cloak=cloak, Draws=draws, Expected=dict(
            Survivors=survivors, DefenderFighters=remaining,
            DefenderShields=remaining_shields, AttackerLosses=attackers-survivors,
            DefenderLosses=defenders-remaining, Rounds=count[0],
            Destroyed=remaining == 0 and remaining_shields == 0)))
assert rows == json.loads((root/'internal/game/testdata/ship-duel-model.json').read_text()), 'Go duel cases differ from archived model'
print('Verified 9 injected-RNG model comparisons; these are not additional DOS sessions.')
