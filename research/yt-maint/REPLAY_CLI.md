# Research-only maintenance recipes and CLI

`cmd/qbmaint-replay` is a separate source-only adapter around the qualified Go
initial maintenance APIs and bounded three-day convergence chain. It does not run a door, load modern saves, generate a
new playable world, import a DOS game into the modern schema, or replace
`yt -maint`. The repository's published release packages remain unchanged.

## Reuse an existing fixture

From the repository root, with Go and Python installed:

```sh
replay_work=$(mktemp -d)
python3 scripts/export_replay_cli_recipes.py --out "$replay_work/cases"
go build -o "$replay_work/qbmaint-replay" ./cmd/qbmaint-replay
"$replay_work/qbmaint-replay" \
  -recipe "$replay_work/cases/matrix-late-observed-a/recipe.json" \
  -before "$replay_work/cases/matrix-late-observed-a/before" \
  -source-root "$PWD" \
  -out "$replay_work/result"
```

Read the six original DOS filenames and `receipt.json` under
`$replay_work/result/replay/`. The output parent must already exist; `result`
itself must not exist. A retry needs a new output path. Existing directories,
files and symlinks are refused; no force/overwrite option exists.

The exporter assembles32 recipes from existing portable fixtures:29 ordinary
`initial` cases and3 repeated late-clock `initial-wanderer` cases. It writes
three before files, a recipe and separate native `oracles.json` per case. The
oracles are test expectations only; the Go CLI never opens them or accepts them
as recipe fields. No native acquisition or duplicate after-world file is added.
Windows uses the same flags with its own paths; the CLI cross-builds for Windows,
but native Windows filesystem acceptance is not claimed. PR #164 separately
addresses pre-existing Windows-reserved checkout paths.

## Recipe format v1

All fields are mandatory and use the canonical lowercase/snake-case spelling.
Unknown fields, duplicates (including case aliases), nulls, trailing JSON and
excessive nesting/size fail. A minimal structural outline, with arrays abbreviated
only here, is:

```text
format: "qbmaint-replay-v1"
profile: "initial" | "initial-wanderer"
name: case label (letters, digits, . _ / -; at most128 bytes)
before_sha256: exact YTDATA.DAT, YTNAME.DAT, YTNEWS.DAT identities
source_sha256: relative source paths and lowercase SHA256 identities
recipe:
  ports: days[1000], timer_minutes[1000], capped (explicit boolean)
  wanderer_day, xannoron_day, base_day, final_day: source days1..732
  initial_state: explicit24-bit integer (zero is valid, not a default)
  helper_one: 41 or42 raw TIMER samples in source order
  helper_two: 19 raw TIMER samples
  xannoron_timer: raw creation TIMER
  aux: news_date, news_clock, score_date, score_clock
```

Each raw SINGLE is exactly eight lowercase hex digits representing its four
original MBF bytes in file order. Exponent-zero mantissa/sign residues are not
converted to host floats or canonicalized. Days and auxiliary clocks remain
independently sampled inputs. The core APIs retain their existing semantic
admission, including rejection of a late encounter through the strict profile;
the adapter never silently switches profiles.

The three before files are snapshotted, bounded in size and hash-checked before
use. Source paths must remain within the declared source root and name regular
files; traversal, alternate-stream/backslash paths and symlink escapes fail.
V1 source references are Python files under `scripts/`, the existing calendar/
clock-matrix pin manifests, and the immutable original
`archive/dos-original/YTMAINT.EXE` (whose SHA256 is mandatory). Native after files
and expected-output oracle paths are not source references in this format.
Every declared source file must match its recipe hash. The recipe is limited to
2MiB; YTDATA has the qualified default extent and before name/news files are each
limited to1MiB. No after-target field or target-derived correction is accepted.

These checks bind declared inputs and source references. They do not authenticate
the recipe author, rerun native acquisition audits, attest the compiled Go
binary, or prove arbitrary clock combinations came from a native run. Existing
fixture provenance remains covered by the established exporter/CI audits. The
v1 adapter does not broaden its initial-world corpus to evolved or arbitrary worlds.

## Output and receipt

All replay/validation work completes before a bundle is published. Files are
staged together and renamed into a newly reserved `OUT/replay/` directory; failed
runs remove their staging files and never reuse an existing output. Output must
be outside both before and source trees, including aliases. This is complete
bundle publication, not a claim of tested power-loss durability on every host.
Inputs and modern saves are never rewritten.

`qbmaint-receipt-v1` records the exact recipe-byte SHA256, profile/name, verified
before/source hashes, all six generated output hashes, total draw count, final
state and derived encounter receipts. `state_evidence` explicitly says
`modeled-not-native-endpoint`: these are calculated endpoints, not new native
RNG observations. There is no host timestamp or hidden clock input.

