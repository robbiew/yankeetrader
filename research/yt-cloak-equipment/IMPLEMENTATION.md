# Bounded cloak purchasing and login-local anti-cloak

The [37-control DOS recovery](RECOVERY.md) is now integrated into both interfaces
with exact credit debits, existing ship/session authorization and atomic saves.
The original byte evidence remains unchanged. This implementation does not claim
complete DOS numeric, random-state or simultaneous-observer parity.

## Recharge, quantity defaults and receipts

Earth item 1 buys whole percentage points at 1,000 credits per point. Compact mode
uses `EQUIP cloak <points>` while docked at Earth. The classic quantity prompt
shows the default bounded by missing whole points and affordable whole points;
blank accepts it and zero cancels. Full-energy blank input therefore costs zero
and prints cancellation, not a purchase receipt. Over-capacity requests renew the
classic quantity prompt and discard queued correction commands.

Both paths require a current Earth docking token and positive integer quantity.
They reject unaffordable, over-capacity, remote or stale purchases. The gameplay
clock is sampled inside the world lock; session deadlines are checked before and
after mutation. Negative, decimal and malformed input does not buy anything.
Strict whole-number parsing deliberately differs from DOS accepting `1.9` as one
point. Existing ordinary equipment quantity behavior is unchanged.

Existing energy is fractional. Missing capacity within less than 1e-9 percentage
points of an integer is normalized to that integer to avoid accumulated binary
floating drift; other fractional capacity is floored. Payment remains integer,
with at most 100 points per purchase and a final energy clamp at one. No arbitrary
round-up of a material fractional point, free energy refill or monetary float is
introduced. A ship with 99.5% energy cannot buy another whole point.

Recharge spends no additional turn. Docking still costs its existing turn and
normal cloak consumption applies at the existing turn boundaries. New/replacement
energy, mine damage and daily maintenance retain their existing rules. Recharge
persists across reconnects and contributes no new asset-score bonus; only spent
credits reduce live value. Stored-score publication timing is unchanged. Earth
expenditure remains an economic sink, without port-treasury credit.

Only after save success does the receipt print purchased points, actual saved
credit debit/balance and energy before/after. Cancellation, rejection, expiration
and save failure never print a success receipt. The classic shop propagates a
committed directory-sync warning as a committed update, rather than calling it a
rejected purchase.

## Activation, visibility scope and deliberate differences

Earth item 6 or compact `ANTICLOAK` offers one activation for 500,000 credits. It
first checks current docking, affordability, living ship generation and the
login's visibility binding. The warning clears pending commands and terminal
typeahead, explains that repeats and empty results charge again, and requires a
fresh exact Y. Blank, No, stacked replies, invalid replies or disconnect cancel.
This fresh-input policy is intentionally stricter than legacy command stacking.

Activation traverses at most 50 validated players, in player-number order. It
reveals other currently living, nonretired, positively cloaked ship incarnations
to the buyer's existing visibility cache. Already visible targets count as zero
new reveals. Zero-cloak ships need no reveal, and the buyer does not gain a new
self entry. Both sensors and supported visible attack/missile target selection
reuse that same cache; authoritative life, team, position and combat checks still
apply. Global notices list only newly revealed player numbers/aliases, without
inventing locations or exposing private balances and inventories.

There is no permanent device or saved global reveal. Other observer logins keep
their own caches, and reconnect starts a fresh one. New or replacement ships do
not inherit a prior incarnation's reveal; a later paid activation can reveal them
under then-current rules. An activation remains labelled active for its login
even if its former targets disappear; that label grants no authority over future
targets. Each repeat is a newly confirmed fixed-price transaction. Empty results
remain paid and report zero newly revealed ships honestly.

The buyer and every victim retain their actual stored cloak. Information screens
show real energy and a separate active-login label. Unlike DOS's FAIL display and
own-decay suppression, ordinary modern cloak consumption continues. This is an
explicit implementation policy, not an assertion of original parity. Anti-cloak
has no asset-score bonus and generates no public newspaper event. NPC ship groups
have no player cloak cache and are outside this equipment effect.

## Transaction, deadlines and replay

A quote captures the actor's risk-relevant ship state, docking expiry, maintenance
marker and login activation counter. Store adds a cryptographic single-use nonce
bound to that login's exact cache. A new quote supersedes an old one. Commit
consumes its nonce before attempting the transaction, including aborted attempts;
wrong logins/cache pointers, stale state, expired docking/deadline and obsolete
ship generations cannot spend or activate. Counter exhaustion refuses instead
of wrapping.

Commit obtains the world lock before staging the visibility cache. The live cache
is locked until the save outcome is known; the private clone changes alongside
the reloaded world's debit. Concurrent sensors cannot read staged effects. All
visibility reads and updates use the cache mutex, with world-before-cache ordering
for transactional operations. No mutex is copied into a clone.

Ordinary callback, validation or pre-replacement storage failure discards both
world mutations and staged visibility. After successful atomic file replacement,
a directory-sync failure remains explicitly committed: debit and cache both stay
committed, the nonce remains consumed, and no normal success receipt is printed.
A reload sees the debited balance, and retrying that old confirmation cannot pay
or reveal again. Output failure or disconnect after a committed purchase does
not refund it; ending the login discards the ephemeral activation.

The normal post-save activation receipt gives the exact debit, saved balance and
actual number of new reveals, followed by their bounded public labels. It does
not claim that energy was erased, a permanent device installed or a repeated
activation revealed ships again. Quotes show the cost before payment without
publishing speculative target lists.

## Compatibility and validation

World version **21 is unchanged**. Recharge reuses persisted `Player.Cloak`;
activation counters, reveals and nonces remain in memory. No schema migration,
free energy, credit, equipment or reveal grant is added. Prior version-21 binaries
can still read these saved balances and energy; normal stopped-world backups
remain appropriate for operational rollback. Historical replay and full DOS save
import remain separate.

Validated locally on macOS arm64 on 2026-10-30:

- Full race-enabled Go suite and vet; exact/poor/full/fractional-capacity/default
  purchases, saturation and score timing; positive whole-point bounds; snapshot,
  session/ship-incarnation and nonce guards; parallel purchase/activation spending;
  world/cache-lock waits and late deadline/docking expiry; byte-exact rollback and committed
  directory-sync/reload/replay; concurrent readers blocked until cache outcome.
- Compact/classic tests cover exact saved receipts, full/poor/blank/default inputs,
  over-capacity queued correction rejection, fresh/stacked/cancelled/EOF activation,
  paid zero-new-target repeats, real energy and active status.
- Twelve real terminal smoke scripts plus the ASCII port variant pass: the new
  cloak-equipment flow, DOS Earth-port parity, cloak, attacks, scanner/warp,
  startup, idle prompt clock, ports, navigation, missiles, bribery and spies.
  The new flow checks purchase/reconnect/defaults, actual reveal counts, observer
  isolation, unchanged victim energy and normal turn-boundary decay. Existing
  parity checks retain character/color comparisons and the unsupported lottery
  assertion. Regenerated historical smoke captures are restored.
- The 37-session/10-native-observation cloak verifier and 23 corruption controls,
  the existing 41-session scanner/warp verifier and all 4,682 archive hashes pass.
  Linux/amd64 and Windows/amd64 cross-builds pass.

Validation uses an external temporary module-file override pointing to the existing
local GoDoors checkout. Repository module files and GoDoors sources are unchanged.
Live BBS acceptance and native Windows durability remain unverified. Exact MBF/RNG
parity, the full original concurrent-observer/replacement-target behavior, paid
lottery, Genesis and other remaining gameplay are separate work.
