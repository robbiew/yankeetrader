# Bounded danger scanner and manual emergency warp

The recovered scanner purchase, warning queue and manual-warp rules are now
playable in both interfaces. [The recovery report](RECOVERY.md) retains the DOS
facts and limitations. This implementation uses exact credits, bounded work and
the existing locked atomic store rather than the original separate writes.

## Scanner purchase, value and lifetime

Earth item `5` immediately installs one danger scanner for 250,000 credits without
a quantity prompt. Compact mode uses `EQUIP scanner 1` after docking. Both paths
validate the current Earth docking token and session deadline after acquiring the
store lock. Duplicate, unaffordable, remote, expired and non-unit purchases do not
charge or install. Earth expenditure remains an economic sink; no treasury is
credited. A saved receipt reports the exact debit and resulting balance.

The shop displays actual availability and ship information displays actual
installation status. Installation survives reconnect and daily maintenance. New,
legacy-upgraded and replacement ships receive no free scanner. Death and
retirement clear it. Mine damage also persists scanner loss: shielded bursts with
positive shields remaining use strict `RND>.95`; the first collapse to zero shields
keeps the scanner without that roll, and a later unshielded burst clears it.
Existing ships without scanners consume no new scanner-loss random draw.

An installed scanner contributes 250,000 points to live rankings. Retained DOS
`shop-exact` and `shop-leave` saves both score 10,140,250 despite replacing 250,000
cash with the scanner; `shop-above` scores one point more. Stored-score publication
continues on the existing explicit/login/logout/daily paths, not during purchase.
Score-scanner equipment remains unimplemented.

## Movement warnings and autopilot

Installed scanners inspect only real current mine layers and hostile sector
fighters. Own and same-team fighters are exempt. NPC and human labels come from
actual owners; no private balances or imagined disruption state is displayed.
The warning prints quantities and clears pending commands/typeahead before a
fresh decision. Invalid/nonadjacent movement is rejected before warning.

Acceptance enters one adjacent sector, spends one movement turn and resolves
mines. Hostile fighters remain in place and block ordinary actions until their
encounter is resolved. Decline, blank, stacked confirmation or disconnect spends
no new turn. A warning stops autopilot even when accepted, preserving already
completed hops. Uninstalled ships retain the prototype's conservative mine-entry
confirmation and blocked hostile-fighter movement; this existing safety policy
is broader than the original absent-scanner behavior.

Warning snapshots include position, ship incarnation, risk-relevant inventory,
turns, scanner/team status, access tokens, current maintenance marker and exact
mine/hostile-defense state. Owner-team changes are also checked. Acceptance
revalidates them under the store lock and, during autopilot, rechecks the remaining
route/avoid list/budget. A changed warning requires a new decision. The same save
contains the hop, damage, scanner loss, escape and death/estate effects.

## Manual warp and receipts

Main `W`/`WARP` is available in both interfaces, including from hostile fighter
encounters. It needs at least one turn and no purchased hardware or credits.
Current unresolved mines must first be resolved by the existing hazard path.
A new risk confirmation discards queued input; this is a modern safety policy
rather than the original acceptance of stacked `W;Y`.

Heat work is bounded to 139 steps, using the mathematical integer part of
`70*(RND+RND)`. Each strict `RND>.75` adds a heat mark, stopping at 31. A single
indexed draw chooses from sorted actual sector IDs, preserving current-sector,
avoid-list and nonadjacent eligibility. The recovered overwritten draw is consumed.
Normal recharge is `min(remaining turns, 4*heat + floor(4*RND))`; 31 marks spends
all remaining turns. Every draw must be finite and within `[0,1)`.

A mathematical zero-turn recharge remains possible. A saved monotonically
increasing per-account warp sequence invalidates older confirmations even for a
zero-cost same-sector outcome. A login-local single-use nonce additionally
consumes each attempted confirmation, including rolled-back or expired attempts.
A sequence at uint64 maximum rejects further warps instead of wrapping. Ship
replacement keeps the sequence and separately invalidates the old incarnation.

