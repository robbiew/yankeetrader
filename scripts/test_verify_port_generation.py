"""Semantic corruption controls for the independent DOS port verifier."""
import gzip, json, tempfile, shutil, unittest
from pathlib import Path
from verify_port_generation import ROOT, SHA, verify, verify_native

class PortEvidenceTests(unittest.TestCase):
 def test_retained(self):
  self.assertEqual(verify(ROOT/"research/yt-port-generation/dos")["midnight"]["ports"],1000)
 def test_native_contract_and_truncation(self):
  source=ROOT/"research/yt-port-generation"
  verify_native(source)
  for damage in ("missing","empty","truncated"):
   with self.subTest(damage=damage), tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    for p in source.glob("*-rea.json"):shutil.copy2(p,root/p.name)
    p=root/"runtime-rea.json";bundle=json.loads(p.read_text())
    if damage=="missing":bundle["records"].pop()
    else:
     n=bundle["records"][0]["normalized_result"];n["bytes_hex"]="" if damage=="empty" else n["bytes_hex"][:-2];n["returned_bytes"]=len(n["bytes_hex"])//2
    p.write_text(json.dumps(bundle))
    with self.assertRaises(AssertionError):verify_native(root)
 def test_rehashed_false_worlds(self):
  for offset in (49,61,73,93):
   with self.subTest(offset=offset), tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/"dos";shutil.copytree(ROOT/"research/yt-port-generation/dos",root)
    d=root/"midnight";p=d/"before-maint.dat.gz";b=bytearray(gzip.decompress(p.read_bytes()))
    at=3051*137+offset;b[at:at+4]=bytes(4);p.write_bytes(gzip.compress(b,mtime=0))
    # Stock zero was already valid; use explicit MBF1 for that corruption.
    if offset==49:
     b[at:at+4]=bytes.fromhex("00000081");p.write_bytes(gzip.compress(b,mtime=0))
    m=json.loads((d/"result.json").read_text());m["files"][p.name]=SHA(p.read_bytes());(d/"result.json").write_text(json.dumps(m))
    with self.assertRaises(AssertionError):verify(root)
 def test_rehashed_missing_return(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/"dos";shutil.copytree(ROOT/"research/yt-port-generation/dos",root);d=root/"midnight"
   p=d/"INITRET.LOG";p.write_bytes(b"did not return")
   m=json.loads((d/"result.json").read_text());m["files"][p.name]=SHA(p.read_bytes());(d/"result.json").write_text(json.dumps(m))
   with self.assertRaises(AssertionError):verify(root)
if __name__=="__main__":unittest.main()
