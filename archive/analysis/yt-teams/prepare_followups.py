"""Copy completed primary evidence before a later-clock successor/rejoin login."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parent.parent/'yt-combat/experiments'
for name in ['banish','quit']:
 s=r/('team-'+name);d=r/('fixture-team-after-'+name)
 assert (s/'YTDATA.DAT').exists()
 assert ('Now change your Team Password!' if name=='banish' else 'You have been removed from Team play') in (s/'GAME.LOG').read_text(errors='replace')
 shutil.copytree(s,d);shutil.copy2(d/'YTDATA.DAT',d/'before.dat')
print('Use YT_PLAYER=Enemy YT_DOS_TIME=00:01:00 for followups. Existing directories are never overwritten.')
