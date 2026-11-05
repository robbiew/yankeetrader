# Host-side TIMER observation plan — static only

No emulator, debugger target, Frida session or process capture was launched by
this worker. No guest instructions, executable, configuration or repository files
were changed. Parent owns any subsequent runtime observation and cleanup.

## Identity and retained primary sources

Installed command `/opt/homebrew/bin/dosbox-staging` resolves to
`/opt/homebrew/Cellar/dosbox-staging/0.83.0/bin/dosbox`, arm64 Mach-O,
22,872,608 bytes, SHA256
`781d61c874271a315d672c597697cf0fb3aa0f6a727934bce4d2a9ad34057de5`.
Preferred Mach-O image base is `0x100000000`; __TEXT file offset is zero.
The Homebrew install receipt and static symbols/load commands are retained.

Official v0.83.0 tag resolves to upstream commit
`7b40053b7ac580843d0461eba8c36a47a990e66c`. The tag and immutable-commit contents
of the four decisive files agree byte-for-byte. `sources.json` records every
retrieved official versioned URL and SHA256. These are primary source records,
not a claim that the installed bottle was built bit-for-bit from an unpatched
upstream tree. Installed instruction/offset corroboration is separate below.

Canonical immutable source base:
https://raw.githubusercontent.com/dosbox-staging/dosbox-staging/7b40053b7ac580843d0461eba8c36a47a990e66c/

Key files:
- src/cpu/registers.h: CPU_Regs/GenReg32, segment structure and register aliases.
- src/hardware/memory.h: PhysPt/HostPt and direct physical-memory accesses.
- src/hardware/memory.cpp: MemBase initialization and GetMemBase implementation.
- src/dos/dos.cpp: DOS_21Handler, AH2c clock computation, overhead and installation.
- src/cpu/callback.cpp: CB_INT21 emitted stub and native callback layout.
- src/dosbox.cpp: host-time/frame catchup and optional automatic-cycle logic.

## Installed symbols and exact observer offsets

`installed-host.json` pins native bytes and symbol coordinates. All addresses in
this table are preferred/unslid addresses, not usable ASLR runtime pointers:

| Item | Preferred address | Runtime module-relative offset |
| --- | --- | --- |
| DOS_21Handler | 1000db990 | db990 |
| cpu_regs | 101396d60 | 1396d60 |
| Segs | 101396e78 | 1396e78 |
| MemBase pointer storage | 1023abb90 | 23abb90 |
| CPU_CycleMax | 100464ac4 | 464ac4 |
| CPU_CycleAutoAdjust | 101396ec0 | 1396ec0 |

The Mach-O symbol name for the handler is `__ZL13DOS_21Handlerv` (`nm` leading
Mach-O underscore included). Frida may enumerate the corresponding mangled name
without that extra underscore; resolve against the actual symbol list or use
these pinned module-relative addresses after verifying the exact host digest.
Use `Process.mainModule.base`; the real executable basename is `dosbox`, so a
lookup solely for a module called `dosbox-staging` can fail.

`DOS_21Handler-only-arm64.txt` contains the selected function. At db9c0..db9c8
it constructs cpu_regs address and loads AH at byte1. Native AH2c code at
dc4e4..dc5d4 loads CX/DX at offsets4/8 and finally writes DL8, DH9, CL4, CH5.
At dc748..dc754, compiled DOS_OVERHEAD increments guest IP at offset32 by2.
`GetMemBase-arm64.txt` independently shows a64bit load from MemBase's storage.

## Layout derived from official fixed-width types, corroborated by native use

CPU_Regs is40bytes: eight4-byte GenReg32 unions, a4-byte IP union and flags u32.
The next installed global cpu is exactly40bytes beyond cpu_regs. All reads are
little-endian on this installed arm64 host:

| Guest value | cpu_regs byte offset |
| --- | ---: |
| AX / AL / AH | 0 / 0 / 1 |
| CX / CL / CH | 4 / 4 / 5 |
| DX / DL / DH | 8 / 8 / 9 |
| BX | 12 |
| SP | 16 |
| BP | 20 |
| SI | 24 |
| DI | 28 |
| IP | 32 |
| FLAGS | 36 |

Segments contains val:uint16[8] at offset0, then phys:uint32[8] at offset16.
It is48bytes; the next installed CPU_Cycles symbol is48bytes beyond Segs.
Segment enum order is ES0,CS1,SS2,DS3,FS4,GS5. Thus DS value is Segs+6 and cached
DS physical base is Segs+28; SS value is+4/physical+24; CS value is+2/physical+20.

MemBase is a host pointer, so read its pointer value once; do not add guest offsets
to the address of the pointer variable. In this real-mode low conventional-memory
fixture the proposed read is:

    memory = readHostPointer(mainModuleBase + 0x23abb90)
    ds = readU16(mainModuleBase + 0x1396e78 + 6)
    portRaw = read4(memory + (ds << 4) + 0x7ad6)

