"""Exercise private seller notices through real compact/classic GoDoors."""
import json
from pathlib import Path
import subprocess
import tempfile
from smoke_newspaper import BINARY,play,run_on_stable_date
ROOT=Path(__file__).resolve().parents[1]
def exercise(guard):
    transcript=''
    with tempfile.TemporaryDirectory(prefix='yt-port-sale-notices-') as temp:
        for classic in (False,True):
            data=Path(temp)/str(classic)
            guard.run(subprocess.run,[BINARY,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
            for alias in ('Buyer','Seller','Visitor'):guard.run(play,data,alias,'q')
            path=data/'world.json';w=json.loads(path.read_text())
            w['Players']['1'].update(Sector=2,Credits=100000)
            w['Players']['2']['Credits']=2000
            w['Ports']['2'].update(Owner=2,Treasury=777,Name='Old Harbor')
            path.write_text(json.dumps(w));news_before=w['NextNews']
            quit_keys='q;y' if classic else 'q'
            transcript+=guard.run(play,data,'Buyer','b;n;'+quit_keys,classic=classic)
            declined=json.loads(path.read_text());assert declined['Ports']['2']['Owner']==2 and not declined.get('Radio')
            transcript+=guard.run(play,data,'Buyer','b;y;'+quit_keys,classic=classic)
            saved=json.loads(path.read_text());assert saved['Version']==30
            assert (saved['Players']['1']['Credits'],saved['Players']['2']['Credits'],saved['Ports']['2']['Owner'],saved['Ports']['2']['Treasury'])==(99969,2808,1,0)
            assert saved['Players']['1']['Turns']==500 and len(saved['Radio'])==1
            mail=saved['Radio'][0];assert mail['System']=='port-sale' and mail['From']==0 and mail['To']==2 and mail['Unread'] and mail['Text']==''
            assert mail['PortSale']==dict(BuyerAlias='Buyer',PortName='Old Harbor',Sector=2,AskingPrice=31)
            # Names change after publication, while original private snapshots persist.
            saved['Ports']['2']['Name']='New Harbor';saved['Players']['1']['Alias']='Renamed Buyer';path.write_text(json.dumps(saved))
            for alias in ('Renamed Buyer','Visitor'):
                # Local account identity follows its original login name.
                login='Buyer' if alias=='Renamed Buyer' else alias
                out=guard.run(play,data,login,'messages;news;q',page_news=True);transcript+=out
                assert 'bought your port' not in out,out
            command='c;6;1;q;y' if classic else 'messages;q'
            out=guard.run(play,data,'Seller',command,classic=classic);transcript+=out
            expected='Buyer bought your port "Old Harbor" in 2 for 31 credits'
            assert expected in out and 'The Mercenaries' in out and 'for 808 credits' not in out,out
            after=json.loads(path.read_text());assert len(after['Radio'])==1 and not after['Radio'][0]['Unread'] and after['Players']['2']['Credits']==2808
            out=guard.run(play,data,'Seller','messages;q');transcript+=out;assert expected in out
            after=json.loads(path.read_text());assert all(n['Kind']=='login' for n in after['News'] if n['ID']>=news_before)
            assert after['Ports']['2']['Owner']==1 and len(after['Radio'])==1
        (ROOT/'evidence/port-sale-notices-smoke.txt').write_text('\n'.join(line.rstrip() for line in transcript.splitlines())+'\n')
if __name__=='__main__':
    run_on_stable_date(exercise)
    print('Port-sale notices PTY passed: compact/classic, decline, exact settlement, old-name snapshots, private reconnect delivery, acknowledgement/history and no public purchase news.')
