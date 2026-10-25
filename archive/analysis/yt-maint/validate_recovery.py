"""Recheck preserved DOS outputs against the recovered rules and controls."""
from pathlib import Path
import json,math,re,hashlib
from experiments import get,record
from recovered_rules import update_planet,tax,xannor_regeneration
ROOT=Path(__file__).resolve().parent
E=ROOT/'experiments'
checks=[]
def check(label,condition):
    assert condition,label
    checks.append(label)
def data(name,file='YTDATA.DAT'):return (E/name/file).read_bytes()
def log(name,file='MAINT.LOG'):return (E/name/file).read_bytes().decode('cp437')

def economy(name,rec,ground=True):
    before=record(data(name,'BEFORE.DAT'),rec)['fields'];after=record(data(name),rec)['fields']
    model,d=update_planet(before,after['41'],after['89'])
    offsets=[45,49,53,57,61,65,69,113,117,125,129]+([77] if ground else [])
    for off in offsets:check(f'{name}/record{rec}/offset{off}',math.isclose(after[str(off)],model[off],rel_tol=2e-6,abs_tol=.01))
    return d

for i in range(6):economy('production-v2',4054+i,ground=i!=0)
# NPC combat is explicitly reported against zero-bank; its ground count is
# excluded rather than incorrectly attributed to production.
check('NPC-ground-interference-recorded','attacked the planet "zero-bank"' in log('production-v2'))
for rec in [4055,4056,4057]:economy('periods',rec)
check('negative-time-clamps-ten-days',economy('future-clock',4055)==10)
economy('interest-two-updates',4055)
check('two-day-catchup-simple-interest',get(data('production-v2'),4058,117)==1020000)
check('two-separate-days-compound',get(data('interest-two-updates'),4055,117)==1020100)

before=data('taxes','BEFORE.DAT');first=data('taxes','FIRST.DAT');second=data('taxes')
for port in range(1,9):
    a=get(before,3051+port,89);b=get(first,3051+port,89);c=get(second,3051+port,89)
    check(f'port{port}/first-tax',b==a-tax(a,port))
    check(f'port{port}/repeat-tax',c==b-tax(b,port))
check('same-day-warning-does-not-stop','Maintenance not needed!' in log('taxes','REPEAT.LOG') and get(second,3059,89)==810000)

for name in ['xannor-low','xannor-mid','xannor-high','xannor-below-cap','xannor-fraction']:
    r=json.loads((E/name/'results.json').read_text());expected=xannor_regeneration(r['score'],r['before_xannor']['total'])
    observed=float(re.search(r'Dynamic Xannor Regeneration is ([\d.]+)',log(name)).group(1))
    check(f'{name}/regeneration-report',observed==expected)
    hq=int(get(data(name,'BEFORE.DAT'),1,117))
    check(f'{name}/hq-regeneration',get(data(name),51+hq,81)-get(data(name,'BEFORE.DAT'),51+hq,81)==expected)
for name,event in [('plague-small',None),('plague-large','A PLAGUE'),('civil-large','CIVIL WAR'),('civil-rich','CIVIL WAR')]:
    r=json.loads((E/name/'results.json').read_text())
    check(f'{name}/event',event in r['events'] if event else 'has struck planet plague-small' not in r['events'])
    if event:
        counterfactual,_=update_planet(r['before']['fields'],r['after']['fields']['41'],r['after']['fields']['89'])
        check(f'{name}/production-reduced',sum(r['after']['fields'][str(o)] for o in [45,49,53])<sum(counterfactual[o] for o in [45,49,53]))
check('civil-war-debits-bank',get(data('civil-rich'),4055,117)<1000000000)
check('xannoron-rebuilt','The Xannor have made a Planet!' in log('missing-xannoron-v2'))
for off in [45,49,53]:check(f'rebuilt-xannoron-production-{off}',get(data('missing-xannoron-v2'),4151,off)==100000)
check('revenge-reported','Xannor REVENGE!' in log('xannor-revenge'))
check('revenge-pointer-consumed',get(data('xannor-revenge'),72,105)==0)
check('top-player-target','Group 20 will hunt for Test Captain' in log('xannor-revenge'))
check('hq-reclaim','attempting to reclaim their base from The Mercenaries' in log('xannor-reclaim') and 'Successful!' in log('xannor-reclaim'))
check('hq-relocation',get(data('xannor-reclaim'),1,117)!=get(data('xannor-reclaim','BEFORE.DAT'),1,117))
originals=json.loads((ROOT.parent/'dos-validation/evidence/original-hashes.json').read_text())
for name,digest in originals.items():check(f'original-unchanged/{name}',hashlib.sha256((ROOT.parent.parent/name).read_bytes()).hexdigest()==digest)
for path in E.glob('*/YTMAINT.EXE'):check(f'unmodified-maint/{path.parent.name}',hashlib.sha256(path.read_bytes()).hexdigest()==originals['YTMAINT.EXE'])
result={'passed':len(checks),'failures':0,'checks':checks,'limits':['Formula comparison uses tolerances for MBF32 rounding; not bit-exact emulation.','Random-event probabilities and full combat/target-selection algorithms are not validated.','Discarded setup probes: production used an invalid hyphenated DOS date; missing-xannoron left a live sector reference. They are not used as evidence for the recovered rules.']}
(ROOT/'validation-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'{len(checks)} evidence checks passed; original files and all DOS maintenance executables unchanged.')
