"""Independent provenance and outcome corruption tests for survivor-chain captures."""
import copy
import gzip
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

import verify_maintenance_survivor_chains as v


def put(world,record,offset,value):
    b=bytearray(world);at=(record-1)*137+offset;b[at:at+4]=v.encode(value);return bytes(b)


class SurvivorChainEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=v.DEFAULT;cls.observer=(cls.root/'acquisition/observe_maintenance_placement.js').read_text();cls.rows={};cls.obs={}
        for profile in v.PROFILES:
            for stage in v.STAGES:
                folder=cls.root/profile/stage/'observed-a';key=(profile,stage)
                cls.rows[key]={kind:{n:gzip.decompress((folder/(kind+'-'+n+'.gz')).read_bytes())for n in v.FILES}for kind in('before','after')}
                cls.obs[key]=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()))
        cls.key=('neutral-survivor','child-1');cls.combat=('mercenary-survivor','child-2')

    def semantics(self,key=None,outputs=None):
        key=self.key if key is None else key;row=self.rows[key]
        return v.verify_semantics(*key,row['before'],row['after']if outputs is None else outputs)

    def observation(self,key=None,ob=None,outputs=None):
        key=self.key if key is None else key;row=self.rows[key]
        return v.verify_observation(self.obs[key]if ob is None else ob,*key,row['before'],row['after']if outputs is None else outputs)

    def changed_news(self,old,new,key=None):
        key=self.combat if key is None else key;out=dict(self.rows[key]['after']);out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(old,new,1)
        self.assertNotEqual(out['YTNEWS.DAT'],self.rows[key]['after']['YTNEWS.DAT']);return out

    def test_complete_pinned_corpus_and_all_output_classifications(self):
        result=v.verify();self.assertEqual((result['profiles'],result['full_runs'],result['output_files'],result['inherited_file_links']),(4,48,288,288))
        self.assertTrue(all(stage['paired']['equal']for rows in result['stages'].values()for stage in rows.values()))

    def test_original_fight_threshold_is_double200_not_its_zero_single_prefix(self):
        from fractions import Fraction
        original=(v.ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
        self.assertEqual(v.SHA(original),v.clocks.GUESTS['YTMAINT.EXE'])
        raw=original[0xfd0+0x8916:0xfd0+0x891e]
        self.assertEqual(raw.hex(),'0000000000004888')
        self.assertEqual(v.clocks.mbf_fraction(raw[:4]),0)
        # Independent exact decode of this positive, normal eight-byte MBF.
        mantissa=int.from_bytes(raw[:7],'little')
        self.assertLess(mantissa,1<<55)
        double=Fraction((1<<55)+mantissa,1<<55)*(2**(raw[7]-129))
        self.assertEqual(double,200)
        self.assertEqual(v.clocks.mbf_fraction(original[0xfd0+0x891e:0xfd0+0x8922]),150)

    def test_saved_active_planet_clocks_cannot_disagree_with_original_callbacks(self):
        for offset,value in ((89,10),(41,999)):
            out=dict(self.rows[self.key]['after'])
            out['YTDATA.DAT']=put(out['YTDATA.DAT'],4052,offset,value)
            with self.subTest(offset=offset),self.assertRaises(AssertionError):
                self.observation(outputs=out)

    def test_independent_four_profile_two_day_recipe(self):
        self.assertEqual(set(v.PROFILES),{'mercenary-survivor','planet-survivor','neutral-survivor','mine-survivor'})
        self.assertTrue(all(rows==( ('11/05/2026','00:00:00'),('11/06/2026','00:00:00'))for rows in v.PROFILES.values()))

    def test_all_six_parent_files_inherit_corresponding_original_mode(self):
        for profile in v.PROFILES:
            for mode in v.MODES:
                folder=self.root/profile/'child-1'/mode
                before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in v.FILES}
                v.verify_inheritance(before,v.parent_inputs(profile,mode))

    def test_all_second_children_inherit_own_profile_and_mode(self):
        for profile in v.PROFILES:
            for mode in v.MODES:
                before={n:gzip.decompress((self.root/profile/'child-2'/mode/('before-'+n+'.gz')).read_bytes())for n in v.FILES}
                previous={n:gzip.decompress((self.root/profile/'child-1'/mode/('after-'+n+'.gz')).read_bytes())for n in v.FILES}
                v.verify_inheritance(before,previous)

    def test_every_changed_parent_file_rejects(self):
        before=self.rows[self.key]['before']
        for n in v.FILES:
            changed=dict(before);changed[n]+=b'changed'
            with self.subTest(name=n),self.assertRaises(AssertionError):v.verify_inheritance(changed,before)

    def test_missing_extra_and_cross_profile_parent_reject(self):
        before=self.rows[self.key]['before']
        for altered in(dict(before,extra=b''),{n:b for n,b in before.items()if n!='YTRMSG.DAT'},self.rows[('mine-survivor','child-1')]['before']):
            with self.assertRaises(AssertionError):v.verify_inheritance(altered,before)

    def test_original_parent_cannot_replace_first_child_output(self):
        key=('mercenary-survivor','child-2')
        with self.assertRaises(AssertionError):v.verify_inheritance(self.rows[key]['before'],v.parent_inputs(key[0],'observed-a'))

    def test_observer_difference_is_classified_without_mask_or_repair(self):
        out=self.rows[self.key]['after'];cases={m:dict(outputs=dict(out))for m in v.MODES}
        cases['observed-c']['outputs']['YTNEWS.DAT']+=b'changed'
        report=v.paired_outputs(cases);self.assertFalse(report['equal']);self.assertEqual(report['differences']['observed-c'],['YTNEWS.DAT'])
        cases.pop('unobserved-b')
        with self.assertRaises(AssertionError):v.paired_outputs(cases)

    def test_actual_three_and_four_planet_source_inventories(self):
        for key in self.rows:
            clocks=self.observation(key);self.assertEqual(clocks['active_planets'],4 if key[0]in('planet-survivor','mine-survivor')else 3)
            self.assertGreater(clocks['helper1'],0)

    def test_source_rng_bytes_are_complete_24bit_callback_witnesses(self):
        for raw in('00','000000ff'):
            ob=copy.deepcopy(self.obs[self.key])
            for side in('before','after'):ob['events'][1][side]['rng_raw']=raw
            with self.assertRaises(AssertionError):self.observation(ob=ob)
        ob=copy.deepcopy(self.obs[self.key]);ob['events'][1]['after']['rng_raw']='01000000'
        with self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_dropped_error_forced_or_false_exit_cannot_be_observation(self):
        for change in(dict(dropped=1),dict(errors=['lost']),dict(observe=False),dict(exit_code=1),dict(exit_code=False)):
            ob=copy.deepcopy(self.obs[self.key]);ob.update(change)
            with self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_missing_reordered_source_events_reject(self):
        for alter in('reverse','missing'):
            ob=copy.deepcopy(self.obs[self.key])
            if alter=='reverse':ob['events'][2],ob['events'][3]=ob['events'][3],ob['events'][2]
            else:ob['events'].pop(2)
            with self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_source_signature_cpu_and_caller_corruption_reject(self):
        for field,value in(('runtime_signature','0'*16),('cycle_max',100000),('caller_code','00')):
            ob=copy.deepcopy(self.obs[self.key]);event=next(e for e in ob['events']if e['before']['runtime_signature']is not None)
            for side in('before','after'):event[side][field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_actual_source_date_not_recipe_date_controls_saved_timestamp(self):
        ob=copy.deepcopy(self.obs[self.key]);event=next(e for e in ob['events']if e['function']==0x2a and e['before']['runtime_signature']is not None);event['after']['dx']=0x0b06
        with self.assertRaises(AssertionError):self.observation(ob=ob)

    def test_port_saved_clock_and_day_bind_their_raw_source(self):
        for offset,value in((101,999),(45,310)):
            out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],3657,offset,value)
            with self.assertRaises(AssertionError):self.observation(outputs=out)

    def test_public_and_score_text_clocks_bind_independent_source_calls(self):
        for n in('YTNEWS.DAT','YTSCORE.ASC'):
            out=dict(self.rows[self.key]['after']);out[n]=re.sub(rb'[0-9]{2}:[0-9]{2}:[0-9]{2}',b'00:00:09',out[n],count=1)
            self.assertNotEqual(out[n],self.rows[self.key]['after'][n])
            with self.assertRaises(AssertionError):self.observation(outputs=out)

    def survivor_trace(self,key=None,outputs=None,trace=None):
        key=self.combat if key is None else key;profile,stage=key;row=self.rows[key]
        raw=(self.root/profile/stage/'observed-a/TRACE.BIN').read_bytes()if trace is None else trace
        return v.verify_survivor_trace(profile,stage,row['before'],row['after']if outputs is None else outputs,raw)

    def test_distinct_publication_clocks_are_preserved_not_shared(self):
        row=self.observation();self.assertEqual(row['publication_clocks'],dict(news='00:00:00',score='00:00:01'))
        out=dict(self.rows[self.key]['after']);out['YTSCORE.ASC']=out['YTSCORE.ASC'].replace(b'00:00:01',b'00:00:00',1)
        self.assertNotEqual(out['YTSCORE.ASC'],self.rows[self.key]['after']['YTSCORE.ASC'])
        with self.assertRaises(AssertionError):self.observation(outputs=out)

    def test_inactive_human_fields_cannot_be_changed_under_zero_alias(self):
        out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],2,77,1)
        with self.assertRaises(AssertionError):self.semantics(outputs=out)

    def test_stale_parent_is_inherited_exactly_but_new_pointer_is_observed(self):
        key=('mercenary-survivor','child-1');row=self.rows[key]
        self.assertEqual(v.field(row['before']['YTDATA.DAT'],51+8,105),109)
        self.assertEqual(v.field(row['before']['YTDATA.DAT'],51+109,81),0)
        self.assertEqual(v.field(row['after']['YTDATA.DAT'],51+8,105),328)
        self.assertEqual(v.field(row['after']['YTDATA.DAT'],51+328,81),2)
        self.assertEqual(self.survivor_trace(key)['stale_pointers'],{})

    def test_actual_new_duplicate_pointers_are_retained(self):
        key=('mine-survivor','child-2');row=self.survivor_trace(key)
        self.assertEqual((row['raw_group_pointers'][2],row['raw_group_pointers'][19]),(1436,1436))
        self.assertEqual((row['raw_group_pointers'][13],row['raw_group_pointers'][15]),(2369,2369))
        out=dict(self.rows[key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],51+2,105,.5)
        with self.assertRaises(AssertionError):self.survivor_trace(key,outputs=out)

    def test_persistent_mines_are_observed_without_assuming_new_hits(self):
        for stage in v.STAGES:
            row=self.semantics(('mine-survivor',stage));self.assertEqual(row['observed_mines']['after'],{439:1,474:1,1169:1})
            self.assertEqual(row['fatal_mines'],[])
        self.assertEqual(self.semantics(('mine-survivor','child-1'))['observed_mines']['before'],{439:1,1169:1})
        key=('mine-survivor','child-2');out=dict(self.rows[key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],51+474,129,.5)
        with self.assertRaises(AssertionError):self.semantics(key,out)

    def test_zero_column_foreign_summary_is_real_and_reconciles(self):
        row=self.semantics(self.combat)
        self.assertIn(dict(first=1,second=0,tag='Xannor'),row['foreign_summaries'])
        self.assertEqual(len(row['foreign_summaries']),18)
        self.assertEqual(row['public_xannor_losses'],sum(e['first']for e in row['foreign_summaries']))
        self.assertEqual(row['observed_mercenary_losses'],sum(e['second']for e in row['foreign_summaries']))
        self.assertEqual(row['public_summary_mercenary_losses'],row['observed_mercenary_losses'])
        self.assertEqual(row['mercenary_attacks'],[])

    def test_changed_zero_or_positive_casualty_column_rejects(self):
        for old,new in((b'lost 1, dstrd 0',b'lost 1, dstrd 1'),(b'lost 6, dstrd 9',b'lost 7, dstrd 9'),(b'lost 6, dstrd 9',b'lost 6, dstrd 10')):
            with self.assertRaises(AssertionError):self.semantics(self.combat,self.changed_news(old,new))

    def test_unknown_or_missing_foreign_summary_cannot_be_guessed(self):
        for old,new in((b'lost 1, dstrd 0',b'lost 0, dstrd 0'),(b'(Xannor ftrs dstrd)',b'(Unknown ftrs dstrd)'),(b' *** Mercenaries: lost 1, dstrd 0 (Xannor ftrs dstrd)\r\n',b'')):
            with self.assertRaises(AssertionError):self.semantics(self.combat,self.changed_news(old,new))

    def test_console_public_outcomes_must_remain_identical(self):
        raw=(self.root/self.combat[0]/self.combat[1]/'observed-a/TRACE.BIN').read_bytes()
        changed=raw.replace(b'lost 6, dstrd 9',b'lost 7, dstrd 9',1);self.assertNotEqual(raw,changed)
        with self.assertRaises(AssertionError):self.survivor_trace(trace=changed)

    def test_console_first_count_binds_earlier_reported_defense_losses(self):
        raw=(self.root/self.combat[0]/self.combat[1]/'observed-a/TRACE.BIN').read_bytes()
        changed=raw.replace(b'93846 Mercenaries moving',b'93847 Mercenaries moving',1)
        self.assertNotEqual(changed,raw)
        with self.assertRaises(AssertionError):self.survivor_trace(trace=changed)

    def test_console_first_activation_binds_inherited_location(self):
        key=('mercenary-survivor','child-1');raw=(self.root/key[0]/key[1]/'observed-a/TRACE.BIN').read_bytes()
        changed=re.sub(rb'(Mercenaries moving from sector )([0-9]+)',rb'\g<1>3001',raw,count=1)
        self.assertNotEqual(changed,raw)
        with self.assertRaises(AssertionError):self.survivor_trace(key,trace=changed)

    def test_invented_combat_and_regeneration_cannot_explain_unchanged_world(self):
        out=self.changed_news(b'  -  Mercenary Report:',b'  -  Mercenary Report:\r\n *** 5 Mercenaries attacking 1 fighters beloning to The Xannor!\r\n *** The Mercenaries Won!',self.key)
        with self.assertRaises(AssertionError):self.semantics(outputs=out)
        out=self.changed_news(b'Regeneration is 0',b'Regeneration is 1',self.key)
        with self.assertRaises(AssertionError):self.semantics(outputs=out)

    def test_neutral_negative_defense_gate_preserves_location_and_force(self):
        key=('neutral-survivor','child-2');row=self.semantics(key);self.assertEqual(row['physical'][0],37)
        for changed in(put(self.rows[key]['after']['YTDATA.DAT'],51+854,81,36),put(put(self.rows[key]['after']['YTDATA.DAT'],51+854,81,0),51+855,81,37)):
            out=dict(self.rows[key]['after']);out['YTDATA.DAT']=changed
            with self.assertRaises(AssertionError):self.semantics(key,out)

    def test_planet_defense_public_counts_reconcile_actual_force(self):
        for stage in v.STAGES:
            row=self.semantics(('planet-survivor',stage));self.assertEqual(row['planet_deaths'],{'Route Haven':18})
            self.assertEqual(row['prior_physical'][-1]-row['physical'][-1],row['public_xannor_losses'])
        key=('planet-survivor','child-1');out=dict(self.rows[key]['after']);out['YTNEWS.DAT']=out['YTNEWS.DAT'].replace(b' *** Xannor fighters destroyed!\r\n',b'',1)
        with self.assertRaises(AssertionError):self.semantics(key,out)

    def test_changed_planet_identity_owner_link_or_ground_rejects(self):
        key=('planet-survivor','child-2');world=self.rows[key]['after']['YTDATA.DAT']
        for changed in(put(world,4053,73,-1),put(world,4053,77,0),put(world,51+854,93,0)):
            out=dict(self.rows[key]['after']);out['YTDATA.DAT']=changed
            with self.assertRaises(AssertionError):self.semantics(key,out)

    def test_public_survivor_score_cannot_be_relabelled(self):
        out=dict(self.rows[self.combat]['after']);out['YTSCORE.ASC']=re.sub(rb'([0-9],[0-9]{3},[0-9]{3})',b'9,999,999',out['YTSCORE.ASC'],count=1)
        self.assertNotEqual(out['YTSCORE.ASC'],self.rows[self.combat]['after']['YTSCORE.ASC'])
        with self.assertRaises(AssertionError):self.semantics(self.combat,out)

    def test_fractional_negative_or_unknown_physical_owner_rejects(self):
        world=self.rows[self.key]['after']['YTDATA.DAT']
        for changed in(put(world,900,81,.5),put(world,900,81,-1),put(put(world,900,81,1),900,85,2)):
            with self.assertRaises(AssertionError):v.physical(changed)

    def test_names_journal_rotation_and_private_notices_are_exact(self):
        for n in('YTNAME.DAT','YTYNEWS.DAT','YTRMSG.DAT'):
            out=dict(self.rows[self.key]['after']);out[n]+=b'fake'
            with self.assertRaises(AssertionError):self.semantics(outputs=out)

    def test_calendar_watermark_and_base_year_cannot_change(self):
        for offset,value in((81,1),(45,27)):
            out=dict(self.rows[self.key]['after']);out['YTDATA.DAT']=put(out['YTDATA.DAT'],1,offset,value)
            with self.assertRaises(AssertionError):self.semantics(outputs=out)

    def modified_case(self,mutate,key=None,mode='observed-a'):
        profile,stage=self.key if key is None else key;temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);folder=Path(temp.name)/mode;shutil.copytree(self.root/profile/stage/mode,folder)
        meta=json.loads((folder/'capture.json').read_text());mutate(folder,meta)
        meta['files']={p.name:v.SHA(p.read_bytes())for p in folder.iterdir()if p.name!='capture.json'};(folder/'capture.json').write_text(json.dumps(meta)+'\n')
        return folder,profile,stage,mode

    def case(self,values):
        folder,profile,stage,mode=values
        return v.verify_case(folder,profile,stage,mode,self.observer,None if stage=='child-1'else self.rows[(profile,'child-1')]['after'])

    def test_rebound_parent_profile_mode_and_parent_pins_reject(self):
        for change in(dict(parent='other'),dict(profile='mine-survivor'),dict(parent_mode='observed-b'),dict(parent_pins='0'*64)):
            with self.assertRaises(AssertionError):self.case(self.modified_case(lambda f,m:m.update(change)))

    def test_metadata_cannot_rebind_combat_lineage_to_clock_parent(self):
        for changed in(dict(v.PARENTS['mine-survivor']),dict(v.PARENTS['mercenary-survivor'],stage='child-1')):
            with self.assertRaises(AssertionError):self.case(self.modified_case(lambda f,m:m.update(parent_source=changed)))

    def test_rebound_child_input_byte_still_fails_actual_inheritance(self):
        def mutate(f,m):
            w=gzip.decompress((f/'before-YTDATA.DAT.gz').read_bytes());w=put(w,1,81,305);(f/'before-YTDATA.DAT.gz').write_bytes(gzip.compress(w,mtime=0));m['inputs']['YTDATA.DAT']=v.SHA(w)
        with self.assertRaises(AssertionError):self.case(self.modified_case(mutate))

    def test_rebound_guest_hash_cannot_replace_original(self):
        with self.assertRaises(AssertionError):self.case(self.modified_case(lambda f,m:m['guests'].update(**{'YTMAINT.EXE':'0'*64})))

    def test_rebound_launch_cannot_change_cpu_or_requested_clock(self):
        for old,new in(('cpu_cycles=200000','cpu_cycles=100000'),('time 00:00:00','time 00:00:09')):
            def mutate(f,m):
                argv=json.loads((f/'launch.json').read_text());argv[argv.index(old)]=new;m['argv']=argv;(f/'launch.json').write_text(json.dumps(argv))
            with self.assertRaises(AssertionError):self.case(self.modified_case(mutate))

    def test_rebound_actual_shell_clock_must_agree_with_request(self):
        def mutate(f,m):
            p=f/'DOSTIME.LOG';raw=p.read_bytes();changed=re.sub(rb'Current time: [^\r]+',b'Current time: 0:00:09.98am',raw,count=1);self.assertNotEqual(raw,changed);p.write_bytes(changed)
        with self.assertRaises(AssertionError):self.case(self.modified_case(mutate))

    def test_changed_loaded_observer_cannot_pass_rebound_hash(self):
        with self.assertRaises(AssertionError):self.case(self.modified_case(lambda f,m:(f/'loaded-observer.js').write_text((f/'loaded-observer.js').read_text()+'// altered\n')))

    def test_forced_controller_and_missing_flush_reject(self):
        def mutate(f,m):
            c=json.loads((f/'controller.json').read_text());c['forced']=True;m['controller']=c;(f/'controller.json').write_text(json.dumps(c))
        with self.assertRaises(AssertionError):self.case(self.modified_case(mutate))

    def test_missing_raw_return_witness_rejects_rebound_inventory(self):
        with self.assertRaises(AssertionError):self.case(self.modified_case(lambda f,m:(f/'RETURN.LOG').unlink()))

    def test_forged_manifest_cannot_admit_new_corpus(self):
        with tempfile.TemporaryDirectory()as tmp:
            (Path(tmp)/'pins.json').write_text('{"files":{}}')
            with self.assertRaises(AssertionError):v.verify(Path(tmp))


if __name__=='__main__':unittest.main()
