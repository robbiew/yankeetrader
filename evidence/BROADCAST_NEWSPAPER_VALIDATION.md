# Broadcast newspaper publication validation

## Implemented scope

`RADIO ALL` and classic computer option 5 retain individually addressed current-
roster copies, and now atomically publish one public sender-alias/body snapshot.
The final preview names the public audience and actual sender before fresh Send.
Direct/team mail remains private. Abort, stale state, journal clock/sequence
failure, insufficient mailbox capacity and failed store transactions publish no
partial mail/news. No turns or assets are charged.

Public news uses the existing 1,024-event rolling today/yesterday journal. Reads
never acknowledge private mail. Retained-draft retries do not recreate news,
including after journal pruning, roster changes or committed storage warnings.
Version 27 upgrades versions 1–26 without inventing historical public broadcasts;
read-only loads do not rewrite the save. Pre-27 saves claiming the new public kind
or text field are rejected.

## Local checks

- Full race-enabled Go suite (`-count=1`) and vet passed using the supported local
  GoDoors checkout through a temporary modfile; repository dependencies unchanged.
- Focused final game/door/store race tests passed for typed public validation,
  bounded rollover, backward clocks, exhausted sequences, late/partial batch
  failures, draft replay after pruning, actual alias snapshots, migration,
  unchanged private direct/team scope and public rendering in both interfaces.
- Actual store rollback and directory-sync fault tests verify all private copies
  and public news remain absent together or visible together. Eight concurrent
  retained-draft retries preserve one entry and independent unread flags.
- Receipt-boundary output failures (EOF, closed pipe and other error) preserve
  the committed storage warning and terminate the login. A journal failure prints
  no saved receipt. Storage fault injection remains in store tests; no production
  fault switches were added.
- Real broadcast PTYs passed compact/classic Send/Abort, literal semicolon/slash
  text, explicit public preview, offline recipients, independent acknowledgements,
  later-account private isolation, public reading in both interfaces and reconnect
  without duplicate publication.
- Linux/amd64 and Windows/amd64 cross-builds passed.

All 70 CI evidence/control commands passed, including verification of all 4,682
original archive hashes. All 53 CI terminal/control commands passed, including direct/team/broadcast
radio, newspaper, schema migrations and affected gameplay flows. Unrelated
generated historical captures were restored; the refreshed broadcast transcript
is retained.

## Deliberate differences and unverified acceptance

The shared DOS delivery counter and multiline editor are separate work. This
implementation adds public publication while retaining the documented private-
copy delivery policy. Its calendar-based public retention is the existing Go
newspaper policy, not a claim of matching DOS radio exhaustion or maintenance.
The recovered 72-versus-74-byte maintenance text-width question remains unprobed.
Live BBS gameplay/transport and native Windows crash durability remain unverified.
