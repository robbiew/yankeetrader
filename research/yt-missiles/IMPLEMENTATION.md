# One-hop missile attacks and retaliation — 2026-10-27

## Playable scope

`MISSILE <sector> <quantity>` and classic `!` offer a fresh, separately entered Y
confirmation. Missing sector/quantity are prompted. Stacked Y, command replay,
Escape, disconnect and deadline expiration cannot approve a launch. The prompt
shows the actual visible target, mine stock, own shields and counterfire warning.
All selected missiles and one launching turn are consumed; unused in-flight shots
are not refunded. Ordinary turn-based cloak decay applies to that launch.

This first integration supports exactly one visible enemy ship, or minefield-only
clearing, in a one-hop corridor linked in both directions. That corridor boundary
keeps the known outgoing/return encounter explicit; it is not a claim about the
original full route engine. Teammates and hidden ships are excluded. Multiple
visible enemies, deployed sector fighters and any planet at the destination are
rejected until interception, multi-ship sequencing and bombardment are implemented.
Same-sector launches are rejected without spending stock, rather than retaining
the DOS self-destructing-volley negative-control behavior.

Preparation binds the observer and source/target generations, origin, destination,
quantity and mine layers. Commit rechecks current position, graph, eligibility,
visibility, team protection, turns, stock and unchanged target/mine warning before
RNG or mutation. Current defensive quantities, rather than quoted damage, determine
the outcome. Unexpected target arrival/departure/replacement or a changed field
requires a new confirmation. Bound-session mine guards still prevent firing out
of an unresolved current-sector field.

## Damage, ammunition and deaths

Existing destination mines absorb one missile each, consuming FIFO provenance
layers without RNG. Remaining missiles enter the ship loop with cumulative fighter
kills K and shield damage S, initially zero. Per missile:

1. Consume the original scanner-check random draw. Go currently has no installed
   scanner equipment, so there is no scanner state to disable here.
2. Add `floor(RND*4001)` to K.
3. If `RND*original_fighters < K`, add `floor(RND*1001)` to S. The comparison uses
   original fighters and cumulative K, not remaining fighters. Integer scaling
   preserves the strict threshold without converting balances to floats.
4. Stop when both defenses are exhausted or the available shots end. Cap final
   blast damage at the original defenses.

The original post-loop death test is **shield exhaustion**, even if escort
fighters remain (`1f42:7818..7826`). The integration retains it. Remaining escorts
are consumed with the destroyed ship and reported separately, making the saved
defeated state consistent with existing death/loot primitives. Zero-shield ships
are vulnerable even to a volley whose fighter draw is zero. New prototype ships
still have their existing zero-shield initialization; buying shields is important.
This milestone does not silently grant shields to legacy/new accounts.

A kill samples and consumes inventory once, transfers ordinary port titles and
treasuries to the actual living shooter, and invalidates the victim's generation,
team access and docking state. Non-Earth unsalvaged mines become a source-attributed
wreck field; remaining launched missiles clear that field one-to-one before
otherwise dissipating. Earth disarms the remainder. A remote wreck never damages
or teleports the distant shooter. Existing occupants encounter remaining fields
through the normal mine-resolution guards on their next action/reconnect.

Primary missile deaths use `Cause=missile`; return-fire deaths use
`Cause=retaliation`. Both preserve the actual shooter account. Other estate and
replacement policies are unchanged, including retained planets and no turn refill.

## Retaliation and score cache

Only a surviving ship actually struck by the primary volley may respond. A volley
fully intercepted by mines does not provoke an unhit ship. Dead ships cannot fire.
The living defender chooses one return volley using the initiating attacker's
stored score S and its own available missiles M:

- M=0: no response.
- Positive S: `N = floor(S/100000)+1`.
- If N is zero or exceeds M: `N = floor(RND*M)+1`.

The full selected N is deducted from the defender before impact, even if the
original attacker dies after only one effective shot. This is not `min(N,M)`.
A score of 500,000 with stock 100 fires six, whereas an over-stock score falls
back to a random 1..M volley. Score division and random stock sampling are exact
integer operations. Return fire consumes no defender daily turns, can occur at
zero turns, and cannot recurse into another automatic response.

The same locked encounter supplies an explicit original-attacker target despite
its cloak. No global reveal, cached cloak clearing or other hidden-ship hit is
created. Explicit role IDs replace the original temporary actor-identity switching
that produced false suicide attribution in the captured DOS counterdeath case.

