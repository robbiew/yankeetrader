# Planet-creation and port-acquisition event checklist

Target: the archived DOS 3.6 `YT.EXE`, SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
Only disposable copied worlds are executed. No archived executable/data or live
BBS world is modified, and this milestone adds no Go gameplay or save fields.

| Question | Evidence required | Disposition |
| --- | --- | --- |
| What successful planet-creation event is public? | Actual news-file suffix, accepted name, new owner/location and fee; native writer call | Answered: exact creator/name line after successful creation |
| Do cancelled/failed creations publish anything? | Separate initial consent, blank/reserved name, name retry, funds, slot flags, existing planet and zero-turn controls | Answered for selected gates; slot flags are synthetic |
| Which name is recorded after retry/truncation? | Accepted stored name versus rejected input, exact news text and native name-helper bytes | Answered: final normalized 41-character name only |
| Does acquiring a port publish public news? | Exact before/after news for owned/unowned/renamed/cancelled purchases; bounded native caller search | Answered for tested ordinary paths: no public purchase append |
| Who receives a port-sale notice, and what is disclosed? | Exact recipient/system sender/message record, settlement, seller and buyer reload chains | Answered: old owner, system sender -2, old name/sector/price |
| Is rename refusal purchase cancellation? | Initial refusal versus accepted purchase/name retry, final ownership, one payout and notice | Answered: initial refusal cancels; rename refusal retries |
| Do events/notices survive a real reload? | Exact parent world and every auxiliary file, normal return, independent read histories | Answered: four exact world/auxiliary reload chains |
| What remains to implement? | Compare confirmed scopes with current Go event producers without inventing public acquisition announcements | Answered: public creation plus private seller notice remain follow-ups |

[Recovery report](RECOVERY.md) records final dispositions after the normal-return
controls and independent verification. [Native evidence](NATIVE.md) separates
static observations from runtime results. Slot saturation deliberately sets only
the legacy occupancy-length flags in a synthetic table; it is not a naturally
populated universe or proof of every legacy catalog invariant. Exact DOS colors,
all string encodings/aliases, concurrent writers and crash behavior remain outside
this bounded research.
