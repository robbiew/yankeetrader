from experiments import *

def do(name,mode):
 d=setup(name);data=bytearray((d/'YTDATA.DAT').read_bytes());hq=int(get(data,1,117))
 if mode=='missing':
  put(data,51+hq,93,0);put(data,4151,85,0)
 else:
  p=137;data[p:p+137]=bytes(137);data[p:p+41]=b'Test Captain'.ljust(41,b' ')
  for off,v in {41:297,45:297,57:8,61:10000,73:100000,85:12,109:10000000,125:0}.items():put(data,2,off,v)
  if mode=='revenge':put(data,51+21,105,2)
  if mode=='reclaim':put(data,51+hq,85,-2);put(data,51+hq,81,100)
 (d/'YTDATA.DAT').write_bytes(data);(d/'BEFORE.DAT').write_bytes(data);run(d)
 a=(d/'YTDATA.DAT').read_bytes();log=(d/'MAINT.LOG').read_bytes().decode('cp437')
 result={'old_hq':hq,'new_hq':get(a,1,117),'before_hq':record(data,51+hq),'after_old_hq':record(a,51+hq),'revenge_pointer_after':get(a,72,105),'xannoron_records':[(r,record(a,r)) for r in range(4052,4152) if record(a,r)['text']=='Xannoron'], 'events':[l for l in log.splitlines() if any(t in l for t in ['Planet','planet','Headquarters','base','Successful','Failed','REVENGE','Group 20','Dynamic'])]}
 (d/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(name,json.dumps(result))
if __name__=='__main__':
 do('missing-xannoron-v2','missing');do('xannor-revenge','revenge');do('xannor-reclaim','reclaim')
