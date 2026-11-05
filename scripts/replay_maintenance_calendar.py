"""Explicit independent calendar profiles; before-only synthesis, no output corrections."""
import datetime
from replay_maintenance_records import Inputs,synthesize
from verify_maintenance_clock_neutral import verify_observation

CASES={'next-day':('11/03/2026','00:00:00',(41,19),{}),
       'new-year':('01/01/2027','00:00:00',(41,19),{581:6349}),
       'leap-day':('02/29/2028','00:00:00',(41,19),{}),
       'noon':('11/02/2026','12:34:00',(42,19),{324:6350})}


def parameters(name,observation):
    if name not in CASES:raise ValueError('only the four retained calendar profiles are admitted')
    date,clock,helpers,refills=CASES[name]
    raw=verify_observation(observation,helper_counts=helpers,cycle_refills=refills)
    startup=bytearray(raw['startup']);startup[2]^=128
    initial=5|((startup[0]^startup[2])<<8)|((startup[1]^startup[3])<<16)
    return Inputs(datetime.datetime.strptime(date,'%m/%d/%Y').date(),clock,
                  tuple(raw['port_minutes']),tuple(raw['helper1']),tuple(raw['helper2']),raw['xannoron'],initial)


def replay(before,name,observation):
    return synthesize(before,parameters(name,observation))
