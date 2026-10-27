"""Verify Go salvage fixtures against the DOS-grounded research model."""
import sys
sys.dont_write_bytecode=True
import importlib.util,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rules',root/'research/yt-ships/loot_rules.py');rules=importlib.util.module_from_spec(spec);spec.loader.exec_module(rules)
rows=[]
for name,winner,cargo,holds,stocks,draws in [
 ('at-cap',1000,[11,23,37],100,[10000,41,43,47,5],[.785,.76755,.105,.735,.645,.455]),
 ('mixed',10,[11,23,37],100,[10000,41,43,47,5],[.785,.76755,.105,.735,.645,.455,0,.2,.6,.99]),
 ('cap-990',990,[11,23,37],100,[10000,41,43,47,5],[.785,.76755,.105,.735,.645,.455,0,.2,.6,.99]),
 ('cap-999',999,[11,23,37],100,[10000,41,43,47,5],[.785,.76755,.105,.735,.645,.455,0,.2,.6,.99]),
 ('ore',10,[100,0,0],100,[0,0,0,0,0],[.785]),('org',10,[0,100,0],100,[0,0,0,0,0],[.785]),
 ('equipment',10,[0,0,100],100,[0,0,0,0,0],[.785]),('empty',10,[0,0,0],100,[0,0,0,0,0],[.785]),
 ('unit-stocks',10,[0,0,0],10,[1,1,1,1,1],[.999999])]:
 i=[0]
 def rng():r=draws[i[0]%len(draws)];i[0]+=1;return r
 result=rules.salvage(holds,*stocks,cargo,winner,rng)
 rows.append(dict(Name=name,WinnerHolds=winner,Victim=dict(Holds=holds,Credits=stocks[0],Missiles=stocks[1],Plasma=stocks[2],Ground=stocks[3],Mines=stocks[4],Cargo=cargo),Draws=draws,Expected={k.title():v for k,v in result.items()}))
assert rows == json.loads((root/'internal/game/testdata/salvage-model.json').read_text()), 'Go salvage fixtures differ from the research model'
print('Verified 9 injected-RNG salvage model fixtures; exact-money extremes are tested separately in Go.')
