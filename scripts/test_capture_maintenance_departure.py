"""Portable exit-flush receipt corruption checks; no Frida or DOS process runs."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
CONTROLLER=ROOT/'scripts/capture_maintenance_departure.mjs'
OBSERVER=ROOT/'scripts/observe_maintenance_departure.js'
ENC=lambda value:(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode()


class FlushReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)
        self.trace=dict(recipe='host-dos-placement-cache-observer-v1',observe=True,module=dict(path='/fixture/é'),exit_code=0,events=[dict(ordinal=1)],errors=[],dropped=0)
        raw=ENC(self.trace)
        self.receipt=dict(recipe='departure-exit-flush-receipt-v1',exit_code=0,bytes=len(raw),expected_bytes=len(raw),events=1,errors=0,dropped=0)
        self.messages=[];self.mode='observed'

    def run_validation(self,ok=True,body=None,receipt=None):
        (self.path/'host-time.json').write_bytes(ENC(self.trace)if body is None else body)
        if receipt is not False:(self.path/'host-flush.json').write_bytes(ENC(self.receipt)if receipt is None else receipt)
        code="const {validateFlush}=await import(process.argv[1]);const x=validateFlush(process.argv[2],JSON.parse(process.argv[4]),process.argv[3]);console.log(JSON.stringify({acknowledged:x.acknowledged,bytes:x.receipt.bytes}));"
        result=subprocess.run(['node','--input-type=module','-e',code,CONTROLLER.as_uri(),str(self.path),self.mode,json.dumps(self.messages)],capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode==0,ok,result.stderr)
        return result

    def ack(self):return dict(type='send',payload={**{k:v for k,v in self.receipt.items()if k!='recipe'},'kind':'flushed'})

    def test_complete_synchronous_receipt_accepts_lost_async_ack(self):
        result=self.run_validation();self.assertFalse(json.loads(result.stdout)['acknowledged'])

    def test_complete_agreeing_async_ack_is_also_accepted(self):
        self.messages=[self.ack()];self.assertTrue(json.loads(self.run_validation().stdout)['acknowledged'])

    def test_utf8_byte_count_does_not_use_javascript_character_length(self):
        self.assertGreater(len(ENC(self.trace)),len(ENC(self.trace).decode()))
        self.receipt['bytes']=self.receipt['expected_bytes']=len(ENC(self.trace).decode());self.run_validation(False)

    def test_missing_receipt_is_never_a_success(self):self.run_validation(False,receipt=False)
    def test_partial_trace_is_rejected(self):self.run_validation(False,body=ENC(self.trace)[:-5])
    def test_missing_trace_newline_is_rejected(self):self.run_validation(False,body=ENC(self.trace)[:-1])
    def test_partial_receipt_is_rejected(self):self.run_validation(False,receipt=ENC(self.receipt)[:-5])
    def test_missing_receipt_newline_is_rejected(self):self.run_validation(False,receipt=ENC(self.receipt)[:-1])

    def test_actual_byte_and_count_fields_must_all_agree(self):
        for field in('exit_code','bytes','expected_bytes','events','errors','dropped'):
            old=self.receipt[field];self.receipt[field]=old+1
            with self.subTest(field=field):self.run_validation(False)
            self.receipt[field]=old

    def test_receipt_fields_are_exact_nonnegative_integers(self):
        for value in(-1,.5,True,'1',None):
            self.receipt['events']=value
            with self.subTest(value=value):self.run_validation(False)

    def test_unknown_schema_fields_are_rejected(self):
        self.receipt['extra']=0;self.run_validation(False)

    def test_trace_errors_drops_and_nonzero_exit_reject_even_matching_receipt(self):
        for field,value,receiptfield in(('errors',['durability warning'],'errors'),('dropped',1,'dropped'),('exit_code',1,'exit_code')):
            original=copy.deepcopy(self.trace);prior=copy.deepcopy(self.receipt);self.trace[field]=value
            self.receipt[receiptfield]=len(value)if isinstance(value,list)else value
            self.receipt['bytes']=self.receipt['expected_bytes']=len(ENC(self.trace))
            with self.subTest(field=field):self.run_validation(False)
            self.trace=original;self.receipt=prior

    def test_any_observer_error_message_rejects(self):
        self.messages=[dict(type='error',description='observer failed')];self.run_validation(False)

    def test_disagreeing_or_duplicate_async_ack_rejects(self):
        self.messages=[self.ack()];self.messages[0]['payload']['bytes']+=1;self.run_validation(False)
        self.messages=[self.ack(),self.ack()];self.run_validation(False)

    def test_attach_only_requires_zero_events_and_false_observe(self):
        self.mode='attach-only';self.trace['observe']=False;self.trace['events']=[];self.receipt['events']=0
        self.receipt['bytes']=self.receipt['expected_bytes']=len(ENC(self.trace));self.run_validation()

    def test_dos_event_acquisition_and_exit_hook_identity_are_unchanged(self):
        old=(ROOT/'scripts/observe_maintenance_placement.js').read_text();new=OBSERVER.read_text()
        self.assertEqual(old.split('function flush(code){')[0],new.split('function flush(code){')[0])
        suffix="for(const name of ['exit','_exit'])"
        self.assertEqual(old[old.index(suffix):],new[new.index(suffix):])

    def test_observer_requires_full_body_and_receipt_write_before_send(self):
        code=r"""
import fs from 'node:fs';import vm from 'node:vm';
const source=fs.readFileSync(process.argv[1],'utf8');
const start=source.indexOf('function flush(code){'),end=source.indexOf("for(const name of ['exit','_exit'])",start);
for(const short of [null,'body','receipt']){
 let writes=0,acks=[],files={},names={},next=1;
 const context={flushed:false,CONFIG:{observe:true,output:'body',flush_output:'receipt'},identity:{path:'é'},events:[{}],errors:[],dropped:0,
 Memory:{allocUtf8String:x=>x},creat:name=>{const fd=next++;names[fd]=name;return fd;},close:()=>0,
 write:(fd,text,count)=>{writes++;const bytes=Buffer.from(text);if(bytes.length!==count)throw Error('wrong UTF8 byte allowance');const actual=names[fd]===short?count-1:count;files[names[fd]]=bytes.subarray(0,actual);return actual;},send:x=>acks.push(x)};
 vm.createContext(context);vm.runInContext(source.slice(start,end),context);
 let failed=false;try{context.flush(0);}catch(e){failed=true;}
 if(short!==null){if(!failed||acks.length)throw Error('short write accepted');if(short==='body'&&writes!==1)throw Error('receipt after short body');}
 else if(failed||acks.length!==1||writes!==2)throw Error('complete receipt failed');
}
"""
        result=subprocess.run(['node','--input-type=module','-e',code,str(OBSERVER)],capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
