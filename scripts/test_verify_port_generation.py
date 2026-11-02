"""Semantic corruption controls for the independent DOS port verifier."""
import gzip, json, tempfile, shutil, unittest
from pathlib import Path
from verify_port_generation import ROOT, SHA, get, verify, verify_native

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
    d=root/"later";p=d/"before-maint.dat.gz";b=bytearray(gzip.decompress(p.read_bytes()))
    at=3051*137+offset;b[at:at+4]=bytes(4);p.write_bytes(gzip.compress(b,mtime=0))
    # Stock zero was already valid; use explicit MBF1 for that corruption.
    if offset==49:
     b[at:at+4]=bytes.fromhex("00000081");p.write_bytes(gzip.compress(b,mtime=0))
    m=json.loads((d/"result.json").read_text());m["files"][p.name]=SHA(p.read_bytes());(d/"result.json").write_text(json.dumps(m))
    with self.assertRaises(AssertionError):verify(root)
 def test_rehashed_sector_links_in_both_snapshots(self):
  for snapshot in ("before-maint.dat.gz","after-maint.dat.gz"):
   for mode in ("missing","wrong","fractional","all-cleared"):
    with self.subTest(snapshot=snapshot,mode=mode), tempfile.TemporaryDirectory() as tmp:
     root=Path(tmp)/"dos";shutil.copytree(ROOT/"research/yt-port-generation/dos",root)
     d=root/"later";p=d/snapshot;b=bytearray(gzip.decompress(p.read_bytes()))
     if mode=="all-cleared":
      for sector in range(1,3001):
       at=(50+sector)*137+65;b[at:at+4]=bytes(4)
     else:
      at=51*137+65
      # Earth must link to port1; zero, port2 and fractional1.5 are all invalid.
      b[at:at+4]={"missing":bytes(4),"wrong":bytes.fromhex("00000082"),"fractional":bytes.fromhex("00004081")}[mode]
     p.write_bytes(gzip.compress(b,mtime=0))
     m=json.loads((d/"result.json").read_text());m["files"][p.name]=SHA(p.read_bytes());(d/"result.json").write_text(json.dumps(m))
     with self.assertRaisesRegex(AssertionError,"sector port link"):verify(root)
 def test_original_duplicate_location_uses_last_port(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/"dos";shutil.copytree(ROOT/"research/yt-port-generation/dos",root);d=root/"later"
   m=json.loads((d/"result.json").read_text())
   for snapshot in ("before-maint.dat.gz","after-maint.dat.gz"):
    p=d/snapshot;b=bytearray(gzip.decompress(p.read_bytes()))
    old=int(get(b,4051,93));new=int(get(b,3056,93))
    # Copy port5's sector MBF to port1000 and preserve last-writer-wins links.
    b[4050*137+93:4050*137+97]=b[3055*137+93:3055*137+97]
    at=(50+old)*137+65;b[at:at+4]=bytes(4)
    at=(50+new)*137+65;b[at:at+4]=bytes.fromhex("00007a8a") # MBF1000
    p.write_bytes(gzip.compress(b,mtime=0));m["files"][p.name]=SHA(p.read_bytes())
   (d/"result.json").write_text(json.dumps(m))
   self.assertEqual(verify(root)["later"]["overwritten_ports"],1)
 def test_rehashed_missing_return(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/"dos";shutil.copytree(ROOT/"research/yt-port-generation/dos",root);d=root/"midnight"
   p=d/"INITRET.LOG";p.write_bytes(b"did not return")
   m=json.loads((d/"result.json").read_text());m["files"][p.name]=SHA(p.read_bytes());(d/"result.json").write_text(json.dumps(m))
   with self.assertRaises(AssertionError):verify(root)
if __name__=="__main__":unittest.main()
