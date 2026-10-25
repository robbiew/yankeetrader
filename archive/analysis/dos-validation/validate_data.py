"""Decode and validate this preserved Yankee Trader 3.6 DOS run."""
from pathlib import Path
from collections import Counter, deque
import hashlib, json, math
ROOT=Path(__file__).resolve().parent
EVIDENCE=ROOT/'evidence'

def mbf32(raw):
    assert len(raw)==4
    mant=int.from_bytes(raw[:3],'little'); exponent=raw[3]
    if not exponent:return 0.0
    return (-1 if mant & 0x800000 else 1) * (1+(mant & 0x7fffff)/2**23) * 2.0**(exponent-129)

def record(data,number):
    raw=data[(number-1)*137:number*137]
    assert len(raw)==137
    return {'number':number,'text':raw[:41].decode('cp437').rstrip(' '),'fields':[mbf32(raw[41+4*i:45+4*i]) for i in range(23)],'tail_hex':raw[133:].hex()}

def main():
    data=(EVIDENCE/'YTDATA.DAT').read_bytes()
    assert len(data)==4151*137
    config=record(data,1)
    expected={49:500,53:51,57:3051,61:4051,65:25,69:1005,73:10,77:14,85:-1,93:4151,101:5,105:300,121:1000,125:6324}
    for offset,value in expected.items():assert mbf32(data[offset:offset+4])==value,(offset,value)
    assert config['text']=='YTSCORE.ASC'
    assert data[105:109]==bytes.fromhex('00001689')
    assert b'Ports needed to initiate Genesis: 450' in (EVIDENCE/'INIT.LOG').read_bytes()
    assert b'Ports needed to initiate Genesis: 300' in (EVIDENCE/'CONFIG.LOG').read_bytes()
    sectors=[record(data,51+s) for s in range(1,3001)]
    graph={s:[int(w) for w in r['fields'][:6] if w] for s,r in enumerate(sectors,1)}
    assert all(w==int(w) and 0<=w<=3000 for r in sectors for w in r['fields'][:6])
    seen={1};queue=deque([1])
    while queue:
        for w in graph[queue.popleft()]:
            if w not in seen:seen.add(w);queue.append(w)
    assert len(seen)==3000
    ports=[record(data,3051+p) for p in range(1,1001)]
    assert ports[0]['text']=='Earth'
    assert all(p['text'] for p in ports)
    tails=Counter(data[i+133:i+137].hex() for i in range(0,len(data),137))
    manifest=json.loads((EVIDENCE/'original-hashes.json').read_text())
    original_root=ROOT.parent.parent
    for name,digest in manifest.items():assert hashlib.sha256((original_root/name).read_bytes()).hexdigest()==digest,name
    result={'emulator':'DOSBox Staging 0.83.0','initialization_completed':True,'initial_maintenance_completed':True,
        'original_distribution_unchanged':True,'data_file_bytes':len(data),'record_bytes':137,'record_count':len(data)//137,
        'data_sha256':hashlib.sha256(data).hexdigest(),'genesis':{'initializer_prints':450,'configuration_displays':300,'stored_value':300,'file_offset':105,'bytes_hex':data[105:109].hex(),'gameplay_reset_trigger_tested':False},
        'verified_config_values_by_offset':expected,'config_record':config,'all_sector_warp_slots_valid':True,
        'sectors_reachable_from_earth':len(seen),'nonempty_port_names':len(ports),'record_tails':dict(tails),
        'samples':{'earth_sector':sectors[0],'earth_port':ports[0],'xannor_hq_sector':record(data,51+int(config['fields'][19]))},
        'generated_files':{name:{'bytes':(EVIDENCE/name).stat().st_size,'sha256':hashlib.sha256((EVIDENCE/name).read_bytes()).hexdigest()} for name in ['YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC']}}
    (EVIDENCE/'decoded-data.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['samples','config_record','generated_files','verified_config_values_by_offset']},indent=2))
if __name__=='__main__':main()
