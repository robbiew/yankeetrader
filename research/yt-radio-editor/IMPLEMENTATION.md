# Bounded multiline radio editor

`RADIO EDIT <recipient>` and computer 5 `EDIT <recipient>` select the editor.
The existing one-line interface remains available. This work depends on the
version-27 broadcast newspaper implementation in PR #61; it adds no save fields.

## Native evidence

Six independent original DOS runs in [dos](dos/) cover List/Continue, accepted
and rejected substring edits, confirmed Abort, the 20-line limit and two-line
ALL publication. Continue resumes the final line: FIRST / SECOND followed by
THIRD becomes FIRST / SECONDTHIRD. Edit replaces the first case-sensitive match
and asks before saving. Native ALL stores one shared mailbox record per line and
writes one author header followed by the document lines to the newspaper.

The independent verifier checks source auxiliary baselines, binary hashes,
login identities, keys, clocks, normal return, unchanged resources and exact
74-byte mailbox text. Seventeen rehashed corruptions exercise its semantic checks.

## Implementation and deliberate limits

Documents contain 1–20 nonblank printable ASCII lines, each at most 74 bytes.
Continue appends a suffix to the final line; confirmed Edit changes its first
matching substring. Oversize or unsafe input is rejected without truncation.
Native character-level wrapping and backspace editing are not reproduced.

Editor Send only opens the full final preview. A separate fresh S is required.
Recipient generation, team/active roster, sender life/season, expiry, archive
capacity and sequence limits are checked before publication. Every line and
recipient copy commits together; ALL public entries share that transaction.
Whole-document retries preserve read flags and create no duplicates. Aborted,
interrupted and rejected drafts publish nothing. Committed durability warnings
end the session even when the receipt cannot be printed.

Each line uses an existing mailbox record and ALL uses one typed news event per
line. Public rendering therefore repeats author headers. Independent unread flags,
rolling news retention and the bounded archive remain modern policies rather than
native shared-counter parity. No native Windows or live BBS acceptance is claimed.

## Validation

```sh
python3 scripts/verify_radio_editor.py
python3 scripts/test_radio_editor_verifier.py
go test -race ./...
go vet ./...
python3 scripts/smoke_radio_editor.py
```

Game tests cover all three delivery scopes, immutable drafts, bounds, retry,
partial-injection rejection and late-failure rollback. Store tests cover aborted
updates, committed sync warnings and concurrent retries. Door tests cover menu
editing, limit/Continue behavior, alias compatibility, interruption and fresh final
confirmation. The [PTY transcript](../../evidence/radio-editor-smoke.txt) exercises
compact and classic entry, literal text, direct/team/public lines and privacy.
