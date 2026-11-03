# Sysop guide: saves, backups, exports and restores

These procedures are for the Go reconstruction. Original DOS `.DAT` files cannot
be imported, and Go saves cannot be exported into the DOS format. There is no
in-game upload/import operation, account merge, or automatic archive importer.

## What to keep

All nodes for one game must use the same `-data` directory. `world.json` is the
complete persistent game: players and BBS identity mappings, ships, teams, planets,
ports, economy, private mail, public news and season history. `world.lock` provides
process coordination; it is not game content. Never delete or replace that lock
while any game or maintenance process is running. Temporary `.world-*` files are
not authoritative saves.

Keep a record of the exact game binary/commit, save schema, BBS `-system` identity
namespace, door launch configuration, file ownership and scheduler settings with
each backup. Drop files are supplied by the BBS for each caller; they are not a
substitute for a game backup. Login-local state such as pending confirmations and
spy visibility is not restored from a save.

Private archives and saves include identities, mail and team password hashes.
Store them outside public download/web directories. Restrict the backup directory
to the BBS operator. POSIX exports use mode 0600; configure Windows directory ACLs
separately. Examples below use POSIX commands and assume the game binary is
`./bin/yt`; Windows operators can use the same game flags with their own paths.

## Export a live snapshot

Create a private destination directory and choose a filename that does not exist:

```sh
mkdir -p /secure/backups/yankeetrader
chmod 700 /secure/backups/yankeetrader
./bin/yt -data /srv/yankeetrader/data -season-export /secure/backups/yankeetrader/season-1.json
```

Export takes the same world lock as normal saves, reads and validates the whole
world, and writes a consistent snapshot. It does not advance maintenance or change
the active save. Players may continue after export, so later actions will not be
in that snapshot. Existing files and symlinks are rejected; the destination parent
must exist. Retain the success receipt and World SHA-256 with the backup.

Format 1 is a JSON envelope containing `Format`, `Exported`, `WorldSHA256` and
`World`. The checksum covers the exact compact JSON bytes of `World`, not the
whole archive file. It detects accidental changes; it does not authenticate a
file from an untrusted source. Export contains the current full world and retained
season results, not full worlds already discarded by earlier Genesis resets.

## Take a stopped-door backup

1. Disable new door launches and scheduled maintenance. End every running game
   process on every node; disconnecting the visible caller alone is insufficient.
2. Copy the entire data directory to a new private backup location. Preserve the
   matching binary and launch configuration separately. Do not move the live data
   directory while processes may still hold its lock.
3. Validate the copied world with the matching binary using an export to a new
   file, as below. Then re-enable the original installation if it is staying live.

```sh
cp -pR /srv/yankeetrader/data /secure/backups/yankeetrader/data-before-upgrade
./bin/yt -data /secure/backups/yankeetrader/data-before-upgrade -season-export /secure/backups/yankeetrader/checked-before-upgrade.json
```

Use a new destination for each backup; copying into an existing directory can
accidentally nest files. A successful export confirms the copied save can be
loaded and validated. It does not exercise the target BBS transport or disk crash
recovery.

## Restore a raw Go save or move a game to another host

1. Stop all door and maintenance processes and block new launches on both hosts.
   Preserve a stopped backup of the destination before replacing anything.
2. Prepare a new private staging directory. Copy the backed-up `world.json` into
   it under that exact name. Do not copy a season-export envelope directly to
   `world.json`; extract its World payload using the next section.
3. Use the binary matching the backup to run `-season-export` against staging.
   A malformed, unsupported or invalid save must be resolved before installation.
4. With every node still stopped, install the validated staging `world.json` into
   the destination data directory. Preserve the destination lock file, correct
   ownership/permissions for the BBS service account, and point every node at the
   same data path. Do not merge JSON fields or individual accounts between worlds.
5. Restore the BBS identity namespace and launch configuration. Test one login
   before reopening callers and maintenance. Login can run daily maintenance;
   use export, rather than a test login, for read-only validation.

Example validation of an already prepared staging directory:

```sh
./bin/yt -data /secure/restore-staging -season-export /secure/backups/yankeetrader/restore-validation.json
```

Restoring discards all changes since the backup. It can reuse an earlier season
number and player/ship IDs. Every old process must exit before restore; season
guards cannot make an old process safe across rollback. On another host, retain
the same `-system` namespace and BBS user identifiers so existing accounts map to
the same players. Backups from untrusted sources must not be installed.

## Extract a season archive for restoration

Work in a new private staging directory, never directly in a running data
directory. The following Python 3 example checks the archive format and checksum
and exclusively creates `world.json`. Adjust the two paths first. It preserves
the exact payload bytes so JSON reformatting cannot alter the checksum check.

