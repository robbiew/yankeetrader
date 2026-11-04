"""Verify retained full QB campaign snapshots, daily deltas and endgame evidence."""
import argparse
import datetime
import gzip
import hashlib
import json
import re
from pathlib import Path


def verify(root):
    root = Path(root)
    manifest = json.loads((root/'manifest.json').read_text())
    report = json.loads((root/'summary.json').read_text())
    days = report['days']
    assert isinstance(days, int) and 3 <= days <= 24, 'daily coverage'
    names = {f'{name}.json.gz' for name in ('initial','earned-budget','before-genesis','after-genesis','reconnected')}
    names |= {'summary.json','actions.json','transcript.txt.gz','driver.go.txt'}
    names |= {f'day-{day:02d}-{phase}.json.gz' for day in range(1,days+1) for phase in ('before','after','repeat')}
    assert set(manifest) == names, 'incomplete evidence manifest'
    assert (root/'driver.go.txt').read_bytes()==(Path(__file__).resolve().parents[1]/'internal/door/qb_campaign_test.go').read_bytes(), 'driver source provenance'
    for name, digest in manifest.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, f'hash: {name}'
    def world(name):
        return json.loads(gzip.decompress((root/f'{name}.json.gz').read_bytes()))
    initial, earned, before, after, reconnected = [world(n) for n in ('initial','earned-budget','before-genesis','after-genesis','reconnected')]
    initial_at=datetime.datetime.fromisoformat(initial['Created'].replace('Z','+00:00'))
    reset_at=initial_at+datetime.timedelta(days=days)
    assert datetime.datetime.fromisoformat(after['Created'].replace('Z','+00:00'))==reset_at, 'reset clock does not match campaign days'
    assert before['LastMaintenance']==after['LastMaintenance']==reset_at.date().isoformat(), 'reset campaign date'
    assert reconnected['Created']==after['Created'] and before['Created']==initial['Created'], 'season clock continuity'
    recipe = initial['QBRecipe']
    assert recipe['Profile']=='qb36-v1' and recipe['State']==0xc805 and recipe['Date']=='2027-01-01', 'source recipe'
    assert recipe['SourceSHA256']=='e6d5ab5b3fab7563b279e976cdde3c4e6e494c2dffd5c35a74a60fac38fdf328', 'retained native source fingerprint'
    assert report['outcome']=='passed' and report['threshold']==300 and report['purchases']==300, 'campaign outcome'
    assert report['boundary_battles']>=1, 'missing NPC frontier coverage'
    assert report['ports']==1000 and report['sectors']==3000 and report['old_login_rejected'], 'coverage'
    assert report['source_recipe']==recipe, 'summary recipe'
    assert report['sessions']>10 and report['commands']>300 and report['trade_cycles']>1, 'campaign too short'
    assert initial['Season']==1 and initial['Players']=={} and initial.get('GenesisPorts') is None, 'initial default'
    assert earned['Players']['1']['Credits']>=2_500_000 and earned['Players']['1']['Holds']==1000, 'earned budget'
    def owned(w):
        return sum(p['Owner']==1 for key,p in w['Ports'].items() if key!='1')
    assert owned(before)==300 and before['Season']==1, 'actual 300 owned ports'
    assert after['Season']==2 and after['Players']=={} and owned(after)==0, 'reset world'
    result = after['SeasonResults']
    assert len(result)==1 and result[0]['Started']==initial['Created'] and result[0]['Ended']==after['Created'], 'winner clock continuity'
    assert len(result)==1 and result[0]['Winner']=='Atlas' and result[0]['Ports']==300 and result[0]['Threshold']==300 and not result[0].get('Administrative'), 'winner history'
    assert reconnected['Players']['1']['Identity']=='acceptance:atlas' and reconnected['Players']['1']['Credits']==1005 and owned(reconnected)==0, 'new season reconnect'
    for w in (initial,earned,before,after,reconnected):
        assert w['QBRecipe']==recipe and w['Version']==35 and len(w['Sectors'])==3000 and len(w['Ports'])==1000, 'recipe/geometry'
        assert w.get('GenesisPorts') is None, 'overridden Genesis threshold'
        for key, port in w['Ports'].items():
            assert port['ID']==int(key) and w['Sectors'][str(port['Sector'])]['Port']==port['ID'], 'port link'
        for player in w['Players'].values():
            assert player['Credits']>=0 and 0<=player['Turns']<=500 and 0<=sum(player['Cargo'])<=player['Holds'], 'player assets'

    # Economy may evolve during maintenance. Reset must restore SOURCE economy,
    # not preserve random maintenance changes from the just-finished season.
    for key,p in initial['Ports'].items():
        q=after['Ports'][key]
        assert all(q[f]==p[f] for f in ('Sector','Name','Production','Coefficient')), 'reset source port'
        assert q['Owner']==q['Treasury']==0 and q['Supply']==[v*10 for v in q['Production']], 'initial stock reset'
        assert q['Updated']==after['Created'], 'reset port watermark'
    for key,s in initial['Sectors'].items():
        assert after['Sectors'][key]['Warps']==s['Warps'], 'reset source map'
    assert after['Xannor']['HQ']==initial['Xannor']['HQ'], 'reset HQ'
    assert after['LastMaintenance']==after['Created'][:10], 'reset maintenance date'
    receipts = report['maintenance']
    assert len(receipts)==days, 'missing daily receipts'
    previous = initial['LastMaintenance']
    defense_changes=0
    wanderer_moves=0
    for day, receipt in enumerate(receipts,1):
        pre, post, repeated = [world(f'day-{day:02d}-{p}') for p in ('before','after','repeat')]
        assert (datetime.date.fromisoformat(receipt['date'])-datetime.date.fromisoformat(previous)).days==1 and receipt['date']==post['LastMaintenance'], 'daily ordering'
        assert pre['LastMaintenance']==previous and post==repeated, 'same-day maintenance repeated'
        assert all(w['QBRecipe']==recipe and w['Season']==1 for w in (pre,post,repeated)), 'maintenance rerolled season/recipe'
        assert receipt['ran'] and receipt['same_day_noop'] and receipt['turns_before']==pre['Players']['1']['Turns'] and receipt['turns_after']==post['Players']['1']['Turns']==500, 'turn replenishment'
        changed=sum(p['Supply']!=pre['Ports'][key]['Supply'] for key,p in post['Ports'].items())
        assert changed==receipt['ports_changed'] and changed>0, 'daily economy delta'
        defense_changes+=sum(s.get('Defense')!=pre['Sectors'][key].get('Defense') for key,s in post['Sectors'].items())
        wanderer_moves+=post['Planets']['1']['Sector']!=pre['Planets']['1']['Sector']
        for key, sector in pre['Sectors'].items():
            assert post['Sectors'][key]['Warps']==sector['Warps'], 'maintenance rerolled map'
        for key, port in pre['Ports'].items():
            assert all(post['Ports'][key][f]==port[f] for f in ('ID','Sector','Name')), 'maintenance moved port'
        previous=receipt['date']
    assert previous==reset_at.date().isoformat(), 'final maintenance date'
    assert defense_changes>0 and wanderer_moves>0, 'NPC maintenance effects missing'
    transcript=gzip.decompress((root/'transcript.txt.gz').read_bytes()).decode()
    assert '1 short' in transcript and '300 ports (required 300)' in transcript, 'threshold terminal receipts'
    actions=json.loads((root/'actions.json').read_text())
    headers=list(re.finditer(r'^SESSION ([1-9][0-9]*) UTC (\S+) INPUT (\[.*\])$',transcript,re.MULTILINE))
    assert [int(h[1]) for h in headers]==list(range(1,report['sessions']+1)), 'session input count/order'
    recorded=[]
    previous_at=initial_at
    for header in headers:
        at=datetime.datetime.fromisoformat(header[2].replace('Z','+00:00'))
        assert previous_at<=at<=reset_at, 'session UTC order/range'
        previous_at=at
        # Go's %q slice contains whitespace-separated quoted input strings.
        payload=header[3][1:-1]
        literals=re.findall(r'"(?:[^"\\]|\\.)*"',payload)
        assert literals and not re.sub(r'"(?:[^"\\]|\\.)*"','',payload).strip(), 'session input encoding'
        recorded.extend(json.loads(literal) for literal in literals)
    assert previous_at==reset_at and recorded==actions and len(actions)==report['commands'], 'actions disagree with session transcript/command count'
    trades=[a.split() for a in actions if a.startswith(('buy ','sell '))]
    assert len(trades)==2*report['trade_cycles'] and transcript.count('Trade saved.')==len(trades), 'trade cycle receipts/count'
    for buy,sell in zip(trades[::2],trades[1::2]):
        assert len(buy)==len(sell)==3 and buy[0]=='buy' and sell[0]=='sell' and buy[1:]==sell[1:] and buy[1] in ('ore','organics','equipment') and int(buy[2])>0, 'trade cycle inputs'
    equipment=[a.split() for a in actions if a.startswith('equip ')]
    assert all(len(a)==3 and a[1] in ('holds','fighters') and int(a[2])>0 for a in equipment), 'equipment inputs'
    assert transcript.count('Equipment purchased and saved.')==len(equipment), 'equipment receipts/count'
    assert 10+sum(int(a[2]) for a in equipment if a[1]=='holds')==earned['Players']['1']['Holds']==before['Players']['1']['Holds'], 'earned holds input trail'
    battles=re.findall(r'Defense encounter saved: (\d+) attackers lost, (\d+) defenders destroyed, (\d+) surrendered\.',transcript)
    assert 25+sum(int(a[2]) for a in equipment if a[1]=='fighters')-sum(int(b[0]) for b in battles)+sum(int(b[2]) for b in battles)==before['Players']['1']['Fighters'], 'earned fighters input trail'
    assert actions.count('b')==300 and actions.count('y')==300+2*report['boundary_battles'] and 'GENESIS' in actions, 'confirmed action trail'
    assert sum(a.startswith('breach ') for a in actions)==report['boundary_battles'] and transcript.count('Defense encounter saved:')==report['boundary_battles'], 'NPC boundary receipts'
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
    report=verify(args.root)
    print(f"Verified full QB campaign: {report['days']} UTC days, {report['purchases']} confirmed ports, default 300-port Genesis.")

if __name__=='__main__':
    main()
