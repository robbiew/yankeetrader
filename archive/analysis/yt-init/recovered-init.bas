' MANUALLY RECONSTRUCTED OUTLINE from static binary analysis.
' Not recovered original BASIC; uncertain runtime semantics omitted.
' Addresses refer to Ghidra code segment 1000.

PortCount = 1000         ' 0078
SectorCount = 3000       ' 0083
MaxPlanets = 100         ' 008E
PlayerCount = 50         ' 0AC5

' 03C9: mode R, record length 137; FIELD maps only 133 bytes.
OPEN "YTDATA.DAT" FOR RANDOM AS #1 LEN = 137
' One 41-byte text field, then 23 four-byte packed fields.
' Four additional bytes in the record remain unexplained.

StartFighters = 25       ' 07A3
StartCredits = 1005      ' 07DB
StartHolds = 10          ' 0810
DeadPlayerDelay = 14     ' 0845
LastMaintenance = Yesterday ' 087A, date routine not fully decoded
TurnsPerDay = 500        ' 08B7
LotteryPlaysPerDay = 5   ' 08EC

' 098D prints 450, but 099A loads and stores 300.
PRINT "Ports needed to initiate Genesis: 450"
GenesisThreshold = 300  ' Likely meaning; requires game/config cross-check.
MaxHolds = 1000         ' 09AA

INPUT "Scoreboard path"; ScoreboardPath$
IF ScoreboardPath$ = "" THEN ScoreboardPath$ = "YTSCORE.ASC"

' Inferred default allocation:
' Record 1: config
' Records 2..51: players
' Records 52..3051: sectors
' Records 3052..4051: ports
' Records 4052..4151: planets

' Generate/repair six-column warp graph; write sectors.
' Generate ports; first port name Earth; random syllables for others.
' Backdate production by ten days.
' Clear planet slots and initialize Xannor HQ.
' Initialize YTNEWS.DAT, YTNAME.DAT, YTRMSG.DAT.
' Invoke YTMAINT.EXE.
