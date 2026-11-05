# Date / text-clock matrix: independent static findings and limits

Read-only work. No DOSBox/runtime launch, repository edit, git action or original
archive modification by this worker. Parent owns acquisition and model changes.

## Evidence and exact source bindings

New focused REA/Ghidra12.1.4 reads in rea.json:
-BRUN30.EXE0x1c06b length196, ev_3bb96617b6515db3d7fe6e07c98dd83a004a19704c24c61838d7a20ebb4eb5c1
 (DATE$ plusTIME$ implementation, throughc12fexclusive).
-YTMAINT.EXE0x179e3 length805, ev_99582769e125e137cbb52e7880aa75f843f8575dddcc893a165db38d20754506
 (complete calendar helper, through7d08exclusive).
Both reads independently match all in-range relocated original MZ bytes.
Original hashes:
BRUN30 3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8
YTMAINT 8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6

Existing scoreboard observation0x18534 length1202 includes itsDATE$/TIME$ calls:
ev_784fb33fc1253b419634f88b11a7791bcc91eac95e3137c94953a3330442d4b0.
Existing runtime TIMER0x1c12f length133:
ev_57bcde57ba704792310ee10df602be185e16a5358d60bbd3bb400ab7ca6695fc.
Existing main port-loop0x107bf length1928:
ev_cf13e47dc2ef79bc24eb65c68bb2f6a56df735e83d4b3ba9b90c6187f46a141b.
Historical runtime-aware archive/analysis/yt-maint/qb-annotated.txt supplies
call-site context, cross-checked against literal dispatch bytes in the original.
Retained original officialDOSBox0.83 src--dos--dos.cpp in clock-neutral-host
explains DOSAH2a/AH2c/AH2d behavior. Static interpretation is not a runtime result.

## TIME$ rounds: it is not TIMER formatting or simple truncation

BRUNTIME$ startsmodulec0e3, callsDOSAH2c atc0f5, returnsfromDOS atc0f7.
Its c0f7..c10e code compares DL with50; ifhundredths>=50 it increments seconds.
It carries60seconds to0/minutes+1, and60minutes to0/hours+1.
There is NOhour24->0 wrap before c111..c127 printsHH:MM:SS.
Therefore23:59:59.50 can produce text24:00:00 while the separately sampled DOS
calendar still reports the preceding date. This is a native branch observation;
this worker has not claimed that the selected acquisition has reached it.

text_clock_contract.py models only that integer register/string behavior:
00:00:59.49->00:00:59; .50->00:01:00;
23:59:59.49->23:59:59; .50->24:00:00.
Four static examples pass. This formatting must not use datetime.time for24:00:00
or increment an unrelatedDATE$ sample to cosmetically reconcile the text.

TIMER is separate: entryc12f, DOSreturnc137, fractionalseconds fromDOSCX/DX;
port then divides by60. It does not useTIME$'s roundedsecond. Both returnCX/DX
must be captured immediatelyafterDOS, before original runtime restores registers.

## DATE$ native path

DATE$ startsc06b and makesDOSAH2a atc07d, returningatc07f. DOS supplies
CX=fullcalendar year,DH=month,DL=day,AL=weekday. Native formatting printsMM-DD-
YYYY; the selected2026..2028 domain is straightforward. No claim about allfuture
centuries or arbitrary out-of-range DOS years is made here.

BothDATE$ andTIME$ pushAX,CX,DX,SI plus two temporary words beforeDOSINT21.
At the DOS callback frame their inner application farreturnIP/CS are expected
words9/10, unlikeTIMER's words7/8; confirm actual stacks in new observed corpus.
DATE$ signature begins8926080a50515256;TIME$ has the same prefix but another
entry/return address, so classify byAH2a/2c + runtime returnc07f/c0f7 and matching
original far-call target, not the common prefix alone.

To identify which calendar-helper invocation producedDATE$, capture guestBP and
readSS:BP+2/+4 for helper's callerIP/CS, +6/+8 for year/day argument pointers.
Existing helper probes establish BP+2 caller attribution; do not guess a deeper
SP-relative frame beyond DATE$'s inner79edreturn. Bind framebytes to source and
check context preservation before accepting those fields.

## Complete literal writer inventory (bounded direct-encoding search)

DATE$ dispatchCD3d239090 occurs atmain04a8,06a8,79e8,85f4.
TIME$ dispatchCD3d249090 occurs at0497,068f,860d.
TIMER dispatchCD3d439090 occurs at0078,0922,1256,2186,78f8,793e.
These are complete searches of the original main image's literal encodings, not
proof against indirect/computed calls. Source paths are:

