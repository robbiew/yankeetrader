"""Verify the complete consolidated archive without requiring Downloads."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'archive/manifest.json').read_text())
for item in manifest['files']:
 p=root/item['path']
 assert p.stat().st_size==item['bytes'],str(p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],str(p)
print(f"Verified {len(manifest['files'])} archived files.")
