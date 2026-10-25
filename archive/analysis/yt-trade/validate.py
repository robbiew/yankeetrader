from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis/yt-maint'))
from experiments import get
R=ROOT/'analysis/yt-combat/experiments';checks=0
def ck(v,msg):
 global checks
 assert v,msg
 checks+=1
def data(n):return (R/n/'YTDATA.DAT').read_bytes()
for n,cash,cargo,treasury in [('high',999900,10,0),('low',999810,10,0),('sell',1000300,90,0),('self',999900,10,1),('other',999900,10,100)]:
 b=data('trade-'+n)
 for rec,off,want in [(2,81,cash),(2,69,cargo),(3053,89,treasury),(2,49,499)]:ck(get(b,rec,off)==want,n+f' {rec}:{off}')
 ck(abs(get(b,3053,49)-(90 if n=='low' else 990))<.03,n+' supply/demand decrement plus elapsed production')
b=data('trade-port-buy');ck(get(b,2,81)==999969,'31 credit normal port price');ck(get(b,3053,97)==2 and get(b,2,117)==1,'normal port ownership')
b=data('trade-earth-buy');ck(get(b,2,81)==1000000,'Earth purchase cost');ck(get(b,3052,97)==2 and get(b,2,117)==1,'Earth ownership')
for n,owner,buyer,fighters,treasury in [('trade-earth-gear',1000000,900000,1025,100000),('trade-earth-withdraw',1100000,900000,1025,0),('trade-earth-gear2',1100000,800000,2025,100000),('trade-earth-withdraw2',1200000,800000,2025,0)]:
 b=data(n)
 for rec,off,want in [(2,81,owner),(3,81,buyer),(3,61,fighters),(3052,89,treasury)]:ck(get(b,rec,off)==want,n+f' {rec}:{off}')
 ck(get(b,2,81)+get(b,3,81)+get(b,3052,89)==2000000,n+' shared cash conservation')
 ck(get(b,3052,97)==2,n+' ownership retained')
print(f'{checks} checks passed across eleven trading/equipment sessions.')
