Echo off
:RESTART
c:
cd \quickbbs
quickbbs %1

:afterbbs

if errorlevel 50 goto YT
if errorlevel 1 goto RESTART

Rem Allow exiting of batch file.
goto endit

:RELOGIN
c:
cd \quickbbs
quickbbs -r -e1
goto afterbbs

:YT
Rem Yankee Trader Batch File
c:
cd \quickbbs\doors\yt
yt.exe c:\quickbbs\dorinfo1.def
goto relogin

:Endit
Echo QuickBBS is now down.