The six DOS files preserve byte contents, including native CRLF/EOF and raw
numeric residues. The seventh file, `receipt.json`, is adapter metadata, not an
original DOS output. A successful CLI run exits0; validation/replay/publication
errors exit1 without a published replay bundle. If status output fails after
publication, the error explicitly identifies the already published bundle;
retrying that output path still fails rather than replacing it.

## Verification

```sh
python3 scripts/test_export_replay_cli_recipes.py
python3 scripts/smoke_replay_cli.py
go test -race ./internal/qbreplay ./cmd/qbmaint-replay ./internal/qbmaint
go vet ./internal/qbreplay ./cmd/qbmaint-replay ./internal/qbmaint
```

The compiled CLI reproduces all192 complete native files in the32 retained
cases and agrees with existing independent model endpoints/encounters. Tests
separate expected native hashes from recipe inputs and exercise existing-output,
changed-before, changed-source and strict-profile refusals. Go regressions cover
schema defaults/duplicates/nulls, raw zero residues, rooted file access, output
aliases, concurrent reservation and publication isolation. Original native
observations and unrelated smoke captures remain unchanged. Gameplay/save35,
release packaging and live BBS/native Windows acceptance remain separate.

## Three-day chain recipe v2

The separate `qbmaint-replay-v2` format selects only `convergence-three-day`.
The v1 schema and its two initial profiles retain their existing behavior. To
reuse the existing convergence fixtures from the repository root:

```sh
chain_work=$(mktemp -d)
python3 scripts/export_chain_cli_recipes.py --out "$chain_work/cases"
go build -o "$chain_work/qbmaint-replay" ./cmd/qbmaint-replay
"$chain_work/qbmaint-replay" \
  -recipe "$chain_work/cases/observed-a/recipe.json" \
  -before "$chain_work/cases/observed-a/before" \
  -source-root "$PWD" \
  -out "$chain_work/result"
```

The exporter assembles three source-clock sequences from existing qualified
fixtures. Only original day-one before files are exported as inputs. Separate
`oracles.json` files contain comparison hashes/states; the command never reads
those files. Native observations and hashes are unchanged.

All v2 fields are required, canonically spelled and non-null. Duplicate/case-alias
keys, unknown fields, trailing JSON, excessive size/nesting and malformed raw hex
fail as in v1. Structural outline (arrays abbreviated only here):

```text
format: "qbmaint-replay-v2"
profile: "convergence-three-day"
name, before_sha256, source_sha256: as in v1
days[3]:
  day: 306, 307, then 308
  initial_state: explicit 24-bit startup seed for this DOS run
  ports: days[1000], timer_minutes[1000] (no capped field)
  planets: ordered {record, day, timer_minutes} (one then four active records)
  creation: [{wanderer_day, xannoron_day, base_day, xannoron_timer}] on day one;
            [] on days two/three
  home_helpers, tail_helpers: ordered {family: 1|2, caller: uint16, timer: raw hex}
  aux: news_date, news_clock, score_date, score_clock
```

The chain accepts only the three measured original file identities. Raw SINGLE
bytes are preserved, including zero residues. Dates must match each explicit
source day. Detailed phase admission and helper caller/consumption checks remain
in the Go chain. State is computed between phases within a day; each new DOS run
starts from its own explicit source-derived seed. No child world, expected output,
cache correction or observed RNG endpoint field exists.

V2 additionally permits only the existing convergence-chain, occupied-route and
placement-cache `pins.json` manifests as source references. They are hashed as
provenance references, never decoded to influence replay. All other source/path,
size and isolated-output rules remain as above. These checks do not authenticate
recipe authors or attest the compiled binary; existing fixture provenance/native
qualification remains a separate CI audit.

Successful output contains `OUT/replay/day-1/`, `day-2/`, `day-3/` (six DOS files
each) plus one `OUT/replay/receipt.json`. All three days must finish before any
bundle is published; a late failure publishes nothing. Existing output paths are
refused. `qbmaint-receipt-v2` records all 18 relative output hashes and a `days`
array of source day, startup state, final state and draw count. Top-level draws
are the sum of the three runs; top-level final state is the last run's final
state, not a cross-process continuation seed. All states remain explicitly
`modeled-not-native-endpoint`. There is no host clock input.

```sh
python3 scripts/test_chain_cli_recipes.py
```

Compiled-CLI tests match all nine complete six-file results across three chains,
including previous-news rotation and daily receipt states/draws. They reject late
helper failures, changed before/source bytes, unknown endpoints and output reuse,
and prove comparison-side oracle files are not inputs. Schema regressions cover
explicit zeros, raw residues, missing/null/duplicate fields, wrong days/records,
creation context and unsupported references. Existing one-day CLI/native hashes
remain covered separately. This is source-only research; it does not replace
`yt -maint`, add a playable profile, change save 35 or ship new release binaries.
