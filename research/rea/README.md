# REA research tool

REA is an optional analysis tool for the original Yankee Trader DOS binaries.
It is not a dependency of the Go game. The wrapper pins REA 6.8.0 and defaults
to a separate Ghidra 12.1.4 installation at
`~/.local/share/rea/ghidra_12.1.4_PUBLIC`. Set `GHIDRA_INSTALL_DIR` and `JAVA_HOME`
to use another supported installation. REA 6.8.0 requires Ghidra 12.1.x and
a compatible full JDK; the existing Homebrew Ghidra 12.2 is kept separately.

From the repository root:

```sh
sh scripts/rea.sh doctor --provider ghidra --json
sh scripts/rea.sh inspect archive/dos-original/YT-INIT.EXE --provider ghidra --json
sh scripts/rea.sh inspect-native-load-image archive/dos-original/YT-INIT.EXE --provider ghidra --json
```

Use absolute target paths if invoking outside the repository root. The first
wrapper invocation may download the pinned npm package. Node.js and npm must
be installed; consult REA's installation guide for supported Node versions.

## Investigation rules

- Keep original EXEs unchanged. REA imports private snapshots; it does not
  reuse or update the archived `YankeeTrader.gpr` project.
- Start from one concrete question and a known string, routine, or file offset.
  Retain the executable SHA-256, REA/Ghidra versions, evidence IDs, address
  conventions, and limitations with each finding.
- REA's DOS load segment is `0x1000`. Its linear analysis addresses are not
  file offsets and may differ from addresses in older research listings.
- QuickBASIC runtime interrupts need runtime-aware interpretation. Treat
  pseudocode as a lead, and corroborate recovered rules with the annotated
  listings and isolated DOSBox before/after experiments.
- A verified loaded image establishes static import integrity, not gameplay
  parity or observed DOS runtime behavior.
- MCP annotations are temporary and are discarded when the binary session
  closes. Export evidence and record useful conclusions before closing.

Codex's REA registration is user-wide. Restart Codex after setup to discover
its tools; the CLI wrapper can be used immediately.

## Local setup and smoke check (2026-10-25)

- REA 6.8.0 setup reported `ready`; scoped Codex/Ghidra readiness passed.
- Ghidra 12.1.4 came from the official `Ghidra_12.1.4_build` release.
  Archive SHA-256: `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db`.
- The official archive lacked a macOS native decompiler. Its bundled
  `Ghidra/Features/Decompiler/src/decompile/cpp` sources were built with
  `make -j4 ghidra_opt ARCH_TYPE= OSDIR=mac_arm_64`; the resulting `ghidra_opt`
  was installed as `Ghidra/Features/Decompiler/os/mac_arm_64/decompile`.
- [Overview evidence](yt-init-overview.json) identified DOS MZ, 16-bit real mode,
  nine memory blocks, 18 defined procedures and 91 defined strings. These
  counts do not establish complete QuickBASIC code or string discovery.
- [Load-image evidence](yt-init-load-image.json) returned `verified`, with
  entry address `0x10030`, a 512-byte header, a 19,873-byte initialized module
  and no appended overlay. Relocation changes belong to the imported image.
- The original `YT-INIT.EXE` SHA-256 remained
  `601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2`.
- [Entry-routine evidence](yt-init-entry.json), produced with `function` at
  `0x10030`, includes assembly and pseudocode, confirming the native decompiler
  runs. It also reports overlapping instructions, an abnormal stack frame,
  and unresolved QuickBASIC interrupt calls. Its recovered control flow is
  not accepted as a gameplay rule or a faithful source reconstruction.

Upstream: [REA](https://github.com/morluto/rea),
[DOS analysis](https://github.com/morluto/rea/blob/main/docs/ghidra-dos.md),
[installation](https://github.com/morluto/rea/blob/main/docs/installation.md).
