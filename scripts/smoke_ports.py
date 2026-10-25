"""Exercise numbered Earth purchases and cargo agreement over real terminal sessions."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import tempfile
import smoke_startup as terminal

ROOT=terminal.ROOT
OUT=ROOT/'evidence/ports'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render',action='store_true')
    parser.add_argument('--ascii',action='store_true')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='yt-port-smoke-') as temp:
        data=Path(temp)/'world'
        subprocess.run([str(ROOT/'bin/yt'),'-data',str(data),'-init','-sectors','8'],capture_output=True,check=True)
        text,frames=terminal.capture(data,'Caller',new=True,ascii=args.ascii,after_info=[
            ('sector','Main Command (?=Help)? ',b'P\r'),
            ('earth','Buy Which Item? -=>',b'3\r'),
            ('quantity','Buy how many fighters? [0]? ',b'2\r'),
            ('earth-purchased','Buy Which Item? -=>',b'0;M 2;P\r'),
            ('cargo','do you want to buy [ ',b'3\r'),
            ('agreement','Do you agree? [Y/n] ',b'n\r'),
            ('declined','Main Command (?=Help)? ',b'P\r'),
            ('cargo-again','do you want to buy [ ',b'3\r'),
            ('confirmed','Do you agree? [Y/n] ',b'y\r'),
            ('done','Main Command (?=Help)? ',b'Q;Y\r'),
        ])
        if args.ascii:
            assert '\x1b' not in text and all(ord(c)<128 for c in text),'ASCII port mode emitted terminal art/control sequences'
        world=json.loads((data/'world.json').read_text());p=world['Players']['1']
        assert p['Fighters']==27 and p['Cargo']==[3,0,0] and p['Turns']==496,p
        assert p['Credits']==805-3*p['DockPrices'][0] and not p['DockToken'],p
        assert 'Never mind!' in text and "It's Yours!" in text
        assert '[2] Cargo Holds' in text and '[9] Hire Spies (Each)' in text
        destination=OUT/('ascii' if args.ascii else 'ansi')
        destination.mkdir(exist_ok=True)
        (destination/'transcript.txt.gz').write_bytes(gzip.compress(text.encode('utf-8'),mtime=0))
        (destination/'cells.json').write_text(json.dumps(frames,ensure_ascii=False))
        if args.render:
            terminal.OUT=OUT
            terminal.render({k:frames[k] for k in ['earth','cargo','agreement','done']})
        print('Port PTY passed: Earth purchase, leave, travel, declined cargo, confirmed cargo, saved balances and turns.')


if __name__=='__main__':main()
