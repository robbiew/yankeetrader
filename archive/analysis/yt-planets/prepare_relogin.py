"""After planet-bank-large completes, copy its exact persisted world for next login."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parent.parent/'yt-combat/experiments'
s=r/'planet-bank-large';d=r/'fixture-planet-bank-large-relogin'
assert 'Returning to Yankee Trader Local Logon Program' in (s/'GAME.LOG').read_text(errors='replace')
shutil.copytree(s,d)
shutil.copy2(d/'YTDATA.DAT',d/'before.dat')
print('Copied exact first-session save. Run the next login with YT_DOS_TIME=00:01:00.')
