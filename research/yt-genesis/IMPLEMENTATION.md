# Bounded Genesis endgame and safe season resets

This implements the [research contract](SAFE_RESET.md) as deliberate modern
policy. The archived DOS initializer remains untouched. Genesis is available in
both interfaces through main command `G` or `GENESIS`; it is separate from the
planet-creation Genesis Device. `SEASONS` shows public winner history.

## Admission and confirmation

The default requirement is **300 actual personally owned non-Earth ports**.
Teammates' titles and the saved score cache do not count. Genesis is global; no
Earth docking, minimum score or Xannor victory is required. Destroyed ships and
unresolved mine/sector-defense encounters cannot invoke it.

`GenesisPorts` is optional in the save: omission means 300, zero disables it, and
20 through 300 are valid explicit thresholds. Other values fail validation.
`-init -genesis-ports 20` configures a new test season; `-init -genesis-ports 0`
disables the endgame. The flag cannot silently reconfigure an existing season.
A small universe may have an unreachable default; it is never silently lowered.

The two-minute quote binds season, player/ship incarnation, current ship snapshot,
alias, sorted actual port IDs, current public score, universe size, maintenance
watermark and supported explicit settings. The destructive prompt clears queued
commands and terminal typeahead. Only a fresh, exact, uppercase **GENESIS** line
authorizes it. Blank, No, lowercase, command chains, disconnect, expired deadlines,
changed titles/settings/ship or a reset by another caller cannot commit the quote.
A login-local nonce is single-use; rollback also consumes the confirmation.

## One atomic boundary

The existing OS `world.lock` is retained, including its inode. Under that lock,
the store rechecks the epoch and post-wait clocks, recounts ownership and generates
an unpublished candidate. The generator now uses finite partial shuffles for extra
warps rather than rejection sampling. Sector count (8–3000) and unique ports,
reachability and all other world invariants retain the existing validator.

A successful reset preserves universe size, optional `GenesisPorts` and optional
`LotteryDailyLimit`, including **nil versus disabled zero**, and prior season
results. It records a new OS-random generation seed. Migration does not invent an
old seed. Starting resources/daily turns remain the Go game's existing constants;
unsupported native configuration is not synthesized.

All old accounts, teams, assets, ports/treasuries, player planets, mines/defenses,
NPC/revenge state, radio, battle reports, scores, lottery quotas and sequences are
replaced. Fresh ports already have the implemented economy's starting stocks.
Mercenary Base and Xannoron/HQ are explicitly bootstrapped before admission; no
whole daily maintenance pass or awards run on behalf of an empty new season.
Today's watermark makes same-day maintenance a no-op. The Wanderer lifecycle,
exact DOS generation/RNG/MBF parity and other unimplemented native phases remain
separate work.

`SeasonResults` is inside the **same replacement world.json** as the next epoch
and new universe. Each result contains only old season, start/end timestamps,
winner display alias and season-scoped player number, actual port count,
requirement and live public score. It contains no login identity, passwords,
private inventory, balance or message contents. Capacity is 128 results; a full
archive refuses safely rather than discarding winners. Public history is paged.
No marker file, external initializer, second winner file or automatic retry is
part of authorization or commit.

Before replacement, generation/bootstrap/validation/storage failure leaves the
old world and history unchanged. After rename, a directory-sync error means a
**committed reset with uncertain crash durability**, not rollback. The saved
receipt comes directly from that transaction, preserves joined output/storage
errors, and ends the invoking login. It never performs an old bound View to
reconstruct a winner after deleting the players.

## Epoch and compatibility

Save version **23** adds monotonic `Season`, optional `GenerationSeed` and
`GenesisPorts`, and bounded `SeasonResults`. Legacy versions upgrade to epoch one
without resetting, awarding, rewriting on read or backfilling winners. Upgrade
all nodes together with a stopped-world backup; older binaries cannot read the
new schema. An explicit archive export/admin reset command is not included.

Both compact and classic logins capture epoch **inside the authenticated world
transaction**, along with ID and ship generation. Classic startup repeats its BBS identity lookup
under that lock; a stale screen lookup cannot authenticate a reused player slot.
Store reads, updates, score
publication, acknowledgements and spy paths reject an ended epoch. Visibility and
spy caches and every prepared radio/combat/mine/travel/lottery/anti-cloak intent
also bind their original epoch. Reusing player 1 with generation zero cannot
revive an old login, grant its cached visibility or spend the new player's assets.

## Validation

Game/store/door regressions cover default and explicit thresholds, ownership
recount, forged score caches, encounters, confirmation/cancellation and stale
quotes; minimum/maximum generation; configuration preservation; 128-result
capacity and corrupted history; injected generation/bootstrap/validation failure;
byte-exact rollback, directory-sync warnings and receipt-output errors; competing
logins; real process termination before/after replacement; unchanged lock inode;
post-lock expiry; captured-login epoch races and reused-ID read/update/score,
radio/battle/spy acknowledgement and pending-intent rejection. The real GoDoors
PTY script exercises compact/classic reset, cancellation, receipt/logout, fresh
registration, history, explicit config and same-day bootstrap replay.

See [validation log](../../evidence/VALIDATION.md) for completed runs. Live BBS
acceptance and native Windows crash durability remain unverified; cross-builds
and local process-kill controls do not establish those outcomes.
