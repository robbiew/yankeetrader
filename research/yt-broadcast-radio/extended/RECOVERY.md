# Broadcast radio: public records, shared lifetime and history

Research date: 2026-11-01. **Research only: no Go gameplay or save26 change.**
This extends the separate six-control broadcast slice in
[PR #58](https://github.com/robbiew/yankeetrader/pull/58). That proposal deliberately
uses private copies. The new observations below concern the original DOS 3.6
shared record, public newspaper path and exhausted-budget boundary; they do not
describe the private-copy policy as DOS parity.

## Findings

| Question | Evidence and result |
|---|---|
| Selector and team requirement | ALL and lowercase all reach the broadcast editor; both a no-team sender and a declared team member can send |
| Routing | One 86-byte YTRMSG.DAT record per submitted body line, destination -2, sender record2; no recipient-roster fanout |
| Initial lifetime | Each new broadcast line has first field 30 |
| Automatic delivery | Fresh recipient and sender logins each change 30→28; the same recipient reconnecting changes 28→26 |
| Computer history | History rereads leave that budget unchanged; the repeat control opens history twice |
| Boundary 2 | Automatic startup delivery displays once and writes0; the unrelated recipient's following history no longer displays it |
| Boundaries 1,0,-1 | Controlled mailbox patches show no startup or unrelated-recipient history display and no further decrement |
| Public newspaper | A successful send appends a Message from header and body to YTNEWS.DAT; two-line send writes one header and both lines |
| Abort/blank input | Abort, blank recipient and blank-body abort create no new radio record or broadcast news body |
| Costs | Position, turns, money, cargo, scanner, cloak and carried equipment are conserved; a sender with zero turns still sends |
| Deletion | Exhausting the startup budget does not itself remove the physical packet; native maintenance interpretation is separate |

The counter is global, not per reader. A repeated login by one person can use
another two units; one reader does not own an independent unread bit. A full
normal sequence would permit fifteen such decrements from 30 to 0; that is an
arithmetic inference from the recovered writer/reader, not a retained natural
fifteen-login experiment. Computer history is distinct from startup delivery.

The public newspaper bytes are direct runtime evidence. In the send control,
YTNEWS.DAT grows from 480 to 563 bytes, with one unique probe body; abort grows
only for the ordinary login entry. Two-line send retains both body lines once.
Later reader logins append normal login news but do not republish the broadcast.
The record remains in the newspaper independently of the exhausted radio budget.

The manual's phrase unexpired broadcast messages does not establish a calendar
expiry. Native writer/delivery code uses 30 and subtracts 2, with no date comparison
in that selected path. Native maintenance copies nonzero records and omits zero
records. Maintenance was not executed in these sixteen controls, so physical
compaction and full-width text preservation are static findings/limits, not
observed maintenance outcomes.

## Scope of the runtime corpus

The [recipe](dos/recipe.json) contains **16 normally returned fresh DOS controls
and 32 full world snapshots**. Eight start from declared copies. Four child
controls use their exact parent's saved world and complete auxiliary bytes:
recipient-read, sender-read, recipient-repeat and sender-after-recipient.
Another four children deliberately patch only the first radio field to 2, 1, 0
or -1, retaining the parent's world. Those are controlled boundary probes,
not unmodified auxiliary reloads.

The harness copies the source fixture and original YT.EXE, BRUN30.EXE, LOCAL.EXE
and KEYFEED.COM to disposable directories. It never runs archived originals in
place, changes executable memory or uses Go output as DOS evidence. Full mutable
DAT/ASC/DEF/TMP auxiliary bytes are retained, including newly created files.
Children remove inherited fixture side files before loading their parent's
complete saved auxiliary set and refuse an incomplete parent. Topological waves
respect the two-level reader chains.

The source is:

    archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT

SHA-256:

    04eaf42c54d4f35c3412737e27fa968b5abcd22eb295cb5d8b45ab8045fcd0ec

All controls declare DOS date 10/24/2026 and explicitly reset time 00:00:00.
DOSTIME.LOG records 0:00:00.00am. No one-minute elapsed or monotonically advancing
clock claim is made. The independent verifier checks exact inputs, completion/
return markers, raw CP437/rendered agreement, original binaries and source/setup,
the complete saved world/auxiliary witnesses, mail headers/body, shared budget,
public news and resource conservation.

Reproduce only into a new absent directory with DOSBox Staging:

    python3 scripts/recover_broadcast_lifetime.py /tmp/yt-broadcast-new --workers 6

Portable retained checks need no emulator or native provider:

    python3 scripts/verify_broadcast_lifetime.py
    python3 scripts/test_broadcast_lifetime_verifier.py

[Native evidence](NATIVE.md) retains eleven complete byte observations and two
verified MZ load images for YT.EXE and YTMAINT.EXE. Independent reconstruction
checks all 870 and 108 relocations respectively. Selected ranges, contextual
suffixes, static interpretation and incomplete coverage remain explicit.

## Difference from the existing Go proposal

PR #58's current-active-roster private copies, independent acknowledgements and
late-account isolation are documented modern policy. Original ALL has a public
negative destination and a shared counter. Current Go private-message validation
requires real player destinations, so introducing a DOS-style global record is
not just another team fanout.

This slice establishes the newspaper aspect that a private-copy-only design
does not provide. [CONTRACT.md](CONTRACT.md) separates an explicit public-news
follow-up from an original-style global archive. Neither was enabled by this
research milestone. The later [version-27 implementation](../IMPLEMENTATION.md)
now provides public newspaper publication with explicit consent, retaining the
private-copy delivery adaptation; it does not add a shared global radio archive.
The DOS two-line control is a routing/newspaper witness, not recovery of every
20-line editor operation or maximum-length character case.

## Remaining uncertainties

- New-account registration, dead/retired-account delivery and online concurrent
  processes were not newly exercised. Native public eligibility is not a runtime
  observation for every account class.
- Exhausted author-history eligibility is a static predicate interpretation;
  boundary runtime controls read as the other player.
- Natural long counter exhaustion, maintenance execution and 72/74-character
  maintenance payload preservation remain untested here. The native FIELD-width
  mismatch is documented without claiming an executed truncation bug.
- Reentrant writers, file-lock failures, exact original rounding, full multiline
  editing, native BBS acceptance and Windows crash durability remain separate.

See [validation](../../../evidence/VALIDATION.md) for commands actually run.
