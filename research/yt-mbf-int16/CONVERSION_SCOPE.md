# BRUN30 integer conversion scope correction

The previous plan proposed SINGLE-to-signed32 followed by DOUBLE-to-signed32
language conversion. That recommendation assumed a LONG type which the target
language version does not provide. It is withdrawn, not an unimplemented native
parity milestone.

Microsoft's **Q43308, “Differences among QuickBASIC Versions 2.00, 3.00, 4.00,
4.50”**, last modified 18 October 1989, lists long (32-bit) integers as absent
from versions 2.00 and 3.00 and available in 4.00 and 4.50:
[archived Microsoft article](https://msarchive.pcjs.org/kb/Q43308/).
This is historical Microsoft documentation served by an independent archive;
it is not a claim that the archive is the original publisher.

The retained BRUN30 dispatch and kernel observations authenticate the already
qualified signed16 paths, including their mode byte. They do not authenticate
an additional signed32 language conversion. Likewise, a four-byte floating-point
value is not a signed32 integer, and internal multiword arithmetic or a DOS
32-bit file offset does not establish native LONG type support. No exhaustive
absence claim about all internal 32-bit runtime operations is made here.

The next identified conversion slice was the original kernel's explicit mode-4
branch (DS byte `001f` equals 4), separately from the measured default mode 0.
Qualify it with declared mode-setting diagnostic interventions and full native
outcomes before naming or implementing its behavior. Do not infer normal
callers, change gameplay selection, or reuse default-mode results as mode-4
execution evidence. Other MBF arithmetic follows source/call-site audits.

This planning-only correction updates README, current priorities and affected
recovery reports. Original/native captures, fingerprints, Go APIs, gameplay,
save compatibility and sysop procedures are unchanged.


The [mode-4 supplement](../yt-mbf-int16-mode4/RECOVERY.md) now qualifies that
explicit diagnostic intervention for both precisions and entries. Normal callers
remain unestablished; other arithmetic and call-site integration need their own
source evidence. Do not relist mode-4 numeric behavior as unmeasured.
