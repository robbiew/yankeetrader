"""Independent date/clock replay, rejection and before-only boundary regressions."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock
from replay_maintenance_calendar import parameters,replay
from verify_maintenance_calendar import DEFAULT,FILES,verify


def inputs(name):
    d=DEFAULT/name
    before={n:gzip.decompress((d/('before-'+n+'.gz')).read_bytes())for n in FILES[:3]}
    trace=json.loads(gzip.decompress((d/'observed-a/host-time.json.gz').read_bytes()))
    return before,trace


class CalendarTests(unittest.TestCase):
    def test_complete_twelve_native_controls(self):
        self.assertEqual(verify()['byte_mismatches'],0)

    def test_all_profiles_synthesize_without_after_reads(self):
        for name in ('next-day','new-year','leap-day','noon'):
            with self.subTest(name=name):
                before,trace=inputs(name)
                original=Path.open
                def guarded(p,*args,**kwargs):
                    if p.name.startswith('after-'):raise AssertionError('synthesis read after target')
                    return original(p,*args,**kwargs)
                with mock.patch.object(Path,'open',guarded):actual,stats=replay(before,name,trace)
                expected={n:gzip.decompress((DEFAULT/name/'unobserved'/('after-'+n+'.gz')).read_bytes())for n in FILES}
                self.assertEqual(actual,expected)
                self.assertEqual(stats['npcs']['helper_calls']['h1'],42 if name=='noon' else 41)
                self.assertEqual(stats['npcs']['lottery_candidate']is not None,name=='noon')

    def test_refill_and_caller_corruptions_reject(self):
        for name in ('new-year','noon'):
            _,trace=inputs(name)
            for field in ('before-cycles','after-cycles','caller','port'):
                with self.subTest(name=name,field=field):
                    altered=copy.deepcopy(trace)
                    e=next(e for e in altered['events']if e['before']['cycles']==0)
                    if field=='before-cycles':e['before']['cycles']=1
                    elif field=='after-cycles':e['after']['cycles']+=1
                    elif field=='caller':e['before']['application_call']='00'*5;e['after']['application_call']='00'*5
                    else:e['before']['port_raw']='00000000';e['after']['port_raw']='00000000'
                    with self.assertRaises(AssertionError):parameters(name,altered)

    def test_invalid_inputs_and_inventory_reject(self):
        before,trace=inputs('noon')
        with self.assertRaises(ValueError):parameters('arbitrary',trace)
        altered=copy.deepcopy(trace);altered['events'].pop()
        with self.assertRaises(AssertionError):parameters('noon',altered)
        altered=dict(before);altered['YTDATA.DAT']=before['YTDATA.DAT'][:-1]
        with self.assertRaises((AssertionError,ValueError)):replay(altered,'noon',trace)
        _,leap=inputs('leap-day')
        with self.assertRaises(ValueError):replay(before,'leap-day',leap)

    def test_pinned_data_and_metadata_mutations_reject(self):
        for filename in ('after-YTDATA.DAT.gz','host-time.json.gz','capture.json','RETURN.LOG'):
            with self.subTest(filename=filename),tempfile.TemporaryDirectory()as temp:
                root=Path(temp)/'controls';shutil.copytree(DEFAULT,root)
                p=root/'noon/observed-a'/filename;p.write_bytes(p.read_bytes()+b'forged')
                with self.assertRaisesRegex(AssertionError,'pinned calendar artifact'):verify(root)


if __name__=='__main__':unittest.main()
