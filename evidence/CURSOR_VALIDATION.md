# Idle prompt clock cursor regression

The old clock callback saved/restored the input cursor with CSI `s`/`u`. On terminals that ignore those sequences, each refresh left the cursor after the inline clock. A real PTY reproduction using an emulator with CSI save/restore disabled failed with cursor **row 24, column 13**, rather than **row 24, column 38** after the main command prompt. This matches the reported symptom; it is not a claim that the user's terminal type was detected.

The callback now uses VT100 DECSC/DECRC (`ESC 7`/`ESC 8`) to preserve cursor position and attributes around the two clock writes. It samples the remaining time once for both fields and pads the inline field to its initial width, preventing old digits from remaining when the minutes count shrinks.

Validation:

- `python3 scripts/smoke_prompt_clock.py` launches the actual native game over a disposable 80×25 PTY. The screen emulator implements VT100 save/restore but intentionally ignores CSI `s`/`u`.
- The test waits for real one-second input timeouts. It verifies the cursor after idle main/computer prompts and after partial `LO`/`1` input, checks both clocks agree, completes `LOOK`, exits the computer and quits normally.
- The same test failed against the prior executable at the first idle tick, before the cursor fix.
- A Go unit test checks the VT100 save/restore boundaries, shared clock value and padding when the new time is shorter than the original field.
- CI includes the PTY regression. Other startup/port/planet/rename screen comparisons continue to use the same emulator with CSI support enabled by default.

No terminal queries, game rules, save format, compact workflow or ASCII behavior change. The regression models an ANSI compatibility limitation; it does not substitute for acceptance in every real terminal/BBS client.
