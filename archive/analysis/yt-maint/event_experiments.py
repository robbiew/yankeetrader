from experiments import *

def eventcase(name,production,ground,bank=0):
 d=setup(name);data=bytearray((d/'YTDATA.DAT').read_bytes());rec=4055
 p=(rec-1)*137;data[p:p+137]=bytes(137);data[p:p+41]=name.encode().ljust(41,b' ')
 for off,v in {41:297,45:production,49:production,53:production,73:0,77:ground,85:len(name),89:0,117:bank}.items():put(data,rec,off,v)
 put(data,54,93,4)
 (d/'YTDATA.DAT').write_bytes(data);(d/'BEFORE.DAT').write_bytes(data);run(d)
 after=(d/'YTDATA.DAT').read_bytes();log=(d/'MAINT.LOG').read_bytes().decode('cp437')
 result={'before':record(data,rec),'after':record(after,rec),'events':log[log.find('Running planet maintenance'):log.find('Moving The Wanderer')]}
 (d/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(name,json.dumps(result))

def missingplanet():
 d=setup('missing-xannoron');data=bytearray((d/'YTDATA.DAT').read_bytes());rec=4151
 # A missing planet is represented by zero name length; preserve original buffer.
 put(data,rec,85,0)
 (d/'YTDATA.DAT').write_bytes(data);(d/'BEFORE.DAT').write_bytes(data);run(d)
 a=(d/'YTDATA.DAT').read_bytes();log=(d/'MAINT.LOG').read_bytes().decode('cp437')
 (d/'results.json').write_text(json.dumps({'before':record(data,rec),'after':record(a,rec),'events':[l for l in log.splitlines() if 'planet' in l.lower() or 'base' in l.lower()]},indent=2)+'\n')
if __name__=='__main__':
 eventcase('plague-small',1000,100)
 eventcase('plague-large',100000000,100)
 eventcase('civil-large',1000,100000000)
 eventcase('civil-rich',1000,100000000,1000000000)
 missingplanet()