-Newsheader:0497TIME$ (return049c), THEN04a8DATE$ (return04ad), concatenate
  ': Maintenance Program Ran '+revision before57d1 appends it.
-Active player's cloak-expiry private notice:068fTIME$ (return0694), THEN06a8DATE$
  (return06ad). This branch is absent from the all-inactive input fixture.
-Scoreboard header:85f4DATE$ (return85f9), THEN860dTIME$ (return8612).
-Calendar helper79e3:79e8DATE$ (return79ed), parses the date into game day values.

All literal far-call sites to79e3 and their outerreturnIP:
0335->033a initial cached calendar;
0839->083e each ordinary port update (1000 in this fixture);
1046->104b active planet update (none when all planet slots inactive);
1daa->1daf missingWanderer creation;
20f7->20fc missingXannoron creation;
41ce->41d3 missingMercenaryBase creation;
5780->5785 final configuration watermark.
For the prior bootstrap this predicts1005helperDATE$ calls, plus directnews and
scoreboardDATE$=1007program calls, before shell/otherDOS calls are counted. Treat
that as a source-backed inventory expectation, not a new measured count.

## Calendar/base-year behavior and remaining ambiguity

Calendarhelper receives stored configuration year pointer1850 and day result1858
as by-reference parameters. It parses year2digits into7d5c andmonth into7d60,
applies explicit month-offset constants and a year*.25 integer/leap check.
The baseyear is not interchangeable with the observed calendar's year.
7c36..7c52 adds100 to parsedyear when needed for two-digit wrap.7c57 onward
contains a year-difference branch adding365 and leap adjustments.

A SAME2026beforeworld run onJan1,2027 is therefore different from a freshly
initialized2027world: the former retains baseyear26 and enters the year-difference
branch; the latter usesbase27 and doesnot. Jan1/base26 outputday366 is the bounded
one-year interpretation to check against raw observed output. Do NOTsilently
replace the oldbeforeworld with a fresh2027initializer solely to avoid this path.

IMPORTANT2+year uncertainty:7cd1..7cde has an additionalbase/currentyearcomparison
and early7d00exit within the apparentyearloop. Exact multi-year accumulation is
not established by this static worker. Earlier suggested790/791 forFeb29/Mar1,2028
withbase26 was only a mathematical hypothesis and MUSTNOTbe treated as recovered
behavior. Capture the calendar phases/final watermark and retain any mismatch.
Fresh2028base28 and old2026base26 are separate controls. GeneralGregorian century
parity is outside this slice; original helper visibly uses a quarter-year test.

## Host clock/date behavior relevant to safe acquisition

RetainedDOSBoxdos.cppAH2a andAH2c both invokeBIOSINT1a and applyDOS_AddDays when
BIOS reports midnight. AH2c alone has its timing-overhead operation; do not copy
its IP+2/cycles-5 assertion unchanged toAH2a without observing that branch.

AH2d validates requestedhundredths but writesBIOSticks usingHH/MM/SS only; its
seconds expression discardsDL. Thus requesting23:59:59.75 neednot establish a
fractional start. The baseline maintenance body uses about.49emulatedseconds;
a whole-second23:59:59request may notcrossactualmidnight. Report observed date
transitions and roundedTIME$text transitions separately; noCPU tuning or hidden
guesttime writes should force a desired result.

## Minimal staged matrix suggestion, not a claim of successful replay

First collect paired unobserved+observed runs atsamebefore/dateNov2,2026:
1.00:00:02: positive smallTIMER and explicit startupseed change.
2.12:34:56: largeTIMER, nonzero integerXannorontime89 and two-stage division.
3.00:00:59: near-minuteTIME$ rounding/carry; claim a transition only if measured.
Then:
4.Dec31,2026/23:59:59 withsamebase26before: distinguish text24carry from actual
 day rollover; this run may legitimately fail to cross midnight.
5.Jan1,2027/00:00:00 withsamebase26before: year-difference/calendar branch.
6.Feb29 andMar1,2028, each explicitbeforeidentity/baseyear: leap cutoff and
 multi-year behavior, with unsupported branches retained as findings rather than
 automatically fitted. A freshbase28control is a separate useful diagnostic.

