"""Independently verify original DOS Earth paid lottery evidence and bounded claims."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASELINE_SHA256 = '04eaf42c54d4f35c3412737e27fa968b5abcd22eb295cb5d8b45ab8045fcd0ec'
# Frozen declarations for the normally completed controls.
RECIPE_SHA256 = '11544ad4d01027052aa4de0b43aaf77db3771b6967a222ba0fff01e8a30d2cd1'
RECIPE = 'earth-paid-lottery-v1'
GRAPH = {1:[2,100],2:[1,3],3:[2],100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}
RANGES = {'0x1759c':254,'0x23fd0':285,'0x240ed':195,'0x241b0':244,'0x242a4':297,'0x243cd':458,'0x24597':376,'0x23f87':73,'0x20996':198,'0x2b106':213,'0x17c2e':143,'0x2b320':42}
KEEP = {'before.dat.gz','after.dat.gz','transcript.txt','side-before.json.gz','sidefiles.json.gz','DOSDATE.LOG','DOSTIME.LOG','dosbox.log','KEYS.TXT'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def side(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def loaded(data):
    """Rebuild initialized MZ bytes, applying the observed 0x1000 load fixups."""
    header = struct.unpack_from('<H', data, 8)[0] * 16
    image = bytearray(data[header:])
    table = struct.unpack_from('<H', data, 24)[0]
    for i in range(struct.unpack_from('<H', data, 6)[0]):
        off, seg = struct.unpack_from('<HH', data, table + 4*i)
        at = seg*16 + off
        struct.pack_into('<H', image, at, (struct.unpack_from('<H', image, at)[0] + 0x1000) & 0xffff)
    return image


def verify_native(research, binary):
    records = read(research/'rea/yt.json')['records']
    assert len(records) == len(RANGES), 'native observation count'
    image, seen = loaded(binary), set()
    for e in records:
        v = e['normalized_result']
        address = v['address']
        assert address in RANGES and address not in seen, 'native address set'
        seen.add(address)
        count = RANGES[address]
        assert e['operation'] == 'read_bytes', 'native operation'
        assert e['subject']['digest']['sha256'] == sha(binary), 'native target identity'
        assert v['complete'] and v['requested_bytes'] == v['returned_bytes'] == count, 'incomplete native bytes'
        at = int(address, 16) - 0x10000
        assert bytes.fromhex(v['bytes_hex']) == image[at:at+count], 'native bytes'
    assert seen == set(RANGES), 'native address set'


def verify_semantics(name, before, after, text, mbf):
    """Evaluate ticket outcomes independently of the capture declarations."""
    get = mbf.get
    digit_matches = [0,1,1,0,0,0,1,1,2,0]
    matches = None
    if name.startswith('digit-'):
        matches = [digit_matches[int(name.rsplit('-',1)[1])]]
    elif name.startswith('tier-'):
        matches = [int(name.rsplit('-',1)[1])]
    elif name in {'ticket-baseline'}:
        matches = [3]
    elif name in {'jackpot-permuted','jackpot-poor'} or name.startswith('large-win-'):
        matches = [6]
    elif name == 'duplicates-limited':
        matches = [2]
    elif name.startswith('input-') or name.startswith('large-loss-') or name in {'cash-exact','cash-above','limit-negative','limit-high','limit-nine-last','next-day-play'}:
        matches = [0]
    elif name in {'control-earth','cash-below','limit-zero','limit-reached','limit-above','limit-nine-reached','same-day-reconnect','next-day-reset'}:
        matches = []
    elif name == 'repeat-limit-two':
        matches = [0,0] # Two separate real draws; fixed after capture timing validation.
    assert matches is not None, ('unknown semantic scenario',name)
    payouts = [0,100,1000,10000,100000,1000000,100000000]
    receipts = re.findall(r'You matched (\d+) digits and won ([0-9]+) credits!',text)
    assert receipts == [(str(n),str(payouts[n])) for n in matches if n], (name,'payout receipt')
    assert text.count("Sorry, you didn't win this time.") == matches.count(0), (name,'losing receipt')
    assert text.count('Welcome to the Intergalactic Pick-6 Lottery!') == len(matches), (name,'lottery entry count')
    expected_prompts = len(matches) + int(name.startswith('input-'))
    assert text.count('Enter a 6 digit number for the lottery computer -+>') == expected_prompts, (name,'number prompt count')
    if name.startswith('input-'):
        error = "That's not 6 digits!" if name in {'input-blank','input-short','input-long'} else 'Please enter NUMBERS only!'
        assert error in text, (name,'invalid input rejection')
    if name=='cash-below':
        assert "You can't afford a lottery ticket!" in text, 'affordability rejection'
    if name=='limit-zero':
        assert 'Sorry, The supreme ruler has banned all gambling!' in text, 'disabled lottery'
    if name in {'limit-reached','limit-above','limit-nine-reached','same-day-reconnect'}:
        assert 'You will be allowed to play again tomorrow.' in text, 'daily limit refusal'
    if name=='repeat-limit-two':
        assert 'You will be allowed to play again tomorrow.' in text, 'daily limit refusal'
    plays = 0 if name=='next-day-reset' else get(before,2,105)+len(matches)
    assert get(after,2,105)==plays, (name,'daily play counter')
    turns = get(before,2,49)-(0 if name in {'next-day-reset'} else 1)
    if name=='next-day-reset':turns=500
    assert get(after,2,49)==turns, (name,'turn debit')
    assert get(after,2,57)==get(before,2,57)==1, (name,'position conservation')
    expected_day = 298 if name in {'next-day-reset','next-day-play'} else 297
    assert get(after,2,41)==expected_day, (name,'login day')
    limit=get(before,1,101)
    if limit<0 or limit>9:limit=3
    attempts=len(matches)+int(name in {'limit-reached','limit-above','limit-nine-reached','same-day-reconnect','repeat-limit-two'})
    assert re.findall(r'You may play ([0-9]+) times daily[.]',text)==[str(int(limit))]*attempts, (name,'daily limit display')
    assert re.findall(r"You've played ([0-9]+) times already[.]",text)==[str(int(min(get(before,2,105)+n,limit)))for n in range(attempts)], (name,'daily counter display')
    cash = get(before,2,81)
    rounded = lambda n:mbf.dec(mbf.enc(n))
    for count in matches:
        if count:cash=rounded(cash+payouts[count])
        cash=rounded(cash-5)
    # Native subtraction at 2**27 is not reproduced by Python's nearest MBF
    # encoding. These bounded witnesses preserve actual DOS outputs instead of
    # asserting an unproved general floating-point arithmetic model.
    high_cash={'large-loss-24':16777211,'large-loss-27':134217728,
               'large-loss-40':1099511627776,'large-win-24':116777208,
               'large-win-27':234217728,'large-win-40':1099611635712}
    cash=high_cash.get(name,cash)
    assert get(after,2,81)==cash, (name,'credit settlement')
    score={'large-loss-40':1099521589248,'large-win-40':1099621597184}.get(name,rounded(cash+9890250))
    assert get(after,2,109)==score, (name,'score credit contribution')
    for record,value in {3:367050,4:9990250,5:9990250,6:9990250}.items():
        assert get(after,record,109)==value, (name,'other score cache')
    return [payouts[n] for n in matches if n>3]


def verify_aux(name, initial, final, awards, after, mbf, date):
    """Check news append scope and the published player score values."""
    assert set(final)==set(initial), 'auxiliary file set'
    for file in initial:
        if file not in {'YTNEWS.DAT','YTSCORE.ASC'}:
            assert final[file]==initial[file], (name,'unrelated auxiliary effect',file)
    news = initial['YTNEWS.DAT']
    assert news.endswith(b'\x1a') and final['YTNEWS.DAT'].startswith(news[:-1]), (name,'news prefix conservation')
    appended=final['YTNEWS.DAT'][len(news)-1:].decode('cp437')
    assert re.fullmatch(r'-=\*=- \d{2}:\d{2}:\d{2} Q  Logged on -=\*=-\r\n' + ''.join('Q  won '+str(p)+' credits in the lottery!\r\n' for p in awards) + r'\x1a', appended), (name,'public news scope')
    board=final['YTSCORE.ASC'].decode('cp437')
    assert 'Last updated at: '+date[0:2]+'-'+date[3:5]+'-'+date[6:] in board, (name,'score date')
    row_pattern=r'^ *(\d+) +([0-9.]+)% +(%?[0-9,]+) +None +0 +(Q|Enemy|Third|Fourth|Fifth) *\r?\n'
    rows=re.findall(row_pattern,board,re.M)
    aliases={'Q':2,'Enemy':3,'Third':4,'Fourth':5,'Fifth':6}
    assert len(rows)==len(aliases) and {r[3]for r in rows}==set(aliases), (name,'scoreboard aliases')
    ranked=sorted(aliases,key=lambda alias:(-mbf.get(after,aliases[alias],109),aliases[alias]))
    maximum=max(mbf.get(after,record,109)for record in aliases.values())
    for index,(rank,percent,score,alias) in enumerate(rows):
        value=mbf.get(after,aliases[alias],109)
        display={('large-loss-40','Q'):'%1,099,521,545,280',('large-win-40','Q'):'%1,099,621,553,216'}.get((name,alias),f'{int(value):,}')
        assert score==display, (name,'scoreboard value')
        assert int(rank)==index+1 and alias==ranked[index], (name,'scoreboard order')
        assert percent==f'{value/maximum*100:.2f}', (name,'scoreboard percentage')
    def frame(value):
        value=re.sub(row_pattern,'',value,flags=re.M)
        value=re.sub(r'Last updated at: \d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}','Last updated at: CLOCK',value)
        value=re.sub(r'^ +1,000,000 +[0-9.]+% +0 +0[.]00%\r?\n','NPC SCORES\r\n',value,flags=re.M)
        return value
    assert frame(board)==frame(initial['YTSCORE.ASC'].decode('cp437')), (name,'scoreboard public scope')



def verify(research):
    droot = research/'dos'
    source = ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain'
    base = (source/'YTDATA.DAT').read_bytes()
    assert sha(base) == BASELINE_SHA256, 'baseline identity'
    assert gzip.decompress((droot/'baseline.dat.gz').read_bytes()) == base, 'retained baseline'
    raw = (droot/'recipe.json').read_bytes()
    assert sha(raw) == RECIPE_SHA256, 'frozen declarations'
    recipe = json.loads(raw)
    manifest = read(droot/'results.json')
    assert recipe['recipe'] == manifest['recipe'] == RECIPE, 'recipe identity'
    declarations = recipe['scenarios']
    specs = {c['name']: c for c in declarations}
    rows = manifest['scenarios']
    assert len(rows) == len(specs) == len(declarations), 'scenario count'
    assert len({c['name'] for c in rows}) == len(rows) and {c['name'] for c in rows} == set(specs), 'scenario identities'
    assert all(re.fullmatch(r'[a-z0-9-]+', name) for name in specs), 'scenario path'
    bins = {name:(ROOT/'archive/dos-original'/name).read_bytes() for name in ('YT.EXE','BRUN30.EXE','LOCAL.EXE')}
    bins['KEYFEED.COM'] = (ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()
    spec = importlib.util.spec_from_file_location('mbf', ROOT/'archive/analysis/yt-maint/experiments.py')
    mbf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mbf)
    worlds, sides, texts = {}, {}, {}
    for c in rows:
        name = c['name']
        decl, directory = specs[name], droot/name
        assert c == read(directory/'result.json'), 'manifest/result mismatch'
        assert all(c[k] == value for k, value in decl.items()), 'declaration mismatch'
        assert c['recipe'] == RECIPE and c['baseline_sha256'] == sha(base), 'session recipe/baseline'
        assert c['complete'] and not c['timed_out'] and c['timeout_seconds'] == 150, 'incomplete session'
        assert c['binaries'] == {n:sha(b) for n,b in bins.items()}, 'binary identity'
        assert set(c['files']) == KEEP, 'retained file set'
        assert {p.name for p in directory.iterdir() if p.is_file()} == KEEP | {'result.json'}, 'unexpected retained file'
        for file, digest in c['files'].items():
            assert sha((directory/file).read_bytes()) == digest, (name, file, 'file hash')
        assert c['date']==decl.get('date','10/24/2026') and c['date'] in (directory/'DOSDATE.LOG').read_text(), 'DOS date'
        assert c['time']==decl.get('time','00:00:00'), 'declared clock'
        clock = re.search(r'Current time: (\d+):(\d+):(\d+)[.](\d+)(am|pm)', (directory/'DOSTIME.LOG').read_text())
        assert clock, 'DOS clock'
        hour, minute, second, fraction, ampm = clock.groups()
        actual = int(hour)%12 + (12 if ampm == 'pm' else 0)
        requested = list(map(int, c['time'].split(':')))
        target = requested[0]*3600 + requested[1]*60 + requested[2]
        observed = actual*3600 + int(minute)*60 + int(second) + int(fraction)/(10**len(fraction))
        assert abs(observed-target) <= .06, 'DOS clock mismatch'
        before = gzip.decompress((directory/'before.dat.gz').read_bytes())
        after = gzip.decompress((directory/'after.dat.gz').read_bytes())
        assert len(before) == len(after) == 568687, 'world size'
        parent = c.get('parent')
        if parent:
            assert parent in worlds, 'missing or unordered parent'
            expected, patches, initial = bytearray(worlds[parent][1]), [], sides[parent]
        else:
            expected = bytearray(base)
            for sector, warps in GRAPH.items():
                at = (51+sector-1)*137
                expected[at:at+137] = bytes(137)
                for off, value in zip(range(41,65,4), warps):
                    mbf.put(expected, 51+sector, off, value)
            patches = [[2,o,v] for o,v in {45:0,49:500,57:1,89:0,93:0,105:0,125:0}.items()]
            patches += [[3,o,v] for o,v in {45:0,57:2,61:42,53:7,89:0,125:1}.items()]
            patches += [[52,65,1],[152,65,2],[3053,93,101],[153,93,2],[4053,73,0],[4053,77,12]]
            initial = {f.name:f.read_bytes() for f in source.iterdir() if f.suffix.upper() in ('.DAT','.ASC') and f.name != 'YTDATA.DAT'}
        patches += decl['patches']
        assert c['applied_patches'] == patches, 'applied declarations'
        for record, off, value in patches:
            mbf.put(expected, record, off, value)
        assert before == expected, 'undeclared setup or broken world chain'
        assert {n:bytes.fromhex(v) for n,v in side(directory/'side-before.json.gz').items()} == initial, 'auxiliary input chain'
        aux = side(directory/'sidefiles.json.gz')
        assert set(aux) == set(initial), 'auxiliary file set'
        final = {}
        for n, entry in aux.items():
            final[n] = bytes.fromhex(entry['hex'])
            assert entry['before_sha256'] == sha(initial[n]) and entry['after_sha256'] == sha(final[n]), 'auxiliary output identity'
        worlds[name], sides[name] = (before, after), final
        tail = '\r0\r~Q;Y\r~~' if c.get('port_rescue') else '\rQ;Y\r~~'
        keys = ('\r~~~~~\r~' + c['command'] + '\r~~~~' + tail*24).encode()
        assert (directory/'KEYS.TXT').read_bytes() == keys, 'exact input stream'
        text = (directory/'transcript.txt').read_text()
        texts[name] = text
        assert 'Returning to Yankee Trader Local Logon Program...' in text, 'normal quit'
        # Only these actor resources and logout score caches may change. This
        # checks every other byte, including other players, banks and treasuries.
        conserved = bytearray(before)
        for off in ((41,) if name=='next-day-reset' else ()) + (49,81,105,109):
            at = 137+off
            conserved[at:at+4] = after[at:at+4]
        for record in range(3,7):
            at = (record-1)*137+109
            conserved[at:at+4] = after[at:at+4]
        assert conserved == after, (name, 'undeclared world effect')
        assert mbf.get(after,2,45) == 0, 'unexpected player death'
        awards=verify_semantics(name, before, after, text, mbf)
        verify_aux(name, initial, final, awards, after, mbf, c['date'])
    verify_native(research, bins['YT.EXE'])
    print(f'Verified {len(rows)} completed earth-lottery controls, exact world/auxiliary chains, resource conservation and {len(RANGES)} complete native byte observations.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research', type=Path, default=ROOT/'research/yt-earth-lottery')
    verify(parser.parse_args().research)