`Player.StoredScore` is a validated signed integer cache. **Score calculation and
scoreboard maintenance remain unimplemented.** New/migrated accounts default to
zero and therefore use the recovered random-stock fallback unless a validated
cache is populated. No synthetic wealth score, placeholder positive score or
new point reward is invented. The cache persists across ordinary saves and
replacement; positive/negative/over-stock boundaries are covered independently.

## Atomicity and bounded calculation

Launch debit, launching turn, mine interception, primary damage, loot/estate,
wreck fields, defender ammunition, counterfire damage/death and Earth disposal
share one store Update. Every failure is returned so the entire exchange rolls
back, including an invalid counter RNG, late abort or capacity failure. Both volleys
use one atomic-file replacement; a storage failure cannot independently commit
only one volley. Storage durability retains the existing platform limits, and an
error at the storage commit boundary is not automatically retried.
A lethal counter is a successful saved outcome; the frontend reports it before
returning the initiating ship's invalid-generation error. A target destroyed by
the first volley receives no retaliatory turn or shot.

One shared one-million ship-missile calculation budget bounds the primary and
return loops. Extreme zero-damage/large-stock encounters may be rejected in full;
no partial damage is saved or arbitrary smaller counter-volley substituted. Bulk
mine interception is bounded by source-layer count, rather than missile quantity.
Deadlines are checked after confirmation, inside the lock and after calculation.
Reusing an old lethal intent or victim generation cannot replay a killing award;
separate confirmed surviving launches remain separate paid attacks.

## Evidence and corrected interpretation

The basis is the prior [10-session missile/assault recovery](RECOVERY.md) and
[stored-score/counterdeath probes](../yt-ships/RECOVERY.md#missile-retaliation).
`scripts/verify_missile_evidence.py` copies the authoritative archive into a fresh
disposable legacy layout and reruns its historical verifier there: **80 checks
across 10 saved DOS sessions, including four separate model checks**. It also
reruns the ship/retaliation verifier: **141 checks across 17 standalone sessions
and two paired scenarios (21 DOS processes), including six model checks**. These
counts are not new or additional DOS executions. It never
rewrites archived evidence or claims new DOS runs.

Five new REA/Ghidra byte observations are retained in `missile-rea.json` for the
original YT.EXE SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
They cover ship eligibility/damage, scanner-flag persistence, return-volley sizing
and the explicit return call. REA was closed after export. The verifier independently
reconstructs the relocated image, checks all five observations plus scanner-load
and shield-death bytes, and compares eight injected-RNG fixtures against the
independent `missile_rules.py`. This is static-derived interpretation and modern
integer arithmetic, not runtime execution or exact original MBF/RNG replay.

**Correction to the earlier report:** `1f42:7585..758e` loads scanner flag `197c`
into `58ce`; the per-shot branch at `7632..765e` may clear that flag, and
`79ab..79b4` writes it back to `197c`. The earlier “mine-dropping check” label was
incorrect. Death separately reads/consumes mine stock `19a4` at `785c..7908`.
The current report/model comments are corrected; archival source/provenance is
preserved. Scanner equipment/loss behavior remains a future feature.

## Validation, compatibility and next work

Tests cover cumulative damage/strict shield gates, shield-only death and lost
escorts, score selection using the correct initiating account, zero/negative and
over-stock fallbacks, mine interception, wreck clearing, Earth disposal, hidden
and team exclusion, stale warnings/generations/turns/stock, nonrecursive return
fire, zero defender turns and calculation errors. Store tests prove rollback after
primary damage/counter failure, concurrent lethal claims, correct port transfers,
old-session rejection, same-day replacement budgets and saved-score migration.

`scripts/smoke_missiles.py` uses real GoDoors PTYs to cancel then confirm a remote
kill while the victim is online, verify old-session invalidation and mine resource
accounting, and provoke fatal return fire against a fully cloaked initiating ship.
The returning enemy remains the killer, Earth remains unmined, and replacement
retains 36 turns. It also clears mines with no ship target. Controlled zero-defense
fixtures make the lethal paths independent of random damage magnitude; no
production binary or RNG is patched. Transcript: `evidence/missiles-smoke.txt`.
CI reruns the model, saved DOS evidence and terminal checks.

World format is **8**. Supported versions 1–7 upgrade in memory and persist on the
next successful update, with no historical death replay. Version-7 headers must
not already carry new nonzero score or missile-death state. Read-only loads do
not rewrite files. Back up the stopped world, upgrade all nodes together, and use
the matching backup to revert binaries; rollback loses later progress.

Next: sector-fighter interception/deployment/combat, multi-ship and longer missile
routes, planetary bombardment, mine placement and scoreboard/complete maintenance.
Native BBS combat/durability acceptance and full economic exploit-chain playtests
remain open; cross-builds and local PTYs are separate evidence.
