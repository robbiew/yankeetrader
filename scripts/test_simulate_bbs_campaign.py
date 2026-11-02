"""Campaign failures must not become successful acceptance evidence."""
import subprocess
import unittest
from unittest.mock import Mock

from simulate_bbs_campaign import Caller


class CarrierLossTests(unittest.TestCase):
    def caller(self):
        caller=Caller.__new__(Caller)
        caller.proc=Mock();caller.client=Mock();caller.thread=Mock();caller.save=Mock()
        return caller

    def test_hung_carrier_loss_is_failure_after_cleanup(self):
        caller=self.caller()
        caller.proc.wait.side_effect=[subprocess.TimeoutExpired('yt',5),0]
        with self.assertRaisesRegex(AssertionError,'carrier loss'):
            caller.disconnect()
        caller.proc.terminate.assert_called_once()
        caller.save.assert_called_once()

    def test_natural_exit_passes_without_termination(self):
        caller=self.caller();caller.proc.wait.return_value=0
        caller.disconnect()
        caller.proc.terminate.assert_not_called()
        caller.save.assert_called_once()


from pathlib import Path
import json
import tempfile
import threading
from simulate_bbs_campaign import Campaign, CampaignExhausted, run_campaigns


RECEIPT=('A *-BLACK HOLE-* grabs you! Forced warp saved: sector 3 -> 7; heat 31/31; recharge 498 turns; meltdown true.\n'
         'Disruption arrival saved: final sector 7; total action turns spent 499; remaining 0. Queued travel stopped.')


class ExhaustionTests(unittest.TestCase):
    def campaign(self,turns=0,sector=7):
        c=Campaign.__new__(Campaign);c.lock=threading.Lock();c.actions=[]
        c.world=Mock(return_value={'Players':{'1':{'Identity':'door32:campaign-bbs:101','Turns':turns,'Sector':sector}}})
        return c

    def test_only_committed_receipt_with_matching_save_is_retryable(self):
        caller=Mock(uid=101,index=1,alias='Atlas')
        with self.assertRaises(CampaignExhausted):self.campaign().record(caller,'m 3',RECEIPT)
        for turns,sector in [(1,7),(0,8)]:
            with self.subTest(turns=turns,sector=sector),self.assertRaises(AssertionError):
                self.campaign(turns,sector).record(caller,'m 3',RECEIPT)
        for text in ['no turns left','timeout',RECEIPT.split('\n')[0]]:
            self.campaign().record(caller,'m 3',text)

    def test_invariant_failure_is_not_reclassified_by_receipt(self):
        c=self.campaign();c.world.side_effect=AssertionError('invalid money')
        with self.assertRaisesRegex(AssertionError,'invalid money'):
            c.record(Mock(uid=101,index=1),'m 3',RECEIPT)


class RetryTests(unittest.TestCase):
    def setup_campaigns(self,root,results,report_failure=False):
        made=[]
        def factory(path,binary,seed):
            path.mkdir();c=Mock(root=path,callers=[Mock()],findings=[])
            c.report=Mock(side_effect=AssertionError('race or forced exit') if report_failure else None)
            made.append(c);return c
        def play(c):
            result=results[len(made)-1]
            if isinstance(result,BaseException):raise result
            return result
        return made,lambda:run_campaigns(root,Path('unused'),146,make_campaign=factory,play=play)

    def test_exhaustion_restarts_full_fixture_and_retains_attempt_outcomes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'campaign'
            made,run=self.setup_campaigns(root,[CampaignExhausted('receipt proven'),{'winner':'Atlas'}])
            self.assertEqual(run(),{'winner':'Atlas'})
            self.assertEqual([c.root.name for c in made],['attempt-1','attempt-2'])
            for c in made:c.callers[0].finish.assert_called_once();c.report.assert_called_once()
            summary=json.loads((root/'summary.json').read_text())
            self.assertEqual([x['outcome']for x in summary['attempts']],['exhausted','passed'])
            self.assertEqual(summary['winning_attempt'],'attempt-2')

    def test_persistent_exhaustion_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            made,run=self.setup_campaigns(Path(tmp)/'campaign',[CampaignExhausted('receipt proven')]*3)
            with self.assertRaisesRegex(AssertionError,'all 3 fresh'):run()
            self.assertEqual(len(made),3)

    def test_assertions_timeouts_and_cleanup_failures_never_retry(self):
        for error in [AssertionError('privacy leak'),subprocess.TimeoutExpired('yt',5),CampaignExhausted('receipt proven')]:
            with self.subTest(error=error),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/'campaign'
                cleanup=isinstance(error,CampaignExhausted)
                made,run=self.setup_campaigns(root,[error],report_failure=cleanup)
                with self.assertRaises(AssertionError if cleanup else type(error)):run()
                self.assertEqual(len(made),1)
                self.assertEqual(json.loads((root/'summary.json').read_text())['outcome'],'failed')


class ExitAuditTests(unittest.TestCase):
    def test_carrier_loss_forced_or_abnormal_exit_fails_all_attempts(self):
        for outcome in ['exhausted',{'winner':'Atlas'}]:
            for code,forced in [(0,False),(0,True),(-15,True),(1,False)]:
                with self.subTest(outcome=outcome,code=code,forced=forced),tempfile.TemporaryDirectory() as tmp:
                    root=Path(tmp);data=root/'world';data.mkdir();(data/'world.json').write_text('{}')
                    binary=root/'yt';binary.write_bytes(b'fake binary')
                    c=Campaign.__new__(Campaign)
                    c.root=root;c.data=data;c.binary=binary;c.actions=[];c.findings=[];c.started=0
                    c.snapshots_checked=1;c.peak_processes=1;c.driver_source=b'driver';c.runtime_patch=b'';c.initial=b'{}'
                    node=Mock(index=1,uid=1,classic=False,endpoint=('127.0.0.1',1),expected_exit='carrier-loss',forced_stop=forced,hazards=set(),node=root)
                    node.proc.poll.return_value=code;c.callers=[node]
                    if code==0 and not forced:
                        self.assertEqual(c.report(outcome)['outcome'],outcome)
                    else:
                        with self.assertRaises(AssertionError):c.report(outcome)
                        self.assertEqual(json.loads((root/'summary.json').read_text())['outcome'],'failed')


if __name__=='__main__':unittest.main()