```python
import hashlib
import json
import os
from pathlib import Path

archive = Path('/secure/backups/yankeetrader/season-1.json')
staging = Path('/secure/restore-staging')  # must already exist and be private
text = archive.read_text(encoding='utf-8')
decoder = json.JSONDecoder()
index = text.index('{') + 1
fields = {}
payload = None
while True:
    index += len(text[index:]) - len(text[index:].lstrip())
    if text[index] == '}':
        break
    key, index = decoder.raw_decode(text, index)
    index += len(text[index:]) - len(text[index:].lstrip())
    if text[index] != ':' or key in fields:
        raise ValueError('Invalid or duplicate archive field')
    index += 1
    index += len(text[index:]) - len(text[index:].lstrip())
    start = index
    value, index = decoder.raw_decode(text, index)
    fields[key] = value
    if key == 'World':
        payload = text[start:index].encode('utf-8')
    index += len(text[index:]) - len(text[index:].lstrip())
    if text[index] == '}':
        break
    if text[index] != ',':
        raise ValueError('Invalid archive separator')
    index += 1
if text[index + 1:].strip():
    raise ValueError('Trailing archive data')
if fields.get('Format') != 1 or payload is None:
    raise ValueError('Unsupported archive format')
if hashlib.sha256(payload).hexdigest() != fields.get('WorldSHA256'):
    raise ValueError('Archive checksum mismatch')
fd = os.open(staging / 'world.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'wb') as output:
    output.write(payload + b'\n')
    output.flush()
    os.fsync(output.fileno())
print('Extracted; validate with the matching game binary before installing.')
```

This extraction checks the envelope and checksum. The subsequent game export
against staging checks the world schema and game invariants. Both steps must pass
before following the stopped-node installation procedure above.

## Administrative reset

Determine the current season from `SEASONS` or a validated snapshot's
`World.Season`. Schedule downtime and a stopped-door backup if callers must not
lose actions immediately before the reset. Then use the expected season number
and a new archive filename:

```sh
./bin/yt -data /srv/yankeetrader/data -admin-reset 1 -season-export /secure/backups/yankeetrader/season-1-reset.json -seed 77
```

This is destructive to current play: it clears current players, teams, assets and
messages. The old world is exported first; the new world keeps the sector count,
Genesis requirement, lottery quota and public season history. The public result
says administrative reset with no winner. Old logins must reconnect. The expected
number prevents a replay from resetting the next season. Seed defaults to 36.
History is bounded to 128 completed seasons; exporting does not clear the limit.

If a command fails after export, the archive may remain while the original world
is still active. Inspect the current season through another export to a new file
before retrying. A storage durability warning that says the update committed means
the new world is already visible: do not repeat the reset. Preserve both files,
check storage health, and validate the active world before reopening the door.

## RNG research and existing worlds

The QuickBASIC RNG research update keeps save format 34, current `-seed` semantics,
existing world contents and the selected generation profiles unchanged. Its raw
DOS seed inputs are research controls, not new game initialization/import flags.
The shared startup-price primitive produces the same prices. The exact port
replay adds no production flag, save converter or DOS import/export support.
The follow-up [complete initializer replay](../research/yt-initializer-replay/RECOVERY.md)
compares all original pre-maintenance records in bounded controls; it remains
research tooling and supplies no archive import or production initialization mode.
It deliberately reproduces a DOS duplicate-location defect only in the research
model; existing generation safeguards remain active. See the
[port replay boundaries](../research/yt-port-replay/RECOVERY.md) and the
[verified subset and remaining boundaries](../research/yt-rng-seeding/RECOVERY.md)
before treating a research clock or raw state as a production compatibility mode.

## Choosing the warp map

For a separate new world, `./bin/yt -data dos-map -init -dos-warps -seed 36`
selects recovered DOS local warps, wormholes, isolation repair and Earth shortcuts.
Add `-dos-ports` to select the recovered economy too; flags are independent and
initialization-only. Save 34 stores `WarpGeneration: "dos"`, preserved by Genesis,
administrative resets and full-world archive export/restoration. Existing saves
upgrade with their complete maps intact and no warp profile selected.

Maps use the modern seeded Go random stream. Generation keeps 8–3000 sectors,
removes the redundant Earth self-warp, rejects duplicate exits and bounds random
retries. Pathological generation that exhausts its safety limits fails before
publishing a world; it never replaces an existing save. This does not import or
export DOS `.DAT` saves or promise an exact original seed-to-map match. See
[warp rules, validation and limits](../research/yt-warp-generation/RECOVERY.md).

## Choosing the port economy

For a separate new world, `./bin/yt -data dos-economy -init -dos-ports -seed 36`
enables recovered DOS port names, production, coefficients and price references.
Omit the flag for the established uniform-port economy. The new profile is saved
as `PortGeneration: "dos"`; Genesis and administrative resets retain it. Neither
login nor maintenance accepts the flag, and upgrading an old save does not
regenerate its economy. Use a separate data directory to compare profiles.

Full-world exports, stopped raw backups and extracted archive restores retain the
profile with all port records. Restore the whole validated world using the
procedures above; do not copy individual port records or edit a profile to convert
an active economy. DOS `.DAT` import/export remains unsupported. See the
[recovered rules and deliberate differences](../research/yt-port-generation/RECOVERY.md).

## Upgrade and rollback

Current schema is 34. Supported schemas 1–33 upgrade in memory and are persisted
on the next successful write. Export loads/upgrades/validates without rewriting
the source; its snapshot uses the current schema. Retain a stopped raw backup
and matching old binary before upgrading, because an upgraded export cannot be
used by a binary that does not support its schema. Update all nodes together.

For a binary rollback, restore its matching stopped backup on every node; do not
simply install an older binary over newer saves. A reset or export is not a schema
downgrade. Full backup/restore and native Windows crash durability still require
acceptance on the actual BBS host; the automated tests use disposable worlds.
