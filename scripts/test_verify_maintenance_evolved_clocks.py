"""Independent evolved-clock provenance and semantic corruption controls."""
import copy
import gzip
import json
import re
from pathlib import Path
import shutil
import tempfile
import unittest

import verify_maintenance_evolved_clocks as v


def put(world,record,offset,value):
    b=bytearray(world);at=(record-1)*137+offset;b[at:at+4]=v.encode(value);return bytes(b)


class EvolvedClockEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=v.DEFAULT;cls.observer=(cls.root/'acquisition/observe_maintenance_placement.js').read_text();cls.rows={};cls.obs={}
        for profile in v.PROFILES:
            for stage in v.STAGES:
                folder=cls.root/profile/stage/'observed-a'
                cls.rows[(profile,stage)]={kind:{name:gzip.decompress((folder/(kind+'-'+name+'.gz')).read_bytes())for name in v.FILES}for kind in('before','after')}
                cls.obs[(profile,stage)]=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()))
        cls.key=('second-two','child-1')

    def observation(self,key=None,ob=None,outputs=None):
        key=self.key if key is None else key;row=self.rows[key]
        return v.verify_observation(self.obs[key]if ob is None else ob,*key,row['before'],row['after']if outputs is None else outputs)

    def test_complete_immutable_corpus(self):
        r=v.verify();self.assertEqual((r['profiles'],r['full_runs'],r['output_files'],r['inherited_file_links']),(4,48,288,288))
        self.assertEqual(set(r['stages']),set(v.PROFILES))

    def test_independent_profile_schedules(self):
        self.assertEqual(v.PROFILES['second-two'][0],('11/03/2026','00:00:02'))
        self.assertEqual(v.PROFILES['noon'][0],('11/03/2026','12:00:00'))
        self.assertEqual(v.PROFILES['catchup-eleven'][0],('11/13/2026','00:00:00'))
        self.assertEqual(v.PROFILES['new-year'],(('01/01/2027','00:00:00'),('01/02/2027','00:00:00')))

    def test_source_year_uses_retained_base_year(self):
        import datetime
        self.assertEqual(v.source_day(datetime.date(2027,1,1)),366)
        self.assertEqual(v.source_day(datetime.date(2027,1,2)),367)
        self.assertEqual(v.source_day(datetime.date(2026,11,13)),317)
        for date in(datetime.datetime(2027,1,1),datetime.date(2028,1,1)):
            with self.assertRaises(AssertionError):v.source_day(date)

    def test_all_first_children_inherit_verified_same_mode_parent(self):
        for profile in v.PROFILES:
            before=self.rows[(profile,'child-1')]['before'];self.assertEqual(before,v.parent_inputs('observed-a'));v.verify_inheritance(before,v.parent_inputs('observed-a'))

    def test_all_second_children_inherit_own_profile_outputs(self):
        for profile in v.PROFILES:v.verify_inheritance(self.rows[(profile,'child-2')]['before'],self.rows[(profile,'child-1')]['after'])

    def test_any_changed_inherited_file_rejects(self):
        before=self.rows[self.key]['before']
        for name in v.FILES:
            altered=dict(before);altered[name]+=b'changed'
            with self.subTest(name=name),self.assertRaises(AssertionError):v.verify_inheritance(altered,before)

    def test_missing_or_extra_inherited_file_rejects(self):
        before=self.rows[self.key]['before']
        for altered in({k:b for k,b in before.items()if k!='YTSCORE.ASC'},dict(before,other=b'')):
            with self.assertRaises(AssertionError):v.verify_inheritance(altered,before)

    def test_wrong_profile_parent_cannot_replace_second_child(self):
        with self.assertRaises(AssertionError):v.verify_inheritance(self.rows[('noon','child-2')]['before'],self.rows[('second-two','child-1')]['after'])

    def test_skip_generation_rejects(self):
        with self.assertRaises(AssertionError):v.verify_inheritance(self.rows[('second-two','child-2')]['before'],v.parent_inputs('observed-a'))

    def test_output_difference_is_classified_without_masks(self):
        outputs=self.rows[self.key]['after'];rows={m:dict(outputs=dict(outputs))for m in v.MODES}
        self.assertTrue(v.paired_outputs(rows)['equal'])
        rows['observed-c']['outputs']['YTDATA.DAT']+=b'changed'
        report=v.paired_outputs(rows);self.assertFalse(report['equal']);self.assertEqual(report['differences']['observed-c'],['YTDATA.DAT'])

    def test_missing_mode_cannot_be_classified_as_complete(self):
        rows={m:dict(outputs=self.rows[self.key]['after'])for m in v.MODES};rows.pop('attach-only')
        with self.assertRaises(AssertionError):v.paired_outputs(rows)

    def test_actual_source_clocks_authenticate_all_eight_stages(self):
        for key in self.rows:
            with self.subTest(key=key):
                r=self.observation(key);self.assertGreater(r['helper1'],0);self.assertEqual(r['active_planets'],4)

    def test_raw_rng_width_and_range_reject(self):
        for raw in('00','000000ff'):
            ob=copy.deepcopy(self.obs[self.key])
            for side in('before','after'):ob['events'][1][side]['rng_raw']=raw
            with self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_rng_callback_disagreement_rejects(self):
        ob=copy.deepcopy(self.obs[self.key]);event=ob['events'][1];n=int.from_bytes(bytes.fromhex(event['after']['rng_raw']),'little')^1;event['after']['rng_raw']=n.to_bytes(4,'little').hex()
        with self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_dropped_error_unobserved_or_nonzero_exit_rejects(self):
        for change in(dict(dropped=1),dict(errors=['bad']),dict(observe=False),dict(exit_code=1),dict(exit_code=False)):
            ob=copy.deepcopy(self.obs[self.key]);ob.update(change)
            with self.subTest(change=change),self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_reordered_or_missing_ordinal_rejects(self):
        for alter in('reverse','missing'):
            ob=copy.deepcopy(self.obs[self.key])
            if alter=='reverse':ob['events'][2],ob['events'][3]=ob['events'][3],ob['events'][2]
            else:ob['events'].pop(2)
            with self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_forged_source_clock_signature_rejects(self):
        ob=copy.deepcopy(self.obs[self.key]);event=next(e for e in ob['events']if e['before']['runtime_signature']is not None)
        for side in('before','after'):event[side]['runtime_signature']='0'*16
        with self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_wrong_actual_source_calendar_rejects(self):
        ob=copy.deepcopy(self.obs[self.key]);event=next(e for e in ob['events']if e['function']==0x2a and e['before']['runtime_signature']is not None);event['after']['dx']=0x0b04
        with self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_wrong_observed_cpu_rejects(self):
        ob=copy.deepcopy(self.obs[self.key])
        for side in('before','after'):ob['events'][10][side]['cycle_max']=100000
        with self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_saved_raw_port_time_cannot_be_replaced(self):
        out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],3657,101,0)
        self.assertNotEqual(out['YTDATA.DAT'],self.rows[self.key]['after']['YTDATA.DAT'])
        with self.assertRaises(AssertionError):self.observation(outputs=out)

    def test_saved_port_date_cannot_use_gregorian_doy_at_new_year(self):
        key=('new-year','child-1');out=dict(self.rows[key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],3052,45,1)
        with self.assertRaises(AssertionError):self.observation(key,outputs=out)

    def test_news_and_score_headers_bind_own_source_clocks(self):
        for name in('YTNEWS.DAT','YTSCORE.ASC'):
            out=dict(self.rows[self.key]['after']);out[name]=out[name].replace(b'00:00:02',b'00:00:07',1)
            self.assertNotEqual(out[name],self.rows[self.key]['after'][name])
            with self.subTest(name=name),self.assertRaises(AssertionError):self.observation(outputs=out)

    def test_wrong_watermark_rejects(self):
        out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],1,81,1)
        with self.assertRaises(AssertionError):v.verify_semantics(*self.key,self.rows[self.key]['before'],out)

    def test_changed_base_year_rejects(self):
        key=('new-year','child-1');out=dict(self.rows[key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],1,45,27)
        with self.assertRaises(AssertionError):v.verify_semantics(*key,self.rows[key]['before'],out)

    def test_physical_fraction_or_negative_rejects(self):
        w=self.rows[self.key]['after']['YTDATA.DAT']
        for value in(-1,.5):
            with self.assertRaises(AssertionError):v.physical(put(w,900,81,value))

    def test_unknown_physical_owner_rejects(self):
        w=put(self.rows[self.key]['after']['YTDATA.DAT'],900,81,1);w=put(w,900,85,2)
        with self.assertRaises(AssertionError):v.physical(w)

    def test_score_must_match_actual_saved_survivors(self):
        key=('noon','child-1');out=dict(self.rows[key]['after']);out['YTSCORE.ASC']=out['YTSCORE.ASC'].replace(b'830,000',b'830,001')
        self.assertNotEqual(out['YTSCORE.ASC'],self.rows[key]['after']['YTSCORE.ASC'])
        with self.assertRaises(AssertionError):v.verify_semantics(*key,self.rows[key]['before'],out)

    def test_name_rotation_or_private_invention_rejects(self):
        for name in('YTNAME.DAT','YTYNEWS.DAT','YTRMSG.DAT'):
            out=dict(self.rows[self.key]['after']);out[name]+=b'fake'
            with self.subTest(name=name),self.assertRaises(AssertionError):v.verify_semantics(*self.key,self.rows[self.key]['before'],out)

    def semantics(self,key,outputs=None):
        row=self.rows[key]
        return v.verify_semantics(*key,row['before'],row['after']if outputs is None else outputs)

    def test_public_casualties_reconcile_selected_outcomes(self):
        mine=self.semantics(('second-two','child-2'))
        self.assertEqual(mine['public_xannor_losses'],6)
        self.assertEqual(mine['fatal_mines'],[dict(sector=980,force=6,spent_mines=1)])
        noon=self.semantics(('noon','child-1'))
        self.assertEqual((noon['public_xannor_losses'],noon['planet_deaths']),(1700,{'The Wanderer':14}))
        year=self.semantics(('new-year','child-2'))
        self.assertEqual((year['public_xannor_losses'],year['planet_deaths']),(362,{'Mercenary Base':4}))

    def test_changed_public_casualty_count_rejects(self):
        key=('noon','child-1');out=dict(self.rows[key]['after'])
        out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(b'*** 24 Xannor',b'*** 25 Xannor',1)
        self.assertNotEqual(out['YTNEWS.DAT'],self.rows[key]['after']['YTNEWS.DAT'])
        with self.assertRaises(AssertionError):self.semantics(key,out)

    def test_incomplete_fatal_public_pair_rejects(self):
        key=('noon','child-1');out=dict(self.rows[key]['after'])
        out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(b' *** Xannor fighters destroyed!\r\n',b'',1)
        with self.assertRaises(AssertionError):self.semantics(key,out)

    def test_unknown_public_battle_rejects_without_guessing(self):
        key=('noon','child-1')
        for changed in(b'Unknown Planet',b'The Wanderer was destroyed'):
            out=dict(self.rows[key]['after']);out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(b'The Wanderer',changed,1)
            with self.subTest(changed=changed),self.assertRaises(AssertionError):self.semantics(key,out)

    def test_fatal_mine_requires_claimed_sector_expenditure(self):
        key=('second-two','child-2');out=dict(self.rows[key]['after'])
        out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(b'sector 980!',b'sector 981!',1)
        with self.assertRaises(AssertionError):self.semantics(key,out)

    def test_restored_claimed_mine_rejects(self):
        key=('second-two','child-2');out=dict(self.rows[key]['after'])
        old=v.field(self.rows[key]['before']['YTDATA.DAT'],51+980,129)
        out['YTDATA.DAT']=put(out['YTDATA.DAT'],51+980,129,old)
        with self.assertRaises(AssertionError):self.semantics(key,out)

    def test_unreported_physical_loss_rejects(self):
        key=('noon','child-1');out=dict(self.rows[key]['after'])
        out['YTNEWS.DAT']=out['YTNEWS.DAT'].split(b'\r\n',1)[0]+b'\r\n'
        with self.assertRaises(AssertionError):self.semantics(key,out)

    def test_other_profile_news_cannot_explain_survivors(self):
        key=('second-two','child-1');out=dict(self.rows[key]['after'])
        out['YTNEWS.DAT']=self.rows[('noon','child-1')]['after']['YTNEWS.DAT']
        with self.assertRaises(AssertionError):self.semantics(key,out)

    def modified_case(self,mutate,profile='second-two',stage='child-1',mode='observed-a'):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);folder=Path(temp.name)/mode;shutil.copytree(self.root/profile/stage/mode,folder)
        meta=json.loads((folder/'capture.json').read_text());mutate(folder,meta)
        meta['files']={p.name:v.SHA(p.read_bytes())for p in folder.iterdir()if p.name!='capture.json'};(folder/'capture.json').write_text(json.dumps(meta)+'\n')
        return folder,profile,stage,mode

    def case(self,values):
        folder,profile,stage,mode=values
        return v.verify_case(folder,profile,stage,mode,self.observer,None if stage=='child-1'else self.rows[(profile,'child-1')]['after'])

    def test_rebound_metadata_cannot_change_parent(self):
        values=self.modified_case(lambda f,m:m.update(parent='other'))
        with self.assertRaises(AssertionError):self.case(values)

    def test_rebound_metadata_cannot_change_parent_mode(self):
        values=self.modified_case(lambda f,m:m.update(parent_mode='unobserved-a'))
        with self.assertRaises(AssertionError):self.case(values)

    def test_rebound_metadata_cannot_change_guests(self):
        values=self.modified_case(lambda f,m:m['guests'].update(**{'YTMAINT.EXE':'0'*64}))
        with self.assertRaises(AssertionError):self.case(values)

    def test_rebound_hashes_cannot_patch_inherited_world(self):
        def mutate(f,m):
            w=gzip.decompress((f/'before-YTDATA.DAT.gz').read_bytes());w=put(w,2853,81,6553);(f/'before-YTDATA.DAT.gz').write_bytes(gzip.compress(w,mtime=0));m['inputs']['YTDATA.DAT']=v.SHA(w)
        with self.assertRaises(AssertionError):self.case(self.modified_case(mutate))

    def test_rebound_launch_cannot_change_cpu(self):
        def mutate(f,m):
            argv=json.loads((f/'launch.json').read_text());argv[4]='cpu_cycles=100000';m['argv']=argv;(f/'launch.json').write_text(json.dumps(argv))
        with self.assertRaises(AssertionError):self.case(self.modified_case(mutate))

    def test_rebound_launch_cannot_change_request_clock(self):
        def mutate(f,m):
            argv=json.loads((f/'launch.json').read_text());i=argv.index('time 00:00:02');argv[i]='time 00:00:00';m['argv']=argv;(f/'launch.json').write_text(json.dumps(argv))
        with self.assertRaises(AssertionError):self.case(self.modified_case(mutate))

    def test_rebound_actual_shell_clock_cannot_replace_request(self):
        def mutate(f,m):
            p=f/'DOSTIME.LOG';p.write_bytes(re.sub(rb'Current time: [^\r]+',b'Current time: 0:00:09.98am',p.read_bytes(),count=1))
        values=self.modified_case(mutate)
        # Mutation must be actual, not a test that merely rechecks valid input.
        f=values[0];self.assertNotEqual((f/'DOSTIME.LOG').read_bytes(),(self.root/'second-two/child-1/observed-a/DOSTIME.LOG').read_bytes())
        with self.assertRaises(AssertionError):self.case(values)

    def test_changed_loaded_observer_rejects_despite_rebound_hash(self):
        values=self.modified_case(lambda f,m:(f/'loaded-observer.js').write_text((f/'loaded-observer.js').read_text()+'// altered\n'))
        with self.assertRaises(AssertionError):self.case(values)

    def test_forced_exit_or_missing_flush_cannot_pass(self):
        def mutate(f,m):
            c=json.loads((f/'controller.json').read_text());c['forced']=True;m['controller']=c;(f/'controller.json').write_text(json.dumps(c))
        with self.assertRaises(AssertionError):self.case(self.modified_case(mutate))

    def test_missing_artifact_rejects_despite_rebound_inventory(self):
        values=self.modified_case(lambda f,m:(f/'RETURN.LOG').unlink())
        with self.assertRaises(AssertionError):self.case(values)

    def test_missing_stage_mode_or_source_manifest_entry_rejects(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'pins.json';p.write_bytes(b'{"files":{}}')
            with self.assertRaises(AssertionError):v.verify(Path(tmp))


if __name__=='__main__':unittest.main()
