# Yankee Trader: Resurrection — sysop cheat sheet

Choose the package matching your host: Linux x86-64 (`linux-amd64`), Linux ARM64
(`linux-arm64`), or Windows x86-64 (`windows-amd64`). No Go compiler, DOSBox or
original DOS files are needed. Display assets are built into the executable.

## 1. Install and check

These examples are for a fresh installation. For an upgrade, follow step 6 first.

Extract the archive into its own directory. Keep game data outside versioned
release directories so upgrading the binary does not replace saves.

Linux:

```sh
tar -xzf yankeetrader-VERSION-linux-amd64.tar.gz
cd yankeetrader-VERSION-linux-amd64
./yt -version
mkdir -p /srv/yankeetrader /opt/yankeetrader
install -m 755 yt /opt/yankeetrader/yt
```

Windows PowerShell (replace VERSION with the downloaded version):

```powershell
Expand-Archive .\yankeetrader-VERSION-windows-amd64.zip -DestinationPath C:\Doors
Set-Location C:\Doors\yankeetrader-VERSION-windows-amd64
.\yt.exe -version
New-Item -ItemType Directory -Force C:\Doors\YankeeTrader | Out-Null
Copy-Item .\yt.exe C:\Doors\YankeeTrader\yt.exe
```

Verify downloads against `SHA256SUMS.txt`: Linux `sha256sum --ignore-missing -c SHA256SUMS.txt`
from the download directory; Windows `Get-FileHash .\PACKAGE.zip
-Algorithm SHA256` and compare the matching line. Run as the BBS service account,
with write access to the data directory. Keep saves and backups private.

## 2. Generate a world once

Linux:

```sh
./yt -data /srv/yankeetrader/data -init -seed 36 -dos-warps -dos-ports
```

Windows PowerShell:

```powershell
.\yt.exe -data C:\Doors\YankeeTrader\data -init -seed 36 -dos-warps -dos-ports
```

`-init` creates a new world and refuses to overwrite an existing one. The default
is 3,000 sectors/1,000 ports with Genesis enabled at 300 owned ports. Optional
`-genesis-ports 0` disables player-triggered Genesis; otherwise the supported
configured range is 20–300. A sysop administrative reset remains separate.

`-dos-warps` and `-dos-ports` select recovered map/economy rules with modern
safeguards; omit both for the established default generator. They are independent,
initialization-only choices. They do not enable exact DOS RNG replay. Do not add
these switches to ordinary play or maintenance commands. `-seed` makes generation
repeatable, not subsequent gameplay.

For the recovered QB stream, create a separate world instead:

```sh
./yt -data qb-world -init -generation-profile qb36-v1 -qb-state 0xc805 -qb-date 2027-01-01
```

