"""Release archives must be self-contained, safe and reproducible."""
import io
import hashlib
import struct
from unittest.mock import patch
import json
import tarfile
import unittest
import tempfile
from pathlib import Path
import zipfile
from build_release import package, SEMVER, go_license


class ReleasePackageTests(unittest.TestCase):
    def setUp(self):
        self.info=dict(source_commit='a'*40,source_dirty=False,save_schema=34,dependencies=[])

    def test_all_archive_contents_and_modes(self):
        for target in ('linux-amd64','linux-arm64','windows-amd64'):
            with self.subTest(target=target):
                filename,raw=package(target,'0.1.0',b'binary-control',self.info,{'test-LICENSE.txt':b'license-control'})
                self.assertEqual(package(target,'0.1.0',b'binary-control',self.info,{'test-LICENSE.txt':b'license-control'}),(filename,raw))
                if filename.endswith('.zip'):
                    with zipfile.ZipFile(io.BytesIO(raw)) as z:files={n:z.read(n) for n in z.namelist()}
                else:
                    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:
                        files={m.name:t.extractfile(m).read() for m in t.getmembers()}
                        self.assertEqual(t.getmember('yankeetrader-0.1.0-'+target+'/yt').mode,0o755)
                files={n.split('/',1)[1]:b for n,b in files.items()}
                binary='yt.exe' if target.startswith('windows') else 'yt'
                self.assertEqual(files[binary],b'binary-control')
                self.assertEqual(files['licenses/test-LICENSE.txt'],b'license-control')
                self.assertTrue(files['LICENSE'].startswith(b'MIT License'))
                self.assertIn(b'Alan Davenport',files['NOTICE.md'])
                manifest=json.loads(files['RELEASE_INFO.json'])
                self.assertEqual((manifest['version'],manifest['target'],manifest['binary']),('0.1.0',target,binary))
                self.assertNotIn(b'](../',files['SYSOP.md'])
                self.assertIn(b'/blob/v0.1.0/',files['SYSOP.md'])
                self.assertIn(b'Yankee Trader: Resurrection 0.1.0',files['README.md'])
                self.assertFalse(any('world.json' in n or n.endswith('.EXE') for n in files))

    def test_official_and_homebrew_license_locations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'go'; root.mkdir(); (root/'libexec').mkdir()
            (root/'LICENSE').write_bytes(b'Go license control')
            self.assertEqual(go_license(root),b'Go license control')
            self.assertEqual(go_license(root/'libexec'),b'Go license control')

    def test_reject_unsafe_names(self):
        for version in ('../bad','v0.1.0','1.2','1.2.3;bad','01.2.3'):
            with self.subTest(version=version), self.assertRaises(ValueError):package('linux-amd64',version,b'',self.info,{})
        with self.assertRaises(ValueError):package('../bad','0.1.0',b'',self.info,{})
        self.assertIsNotNone(SEMVER.fullmatch('0.1.0-rc.1'))


class ArchivePathSafetyTests(unittest.TestCase):
    def test_rehashed_zip_rejects_windows_paths(self):
        from verify_release_packages import verify
        root='yankeetrader-0.1.0-windows-amd64'
        attacks=(root+'/licenses/..\\..\\..\\escaped.txt',
                 root+'/licenses/C:escaped.txt', root+'/licenses/notice.txt:stream',
                 root+'/licenses/../../escaped.txt', root+'/licenses/./notice.txt',
                 root+'//licenses/notice.txt', 'C:'+root+'/licenses/notice.txt')
        for member in attacks:
            with self.subTest(member=member), tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);sums=[]
                for target in ('windows-amd64','linux-amd64','linux-arm64'):
                    binary=bytearray(128)
                    if target.startswith('windows'):
                        binary[:2]=b'MZ';struct.pack_into('<I',binary,0x3c,64)
                        binary[64:68]=b'PE\0\0';struct.pack_into('<H',binary,68,0x8664)
                    else:
                        binary[:6]=b'\x7fELF\x02\x01'
                        struct.pack_into('<H',binary,18,62 if target.endswith('amd64') else 183)
                    info=dict(source_commit='a'*40,source_dirty=False,save_schema=34,dependencies=[])
                    filename,raw=package(target,'0.1.0',bytes(binary),info,{})
                    if target.startswith('windows'):
                        archive=io.BytesIO(raw)
                        with zipfile.ZipFile(archive,'a') as z:z.writestr(member,b'escape-control')
                        raw=archive.getvalue()
                    (directory/filename).write_bytes(raw)
                    sums.append(hashlib.sha256(raw).hexdigest()+'  '+filename)
                # Rehash a complete otherwise valid matrix, so no checksum or
                # missing-manifest failure can hide the unsafe member.
                (directory/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n')
                with patch('verify_release_packages.smoke'), self.assertRaisesRegex(AssertionError,'safe single-root archive'):
                    verify(directory)



if __name__=='__main__':unittest.main()
