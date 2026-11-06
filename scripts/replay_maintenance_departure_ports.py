"""Before-only port writer for the two-day departure continuation.

Departure edits change no port records. The established bounded midnight survivor writer
is reused unchanged; all 1000 port calendars and raw minutes remain explicit.
The actual zero/two/four-second clocks remain separate inputs, including the
retained observed cohort whose raw port outputs differ from unobserved controls.
No capture files or expected outputs are opened during synthesis.
"""
from replay_maintenance_survivor_ports import replay_ports as _replay_ports
from replay_qb_graph import mbf


def replay_ports(before,days,timer_minutes):
    if type(before)is not bytes or len(before)!=4151*137:
        raise ValueError('complete immutable departure before-world required')
    if (before[(4054-1)*137:(4054-1)*137+41]!=b'Departure Cache'.ljust(41,b' ')or
            mbf.get(before,4054,73)!=0 or mbf.get(before,4054,85)!=15 or
            [s for s in range(1,3001)if mbf.get(before,51+s,93)==3]not in([2999],[3000])):
        raise ValueError('actual neutral departure fixture and unique physical link required')
    return _replay_ports(before,days,timer_minutes)
