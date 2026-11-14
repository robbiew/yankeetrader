"""Exercise real owned-process cleanup with a fake stalled Frida adapter."""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FAKE = r'''
import fs from 'node:fs';
import {spawn} from 'node:child_process';
const stall=()=>new Promise(()=>{});
const phase=process.env.TEST_STALL;
let child;
let message;
export async function getLocalDevice(){return {
 output:{connect(){}},
 async spawn(){
  child=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'});
  fs.writeFileSync(process.env.TEST_PID,String(child.pid));
  return child.pid;
 },
 async attach(){
  if(phase==='attach')return stall();
  return {detached:{connect(){}},async createScript(){
   if(phase==='create')return stall();
   return {message:{connect(fn){message=fn;}},async load(){
    if(phase==='load')return stall();
    if(phase!=='ready')message({type:'send',payload:{kind:'ready'}});
   }};
  }};
 },
 async resume(){if(phase==='resume')return stall();},
 async kill(){throw new Error('cleanup must not depend on a responsive Frida device');}
};}
'''


@unittest.skipUnless(shutil.which('node'), 'Node required for controller cleanup regression')
class CaptureDeadlineTests(unittest.TestCase):
    def test_initialization_and_execution_stalls_kill_owned_target(self):
        for phase in ('attach', 'create', 'load', 'ready', 'resume', 'execution'):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as temp:
                root=Path(temp); module=root/'frida/build/src/frida.mjs'; module.parent.mkdir(parents=True)
                (root/'frida/package.json').write_text(json.dumps({'name':'frida','version':'17.23.2'}))
                module.write_text(FAKE)
                work=root/'capture';work.mkdir();(work/'launch.json').write_text('["unused-target"]')
                observer=root/'observer.js';observer.write_text('// test observer')
                pidfile=root/'owned.pid'
                result=subprocess.run(['node',str(ROOT/'scripts/capture_maintenance_clock_neutral.mjs'),
                    str(module),str(work),str(observer),'observed','300'],
                    env={**os.environ,'TEST_STALL':phase,'TEST_PID':str(pidfile)},capture_output=True,timeout=5)
                self.assertEqual(result.returncode,1,result.stderr.decode())
                report=json.loads((work/'controller.json').read_text())
                # Cold Node startup precedes the controller's deadline timer.
                # Keep the five-second external hang guard, but measure the
                # initialization/deadline/owned-cleanup interval inside Node.
                started=datetime.datetime.fromisoformat(report['started'].replace('Z','+00:00'))
                finished=datetime.datetime.fromisoformat(report['finished'].replace('Z','+00:00'))
                elapsed=(finished-started).total_seconds()
                self.assertGreaterEqual(elapsed,0)
                self.assertLess(elapsed,4,report)
                self.assertFalse(report['success']);self.assertTrue(report['forced'])
                self.assertTrue(report['process_exited']);self.assertNotIn('cleanup_error',report)
                self.assertIn('including initialization',report['error'])
                with self.assertRaises(ProcessLookupError):os.kill(int(pidfile.read_text()),0)


if __name__=='__main__':unittest.main()
