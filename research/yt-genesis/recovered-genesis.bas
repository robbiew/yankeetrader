' Semantic pseudocode, not recovered original source.
' YT.EXE config loader 1f42:be3e..beb4
required = Config.GenesisPorts
IF required < 20 THEN required = 200
' YT.EXE 1000:2728..2858
PRINT "Are you that Trader [y/N]"
answer = ReadAnswer()
IF required > 300 THEN answer = "N": PRINT "*FUNCTION DISABLED*"
IF answer <> "Y" THEN RETURN
IF Player.PortsOwned < required THEN PRINT "You are ... short": RETURN
' No scan of actual port ownership and no score or NPC-defeat predicate.
OPEN "RMTINIT.TMP" FOR OUTPUT AS #5
PRINT #5, RuntimeHandoffString
CLOSE
CHAIN "Rmt-init.exe"
' RMT-INIT reads and deletes handoff, reloads old configuration, regenerates
' players/sectors/ports/planets/NPC initial state, year 6324, lastmaint yesterday.
' Replaces news/name/radio files; announces victory; does not run YTMAINT.
