"""Exercise atomic public planet creation through compact/classic GoDoors."""
import json
from pathlib import Path
import subprocess
import tempfile
from smoke_newspaper import BINARY, play, run_on_stable_date

ROOT=Path(__file__).resolve().parents[1]
def exercise(guard):
    transcript=''
    with tempfile.TemporaryDirectory(prefix='yt-creation-news-') as temp:
        for classic in (False,True):
            data=Path(temp)/str(classic)
            guard.run(subprocess.run,[BINARY,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
            guard.run(play,data,'Creator','q')
            guard.run(play,data,'Reader','q')
            path=data/'world.json';w=json.loads(path.read_text())
            sector=next(int(i) for i,s in w['Sectors'].items() if not s.get('Planet'))
            w['Players']['1'].update(Sector=sector,Credits=50000)
            path.write_text(json.dumps(w));before=w['Players']['1'].copy()
            if classic:
                transcript+=guard.run(play,data,'Creator','l',classic=True,followups=[
                    (b'Do you wish to buy a planet(Y/N) [N]? ',b'n\r'),
                    (b'Main Command (?=Help)? ',b'q;y\r')])
                assert not any(n['Kind']=='planet-created' for n in json.loads(path.read_text())['News'])
                transcript+=guard.run(play,data,'Creator','l',classic=True,followups=[
                    (b'Do you wish to buy a planet(Y/N) [N]? ',b'y\r'),
                    (b'What do you want to name this planet? -=>',b'Rejected Name\r'),
                    (b'Is this OK? (Y/n) [Y] ?',b'n\r'),
                    (b'What do you want to name this planet? -=>',b'Accepted World\r'),
                    (b'Is this OK? (Y/n) [Y] ?',b'y\r'),
                    (b'Main Command (?=Help)? ',b'q;y\r')])
            else:
                transcript+=guard.run(play,data,'Creator','create Accepted World;create Duplicate;q')
            saved=json.loads(path.read_text());entries=[n for n in saved['News'] if n['Kind']=='planet-created']
            assert saved['Version']==28 and len(entries)==1 and entries[0]['PlanetName']=='Accepted World' and entries[0]['Alias']=='Creator'
            assert saved['Players']['1']['Credits']==25000 and saved['Players']['1']['Turns']==before['Turns']
            planet=saved['Planets'][str(saved['Sectors'][str(sector)]['Planet'])]
            assert planet['Name']=='Accepted World' and not saved.get('Radio')
            # Subsequent mutable names cannot change the saved public snapshot.
            planet['Name']='Renamed World';path.write_text(json.dumps(saved))
            command='c;8;t;1;q;y' if classic else 'news;q'
            text=guard.run(play,data,'Reader',command,classic=classic,page_news=True);transcript+=text
            assert 'Creator made a planet: Accepted World' in text and 'Rejected Name' not in text and 'Renamed World' not in text
            again=json.loads(path.read_text());assert len([n for n in again['News'] if n['Kind']=='planet-created'])==1
    (ROOT/'evidence/planet-creation-news-smoke.txt').write_text('\n'.join(line.rstrip() for line in transcript.splitlines())+'\n')
if __name__=='__main__':
    run_on_stable_date(exercise)
    print('Planet creation news PTY passed: compact/classic, decline, name retry, one charge/event, reconnect and immutable public snapshot.')