Recharge spends turns through the existing cloak accounting. Warp clears docking,
landing and departure-grace authorization, then resolves arrival mines in the same
transaction. Existing safe automatic mine escape can add another debit and change
the final position. Death applies normal attribution and estate cleanup; a living
ship at a hostile defended destination remains blocked. No extra ordinary
movement turn is charged. Existing spies advance once on successful living travel
and do not prevent fatal travel from committing.

The post-save receipt identifies the random landing, heat, exact recharge, extra
arrival-escape debit and actual total turns spent. Mine/death/escape output follows,
so a later safe escape is not confused with the random landing. Meltdown reports
that all remaining turns were consumed. Modern daily maintenance restores the
normal turn allowance; there is no additional engine-damage flag. This policy
is distinct from unverified next-day original-DOS repair behavior.

No success receipt is printed before persistence or for cancellation, rejection,
rollback or a committed directory-sync warning. The existing committed-error text
remains explicit. Reload sees the committed sequence/destination/resources, and
old confirmation retries cannot teleport or spend again.

## Save compatibility

World version 21 adds boolean `DangerScanner` and unsigned `WarpSequence`. Valid
older worlds, including version 20, upgrade in memory and persist the new version
on their next successful update. Read-only load does not rewrite files. Existing
identities, assets, balances, factions and private/public histories remain intact;
migration does not grant equipment, move ships, reset turns or invent past warps.
Legacy-labelled worlds with enabled scanner/nonzero sequence state are rejected,
as are malformed field types. A destroyed ship cannot retain an installed scanner.

Older binaries cannot read version 21. Use the README's stopped-world backup,
coordinated node upgrade and matching-backup rollback procedure. No DOS save
import or exact original RNG/MBF behavior is added.

## Validation

Validated locally on macOS arm64 on 2026-10-30 with Go 1.27.3:

- Full race-enabled Go suite and vet pass. Game tests cover exact purchase limits,
  duplicates/quantity/docking errors, score value/cache timing, own/team passage,
  stale ownership/inventory/generation/day warnings, finite RNG, bounded work,
  64 seeded warp worlds, short/full/zero-cost recharge, same-sector/avoided outcomes,
  overflow/replay, mine/scanner loss and fatal arrival/estate cleanup.
- Store tests cover byte-exact callback/validation/late-mine rollback, eight-way
  purchase and zero-cost same-sector warp contention, one-use confirmation,
  post-lock expiry for preparation and commit, stale state, directory-sync failure
  after replacement, reload, old-generation invalidation and read-only migration
  without equipment grants. Door tests cover both interfaces, real debit/turn
  receipts including additional automatic escape, fresh/stacked/cancelled/EOF
  decisions, partial autopilot and hostile arrival gates.
- Twenty real terminal smoke scripts pass, including the new scanner/warp smoke
  for purchase/reconnect/duplicate refusal, fresh manual and autopilot warnings,
  hostile entry, normal/one-turn random warps and actual receipts in both interfaces.
  The other 19 are the previously affected newspaper, awards, Mercenary base,
  mines, missiles, radio, salvage, spies, teams, Xannor lifecycle/mobile/planet/
  revenge/ship/HQ combat, ports, reports, trade reports and overcrowding scripts.
- The 41-session/10-native-observation research verifier, 23 rehashed semantic
  corruption controls, 46-session mine/hazard verifier and all 4,682 archive hashes
  pass. Linux/amd64 and Windows/amd64 cross-builds pass.

Validation uses an external temporary module-file override for the existing local
GoDoors checkout; repository module files and GoDoors sources are unchanged.
Historical regenerated smoke captures are preserved. Native Windows durability
and live BBS acceptance remain unverified. Complete disruptions/black holes,
next-day original-engine repair, lethal-arrival DOS parity and exact RNG/MBF
boundaries remain separate work.
