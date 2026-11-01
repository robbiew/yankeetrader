# Mercenary plasma acquisition: removed sales feature

Research completed 2026-10-31 against the archived DOS **3.6** distribution.
This is a research/backlog correction: no Go gameplay or save 26 change. The
previous suggestion to implement Mercenary plasma sales came from an obsolete
versioned feature and is withdrawn. [Disposition](CONTRACT.md) records the
implementation boundary; [native evidence](NATIVE.md) separates static facts
from the DOS observations below.

## The versioned record resolves the supplier question

| Archived source | Observation | Consequence |
|---|---|---|
| [CHANGES.TXT](../../archive/dos-original/CHANGES.TXT), 3.3 heading at 277 and 307–316 | Introduces a Mercenary Mother Ship selling plasma for 5,000,000 credits each | Historical unit price only; not a current 3.6 price |
| [CHANGES.TXT](../../archive/dos-original/CHANGES.TXT), 3.4 heading at 356 and 390–396 | Introduces planetary production and explicitly removes that mother ship, citing redundancy and program space | Close the obsolete sales backlog |
| [CHANGES.TXT](../../archive/dos-original/CHANGES.TXT), 3.6 heading at 462 and 647–649 | Adds a defended Mercenary home planet, restored by maintenance | Distinct from the removed supplier ship |
| [YTINSTR.DOC](../../archive/dos-original/YTINSTR.DOC), 253–261 | Describes larger planets producing plasma; Earth cannot sell it | Current acquisition is planetary supply |

These are direct versioned documentation observations. There is no historical
3.3 executable in this investigation, so the old price is not combined with
3.6 base hostility, ownership or stock mechanics to fabricate a seller contract.
The later production changes also mean the 3.4 formula is not the final 3.6
production formula; existing planet/maintenance research remains authoritative.

## Bounded current-version observations

The [retained corpus](dos/recipe.json) contains **17 normally returned DOS
controls, 34 full world snapshots and two exact saved-world/auxiliary reload
chains**. Controls use copied original executables and a declared controlled
world; archived sources are never mounted for execution or modified.

| Control | Observed behavior |
|---|---|
| quiet, main-help | Baseline stock and funds retained; current help shows firing and planetary actions |
| earth-menu, earth-poor-menu | Same nine-item Earth menu with 20,000,000 or zero cash; no plasma item; docking costs one turn |
| earth-no-plasma-item | Text selection PLASMA is rejected; no plasma or credit change beyond the ordinary docking turn |
| base-look, base-land-refuse | Mercenary Base is a named planet; foreign defended landing offers assault and refusal preserves assets |
| captured-base-menu, captured-base-take | A controlled already-owned base uses the ordinary planetary help/stock path; taking one moves ship 9→10 and planet 20→19 |
| ordinary-planet-take, ordinary-take-all | An owned ordinary planet supplies one or all 20 bolts, without cargo-hold use or a credit charge |
| ordinary-deposit | The B transfer moves all 9 carried bolts to the planet, 20→29, leaving ship 0 |
| unowned-planet-take | An unowned zero-garrison planet allows the ordinary take path |
| mother-ship-name | Naming an ordinary owned planet Mercenary Mother Ship still produces the normal planetary menu |
| take-zero | Zero cancels without stock/credit debit |
| take-reload, deposit-reload | Exact prior saved world and all auxiliary bytes retain the transfer on a fresh login without repeating it; ordinary lazy planetary growth may continue |

On reload, carried stock remains unchanged; planetary fractional production and bank growth can still occur. The full saved witnesses retain those changes rather than assuming byte-identical outputs across logins.

In the isolated successful planetary transfers, turns remain 500 and cash stays
20,000,000. Those are measured outcomes for this fixture, not a claim that all
travel, landing or combat is free. The owned-base controls patch ownership
explicitly; they do not newly prove conquest or maintenance restoration. The
name control is an ordinary planet with a synthetic name, not a recovered
mother-ship entity. No current-version merchant eligibility, sale quantity cap
or purchase-hostility rule exists in this slice.

The current Earth item 9 is **Hire Spies**, while planetary item 9 is **Take Plasma
Bolts**. Native evidence confirms that Earth parses the first input character;
a supposed unsupported item 10 would instead select cloak item 1. We therefore
use an explicit nonnumeric PLASMA selection and record its actual rejection.

## Capture provenance and reproducibility

Source world:

    archive/analysis/yt-combat/experiments/fixture-planet-transfer/YTDATA.DAT

SHA-256:

    2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19

Original YT.EXE SHA-256:

    c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037

The writer preserves the original 3000-sector/100-planet table geometry, empties
unused players/sectors/planets and installs explicitly declared links, player
inventories and either slot 99 Mercenary Base or slot 2 ordinary supply planet.
Starting plasma is 9 on the ship and 20 on the planet, unless a reload uses its
parent's exact saved bytes. Money is 20,000,000 except the zero-cash Earth control.
Each control retains the original binary hashes, exact input, DOS date/time,
normal-return witness, raw CP437 log, rendered transcript, full before/after
worlds and auxiliary bytes, and file hashes in compressed metadata.

Date is 10/24/2026. Both independent controls and reloads explicitly reset the
DOS clock to 00:00:00, as recorded in metadata, DOSTIME.LOG and dosbox.log.
The reload chains preserve exact saved world/auxiliary bytes; they do not
establish a one-minute elapsed interval or monotonic clock progression.
The reviewed corpus reuses 14 completed exact-declaration controls after checking
normal return, baseline identity and every retained file hash; corrected
deposit and both reloads are fresh observations. An earlier deposit input
incorrectly inserted Q after B, entering quit confirmation rather than leaving
the planet. That incomplete disposable pilot is excluded entirely; it is not
evidence of a merchant, game hang or completed reload. The capture writer now
refuses to execute a child of an incomplete parent.

For a fresh absent destination with local DOSBox Staging:

    python3 scripts/recover_mercenary_plasma.py /tmp/yt-acquisition-new --workers 6

Portable retained evidence checks need no DOS emulator or REA provider:

    python3 scripts/verify_mercenary_plasma.py
    python3 scripts/test_mercenary_plasma_verifier.py

The independent verifier checks declared setup, original bytes, MBF values,
resource movement, menu/rejection/refusal observations, raw/rendered agreement,
normal return, exact reload chains and native relocated ranges. All **38 corruption controls** pass: 30 rehashed DOS semantic/provenance checks,
six native/declaration checks and two altered historical-document checks. Altered
outcomes must fail even after tampered metadata is made consistent.
See [validation](../../evidence/VALIDATION.md) for checks actually completed.

## What this does and does not establish

Twelve complete native byte reads plus one verified MZ load-image observation
cover selected current shell, Earth and planetary acquisition paths. All 870
relocations are independently reconstructed. The current shop has no plasma
item in the inspected menu/dispatcher. This bounded negative observation
corroborates the explicit removal notice; it is not universal proof that every
possible hidden or dynamically assembled binary path was inspected.

Historical 3.3 seller location/movement, caps, fractional input, hostility, taxes,
turn/cloak charges and sequential payment/delivery writes remain unknown. No
current merchant API, atomic purchase intent or schema migration is justified.
Existing Go planetary transfers retain their established guarded saves and
receipts; native sequential record writes are not modern atomicity evidence.
Live BBS acceptance, native Windows crash durability, exact DOS RNG/MBF parity
and unrelated spy/message/newspaper branches remain separate.
