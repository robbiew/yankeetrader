"""Verify release archive contents, checksums, target binaries and runnable Linux setup."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import re
import struct
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from build_release import TARGETS


def verify(directory):
    directory = Path(directory)
    lines = (directory / 'SHA256SUMS.txt').read_text().splitlines()
    assert len(lines) == len(TARGETS), 'complete release matrix'
    found = set()
    for line in lines:
        match = re.fullmatch(r'([0-9a-f]{64})  (yankeetrader-[A-Za-z0-9.-]+\.(?:tar\.gz|zip))', line)
        assert match, 'checksum line or filename'
        digest, filename = match.groups()
        raw = (directory / filename).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest, 'archive checksum'
        modes = {}
        if filename.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                names = archive.namelist(); assert len(names) == len(set(names)), 'duplicate ZIP entry'
                files = {name: archive.read(name) for name in names}
        else:
            with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
                entries = archive.getmembers(); assert all(e.isfile() for e in entries), 'regular files only'
                assert len(entries) == len({e.name for e in entries}), 'duplicate tar entry'
                files = {e.name: archive.extractfile(e).read() for e in entries}
                modes = {e.name: e.mode for e in entries}
        roots = {name.split('/')[0] for name in files}
        assert len(roots) == 1 and all('..' not in Path(n).parts and not n.startswith('/') for n in files), 'safe single-root archive'
        root = roots.pop()
        files = {name[len(root)+1:]: data for name, data in files.items()}
        info = json.loads(files['RELEASE_INFO.json'])
        target = info['target']; assert target in TARGETS and target not in found, 'target coverage'
        found.add(target)
        assert root == 'yankeetrader-' + info['version'] + '-' + target
        binary = 'yt.exe' if target.startswith('windows') else 'yt'
        assert info['binary'] == binary and hashlib.sha256(files[binary]).hexdigest() == info['binary_sha256']
        assert {'README.md','SYSOP.md','SYSOP_CHEAT_SHEET.md','RELEASE_INFO.json','CREDITS.txt',binary} <= set(files)
        assert all(name in {binary,'README.md','SYSOP.md','SYSOP_CHEAT_SHEET.md','RELEASE_INFO.json','CREDITS.txt'} or name.startswith('licenses/') for name in files), 'unexpected bundled file'
        assert b'Original game by Alan Davenport' in files['CREDITS.txt']
        assert b'-init' in files['SYSOP_CHEAT_SHEET.md'] and b'-maint' in files['SYSOP_CHEAT_SHEET.md']
        assert b'@VERSION@' not in files['README.md'] and b'](../' not in files['SYSOP.md']
        data = files[binary]
        if target.startswith('linux'):
            assert data[:6] == b'\x7fELF\x02\x01', '64-bit little-endian ELF'
            assert struct.unpack_from('<H', data, 18)[0] == (62 if target.endswith('amd64') else 183), 'ELF architecture'
            assert modes[root+'/'+binary] & 0o111, 'Linux executable mode'
        else:
            assert data[:2] == b'MZ'
            at = struct.unpack_from('<I', data, 0x3c)[0]
            assert data[at:at+4] == b'PE\0\0' and struct.unpack_from('<H', data, at+4)[0] == 0x8664, 'Windows x86-64 PE'
        if target == 'linux-amd64' and sys.platform == 'linux' and platform.machine() in ('x86_64','AMD64'):
            with tempfile.TemporaryDirectory() as tmp:
                executable = Path(tmp)/'yt'; executable.write_bytes(data); executable.chmod(0o755)
                smoke(executable, info)
    assert found == set(TARGETS)
    print('Verified Linux amd64/arm64 and Windows amd64 archives, manifests and checksums.')


def smoke(executable, info):
    with tempfile.TemporaryDirectory() as tmp:
        world = Path(tmp)/'data'; archive = Path(tmp)/'snapshot.json'
        def run(*args):
            return subprocess.check_output([str(executable), *map(str,args)], text=True, timeout=60)
        assert run('-version').splitlines()[0] == 'Yankee Trader: Resurrection '+info['version']
        run('-data',world,'-init','-seed','36','-dos-warps','-dos-ports')
        before = (world/'world.json').read_bytes()
        duplicate = subprocess.run([str(executable),'-data',str(world),'-init'],capture_output=True, timeout=30)
        assert duplicate.returncode != 0 and (world/'world.json').read_bytes() == before, 'init must refuse overwrite'
        run('-data',world,'-maint')
        run('-data',world,'-season-export',archive)
        snapshot=json.loads(archive.read_text())
        assert snapshot['World']['Version'] == info['save_schema']
        assert snapshot['World']['WarpGeneration'] == snapshot['World']['PortGeneration'] == 'dos'
        reset_archive=Path(tmp)/'reset.json'
        run('-data',world,'-admin-reset','1','-season-export',reset_archive,'-seed','77')
        active=json.loads((world/'world.json').read_text())
        assert active['Season'] == 2 and active['SeasonResults'][-1]['Administrative'] is True
        before_retry=(world/'world.json').read_bytes()
        stale=subprocess.run([str(executable),'-data',str(world),'-admin-reset','1',
                              '-season-export',str(Path(tmp)/'stale.json')],capture_output=True,timeout=30)
        assert stale.returncode != 0 and (world/'world.json').read_bytes() == before_retry, 'stale reset must not change the world'
        print('CLI version, initialization, overwrite refusal, maintenance, export and guarded reset passed.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    verify(parser.parse_args().directory)
