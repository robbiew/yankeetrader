# Earth's paid Pick-6 lottery — research

Historical research milestone. The later [bounded implementation](IMPLEMENTATION.md)
now supports Earth item **4** in the Go door. This report retains its research-stage
contract and evidence boundary. The separate
[maintenance lottery](../yt-maintenance-lottery/RECOVERY.md) awards super-planets
and is not this paid shop action. The research stage retained save version **21**; implementation introduces version **22**.

## Evidence and scope

The retained corpus comprises 49 normally completed original-DOS controls, 98
before/after worlds, three exact parent-world/auxiliary reload edges, and twelve
REA native byte observations. The controls cover ticket price, affordability,
input retries, configured daily limits, repeated play, reconnect/day reset,
matching with duplicates, all six winning tiers, news thresholds, stored scores
and large-balance rounding. The original binaries and archived fixture were
copied into disposable DOSBox Staging directories; the archive was never mounted
for gameplay or rewritten.

The baseline is `fixture-team-captain`, SHA-256
`04eaf42c54d4f35c3412737e27fa968b5abcd22eb295cb5d8b45ab8045fcd0ec`.
The caller is player 2, alias Q, with 100,000 credits unless a control declares
another balance. The recipe declares the navigation graph, restored Earth port
link, player setup, date/time and all per-control patches. Unmodified `YT.EXE`
has SHA-256 `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
Each run retains compressed world snapshots, exact auxiliary inputs/outputs,
keyboard bytes, DOS clock/date, transcript, binary hashes and completion metadata.

The verifier independently reconstructs setup and parent chains, freezes the
recipe, checks exact input streams and native loaded bytes, validates resources,
score caches and news, and rejects unexplained world changes. Rehashed semantic
corruption controls challenge these assertions rather than merely file hashes.
The REA observations retain original record identities from two exported,
closed Ghidra sessions against the same executable and provider version.

Preparatory probes and mistimed repeated-play streams are excluded. One
quit normally but its second choice arrived during draw animation, so it played
only once; another reached a second entry without its intended ticket and timed out. The retained stream waits for the shop to return before each fresh
choice; completion alone is not treated as evidence of repeated play.

## Ticket entry and charging

A ticket costs **5 credits**, checked before eligibility or number entry. Four
credits are refused without increasing the daily counter. Five credits suffice;
a losing ticket leaves zero, and six credits leave one. Docking spends one turn;
a ticket adds no turn debit. The shop's affordability column is cash divided by
five, not the number of daily plays remaining.

The player enters **exactly six decimal digits**. Leading zeroes are valid.
Blank, five/seven characters, letters, a sign, decimal point and an embedded
space are rejected. A fresh valid answer retries within the same admitted play:
one counter increment, one draw and one fee. Blank is not a cancellation in the
original. The modern interface should provide an explicit safe cancellation.

Native ordering matters: eligibility saves the daily counter before requesting
the ticket. A winner's receipt and any news precede the award write, and the
shared shop path subtracts the fee afterward. Completed controls establish final
outcomes; interrupted entry, process failure and news-write failures were not
injected. The pre-input/save ordering is a native-code finding, not a claim that
those failures were reproduced at runtime.

## Daily limits and reconnects

Global record 1 offset 101 supplies the allowed daily plays; this fixture uses
five. Player offset 105 stores plays used. The native loader accepts integer limits zero
through nine; negative or over-nine settings become a session-local default of
three. Runtime controls confirm zero bans gambling, -1 and 10 display three,
and nine allows the ninth play but refuses the tenth. The malformed setting is
not rewritten in the world by these controls.

Already-used values equal to or above the configured limit are refused without
charge, draw or another counter increment. With a limit of two, two tickets are
paid and a third is refused. Reconnecting on the same DOS date preserves the used
count and refusal. A linked next-date login resets the counter, and its linked
purchase consumes one new play. These are login-date controls, not a run of
YTMAINT or proof of year-boundary, clock-rollback or concurrent-login behavior.

## Matching, animation and awards

A real draw selects six digits from 0 through 9. Matching is an **order-independent
multiset intersection**: each occurrence can match once. Ticket `888888` gets two
matches against a draw containing two eights; it does not get six. A permutation
of all six drawn digits gets the same jackpot.

The fixed-clock repeated-digit controls identify the draw's multiset as
`1, 2, 6, 7, 8, 8`. They are experimental witnesses, not a proposed production
seed. The transcript concatenates the animated digit updates: its final six
printed characters are not reliably the six drawn digits. The native code makes
the real draw first and uses extra random draws for display animation. No RNG
patch or binary patch was used to obtain a jackpot.

| Matches | Gross advertised prize | Witness ticket at the controlled clock |
|---:|---:|---|
| 0 | 0 | `000000` |
| 1 | 100 | `100000` |
| 2 | 1,000 | `120000` |
| 3 | 10,000 | `126000` |
| 4 | 100,000 | `126700` |
| 5 | 1,000,000 | `126780` |
| 6 | 100,000,000 | `126788` and permutation `887621` |

The fee is additional; a receipt names the gross prize. Zero matches print the
loss message. **Only four or more matches append public lottery-win news**, with
alias and nominal gross prize. One through three matches remain absent from that
news stream. Ordinary login news and logout score publication remain separate.
No other player's inventory, ownership, bank, treasury or stored credits change.

## Floating-point money defect

The original uses MBF single-precision stored credits. It saves an award first,
then separately saves the fee subtraction. At ordinary small balances a losing
ticket spends exactly five, but larger values and jackpots reveal rounding:

| Starting credits | Ticket outcome | Final saved credits |
|---:|---|---:|
| 100,000 | six matches | 100,099,992 |
| 5 | six matches | 100,000,000 |
| 16,777,216 | loss | 16,777,211 |
| 134,217,728 | loss | 134,217,728 |
| 1,099,511,627,776 | loss | 1,099,511,627,776 |
| 16,777,216 | six matches | 116,777,208 |
| 134,217,728 | six matches | 234,217,728 |
| 1,099,511,627,776 | six matches | 1,099,611,635,712 |

Thus the first jackpot's fee effectively rounds to eight, some large balances
lose no fee, and the largest tested award grows the balance by 100,007,936 despite
advertising 100,000,000. Score caches inherit native rounding; there is no separate
lottery asset or score bonus. At 2^40 credits, even the printed score has an
overflow marker and differs from the stored cache; those two witnesses are checked
separately rather than treated as a universal score/display formula. These observations bound numeric fidelity; they do
not justify importing the money defect into the modern exact-credit engine.

## Native corroboration

The QuickBASIC-aware listings are interpretive aids. Conventional decompilation
can mistake the runtime's software-interrupt argument bytes for ordinary x86
instructions. The retained REA bytes are compared to the preserved executable's
MZ image with relocations applied at the observed load segment 0x1000.

| Loaded address, bytes | Corroborated path |
|---|---|
| `0x1759c`, 254 | Earth item 4 dispatch, affordability, eligibility and input loop |
| `0x23fd0`, 285 | Daily eligibility and early counter save |
| `0x240ed`, 195 | Length and digit validation |
| `0x241b0`, 244 | Six real digit draws and animation setup |
| `0x242a4`, 297 | Duplicate-limited multiset matching |
| `0x243cd`, 458 | Animated output and loss/win branch |
| `0x24597`, 376 | Prize formula, six-match multiplier, news threshold and credit helper call |
| `0x23f87`, 73 | Stored-credit addition/truncation/write helper |
| `0x17c2e`, 143 | Shared shop fee billing |
| `0x20996`, 198 | Login-day comparison and counter reset |
| `0x2b106`, 213 | Record field descriptors including credits and play count |
| `0x2b320`, 42 | Out-of-range configured limit fallback to three |

Relevant annotated anchors are main `1000:759f–7696`, `1000:7c3d–7c50`, and sub
`1f42:4bb0–52e9`, `1f42:1576–163c`, `1f42:bf00–bf27`. The sub listing's annotated
addresses differ from original segment-2000 addresses by 0xbe0; use the retained
loaded addresses for byte verification.

## Proposed bounded implementation

The next milestone should implement Earth item 4 and an explicit compact lottery
command with the following contract:

- Keep the five-credit price, six digits including leading zeroes, multiset
  matching, recovered gross prizes and four-match public-news threshold.
- Use exact integer money and a validated finite daily limit. Add persisted
  per-player day/count and a monotonic action sequence as needed, with a migration
  that grants neither tickets nor credits. Keep the paid shop lottery distinct
  from maintenance's one-shot super-planet award.
- Quote and confirm a complete valid ticket using fresh input. Cancellation,
  malformed input, expiry, stale ship/session, non-Earth position, insufficient
  funds or exhausted plays must not charge or consume a play.
- Under the authoritative world lock, recheck date, eligibility and limits after
  waiting; draw a bounded six digits, match each occurrence once, and settle the
  fee, actual capped award, used count, sequence and optional news atomically.
  Bound all arithmetic; define a capped prize receipt when credit headroom is
  insufficient. Retrying a committed storage warning must not repay a prize.
- Print receipts only after save outcome: entered/drawn digits, matches, exact
  fee, gross/actual award, cap adjustment, balance and plays remaining. Keep score
  publication consistent with the existing explicit cache policy; add no lottery
  asset value or public news below four matches.
- Validate all tiers, duplicates/permutations, poor/limited/cancelled/stale/expired
  calls, UTC reset/rollback policy, concurrency, rollback/reload, committed
  durability warnings and both real terminal interfaces. Update README together.

The proposal above is historical; the later implementation documents its final behavior and deliberate differences. Deliberate changes are exact money,
atomic settlement, explicit cancellation/confirmation, guarded dates and replay,
and accurate capped receipts. Original RNG/animation sequence parity, arbitrary
fractional/malformed counter/configuration values, interrupted originals,
year rollover, multiple concurrent DOS callers and native BBS acceptance remain
outside the demonstrated boundary.

## Reproduction

```sh
python3 scripts/recover_earth_lottery.py /private/tmp/yt-earth-lottery-fresh
python3 scripts/verify_earth_lottery.py
python3 scripts/test_earth_lottery_verifier.py
```

Capture requires the existing DOSBox Staging installation. Verification uses only
Python's standard library and the preserved repository archive. The frozen
recipe and evidence are under [dos](dos/); [REA observations](rea/yt.json) retain
the native evidence. Fresh runtime captures are new evidence and may have host
logging differences; they do not overwrite this corpus automatically.