Windows uses `yt.exe` with the same flags. Omit explicit `-seed`, `-dos-warps`
and `-dos-ports`. Geometry is fixed at 3,000 sectors/1,000 ports. State is raw
24-bit post-RANDOMIZE input (decimal or `0x` hexadecimal); date is required in
2026–2028, excluding January 10. Admission can reject unsafe original layouts
without writing a world or reseeding. Both Genesis and admin resets preserve the
saved recipe and repeat its source layout; current UTC dates and modern bootstrap
remain separate. Play and maintenance use only `-data` and their ordinary flags.
Backups/exports include the recipe. Save 35 requires a compatible binary; rollback
requires an older compatible backup. See [full QB procedures](SYSOP.md#playable-qb36-v1-worlds).

## 3. Test locally

```sh
./yt -data /srv/yankeetrader/data -local Sysop
```

```powershell
.\yt.exe -data C:\Doors\YankeeTrader\data -local Sysop
```

Use `-ascii` for plain text, or `-compact` for the compact command interface.
Local accounts have separate identities from BBS callers. Use `-help` for flags.

## 4. Launch from the BBS

Linux example:

```sh
/opt/yankeetrader/yt -data /srv/yankeetrader/data -drop /srv/bbs/node1 -system mybbs
```

Windows BBS command example (absolute executable path):

```text
C:\Doors\YankeeTrader\yt.exe -data C:\Doors\YankeeTrader\data -drop C:\BBS\NODE1 -system mybbs
```

Point `-drop` to the caller's node directory containing `DOOR32.SYS`; substitute
the BBS's node-directory variable for each caller. All nodes share the same
absolute `-data` directory and stable `-system` value. Changing `-system` changes
caller identity mapping. The Windows launch example assumes you place `yt.exe`
at that stable path when upgrading.

Configure Door32 transport in your BBS: Linux uses the caller's standard I/O;
Windows requires the supported inherited Door32 socket. The drop file alone does
not connect a caller. Caller minutes come from the drop file. Live BBS and native
Windows inherited-socket/durability acceptance remain host-specific checks.

## 5. Run daily maintenance

```sh
/opt/yankeetrader/yt -data /srv/yankeetrader/data -maint
```

```powershell
C:\Doors\YankeeTrader\yt.exe -data C:\Doors\YankeeTrader\data -maint
```

Run once daily as the same service account. Login also advances maintenance.
The game uses **UTC dates**; repeating maintenance on the same UTC day does not
repeat production/turn phases. Player turns reset to 500 on a new UTC day;
missed days do not accumulate extra turns. Do not initialize again to maintain.

Example Linux crontab, using absolute paths and a private writable log location:

```cron
5 0 * * * /opt/yankeetrader/yt -data /srv/yankeetrader/data -maint >> /srv/yankeetrader/maintenance.log 2>&1
```

Cron uses the host's scheduler timezone: arrange the job after UTC midnight, or
configure an equivalent daily schedule in your host's timezone. On Windows,
create a daily Task Scheduler task under the BBS account: program
`C:\Doors\YankeeTrader\yt.exe`, arguments
`-data C:\Doors\YankeeTrader\data -maint`. Set its time after UTC midnight in
the scheduler's timezone and record failures. Internal locking coordinates game,
maintenance and export processes; keep one scheduled task for the game.

## 6. Export, back up and upgrade

Create a private backup directory first; each archive filename must be new:

```sh
mkdir -p /secure/backups/yankeetrader
chmod 700 /secure/backups/yankeetrader
/opt/yankeetrader/yt -data /srv/yankeetrader/data -season-export /secure/backups/yankeetrader/season-1.json
```

```powershell
New-Item -ItemType Directory -Force C:\PrivateBackups\YankeeTrader | Out-Null
C:\Doors\YankeeTrader\yt.exe -data C:\Doors\YankeeTrader\data -season-export C:\PrivateBackups\YankeeTrader\season-1.json
```

Set Windows ACLs to restrict that directory to the operator/service account.
Archives include private player identities, mail and password hashes. Never put
them in a public download directory. Export makes a locked, validated snapshot;
it does not delete or reset the active world. Keep its checksum receipt.

For a raw backup/upgrade: disable new launches and maintenance, stop every node's
game process, copy the **entire data directory**, and retain the matching binary
and launch settings. Replace binaries only after backup; use one compatible
version on all nodes. Keep `-data` and `-system` unchanged. Never delete a live
`world.lock`. Older binaries may not read newer save schemas; use a compatible
backup for rollback. Follow the bundled **SYSOP.md** for checksum-checked archive
extraction, stopped-node restoration, staging validation and rollback. There is
no automatic archive importer or supported original DOS `.DAT` import/export.

## 7. Administrative reset — ends current play

Determine the exact current season using in-game `SEASONS` or a validated export's
`World.Season`. Back up first. Replace `1` below with that exact positive number
and use a new archive filename:

```sh
/opt/yankeetrader/yt -data /srv/yankeetrader/data -admin-reset 1 -season-export /secure/backups/yankeetrader/season-1-reset.json -seed 77
```

```powershell
C:\Doors\YankeeTrader\yt.exe -data C:\Doors\YankeeTrader\data -admin-reset 1 -season-export C:\PrivateBackups\YankeeTrader\season-1-reset.json -seed 77
```

This archives first, ends the season with **no player winner**, clears current
players/assets/mail, preserves settings/history and invalidates old logins.
Stale/replayed expected seasons are rejected. It is not routine maintenance.
An error may leave an archive without resetting. A warning saying **Update
committed** means the new world is already visible: inspect it before any retry;
do not repeat a completed reset. See SYSOP.md for recovery details.
