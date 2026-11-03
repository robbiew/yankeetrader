# Release packages

The release workflow builds these standalone targets with `CGO_ENABLED=0`:

| Host | Archive | Executable |
| --- | --- | --- |
| Linux x86-64 | `yankeetrader-VERSION-linux-amd64.tar.gz` | `yt` |
| Linux ARM64 | `yankeetrader-VERSION-linux-arm64.tar.gz` | `yt` |
| Windows x86-64 | `yankeetrader-VERSION-windows-amd64.zip` | `yt.exe` |

Each archive has one versioned top directory with the binary, package README,
SYSOP_CHEAT_SHEET.md, SYSOP.md, CREDITS.txt, third-party license texts and
RELEASE_INFO.json. The full sysop guide's research links point to the matching
release tag. Display assets are embedded; no save, account, source archive or
original DOS binary is bundled. `SHA256SUMS.txt` hashes the downloaded archives;
each manifest also records its executable hash, source commit, dirty-tree flag,
Go version, save schema and dependency versions/GoDoors commit.

## Local build

Use Go 1.23 or newer and Python 3. The sibling `../godoors` checkout is required
by go.mod; use the same revision pinned in CI/release.yml for official packages:
`9364a49ddd7c396ccbfcdd3c240c104ea9178551`. Existing local Go module overrides may
be supplied through `GOFLAGS`; manifests retain the actual GoDoors revision.
A local dirty-tree build is a candidate, not an official tagged release.

```sh
python3 -m unittest discover -s scripts -p test_build_release.py
python3 scripts/build_release.py --version 0.1.0 --out dist
python3 scripts/verify_release_packages.py dist
```

Choose the intended version; do not include the `v` prefix in `--version`.
The builder sets the centralized `internal/version.Version` with Go linker flags;
it does not edit the source version or save schema. `--target linux-amd64` can
build a single target for development, but the full release verifier requires
all three. Output archives/checksums must not already exist: use a fresh output
directory for a new attempt after a failed or partial local build.

Archive headers, ordering and permissions are normalized. Packaging the same
binary/metadata twice produces identical bytes; different source state, toolchain
or dependencies may produce different packages. This is not a cross-toolchain
bit-reproducibility promise. Build prerequisites are not runtime dependencies.

## GitHub draft release

1. Merge the intended changes and require the full current-head CI to pass.
   Review the README/sysop instructions and save/rollback notes. Choose an unused
   semantic version and update the centralized source version as appropriate.
2. Create and push a matching `vX.Y.Z` tag on that exact verified commit. Tag
   creation/publication is an operator action; adding this tooling does not tag
   or publish the current checkout automatically.
3. The tag workflow checks out the fixed GoDoors revision, runs race tests/vet
   and packaging tests, cross-builds the three targets, verifies archives and
   exercises the packaged Linux amd64 CLI on the Linux runner.
4. It creates a **draft** GitHub Release, attaches all archives and checksums,
   and leaves publication to the maintainer. Reruns may replace assets on the
   same draft; the workflow refuses to overwrite a published release.
5. Review the draft, amend milestone-specific notes, download/verify checksums,
   and perform target-host door checks before publishing. Windows packages are
   cross-built/format-checked; native Windows inherited-socket and crash durability
   acceptance are not established by cross-compilation. Linux ARM64 is likewise
   cross-built/format-checked, not executed on the x86-64 runner.

Normal pull-request CI also builds/verifies the packages with a `0.0.0-ci` version,
including initialization, existing-world overwrite refusal, maintenance, private
export and guarded reset. No GitHub Release is created by a PR build. Release builds use the same
pinned checkout/setup actions and GoDoors revision as CI. Do not upload private
season archives or raw game data as release assets.

For installation and operations see [the sysop cheat sheet](SYSOP_CHEAT_SHEET.md)
and [full save/restore guide](SYSOP.md). Packages do not change save format 34,
existing generation flags, account identity or maintenance/reset behavior.
