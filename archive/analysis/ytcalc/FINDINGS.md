# Yankee Trader player calculator: evidence assessment

Source: `/Users/robbie/Downloads/ytcalc.xls`. Original workbook unchanged. The file's metadata titles it "Yankee Trader Calculator v1.0" and lists Zharous as author. It contains one worksheet, `Data`. Read-only extraction used the standard Excel default password for its legacy protection, without executing macros. `extracted.json` retains the source hash, cell values, and decoded BIFF formulas.

## Value to the reconstruction

The workbook is a useful independent player-created model, especially for combat. Its formulas are candidate rules to test against the particular supplied DOS 3.6 release. They must not supersede directly verified executable behavior.

### New combat leads

| Cells | Spreadsheet calculation | Status |
|---|---|---|
| F7 | Plasma fighter damage = bolts squared * 50,000 | Candidate, not DOS validated |
| H7 | Plasma shield damage = bolts squared * 25,000 | Candidate, not DOS validated |
| I7 | Plasma mine damage = bolts squared * 250 | Candidate, not DOS validated |
| J7 | Plasma ground-force damage = bolts squared * 1,000 | Candidate, not DOS validated |
| K7:L7 | Plasma production damage range = bolts squared * 1,000 .. 3,000 | Candidate, not DOS validated |
| F9:G9 | Missile fighter damage range = missiles * 2,450 .. 2,550 | Candidate, not DOS validated |
| H9 | Missile shield damage = missiles * 1,150 | Candidate, not DOS validated |
| I9 | Missile mine damage = missiles | Candidate, not DOS validated |
| J9 | Missile ground-force damage = missiles * 12.5 | Candidate, not DOS validated |
| K9:L9 | Missile production damage range = missiles * 1,000 .. 3,000 | Candidate, not DOS validated |
| F13 | Xannor maximum planet attack in ground-force units = ROUNDUP(Xannor score / 50,000) | Candidate, not DOS validated |
| J13 | Mercenary bribe cost = ROUNDUP(fighters * 2.5) | Candidate, not DOS validated |
| G16:I16 | Ratio-based surrender model, below | Candidate, not DOS validated |

For attack/defense ratio r and defending fighters D, the workbook predicts surrendering fighters:

```
0                         if r < 1
D * (0.05 + 0.09 * r)      if 1 <= r <= 10
D                         if r > 10
```

Its cached example uses 656,000 attacking and 500,000 defending fighters, yielding r=1.312 and 84,040 surrendering. Boundary jumps at exactly 1 and just above 10 deserve explicit DOS tests. The quadratic plasma model is particularly valuable: increasing the launch from one bolt to two predicts quadruple damage, a strong discriminating test against a linear model.

The sheet has no distance input in its plasma calculation. Damage attenuation, ordered absorption by different defenses, randomness, and version differences therefore still need investigation.

### Independent corroboration of economics

F19:F27 include the same general bank bonus scales recovered from maintenance: ore B/10,000, organics B/20,000, equipment B/30,000, fighters B/500, missiles B/100,000, mines B/250,000, ground forces B/10,000, and plasma B/25,000,000. The sheet also includes 1% daily interest and the 250-credit expenditure to increase each of the three cargo production rates by one.

These are useful cross-checks, but the spreadsheet mixes integer approximations, baseline assumptions, and spending/cargo-transfer estimates. In particular, its plasma bank bonus is floored, whereas the DOS maintenance tests preserve fractional bank-derived plasma production.

## Combat validation update

See [YT.EXE combat recovery](../yt-combat/RECOVERY.md) for 12 captured DOS combat sessions and the recovered algorithms. Plasma cells F7:L7 describe rough scales, not exact damage or guaranteed minima: DOS one-bolt samples destroyed 54,736/54,197 fighters, 25,832 shields, and 351 mines; two bolts destroyed 201,159 fighters. A planet hit reduced total production by 3,221.522, exceeding the nominal 3,000 upper estimate. The 250-mine coefficient materially misses the discrete per-step rounding/increment. Travel and earlier defenses share and consume bolt energy.

The saved surrender example produced 47,242 and 32,993 joining fighters in two DOS runs, versus 84,040 in H16. Original combat proceeds in random batches, cloak energy changes loss odds, and surrender occurs only after surviving committed attackers exceed surviving defenders by 10:1. Xannor and mercenaries refuse. G16:I16 omit those mechanics. The exact >10 immediate-surrender boundary and Xannor refusal were checked in DOS.

The table above retains the original investigation leads; plasma and surrender status is superseded by this update. Missile status is further superseded by the update below; other leads remain unvalidated.

## Missile and assault validation update

[Missile and planetary assault recovery](../yt-missiles/RECOVERY.md) documents 10 additional DOS sessions. Twenty missiles destroyed 39,262 sector fighters, outside F9:G9's suggested 49,000–51,000 range. Against an uncloaked ship they destroyed 35,579 fighters and 228 shields; against an uncloaked ship with no fighters they destroyed 9,211 shields, versus H9's 23,000 prediction. Ship and sector fighter loops differ. Shield damage is conditional on fighter defenses, and cloak/target selection can skip a ship.

I9's one missile per sector mine is confirmed. J9's 12.5 ground-force coefficient matches the mean of the original RND*25 bombardment operation; 20 missiles left 4,766 from a 5,000-ground-force midnight fixture. Only missiles surviving ground-defense absorption attack production, averaging 1,000 per active category per missile. These are means, not guaranteed bounds or simultaneous independent damage budgets.

The workbook contains no direct ground-assault/capture formula. The recovered landing battle has a defending-side advantage, random damage proportional to surviving opposing forces, and survivors become the captured planet's garrison. Do not use J9 or the separate Xannor attack-size helper F13 to predict a player assault. E10 remains unreliable because it also references blank F11 and uses these simplified coefficients.

## Confirmed production discrepancy

With the workbook's saved inputs (G29 = 8,333,250 credits spent, no bank balance or transferred goods), F19:F21 each give 33,334 cargo production, hence total fighter production 100,002 at F22.

However, F23, F24, and F27 omit the three starting cargo-production units from their weapon-rate calculations and cache:

| Daily rate | Workbook | DOS maintenance |
|---|---:|---:|
| Missiles | 39 | 40 |
| Mines | 3 | 4 |
| Plasma bolts | 0 | 1 |

A fresh controlled DOS fixture was created with exactly 33,334/day for each cargo, a zero bank, zero weapon stocks, and one elapsed day. The **unmodified** original YTMAINT.EXE produced approximately 40.0000229 missiles, 4.00000238 mines, and 1.00000060 plasma bolts. The small excess corresponds to the emulated fraction of a second after midnight.

Evidence: `../yt-maint/experiments/spreadsheet-boundary/BEFORE.DAT`, `YTDATA.DAT`, `MAINT.LOG`, `MAINTDAT.LOG`, and `results.json`.

## Other formula cautions

- I7 uses a 250-mine plasma coefficient, but E8 uses 300 in two of its inverse-calculation branches and 250 in another. This is an internal inconsistency, not evidence that either coefficient is correct in DOS.
- E10 refers to F11 in one fighter-damage term while its displayed input is F10; F11 is blank in the supplied file. Do not silently assume intended references.
- Natural growth, stock surplus changes, elapsed-time catch-up, overcrowding, and full maintenance order are not represented by the simple production estimates.

Use this workbook to design discriminating experiments and find constants/routines in YT.EXE. Retain the DOS-verified maintenance model as the authority for the original 3.6 binaries.
