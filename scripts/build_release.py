"""Build standalone Linux/Windows archives and SHA-256 checksums for GitHub Releases."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ('linux-amd64', 'linux-arm64', 'windows-amd64')
SHA = lambda b: hashlib.sha256(b).hexdigest()
SEMVER = re.compile(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?')


def command(args, **kwargs):
    return subprocess.check_output(args, cwd=ROOT, text=True, **kwargs).strip()


def go_license(root):
    root = Path(root)
    for path in (root / 'LICENSE', root.parent / 'LICENSE'):
        if path.is_file(): return path.read_bytes()
    raise FileNotFoundError('Go toolchain LICENSE not found')


def json_stream(text):
    decoder = json.JSONDecoder()
    while text.strip():
        item, end = decoder.raw_decode(text.lstrip())
        yield item
        text = text.lstrip()[end:]


def package(target, version, binary, info, licenses):
    """Return one deterministic archive; no persistent world is read or included."""
    if target not in TARGETS or not SEMVER.fullmatch(version): raise ValueError('invalid release target/version')
    folder = 'yankeetrader-' + version + '-' + target
    ref = 'v' + version
    replacements = {'@VERSION@': version, '@TARGET@': target, '@COMMIT@': info['source_commit'], '@REF@': ref}
    readme = (ROOT / 'packaging/README.md').read_text()
    for key, value in replacements.items(): readme = readme.replace(key, value)
    # Full sysop guide's research links are hosted at the exact release tag,
    # rather than broken relative links to research files absent from the package.
    guide = (ROOT / 'docs/SYSOP.md').read_text()
    def external(match):
        path = match[1]
        if '://' in path or path.startswith('#') or path == 'SYSOP_CHEAT_SHEET.md': return match[0]
        parts = []
        for part in (PurePosixPath('docs') / path.split('#')[0]).parts:
            if part == '..': parts.pop()
            elif part != '.': parts.append(part)
        anchor = '#' + path.split('#', 1)[1] if '#' in path else ''
        return '](https://github.com/robbiew/yankeetrader/blob/' + ref + '/' + '/'.join(parts) + anchor + ')'
    guide = re.sub(r'\]\(([^)]+)\)', external, guide)
    exe = 'yt.exe' if target.startswith('windows') else 'yt'
    manifest = dict(info, target=target, version=version, binary=exe, binary_sha256=SHA(binary))
    files = {exe: binary, 'README.md': readme.encode(), 'SYSOP.md': guide.encode(),
             'SYSOP_CHEAT_SHEET.md': (ROOT / 'docs/SYSOP_CHEAT_SHEET.md').read_bytes(),
             'RELEASE_INFO.json': (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode(),
             'LICENSE': (ROOT / 'LICENSE').read_bytes(), 'NOTICE.md': (ROOT / 'NOTICE.md').read_bytes(),
             'CREDITS.txt': b'Yankee Trader: Resurrection\nOriginal game by Alan Davenport\nBased on Yankee Trader Version 3.6\nhttps://github.com/robbiew/yankeetrader\n\nDoor transport: https://github.com/robbiew/godoors\nGo and golang.org/x dependencies: https://go.dev/\nYankee Trader: Resurrection code is MIT-licensed (LICENSE); original Yankee Trader 3.6 material\nembedded in the game remains Copyright Alan Davenport (NOTICE.md).\nBundled third-party license texts are under licenses/.\n'}
    files.update({'licenses/' + name: data for name, data in licenses.items()})
    output = io.BytesIO()
    if target.startswith('windows'):
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, raw in sorted(files.items()):
                entry = zipfile.ZipInfo(folder + '/' + name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3; entry.external_attr = (0o100755 if name == exe else 0o100644) << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, raw)
        extension = '.zip'
    else:
        with gzip.GzipFile(fileobj=output, mode='wb', mtime=0, filename='') as zipped:
            with tarfile.open(fileobj=zipped, mode='w') as archive:
                for name, raw in sorted(files.items()):
                    entry = tarfile.TarInfo(folder + '/' + name)
                    entry.size = len(raw); entry.mode = 0o755 if name == exe else 0o644
                    archive.addfile(entry, io.BytesIO(raw))
        extension = '.tar.gz'
    return folder + extension, output.getvalue()


def build(version, output, targets=TARGETS):
    if not SEMVER.fullmatch(version): raise ValueError('version must be a semantic version without a v prefix')
    output = Path(output).resolve(); output.mkdir(parents=True, exist_ok=True)
    # Refuse overwriting checksums or partial/old release archives.
    names = ['yankeetrader-' + version + '-' + t + ('.zip' if t.startswith('windows') else '.tar.gz') for t in targets]
    if any((output / name).exists() for name in names + ['SHA256SUMS.txt']): raise FileExistsError('release output files already exist')
    commit = command(['git', 'rev-parse', 'HEAD'])
    schema = int(re.search(r'const WorldVersion = (\d+)', (ROOT / 'internal/game/game.go').read_text())[1])
    env = {**os.environ, 'CGO_ENABLED': '0', 'GOOS': 'linux', 'GOARCH': 'amd64'}
    modules = {}
    for entry in json_stream(command(['go', 'list', '-deps', '-json', './cmd/yt'], env=env)):
        module = entry.get('Module')
        if module and not module.get('Main'): modules[module['Path']] = module
    licenses = {'Go-LICENSE.txt': go_license(command(['go', 'env', 'GOROOT']))}
    dependencies = []
    for name, module in sorted(modules.items()):
        source = module.get('Replace') or module
        directory = Path(source['Dir'])
        dependency = dict(module=name, version=module['Version'])
        if name == 'github.com/robbiew/godoors':
            dependency['commit'] = command(['git', '-C', str(directory), 'rev-parse', 'HEAD'])
        dependencies.append(dependency)
        for filename in ('LICENSE', 'LICENSE.md', 'COPYING', 'NOTICE'):
            path = directory / filename
            if path.is_file(): licenses[name.replace('/', '_') + '-' + filename + '.txt'] = path.read_bytes()
    info = dict(source_commit=commit, source_dirty=bool(command(['git', 'status', '--porcelain'])),
                save_schema=schema, go_version=command(['go', 'version']), dependencies=dependencies)
    results = {}
    with tempfile.TemporaryDirectory(prefix='yt-release-build-') as temporary:
        for target in targets:
            goos, arch = target.split('-'); env.update(GOOS=goos, GOARCH=arch)
            binary = Path(temporary) / ('yt.exe' if goos == 'windows' else 'yt')
            subprocess.run(['go', 'build', '-trimpath', '-buildvcs=false', '-ldflags',
                            '-s -w -X github.com/robbiew/yankeetrader/internal/version.Version=' + version,
                            '-o', str(binary), './cmd/yt'], cwd=ROOT, env=env, check=True)
            name, data = package(target, version, binary.read_bytes(), info, licenses)
            with (output / name).open('xb') as stream: stream.write(data)
            results[name] = SHA(data)
            print(name, results[name], flush=True)
    with (output / 'SHA256SUMS.txt').open('x') as stream:
        stream.write(''.join(digest + '  ' + name + '\n' for name, digest in sorted(results.items())))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'dist')
    parser.add_argument('--target', action='append', choices=TARGETS)
    args = parser.parse_args()
    build(args.version, args.out, tuple(args.target) if args.target else TARGETS)
