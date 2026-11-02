# Private port-sale notice validation

Branch: `feat/private-port-sale-notices`, based on creation-news `8cbda13`.
Current world format: **29**, supported migration from 1–28, without old-sale backfill.

## Passed locally

- Full `go test -race ./...` and `go vet ./...` after implementation and quote
  safeguards, plus focused game/store/door ownership and notice tests.
- Owned, teammate and unowned purchases; exact price/treasury settlement; current
  treasury changes between quote and commit; full-length names; immutable private
  snapshots; seller-only unread/history; no public purchase event.
- Strict system/payload validation, unsupported/future-field migration rejection,
  read-only migration preserving funds and not inventing notices.
- Archive capacity/sequence, price/owner/name/location/clock changes, sealed-preview
  tampering, stale generation/season, wrong bound buyer, pre/late/lock-wait expiry.
- Aborted transaction rollback, concurrent competing buyers, concurrent retries,
  directory-sync committed warnings, receipt EOF retaining warnings, old quote
  replay after resale and fresh legitimate repurchase.
- New compact/classic [GoDoors PTY evidence](port-sale-notices-smoke.txt): decline,
  confirmed buyout, 31 debit/808 seller payout, old-name snapshots, private seller
  reconnect delivery, acknowledgement and retained history; buyer/visitor privacy
  and absence of purchase news.
- Existing ownership, ordinary direct radio and public planet-creation PTY checks.
  Incidental regenerated transcripts are restored; the new evidence is retained.
- Native newspaper-event verifier (34 returned controls/four exact chains), all six
  test methods and 54 negative variants; all 4,682 immutable archive hashes.
- Linux/amd64 and Windows/amd64 cross-builds.

CI includes the new PTY script and current-save smoke assertions now expect 29.
Hosted CI, live BBS acceptance and native Windows crash durability are not claimed.
The research retains distinct source identity, native behavior and modern supported
atomicity/privacy choices. [Implementation rules](../research/yt-newspaper/events/PORT_SALE_IMPLEMENTATION.md).
