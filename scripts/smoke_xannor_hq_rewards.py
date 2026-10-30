"""Exercise real HQ victories, capped receipts, privacy and reconnect in both UIs."""
import copy,json,subprocess,tempfile
from pathlib import Path
from smoke_newspaper import BINARY,play,run_on_stable_date

MAX=9000000000000000


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix='yt-hq-reward-smoke-')as temp:
        root=Path(temp);seed=root/'seed'
        guard.run(subprocess.run,[BINARY,'-data',str(seed),'-init','-sectors','12'],check=True,capture_output=True)
        guard.run(play,seed,'Captain','q');guard.run(play,seed,'Visitor','q')
        original=json.loads((seed/'world.json').read_text())
        for classic in (False,True):
            for weapon in ('fighters','missiles','bribe'):
                for mode,balance,want in [('normal',1005,1000000),('one-credit',MAX-1,1),('full',MAX,0),('cancel',MAX-1,0)]:
                    data=root/(weapon+mode+str(classic));data.mkdir();path=data/'world.json';w=copy.deepcopy(original)
                    w['Players']['1'].update(Sector=7,Fighters=10000,Shields=100,Missiles=3,Credits=balance,Cloak=0)
                    w['Xannor']=dict(HQ=8,Reserve=0);w['Sectors']['7']['Warps']=[8];w['Sectors']['8']['Warps']=[7]
                    w['Sectors']['8']['Defense']=dict(Owner=-1,Fighters=1)
                    path.write_text(json.dumps(w));prompt=b'Main Command (?=Help)?'if classic else b'> '
                    ending=b'news today;q;y\r'if classic else b'news;q\r'
                    answer=b'n\r'if mode=='cancel'else b'y\r'
                    if weapon=='fighters':
                        command='breach 8 10000';replies=[(b'Accept human surrender if offered during this battle? [Y/n] ',b'y\r'),(b'defeat forces emergency escape. [y/N] ',answer),(prompt,ending)]
                    elif weapon=='bribe':
                        command='bribe 8 1';replies=[(b'[y/N] ',answer),(prompt,ending)]
                    else:
                        command='missile 8 3';replies=[(b'[y/N] ',answer),(prompt,ending)]
                    text=guard.run(play,data,'Captain',command,classic=classic,followups=replies)
                    saved=json.loads(path.read_text());p=saved['Players']['1']
                    assert saved['Version']==21 and p['Credits']==balance+want,(mode,text)
                    news=[e for e in saved['News']if e['Kind']=='xannor-hq-victory']
                    if mode=='cancel':
                        assert saved['Sectors']['8']['Defense']['Fighters']==1 and not news and 'Credits added:'not in text,text
                        continue
                    receipt=f'Xannor HQ victory in sector 8. Credits added: {want}.'
                    assert text.count(receipt)==1 and text.count('Ship credit limit capped this bonus.')==int(want<1000000),text
                    assert 'Captain  Defeated the Xannor HQ!'in text and len(news)==1 and news[0]['Alias']=='Captain'
                    assert not saved['Sectors']['8'].get('Defense') and saved['Xannor']['Revenge']['Player']==1
                    assert saved['Players']['2']['Credits']==original['Players']['2']['Credits']
                    # A different caller sees public victory, never the private credited amount.
                    public=guard.run(play,data,'Visitor','news;q')
                    assert 'Captain  Defeated the Xannor HQ!'in public and 'Credits added:'not in public and str(MAX)not in public,public
                    assert 'Ship credit limit capped'not in public
                    # Returning is not another victory; no deferred receipt or money redemption.
                    reconnect=guard.run(play,data,'Captain','q;y'if classic else'q',classic=classic)
                    after=json.loads(path.read_text())
                    assert 'Credits added:'not in reconnect and after['Players']['1']['Credits']==balance+want
                    assert len([e for e in after['News']if e['Kind']=='xannor-hq-victory'])==1
    print('HQ reward PTY passed: real fighter/missile/forced-bribe victories, normal/one-credit/full receipts, cancellation, classic/compact public privacy and reconnect without repayment.')


if __name__=='__main__':run_on_stable_date(exercise)
