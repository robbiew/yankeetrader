from experiments import *

def save(d,data):
 (d/'YTDATA.DAT').write_bytes(data);(d/'BEFORE.DAT').write_bytes(data)
def totals(data):
 groups=[]
 for s in range(1,3001):
  if get(data,51+s,85)==-1:groups.append((s,get(data,51+s,81)))
 return {'total':sum(n for s,n in groups),'sectors':groups}

def taxes():
 d=setup('taxes');data=bytearray((d/'YTDATA.DAT').read_bytes())
 values=[1005,0,9,10,19,101,1005,1000000]
 for p,v in enumerate(values,1):put(data,3051+p,89,v)
 save(d,data);run(d)
 after=(d/'YTDATA.DAT').read_bytes();(d/'FIRST.DAT').write_bytes(after)
 run(d,tag='repeat')
 again=(d/'YTDATA.DAT').read_bytes()
 rows=[{'port':i+1,'before':v,'after':get(after,3052+i,89),'repeat':get(again,3052+i,89)} for i,v in enumerate(values)]
 (d/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('TAXES',rows)

def xannor(score,name):
 d=setup(name);data=bytearray((d/'YTDATA.DAT').read_bytes());rec=2
 p=(rec-1)*137;data[p:p+137]=bytes(137);data[p:p+41]=b'Test Captain'.ljust(41,b' ')
 for off,v in {41:297,45:297,57:8,61:10000,73:100000,85:12,109:score,125:10}.items():put(data,rec,off,v)
 save(d,data);run(d)
 after=(d/'YTDATA.DAT').read_bytes();log=(d/'MAINT.LOG').read_bytes().decode('cp437')
 result={'score':score,'before_xannor':totals(data),'after_xannor':totals(after),'report_lines':[l for l in log.splitlines() if any(s in l for s in ['Dynamic','Group 20','Group:','REVENGE','base','error','Error'])],'player_after':record(after,2)}
 (d/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(name,json.dumps(result))

def periods():
 d=setup('periods');data=bytearray((d/'YTDATA.DAT').read_bytes())
 specs=[('half-day',1,720,1000,2000,3500,0),('twenty-bank',20,0,1000,2000,3000,1000000),('large-prod',1,0,50000,50000,50000,0)]
 for i,(name,days,minute,a,b,c,bank) in enumerate(specs):
  rec=4055+i;p=(rec-1)*137;data[p:p+137]=bytes(137);data[p:p+41]=name.encode().ljust(41,b' ')
  for off,v in {41:298-days,45:a,49:b,53:c,73:0,77:100,85:len(name),89:minute,117:bank}.items():put(data,rec,off,v)
  put(data,51+3+i,93,4+i)
 save(d,data);run(d)
 after=(d/'YTDATA.DAT').read_bytes();r=[{'name':s[0],'before':record(data,4055+i),'after':record(after,4055+i)} for i,s in enumerate(specs)]
 (d/'results.json').write_text(json.dumps(r,indent=2)+'\n');print('PERIODS',json.dumps(r))
if __name__=='__main__':
 taxes();periods()
 for s,n in [(100000,'xannor-low'),(1000000,'xannor-mid'),(10000000,'xannor-high')]:xannor(s,n)
