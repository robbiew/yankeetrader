"""Authenticate independent native controls and compare all six complete files."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import sys
from replay_maintenance_calendar import CASES,replay
from replay_maintenance_records import compare
from replay_qb_initializer import synthesize as initializer
from verify_initial_maintenance import BINARIES
from verify_maintenance_clock_neutral import HOST_SHA,verify as verify_parent
from verify_rng_clock import read_date,read_time

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-maint/calendar-controls'
SHA=lambda b:hashlib.sha256(b).hexdigest()
SOURCE_SHA='570e19521ece6d32697f84d90d4deb5a19136cb837b62dac6a03d9762f630156'
PINS_SHA='7382f01703145f2f2d37afab6a297bb18d226a5a65d6baf682f94ae63812ffc2'
FILES=('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC')
MODES=('unobserved','observed-a','observed-b')


def verify(root=DEFAULT):
    verify_parent()
    acquisition=ROOT/'research/yt-maint/calendar-acquisition'
    source_manifest=(acquisition/'manifest.json').read_bytes()
    assert SHA(source_manifest)==SOURCE_SHA,'immutable actual acquisition source manifest'
    sources=json.loads(source_manifest)
    assert {p.name for p in acquisition.iterdir()}==set(sources)|{'manifest.json'}
    for name,digest in sources.items():assert SHA((acquisition/name).read_bytes())==digest,'actual acquisition source'

    manifest=(ROOT/'research/yt-maint/calendar-pins.json').read_bytes()
    assert SHA(manifest)==PINS_SHA,'immutable independent calendar manifest'
    pins=json.loads(manifest)
    assert {p.name for p in root.iterdir()}==set(CASES),'complete calendar cases'
    actual_files={str(p.relative_to(root))for p in root.rglob('*')if p.is_file()}
    assert actual_files==set(pins),'complete retained calendar inventory'
    for name,digest in pins.items():assert SHA((root/name).read_bytes())==digest,'pinned calendar artifact: '+name
    comparisons=[]
    for name,(date,clock,helpers,refills)in CASES.items():
        case=root/name;day=datetime.datetime.strptime(date,'%m/%d/%Y').date()
        before={n:gzip.decompress((case/('before-'+n+'.gz')).read_bytes())for n in FILES[:3]}
        source,_=initializer(0xc805,day)
        assert before['YTDATA.DAT']==source,'fresh initializer agrees with independent source model'
        assert read_date((case/'init-DOSDATE.LOG').read_bytes())==day
        assert read_time((case/'init-DOSTIME.LOG').read_bytes())==0
        assert (case/'init-ANSWERS.TXT').read_bytes()==b'Y\r\n\r\n'
        assert b'<YT-INIT Normal Termination>'in(case/'init-INIT.LOG').read_bytes()
        assert(case/'init-INITRET.LOG').read_bytes()==b'INITIALIZER_RETURNED\r\n'
        input_meta=json.loads((case/'input.json').read_text())
        assert(input_meta['name'],input_meta['date'],input_meta['clock'],input_meta['binaries'])==(name,date,clock,BINARIES)
        outputs={}
        for mode in MODES:
            d=case/mode;meta=json.loads((d/'capture.json').read_text())
            assert(meta['recipe'],meta['name'],meta['mode'],meta['date'],meta['clock'])==('independent-maintenance-calendar-v1',name,mode,date,clock)
            assert meta['binaries']==BINARIES and meta['host_sha256']==HOST_SHA
            assert isinstance(meta['elapsed_seconds'],(int,float)) and 0<meta['elapsed_seconds']<30
            assert set(meta['files'])=={p.name for p in d.iterdir()}-{'capture.json'}
            for filename,digest in meta['files'].items():assert SHA((d/filename).read_bytes())==digest
            assert read_date((d/'DOSDATE.LOG').read_bytes())==day==read_date((d/'ENDDATE.LOG').read_bytes())
            start=read_time((d/'DOSTIME.LOG').read_bytes());finish=read_time((d/'ENDTIME.LOG').read_bytes())
            assert start==({'00:00:00':0,'12:34:00':45239.91}[clock]) and 0<finish-start<2,'native clock witnesses'
            assert(d/'RETURN.LOG').read_bytes()==b'PROGRAM_RETURNED\r\n'
            assert b'Daily Maintenance Completed OK'in(d/'TRACE.BIN').read_bytes()
            controller=json.loads((d/'controller.json').read_text())
            assert controller['success']is True and controller['forced']is False and controller['process_exited']is True and controller['exit_code']==0
            commands=['date '+date,'time '+clock,'date > DOSDATE.LOG','time > DOSTIME.LOG',
                      'ytmaint > TRACE.BIN','echo PROGRAM_RETURNED > RETURN.LOG','date > ENDDATE.LOG','time > ENDTIME.LOG']
            assert(d/'COMMANDS.TXT').read_text()=='\n'.join(commands)+'\n'
            argv=json.loads((d/'launch.json').read_text());mount=argv[8]
            assert mount.startswith('mount c ')and Path(mount[8:]).name==name+'-'+mode
            expected=['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[
                v for c in [mount,'c:']+commands+['exit']for v in('-c',c)]
            assert argv==expected,'exact isolated native invocation'
            outputs[mode]={n:gzip.decompress((d/('after-'+n+'.gz')).read_bytes())for n in FILES}
            if mode!='unobserved':
                assert controller['ready']is True and controller['detached_reason']=='process-terminated'
                assert 'cleanup_error'not in controller
                identity=controller['frida']
                assert identity['version']=='17.23.2'
                assert identity['module_sha256']=='408959cd8daa899370884ea4c7d763916b1ea2960ef4ce8118956870a600bda9'
                assert identity['package_sha256']=='7efb59d2050b7b6304e1617f463c4eb7b2f7cb7e3e80e677976825a76ee31e8d'
                loaded=(d/'loaded-observer.js').read_text()
                config_text,body=loaded.split(';\n',1)
                config=json.loads(config_text.removeprefix('const CONFIG='))
                assert config=={'observe':True,'output':str(Path(mount[8:])/'host-time.json')}
                assert body==(ROOT/'research/yt-maint/calendar-acquisition/observe_maintenance_clock.js').read_text()
                raw_observation=gzip.decompress((d/'host-time.json.gz').read_bytes())
                flushed=[m['payload']for m in controller['messages']if m['type']=='send'and m['payload']['kind']=='flushed']
                assert len(flushed)==1 and flushed[0]['bytes']==flushed[0]['expected_bytes']==len(raw_observation)
                observation=json.loads(raw_observation)
                actual,stats=replay(before,name,observation)
                comparisons.append((name,mode,actual,stats))
        assert outputs['unobserved']==outputs['observed-a']==outputs['observed-b'],'complete independent observation neutrality'
        for row in comparisons:
            if row[0]!=name:continue
            for mode in MODES:
                result=compare(outputs[mode],row[2])
                assert result['byte_mismatches']==0,'complete calendar replay without masks'
    return {'calendar_cases':4,'native_runs':12,'independent_observations':8,'complete_six_file_comparisons':24,
            'bytes_per_comparison':570059,'byte_mismatches':0}


if __name__=='__main__':print(verify(Path(sys.argv[1])if len(sys.argv)>1 else DEFAULT))
