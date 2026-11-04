"""Audit native January date boundaries independently of replay/Go generation."""
import argparse
import collections
from pathlib import Path
from verify_initializer_controls import verify as verify_controls
from verify_initializer_targets import audit_world

ROOT=Path(__file__).resolve().parents[1]
CASES={'jan09-2026': ('01/09/2026', '', 'f71b42f56951f99b20f525a37b2d3f1df060cae9ca362cf5ae5f4ae721de4a62'), 'jan09-2027': ('01/09/2027', '', 'fc26017e925ed87ca772b0c672e603f7b89af8ff35e7577b8cb8ecd5367dc3de'), 'jan09-2028': ('01/09/2028', '', 'cb8fb803f4c5b086e76b21cc9f66e90106a148f4ac28acd4bd4ee2c27e477eab'), 'jan10-2026': ('01/10/2026', '', 'c84399210090b5e30b3af79b5daf0482e05b285114a0452e75e101f84837005d'), 'jan10-2027': ('01/10/2027', '', '413a49739c26622eecc1256378de3f09b4a3be311b73c9ade3399c4323e957ca'), 'jan10-2027-repeat': ('01/10/2027', '', '413a49739c26622eecc1256378de3f09b4a3be311b73c9ade3399c4323e957ca'), 'jan10-2028': ('01/10/2028', '', '999df777101620da1c08b3690c882cc32128cfeee73e2ba7216d2d52bf571048'), 'jan11-2026': ('01/11/2026', '', '0f2c4643bf60f971951269cd4acc018302b7c06e1b1d36a77fe53c7bac47c0a9'), 'jan11-2027': ('01/11/2027', '', '32468beb9dc80a7b1f1a867b336cbae0e1f4add6f6fd46dc55c1ad71cabcd8b2'), 'jan11-2028': ('01/11/2028', '', '33212a696a85215988390bdf75287ad9c658c7e43b18b61dab309940e332a197')}
# Native 7-class integer/FAC residue, then exact date cancellation clears exponent.
ZERO_BY_CLASS={1:bytes.fromhex('06004000'),2:bytes.fromhex('05002000'),3:bytes.fromhex('04000000')}

def verify(destination=ROOT/'research/yt-initializer-replay/january10-controls'):
    outcomes=verify_controls(destination,cases=CASES)
    for name,case in outcomes.items():
        audit_world(case['world'],case['date'],849)
        counts=collections.Counter()
        for port in range(1000):
            row=case['world'][(3051+port)*137:(3052+port)*137]
            klass={bytes.fromhex('00000081'):1,bytes.fromhex('00000082'):2,bytes.fromhex('00004082'):3}[row[41:45]]
            if case['date'].day==10:
                assert row[45:49]==ZERO_BY_CLASS[klass], 'January 10 class-dependent FAC residue'
            else:
                assert row[45:49]==bytes.fromhex('00008081' if case['date'].day==9 else '00000081'), 'neighboring port date'
            counts[klass]+=1
        assert counts=={1:345,2:345,3:310}, 'unchanged source class stream'
    assert outcomes['jan10-2027']['world']==outcomes['jan10-2027-repeat']['world'], 'independent January 10 repeat'
    return outcomes

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('destination',nargs='?',type=Path)
    args=parser.parse_args();results=verify(args.destination) if args.destination else verify()
    print(f'Verified {len(results)} native January boundary worlds and measured seed controls.')
