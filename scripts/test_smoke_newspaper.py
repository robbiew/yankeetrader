"""Exercise rollover retries without a production test clock or midnight waits."""
import datetime
import unittest

from smoke_newspaper import run_on_stable_date


class DateRetryTests(unittest.TestCase):
    def test_rollover_discards_partial_fixture_and_restarts(self):
        now=[datetime.datetime(2026,10,28,23,59,59,tzinfo=datetime.timezone.utc)]
        fixtures=[]
        def fixture(guard):
            state=[]
            fixtures.append((guard.day,state))
            def game_session():
                state.append("partial old-day history")
                if len(fixtures)==1:
                    now[0]+=datetime.timedelta(seconds=2)
                    raise AssertionError("date-dependent terminal expectation failed")
                return "new-day complete history"
            return guard.run(game_session)
        result=run_on_stable_date(fixture,clock=lambda:now[0])
        self.assertEqual(result,"new-day complete history")
        self.assertEqual([d.isoformat() for d,_ in fixtures],["2026-10-28","2026-10-29"])
        self.assertIsNot(fixtures[0][1],fixtures[1][1])

    def test_real_failure_without_rollover_is_not_hidden(self):
        clock=lambda:datetime.datetime(2026,10,28,tzinfo=datetime.timezone.utc)
        calls=[]
        def fixture(guard):
            calls.append(1)
            return guard.run(lambda: self.fail("real regression"))
        with self.assertRaisesRegex(AssertionError,"real regression"):
            run_on_stable_date(fixture,clock=clock)
        self.assertEqual(len(calls),1)

    def test_persistent_rollover_exhausts_bounded_retries(self):
        now=[datetime.datetime(2026,10,28,tzinfo=datetime.timezone.utc)]
        calls=[]
        def fixture(guard):
            calls.append(1)
            return guard.run(lambda:now.__setitem__(0,now[0]+datetime.timedelta(days=1)))
        with self.assertRaisesRegex(AssertionError,"UTC date kept changing"):
            run_on_stable_date(fixture,clock=lambda:now[0])
        self.assertEqual(len(calls),3)


if __name__=="__main__":unittest.main()
