# Initial-fixture port writer and independent clock boundary

Original YTMAINT.EXE SHA256
8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6.
Fresh REA/Ghidra12.1.4 read_bytes0x107bf length1928 independently equals relocated
original source. EvidenceID ev_cf13e47dc2ef79bc24eb65c68bb2f6a56df735e83d4b3ba9b90c6187f46a141b.
The retained range covers the port loop through its termination predicate.

## Source-backed bounded model

The port loop index7ad6 runs1..1000. Native recordseek computes3051+index; it is
not a3052..4051 record-index variable. This matters for any conditional probe.
Main07bf..0f47 performs the ordinary writer. It reads stocks into double array
7afa, production into single array7b04, and coefficients into7b0e after negative
ABS. At0922 TIMER,0927 divisor60,092c division,0934 store yields the port's
TIMER/60 single at7b1c. Site0934 is exactlycd3f7d9090, five complete bytes.

Elapsed day is day-lastday+(nowminutes-lastminutes)/1440; negative or>10 becomes10.
The admitted clean initial fixture has lastday=day-10, zero stocks/treasury/owner/
lastminutes, bounded positive integer production1000..32766 and absolute integer
coefficients1..100. Therefore elapsed is exactly10 or capped10, and stocks become
10*each rate exactly. No initial production-sum plague threshold is reached.

The max-stock scan0de7..0e7f starts from zero and updates on strict greater-than.
It picks the first maximal stock index1..3, writes class4-index, then negates that
selected coefficient after the initial negative-ABS pass. The selected cargo's
coefficient becomes positive; all others remain negative. Production rates and
all unrelated record bytes remain from the input record. Day45 becomes current
day; time101 is the raw observed TIMER/60 FAC. Copying raw zero preserves its
noncanonical mantissa. The initialzero treasury has no tax debit.

scripts/replay_maintenance_ports.py implements only this admitted initial slice.
Its replay_ports(before,day,timer_minutes) returns137000portbytes+statistics;
inputtimer_minutes is1000independentrawfour-byte observations, never an after-file.
The synthesizer never opens an observed target or copies any target patch table.
The separate timer_epochs helper expands measured1-based epoch starts.

## Clock evidence and remaining mismatch

Default capture script scripts/recover_maintenance_port_clock.py runs an untouched
control, one full main-body-end0934counter and an independently selected binary
search of nth port TIMER/60 FAC observations.17controls are retained in
/private/tmp/yt-maint-port-clock (search.json documents the search).

Probes find ports1..605 raw00004800 and606..1000 raw0e745a76. These are numeric0
with important residual bytes, and0.0008333333535119891minutes respectively.
Using this independently measured schedule, the pure model matches all137000
portbytes of the instrumented counter run, including classes346/336/318, all
production stocks and coefficient signs.

The counter instrumentation is not clock-neutral: versus its own untouched
control the complete world differs only in port606 offset101..104, exactly4bytes.
The untouched run keeps zero through port606 and changes at607. Against that
untouched target, model agreement is136996/137000portbytes. The offset is not
corrected using the target; no per-target table or CPU tuning hides the gap.

Two separately classified diagnostics retain the same one-port timing shift:
- /private/tmp/yt-maint-port-clock-fast replacesPUSHF/POPF withNOP (flags not
  preserved, diagnostic only, not evidence of general neutrality).
- /private/tmp/yt-maint-port-clock-readonly instead uses one386DWORD compare of
  current port MBF index, flags preserved, no per-visit counter writes. Its46-byte
  same-size guard writes immutableCSheader626d5954 at normal body end. Complete
  miss and selected605/606/607 samples still show the same4-byte difference.

The read-only variant needs a386-capable research emulator; it changes no
production executable/runtime. Emulator settings remain200000cycles; no settings
were adjusted to fit target bytes. Both diagnostic recipes are explicitly
labeled separately and are not default capture controls.

Conclusion: economic/class/stock/sign writer is byte-exact for the admitted
fixture given rawclockinputs; the independent-probe-to-untouched time alignment
still has one-port/four-byte uncertainty. Do not claim exact untouched port
replay using the probe schedule. General production, plague/damage, nonempty
stocks/treasuries, arbitrary inputs and general MBF arithmetic remain outside
this model. No original archive or productionGo files changed.