Do not require every newclock to match old1062TIMER inventory. The one-shot
lottery at537e may pass.5 then call53afhelper1 toselect an unnamed player and
abort: still no award, but H1callcount becomes42. Rare fallback/candidate retries
or zero-bound allocation defects can add/change paths. Admit only source-backed
branches, classify incomplete/unsupported runs and retain evidence. Never select
only seeds yielding the old41/19profile and describe that as generalclockparity.

## Pure-model input implications

Do not use one globaldate/clock for a run that can cross boundaries. Ports sample
calendar at0839 for each record and TIMER at0922;Wandererdate-10, Xannorondate,
MercenaryBasedate-10 and finalwatermark each resamplecalendar. News samplesTIME$
BEFOREdate; scoreboardDATE BEFORETIME$. Capture/derive each writer's inputs.

The priorNPCmodel'sxannoronminutes<1/exponentclear rule is narrow. Atmidday,
native2196INT must store an encodedpositive wholeminute, not a zero-residue
special case. Do not infer exact fractional rounding or generalMBF from that.
Startup RANDOMIZE -TIMER is beforeDATElogic and has no dateoperand; positivehelper
reseeds likewise useTIMERrawFAC+oldstate lowbyte. Calendar branches can change
execution time before later reseeds, so date can still indirectly change phase
TIMERinputs and draws. Capture them rather than deriving all seeds from oneclock.

## Nested BIOS callback cycle accounting (source-backed follow-up)

The additional original-release source `src--ints--bios.cpp` is pinned by `bios-source.json` to official DOSBox Staging commit `7b40053b7ac580843d0461eba8c36a47a990e66c`. This is static source acquisition, not a runtime emulator query. Existing retained sources are under repository `research/yt-maint/clock-neutral-host/`.

- `bios.cpp:1325–1327` installs INT 1a as `CB_IRET_STI`; lines 325–336 implement AH=00 by reading BIOS_TIMER and BIOS_24_HOURS_FLAG, clearing the latter, and returning tick words CX/DX.
- `callback.cpp:249–255` emits STI, a native FE38 callback, and IRET for that callback type. Lines 676–684 emit the RunRealInt trampoline INT instruction followed by the native stop callback. The ordinary nested path therefore dispatches five guest instructions: INT1a, STI, BIOS native callback, IRET, stop native callback. This is the ordinary path, excluding any newly serviced interrupt or event side effects.
- `callback.cpp:106–114` enters `DOSBOX_RunMachine()` for this trampoline; `dosbox.cpp` normal_loop dispatches PIC_RunQueue then the current CPU decoder and native callback handler.
- `pic.cpp:530–575` folds CPU_Cycles into CPU_CycleLeft and reallocates a slice, preserving their sum except actual execution/events. CPU_Cycles alone can increase at this boundary even with unchanged PIC tick. `pic.h:27–32` defines the within-tick progress index as CycleMax - CycleLeft - Cycles.
- `core_normal.cpp:135` tests `while (CPU_Cycles-->0)`. An exhausted slice incurs one failed condition evaluation that changes 0 to -1; the next PIC_RunQueue folds that -1 into the remaining budget. This source detail accounts for one extra decrement if the five-dispatch nested path exhausts its initial slice. It is not a sixth executed guest instruction.
- `pic.cpp:607–611` starts a new millisecond by setting CycleLeft=CycleMax, Cycles=0, and incrementing PIC_Ticks. Thus for fixed CycleMax/auto-adjust off, normalized accounting can compare delta(Cycles+CycleLeft) - delta(PIC_Ticks)*CycleMax. The reported pilots show -5 ordinarily, -6 only when the initial Cycles budget is 0..4. This is consistent with the five-dispatch path plus one exhausted-loop sentinel, including when one millisecond boundary is crossed. The retained pilot host-time.json.gz files were independently read here (no emulator recapture): rollover has 2050 normalized -5 / 26 normalized -6 events, and near-midnight-100k has 2072 / 3; every -6 starts with Cycles in 0..4. The exact initial-zero scheduling depends on event queue timing: the threshold is a measured profile property, not a universal predicate based only on entry Cycles.
- `dos.cpp:437–439` overhead() only adds 2 to reg_ip. AH2c calls it; AH2a does not. It must not be described as an explicit five-cycle decrement.

Boundaries: conservation claims apply to the observed fixed-cycle normal interpreter recipe. Auto-adjust changes, another interrupt/event that executes guest code, or a different decoder require separate accounting. The BIOS rollover flag is consumed by AH00 and DOS_AddDays must therefore be observed in chronological order.
