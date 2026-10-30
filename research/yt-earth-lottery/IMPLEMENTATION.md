# Bounded paid Earth lottery — implementation

The [49-control DOS research contract](RECOVERY.md) is now implemented in the Go
door. This is the paid Earth shop action, separate from maintenance's one-shot
super-planet award. The original archive and research captures remain unchanged.

## Playable flow

At Earth, dock with `P` and select shop item `4`. In compact mode, dock and use
`LOTTERY 000000`, or `LOTTERY` to enter a ticket at a prompt. A ticket is exactly
six ASCII decimal digits; leading zeroes are retained. Blank at the ticket prompt
cancels. Invalid length, embedded whitespace, signs, decimals and non-ASCII digits
are rejected without spending credits or a play.

The complete ticket quote names the five-credit fee and remaining UTC daily
plays. Remaining queued commands and terminal typeahead are cleared; only a fresh
single Y confirms. Blank, No, stacked approval, disconnect or expiry does not
settle a ticket. The shop affordability column shows credits divided by five,
matching the recovered display; the quote enforces the separate daily quota.

Each confirmed ticket uses six independently supplied uniform digits 0–9 from OS
cryptographic randomness. World-generation seeds and animation RNG cannot predict
it. Matching is multiset intersection, consuming each duplicate once and ignoring
position. Gross prizes for one through six matches are 100, 1,000, 10,000, 100,000,
1,000,000 and 100,000,000 credits. Zero matches award nothing. There is no extra
turn cost beyond docking, no Earth treasury payment and no lottery asset bonus.

A saved receipt prints the ticket, actual draw, matches, exact fee, nominal gross
prize, actual award, cap reduction, final balance and remaining daily plays. Credit
headroom is measured **after** deducting the fee: at MaxMoney, a winning ticket
awards five back and reports the remaining nominal prize as capped. The net-zero
balance still consumes a play and replay sequence. Public news is generated only
for four or more matches, with alias, match count and actual award; the renderer
also names the nominal prize so capped wins are accurate. It contains no account
balance, identity, ticket or draw. Existing explicit score-cache publication on
logout is retained; live rankings reflect saved credits immediately.

## Account quota and atomic settlement

The default is five plays per player per UTC date. Optional saved world field
`LotteryDailyLimit` accepts integers 0–9; zero disables paid play, omission selects
five, and invalid settings reject the world instead of silently falling back.
This is a stopped-world configuration field, not a caller command.

`LotteryDay`, `LotteryPlays` and `LotterySequence` belong to the player account.
Reconnect, death and ship replacement preserve them. A forward UTC date projects
a fresh quota but does not rewrite anything during a quote or read. Only a
successfully saved ticket advances the date and count. A date before the saved
lottery day or maintenance/history clock is rejected. Crossing UTC midnight
invalidates the old quote; the caller must request and confirm a new one.

The quote captures current ship generation, position/team/resources, docking token
and expiry, maintenance date, ticket, UTC day, effective limit, used count and
monotonic sequence. A cryptographic nonce and exact immutable quote are bound to
one login. Altered tickets, cross-login quotes, stale ships/docks/resources,
changed quota/configuration, cancellation and consumed nonces cannot authorize a
purchase. A successful ticket invalidates other logins' old quotes even when
credit capping leaves the balance unchanged.

The store holds its login encounter mutex and authoritative world lock. It
resamples the game clock after waiting, checks the real session deadline after
that clock callback and around every random-source call, revalidates the entire
quote and draws at most six digits. Invalid entropy or an expired deadline aborts.
All fallible checks, including public-news sequence availability for a large win,
precede in-memory resource mutation. Fee, bounded actual award, quota, replay
sequence and optional typed public news save together through the existing atomic
store. Ordinary failures expose no saved receipt and preserve the file exactly.
A directory-sync warning after replacement retains the committed settlement and
prints its exact receipt, then ends the session with the storage warning. It
cannot replay or repay that ticket. A new confirmation is needed after any
attempted settlement, including an ordinary rollback.

## Save compatibility and deliberate differences

Save version **22** adds the optional quota configuration, account date/count and
monotonic sequence, plus typed paid-lottery news fields. Version 1–21 migration
retains existing assets, dates, scanner/warp and session-independent cloak state;
it creates no tickets, prizes or synthetic history. Read-only loading upgrades
in memory without rewriting the file. A legacy version containing future lottery
fields is rejected. Upgrade all nodes together with a stopped-world backup;
older binaries cannot read the new save.

The original's pre-input counter write, separate award/fee saves, MBF rounding,
mandatory retry on blank, loose invalid-limit fallback and animation/random
sequence are deliberately not copied. Modern settlement uses exact integer
money, explicit safe cancellation, fresh confirmation, validated limits, bounded
random work, authoritative UTC guards, replay protection and accurate caps/news.
Historical DOS controls remain research references, not current save fixtures.

## Validation

Focused tests cover all tiers, duplicate and permuted tickets, exact poor/exact/
large balances, configured zero/one/nine quotas, UTC reset/rollback/midnight,
replacement persistence, entropy failures and news exhaustion without mutation,
credit caps, stale/tampered/cross-login confirmations, parallel net-zero capped
attempts, cancellation, post-lock/clock/draw expiry, byte-exact rollback,
committed durability/reload/replay and version-21 migration without gifts.

Both interface tests verify saved receipts, literal fresh confirmations,
malformed/declined/disconnected/expired paths, numbered-shop and compact dispatch,
and capped public reporting. A real GoDoors PTY script plays five actual random
tickets in each interface, independently evaluates every observed draw and receipt,
checks count/sequence/credits/news, then reconnects and verifies the quota remains
exhausted. Its public-history fixture also checks capped-win wording and private
field exclusion. The port parity smoke compares the restored lottery affordability
column directly against the original character/color capture.

Full race tests and vet, affected real terminal smokes, lottery/cloak/scanner
research and semantic corruption checks, all 4,682 archive hashes and Linux/Windows
cross-builds are recorded in the repository validation log. Live BBS gameplay,
native Windows durability and exact original RNG/MBF/animation parity remain
unverified; cross-builds and PTYs do not establish those operational results.
