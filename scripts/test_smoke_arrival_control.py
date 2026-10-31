"""Regression controls for selecting unaffected historical PTY fixtures."""
import tempfile
import unittest
from pathlib import Path
from smoke_arrival_control import DisruptionInterruption, MARKER, observe_disruption, reject_disruption, without_disruption

class ArrivalSmokeControl(unittest.TestCase):
    def test_retry_restores_exact_save_and_stable_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            data=Path(temp);p=data/'world.json';p.write_bytes(b'original\r\n');lock=data/'world.lock';lock.touch();inode=lock.stat().st_ino;calls=[]
            @without_disruption
            def run(data):
                calls.append(p.read_bytes())
                if len(calls)==1:
                    p.write_bytes(b'committed interrupted attempt');reject_disruption(MARKER)
                return 'quiet returned run'
            self.assertEqual(run(data),'quiet returned run');self.assertEqual(calls,[b'original\r\n']*2);self.assertEqual(lock.stat().st_ino,inode)
    def test_real_failure_is_not_retried(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'world.json';p.write_bytes(b'original');calls=[]
            @without_disruption
            def run(data):
                calls.append(1);raise AssertionError('real regression')
            with self.assertRaisesRegex(AssertionError,'real regression'):run(temp)
            self.assertEqual(len(calls),1)
    def test_dedicated_observer_does_not_filter_or_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'world.json';p.write_bytes(b'original')
            @without_disruption
            def run(data):p.write_bytes(b'saved arrival');reject_disruption(MARKER);return 'arrival'
            with observe_disruption():self.assertEqual(run(temp),'arrival')
            self.assertEqual(p.read_bytes(),b'saved arrival')
    def test_scanner_disruption_warning_is_separate_from_ordinary_sensors(self):
        reject_disruption(b'[ Sensors Activated ]\r\nSector: 2 | Warps: [3]\r\n** Space-time disruption detected! **')
        with self.assertRaises(DisruptionInterruption):
            reject_disruption(b'Danger scanner has detected the following in sector 9!\r\n** Space-time disruption detected! **')
        with observe_disruption():
            reject_disruption(b'Danger scanner has detected the following in sector 9!\r\n** Space-time disruption detected! **')
    def test_bounded_retries(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp)/'world.json').write_bytes(b'original');calls=[]
            @without_disruption
            def run(data):calls.append(1);raise DisruptionInterruption()
            with self.assertRaisesRegex(AssertionError,'128 bounded'):run(temp)
            self.assertEqual(len(calls),128)

if __name__=='__main__':unittest.main()
