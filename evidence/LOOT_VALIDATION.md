# Loot and estate research validation — 2026-10-27

Research only; no Go engine or player-command changes.

Passed:

- 37 normally returned original DOS sessions, 74 packaged save snapshots. All
  executable copies match original Yankee Trader 3.6. Four duplicate pilots are
  excluded from this packaged count; unsuccessful hypotheses remain as explicit
  normally completed negative controls.
- `python3 scripts/verify_loot_evidence.py`: reconstructed every input from the
  pristine archive fixture, active-planet template and recorded patches; verified
  snapshot/input/transcript/log hashes, concrete outcomes and bounded model checks.
- Eight REA static observations independently matched against the original DOS
  executable after reconstructing its MZ loader relocations. The REA session was
  closed after evidence export. Static observations are separate from execution.
- Active-planet controls verify full records, defenses, banks and sector links;
  initial inactive-planet probes are not used to claim active planet retention.
- Normal versus stale-count ordinary-port capture, captured treasury collection,
  unrelated ownership controls, team death removal and chained attacker death.
- Credit scaling/zero/one boundaries, hold-cap boundaries, full/empty/monocargo
  holds and weapons; four different DOS clock seeds and one large MBF balance.
- `python3 scripts/verify_archive.py`: all 4,682 originals unchanged.
- Python syntax checks; authored-source whitespace checks. Raw DOS transcripts
  and logs preserve their original spacing/line endings and are hash-pinned.

The original DOS program ran in fresh copied directories under DOSBox Staging
0.83.0, with the archive never mounted. The replay driver refuses existing output
directories. All 37 cases can be reproduced using `scripts/recover_loot.py`.
The new evidence verifier is included in CI, but this research commit has not
been pushed for CI.

These are bounded DOS observations plus runtime-aware/static recovery, not exact
RNG/MBF replay, proof of a full player-accessible farming exploit, or live-BBS
acceptance. NPC/deleted-killer cleanup, nondefault configuration, explicit
suicide, equipment overflow and complete combat integration remain pending.
See [the findings and evidence index](../research/yt-ships/LOOT.md).
