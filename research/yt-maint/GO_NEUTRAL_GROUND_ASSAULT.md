# Bounded Go strong neutral-planet ground assault

`ReplayNeutralGroundAssault` implements the existing occupied Python
`ground_assault` rule in a separate Go primitive. Inputs are a complete default
world, moving group 2–20, sector 854, whole force 1–10000 and a modeled 24-bit RNG
state. Sector 854 must link slot 2 and contain no physical defense or mines.
Record 4053 must be the exactly padded, length-11 `Route Haven`, neutral owner 0,
with numeric ground in (500000,505000]. Unsupported contexts return nil world and
zero statistics; all caller bytes remain unchanged.

The source truncates admitted starting ground to a whole integer. Each round
spends one ground point and subtracts `INT(SINGLE(RND * 1000)) + 1` attackers.
The actual recovered RNG supplies damage 1–1000. The signed final force can be
negative and is retained separately from the capped zero surviving force.
Returned statistics contain starting/final ground, starting/raw/capped force,
draw count and modeled initial/final RNG states. Every successful result owns
its world storage and changes only the four ground bytes. Title, owner, sector
link, stocks, production rates and raw zero aliases remain untouched. Production
assault, capture/deletion and moving-group pointer writes are excluded.

## Existing captures and modeled receipts

The exporter instruments the existing ten-case occupied Python replay, recording
57 calculated encounter before/after worlds and RNG receipts: nineteen attacks
in each of three observed clock streams. The native-qualified scenario spends
25 ground points, from 505000 to 504975. Go tests also feed each preceding
calculated ground value into the next encounter while keeping other routing
prefix bytes independently modeled; this is not yet complete Go route chaining.

The complete Python run precedes all native target reads. Its independent audit
checks **180 complete six-file comparisons /1080 native files and 1872 RNG
witnesses**, plus the existing original native source packet. Encounter worlds
and RNG states are modeled intermediate oracles, not newly captured phase
endpoints. Native case before files, target outputs and captured RNG fields do
not enter synthesis. No native observations, hashes or acquisition source
attribution were changed; no new captures were acquired.

Thirty-six synthetic controls combine small/maximum moving forces, whole and
fractional starting ground, and explicit real LCG states. Inverse seeds select
zero, exact half and maximum 24-bit draws without injecting fake rolls. These
check minimum/maximum damage, signed overkill, fractional-ground truncation and
bounded repeated rounds; they are source/mathematical controls, not DOS runs.

Go tests match all complete modeled world hashes, force/ground receipts, draw
counts and final states. Additional checks cover exact ground-only write bounds,
unchanged caller bytes, owned output, canonical geometry, wrong title/padding,
owner/slot/force/ground/hazard refusals and retained numeric-zero aliases.
Exporter tests reject changed inputs/receipts/source identities, altered native
targets and poisoned independent RNG witnesses; they enforce synthesis-before-
target ordering and accept portable recompression by full decompressed bytes.

```sh
python3 scripts/export_neutral_ground_fixture.py --check
python3 scripts/test_export_neutral_ground_fixture.py
go test ./internal/qbmaint -run TestNeutralGround
```

Next integrate ordinary economy, foreign-defense and neutral-ground primitives
into bounded occupied-world routing/shared pursuit, skipped scans and moving
groups. Casualty news/scores, downstream tail and complete occupied-world six-file
Go qualification follow separately. Existing convergence/initial APIs and CLI
profiles, modern gameplay, save 35, releases and native Windows/live BBS
acceptance are unchanged.