Alternatively use cached Segs.phys[DS], after observing it equals ds<<4. This
simple formula is scoped to the low ordinary RAM used here, not protected-mode,
A20-wrapped, remapped EMS/MMIO or arbitrary paged guest addresses. No memory helper
needs to be called from an observer; all proposed accesses are bounded reads.

## DOS AH2c and guest attribution

At host DOS_21Handler entry select cpu_regs[AH]==2c. The function computes time
from BIOS ticks via INT1a, writes CH=hour,CL=minute,DH=second,DL=hundredths, and runs
its ordinary DOS overhead. Capture final CX/DX on the matching host onLeave;
retain a per-invocation/thread entry snapshot so internal callback execution does
not erase the original AH/DS/SS/SP context. Do not suppress or replace the actual
BIOS/DOS calls or alter guest return values. Function return Bitu is not the time.

The official CB_INT21 stub emits STI; four-byte native callback FE38<id>; IRET;
RETF. There is no extra guest PUSH before the C++ callback. DOS_21Handler writes
saved registers below SP but does not change SP for the AH2c path. The guest IP
register at this point addresses the DOS callback, not the original application's
TIMER call, and DOS_OVERHEAD changes it by2. Use the guest stack to attribute calls.

Existing pinned BRUN30 TIMER evidence is reused, not recaptured:
`research/yt-rng-seeding/runtime-rea.json`, read0x1c12f length133,
EvidenceID `ev_57bcde57ba704792310ee10df602be185e16a5358d60bbd3bb400ab7ca6695fc`.
Its bytes show:

    c12f PUSH AX; PUSH BX; PUSH CX; PUSH DX
    c133 MOV AH,2c
    c135 INT21
    c137 [compute TIMER from returned CH/CL/DH/DL]
    c167 POP DX;POP CX;POP BX;POP AX;RETF

No DS change occurs before this INT21. For the normal direct far-call path the
proposed host-entry guest SS:SP frame is:

| Stack offset | Expected content |
| --- | --- |
| 0 | DOS INT return IP c137 |
| 2 | runtime code segment |
| 4 | saved guest FLAGS |
| 6 / 8 / 10 / 12 | saved DX / CX / BX / AX |
| 14 / 16 | application far-return IP / code segment |

Validate the frame in actual runtime records before depending on it. In
particular first-use QuickBASIC software-INT dispatch could differ from its
normally patched far-call path. The eight guest bytes before the first return
IP should be50535152b42ccd21, authenticating this BRUN TIMER handler.
The application's port TIMER opcode is main0922 and returns to0927, so that
far-return IP can distinguish port calls from startup/helper TIMER calls. Verify
its code segment/module identity and observe DS:7ad6 as the port MBF index1..1000;
do not merely count all DOS time calls as ports.

## Bounded runtime plan for parent

1. Verify exact installed binary digest, fresh DOS fixture and normal200000cycle,
   isolated headless command recipe. Parent creates/owns the process/session.
2. Resolve globals and handler from that runtime module's ASLR base. Read-only
   sanity checks: pointer non-null, real-mode DS cache agrees, handler signature
   and guest stack/code identities agree.
3. Intercept the DOS handler entry/return pair. Save only bounded entry context;
   retain final DOS time bytes plus decoded/preserved raw port index for qualifying
   port calls. The expected complete selected sequence is exactly ports1..1000.
   Do not infer completeness from a successful process exit alone.
4. Use a strict event/runtime bound and retain dropped/truncated events, errors,
   first-use frame variation and cleanup outcome. No mutation, sleeps or network
   actions are needed in the observer script. Batch host logging where possible.
5. Compare the entire untouched-versus-observed DAT/ASC file sets and bytes under
   identical external inputs. Also compare source/runtime executable hashes and
   normal completion/return witnesses. Any mismatch is a neutrality failure for
   that recipe, not a reason to fit guest clock values or remove the mismatch.

## Important limitations

This is a hook plan, not a runtime observation or neutrality result. Frida changes
host in-process machine instructions while attaching an interceptor; absence of
guest instruction insertion does not mean absence of instrumentation effects.

Prefer the whole native function entry/return pair over an arbitrary interior
hook unless patch span and every incoming native branch are checked. The final
AH2c store is dc5d0 and its branch dc5d4 immediately precedes another jump-table
case atdc5d8; a16byte patch at the end could corrupt a neighboring case target.

Even fixed cycle settings do not establish host-pause neutrality. The official
increase_ticks reads host GetTicksUs, updates/caps frame catchup, then skips cycle
heuristics only when CPU_CycleAutoAdjust is false. A debugger/JS hook can delay
host execution. Paired strict output equality must establish any bounded claim.
Source/native agreement supplies offsets; actual frame validity, event coverage,
raw timestamps, process disposition and all-output neutrality remain unobserved.

Fresh host native records here are pinned nm/llvm-objdump/raw-byte observations,
not new REA Evidence IDs. Existing REA TIMER evidence is reused above. No native
analysis/debug session remains open.
