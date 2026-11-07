"""Portable stock-controller receipt and bounded natural-reap regression checks."""
import subprocess
from pathlib import Path
import unittest
from unittest.mock import patch

import test_capture_maintenance_departure as prior

ROOT=Path(__file__).resolve().parents[1]
CONTROLLER=ROOT/'scripts/capture_maintenance_stock_conversion.mjs'


class StockReceiptRegression(prior.FlushReceiptTests):
    """Run all seventeen established receipt corruptions against the NEW controller."""
    def setUp(self):
        super().setUp()
        controller=patch.object(prior,'CONTROLLER',CONTROLLER)
        controller.start();self.addCleanup(controller.stop)


class BoundedNaturalReap(unittest.TestCase):
    def node(self,code):
        source="import assert from 'node:assert/strict';const {waitForNaturalExit}=await import(process.argv[1]);\n"+code
        result=subprocess.run(['node','--input-type=module','-e',source,CONTROLLER.as_uri()],capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_initially_alive_then_naturally_gone_passes_after_event_loop_yield(self):
        self.node("""
let clock=0,checks=0,delays=[];
const result=await waitForNaturalExit(123,{timeoutMs:25,pollMs:10,now:()=>clock,pause:async ms=>{delays.push(ms);clock+=ms;},probe:()=>++checks<3});
assert.deepEqual(delays,[0,10,10]);assert.deepEqual(result,{checks:3,elapsed_ms:20});
""")

    def test_real_owned_short_child_is_reaped_without_forced_signal(self):
        self.node("""
const {spawn}=await import('node:child_process');const {once}=await import('node:events');
const child=spawn(process.execPath,['-e','setTimeout(()=>process.exit(0),30)'],{stdio:'ignore'});
const exit=once(child,'exit');
try{
 const result=await waitForNaturalExit(child.pid);
 const [code,signal]=await exit;assert.equal(code,0);assert.equal(signal,null);
 assert.ok(result.checks>=1&&result.elapsed_ms<=2000);
 assert.throws(()=>process.kill(child.pid,0),{code:'ESRCH'});
}finally{if(child.exitCode===null)child.kill('SIGKILL');}
""")

    def test_persistent_alive_rejects_at_finite_deadline(self):
        self.node("""
let clock=0,checks=0;
await assert.rejects(waitForNaturalExit(123,{timeoutMs:25,pollMs:10,now:()=>clock,pause:async ms=>{clock+=ms;},probe:()=>{checks++;return true;}}),/natural-exit deadline/);
assert.equal(clock,25);assert.equal(checks,4);
""")

    def test_process_disappearing_only_after_deadline_is_not_accepted(self):
        self.node("""
let clock=0,checks=0;
await assert.rejects(waitForNaturalExit(123,{timeoutMs:20,pollMs:10,now:()=>clock,pause:async()=>{clock=21;},probe:()=>{checks++;return false;}}),/natural-exit deadline/);
assert.equal(checks,0);
""")

    def test_esrch_is_the_only_process_error_accepted_as_disappearance(self):
        self.node("""
let yielded=false;
const result=await waitForNaturalExit(123,{now:()=>0,pause:async()=>{yielded=true;},probe:()=>{assert.ok(yielded);const e=Error('gone');e.code='ESRCH';throw e;}});
assert.equal(result.checks,1);
for(const code of ['EPERM','EINVAL','EIO']){
 const error=Error('probe '+code);error.code=code;
 await assert.rejects(waitForNaturalExit(123,{now:()=>0,pause:async()=>{},probe:()=>{throw error;}}),e=>e===error);
}
""")

    def test_wait_errors_propagate_without_becoming_success(self):
        self.node("""
const error=Error('event loop wait failed');
await assert.rejects(waitForNaturalExit(123,{now:()=>0,pause:async()=>{throw error;},probe:()=>false}),e=>e===error);
""")

    def test_unknown_liveness_values_cannot_be_falsy_success(self):
        self.node("""
for(const value of [undefined,null,0,1,'false'])await assert.rejects(waitForNaturalExit(123,{now:()=>0,pause:async()=>{},probe:()=>value}),/exact boolean/);
""")

    def test_time_budget_and_owned_pid_are_strictly_bounded(self):
        self.node("""
for(const pid of [0,-1,.5,true,'123'])await assert.rejects(waitForNaturalExit(pid),/positive owned PID/);
for(const timeoutMs of [0,-1,.5,2001,Infinity])await assert.rejects(waitForNaturalExit(123,{timeoutMs}),/at most 2000/);
for(const pollMs of [0,-1,.5,101,Infinity])await assert.rejects(waitForNaturalExit(123,{pollMs}),/at most 2000/);
""")

    def test_nonfinite_or_backward_clocks_are_rejected(self):
        self.node("""
await assert.rejects(waitForNaturalExit(123,{now:()=>NaN}),/finite monotonic/);
let calls=0;
await assert.rejects(waitForNaturalExit(123,{now:()=>calls++?9:10,pause:async()=>{},probe:()=>false}),/monotonic/);
""")

    def test_receipt_validator_and_owned_cleanup_are_unchanged(self):
        old=(ROOT/'scripts/capture_maintenance_departure.mjs').read_text();new=CONTROLLER.read_text()
        self.assertEqual(old[:old.index('export async function main')],new[:new.index('export async function waitForNaturalExit')])
        start='async function terminateOwned()';end='const outcome='
        self.assertEqual(old[old.index(start):old.index(end)],new[new.index(start):new.index(end)])
        self.assertIn('outcome.natural_exit_wait=await bounded(waitForNaturalExit(pid));',new)
        self.assertLess(new.index('const deadline=new Promise'),new.index('const frida=await bounded(import'))
        self.assertLess(new.index('await bounded(detached);'),new.index('outcome.natural_exit_wait='))
        self.assertIn("if(trace.exit_code!==0)throw new Error('capture did not exit naturally and cleanly');",new)
        self.assertIn('outcome.forced=forced;process.exitCode=1;',new)


if __name__=='__main__':unittest.main()
