# Planet-creation newspaper entries and private port-sale notices

This milestone investigates the original DOS 3.6 newspaper producers identified
by the earlier [newspaper research](../RECOVERY.md). It adds research, portable
verification and documentation only. Planet creation and port acquisition are
already playable in Go; the public creation entry and private seller notice
remain follow-up work. Current save format stays 27.

## Findings and scope

A successful planet creation appends exactly:

```
  -  Q  made a planet: New Eden
```

The creator's public alias and accepted planet name are snapshots. The line does
not include sector, team, price, balances, cargo, weapons or account identity.
The selected controls show a 25,000-credit debit, a new planet/sector link with
the creator as owner, and no turn charge. An exact-credit caller ends at zero;
a zero-turn caller can still create. Normal login news is a distinct append,
not evidence that a failed creation produced an event.

Initial purchase decline/default, insufficient funds, an existing planet,
blank/reserved name and saturated slot-length flags produce no new creation
entry or debit. A refused name confirmation repeats naming; only the eventually
accepted name is recorded once. Planet confirmation defaults to acceptance;
port name confirmation defaults differently. Names are normalized and bounded to 41 characters
by the original helper. The long-name control stores/publishes
`Abcdefghijklmnopqrstuvwxyzabcdefghijklmno`, rather than its uppercase input. Punctuation/case and a longer-name control distinguish
accepted text from the prompt's earlier rejected input.

**Port acquisition is not a recovered public newspaper event.** The owned,
unowned, renamed, teammate, repeat and zero-turn controls compare the entire
actual news suffix with ordinary login bookkeeping. The purchase block's
complete bounded native search contains no direct shared-news append. Instead,
a buyout of another owner's port writes one private sale notice:

```
Q  bought your port "Test Port" in 101 for 31 credits
```

The fixed 86-byte record has an MBF read budget of 1, old-owner recipient 3 and
system sender -2, followed by a padded 74-byte body. DOS renders that legacy
system selector as **From: The Mercenaries**, not as the buyer's identity.
The seller's next login automatically displays it and changes the budget from
1 to 0; computer-6 history displays the same retained record without another
decrement. The buyer's history does not receive this seller-only notice. Recipient and system origin
are not inferred from a filename or from merely finding the wording in a log.
The tested old owner gets 31 asking-price credits plus 777 treasury credits:
2,000 becomes 2,808, buyer 100,000 becomes 99,969, treasury becomes zero, and
port ownership/counts move once. The private text names the 31-credit asking
price, not the entire 808-credit payout. Unowned purchases have no seller notice.

The notice is constructed using the **old** port name before optional rename.
Initial purchase refusal cancels. Refusing a name after Sold repeats the naming
dialog; it does not undo settlement. A stopped or timed-out process in that
middle state cannot count as a normally returned cancelled purchase. The bounded
controls finish the dialog, and the modern follow-up must make the complete
world/notice transaction atomic rather than reproducing sequential DOS writes.

## Evidence collection

The capture runner retains **34 normally returned processes: 18 planet controls,
12 acquisition controls and four exact reload chains** for the creator, old seller, renamed-port seller and buyer.
Every retained success control must return through LOCAL and emit the shell
return marker; timeouts and partial prefixes do not qualify. The runner reuses
the copied-world capture engine under an explicit new recipe and declared graph,
MBF patches, actor, date/time and key feed. It mounts only fresh temporary copies
from `archive/analysis/yt-combat/experiments/fixture-team-captain` and uses the
unchanged archived `YT.EXE`, `BRUN30.EXE`, `LOCAL.EXE` and key feeder.

Root controls start from the captured baseline with deterministic sector links,
resources, price/treasury and owner patches. Slot saturation sets the legacy
occupancy-length flags in a synthetic table solely to exercise the full-slot
exit. It is not a naturally generated full universe or proof that every inactive
record's name/link fields form a valid catalog. No unrecorded clock, executable
patch or forced instruction is used. The source's historical news is preserved;
new conclusions concern the exact appended suffix and its later reads.

Each child uses the parent's exact final world and every auxiliary file, with no
reconstructed substitute or resource patch, then loads the named actor at
00:10:00. Roots start on 10/24/2026 at 00:00:00. DOSDATE/DOSTIME and return logs
record the actual invocation inputs. Full before/after worlds, raw/compressed
logs, normalized transcripts, auxiliary bytes, keys and hashes are retained.
Queries are read-only in the selected resource fields, but normal logout score
caches and lazy port/planet display production are allowed and checked separately.
Whole-world byte equality is not claimed for these returned sessions.

The [native dossier](NATIVE.md) retains 21 complete byte observations, four
bounded direct-call searches and one complete load-image observation with all
870 relocations. It distinguishes the public `ytnews.DAT` append from the
private `ytRMSG.DAT` writer and anchors planet consent/name/fee ordering. Native
bytes establish static code and limited direct encodings; runtime files establish
which branches actually executed. Neither is a BASIC source decompilation.

## Reproduction and independent checks

With DOSBox Staging installed, choose a new destination:

```
python3 scripts/recover_newspaper_events.py /private/tmp/yt-newspaper-events-new
python3 scripts/verify_newspaper_events.py /private/tmp/yt-newspaper-events-new
python3 scripts/test_newspaper_events_verifier.py
python3 scripts/verify_archive.py
```

The portable verifier is independent of the capture writer. It reconstructs root
inputs from the frozen recipe/source and verifies exact child world/aux chains,
real action and resource effects, output execution witnesses, normalized/raw
logs, declared actors/clocks, public suffixes, private packet routing and native
bytes/load/search coverage. Six tests reject 16 native byte/load/search corruptions, 37 rehashed runtime
semantic/provenance corruptions and one frozen-recipe mutation (54 negative
variants total). They assert the intended rejection cause after refreshing file
and auxiliary hashes. A valid elapsed-display variation passes, so the checker
does not merely require a golden whole-output hash. All 76 portable CI evidence/control commands and 4,682 original archive hashes
passed. CI runs these checks without DOSBox.

[Questions and evidence boundaries](QUESTIONS.md) and the
[follow-up implementation contract](CONTRACT.md) separate recovered behavior from
modern atomic-save/private-history policies. Exact DOS colors, untested string
cases/indirect dispatch, interrupted writes, simultaneous DOS writers, live BBS
acceptance and native Windows durability remain separate. No public purchase
notice should be invented from the old broad “acquisition event” backlog.

Executed checks are recorded in the [validation record](../../../evidence/NEWSPAPER_EVENT_RESEARCH_VALIDATION.md).
