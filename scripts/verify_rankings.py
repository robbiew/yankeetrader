"""Verify DOS ranking evidence, fixed outcomes and provenance independently."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("mbf",ROOT/"archive/analysis/yt-maint/experiments.py")
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)


def check(path):
    scenarios=json.loads((path/"results.json").read_text())["scenarios"]
    source=(ROOT/"archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT").read_bytes()
    base=bytearray(source)
    mbf.put(base,2,89,0)
    for off in (53,61,65,69,73,77,81,89,93,97,109,113,117,121,125,129):mbf.put(base,3,off,0)
    for off,value in {57:200,65:10,81:1000,109:-1}.items():mbf.put(base,3,off,value)
    for r in range(52,3052):
        for off in (81,85):mbf.put(base,r,off,0)
    for r in range(3052,4052):mbf.put(base,r,89,0)
    for r in range(4052,4152):mbf.put(base,r,73,0)
    digest=lambda b:hashlib.sha256(b).hexdigest()
    expected=json.loads((ROOT/"research/yt-rankings/expected.json").read_text())
    assert len(scenarios)==len(expected) and {r["name"] for r in scenarios}==set(expected),"scenario set"
    for result in scenarios:
        name=result["name"];d=path/name;gold=expected[name]
        assert json.loads((d/"result.json").read_text())==result,(name,"manifest copies disagree")
        assert result["complete"],(name,"incomplete")
        assert result["executable_sha256"]=="c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037",name
        assert result["keyfeed_sha256"]==digest((ROOT/"archive/analysis/yt-combat/KEYFEED.COM").read_bytes()),name
        assert result["source_sha256"]==digest(source) and result["baseline_sha256"]==digest(base),name
        before=gzip.decompress((d/"before.dat.gz").read_bytes());after=gzip.decompress((d/"after.dat.gz").read_bytes())
        assert digest(before)==result["before_sha256"] and digest(after)==result["after_sha256"],name
        patched=bytearray(base)
        assert result["patches"]==gold["patches"],(name,"patch provenance")
        for record,off,value in result["patches"]:mbf.put(patched,record,off,value)
        assert before==patched,(name,"unrecorded patch")
        assert set(result["files"])=={"KEYS.TXT","transcript.txt","scoreboard.txt","dosbox.log"},name
        for filename,sha in result["files"].items():assert digest((d/filename).read_bytes())==sha,(name,filename)
        assert mbf.get(after,3,109)==gold["score"]==result["target_score"],(name,"score mismatch")
        for player in (2,3):
            for off in (49,53,57,61,65,69,73,77,81,97,113,121,125,129):
                assert mbf.get(before,player,off)==mbf.get(after,player,off),(name,player,off,"ship mutation")
        text=(d/"transcript.txt").read_text()
        assert "Entering a new player" not in text and "Entering a new ship" not in text,(name,"invalid login")
        assert "Enter 'O' to see OLD scoreboard" in text and "Returning to Yankee Trader" in text,name
        assert mbf.get(after,2,49)==500,(name,"turn charge")
        if name=="old-board":
            assert "STALE SCOREBOARD PROBE" in text.split("Generating ScoreBoard")[0],name
        else:
            assert "P l a y e r  R a n k i n g s" in text,name
            assert text.count("Y a n k e e   T r a d e r   S c o r e b o a r d")>=2,(name,"missing updated report")
        board=(d/"scoreboard.txt").read_bytes().decode("cp437")
        if name in ("dead-target","zero-score"):assert re.search(r"0\.00%\s+0\s+None\s+0\s+Enemy",board),"zero/dead account score"
        if name=="tie-score":
            rows=[line for line in board.splitlines() if re.match(r"\s*\d+\s+100\.00%",line)]
            assert len(rows)==5 and [line.split()[-1] for line in rows]==["Q","Enemy","Third","Fourth","Fifth"],"tie order"
        if name=="team-members":
            assert re.search(r"100\.00%\s+10,016,250\s+1\s+Orion",board),"team score is not the sum of members"
    evidence=json.loads((ROOT/"research/yt-rankings/rea.json").read_text())
    executable=(ROOT/"archive/dos-original/YT.EXE").read_bytes()
    assert evidence["status"]=="verified" and evidence["subject"]["digest"]["sha256"]==digest(executable),"REA target"
    u16=lambda pos:int.from_bytes(executable[pos:pos+2],"little")
    header=u16(8)*16;image=bytearray(executable[header:])
    for i in range(u16(6)):
        pos=u16(24)+i*4;offset=u16(pos)+u16(pos+2)*16
        value=(int.from_bytes(image[offset:offset+2],"little")+0x1000)&0xffff
        image[offset:offset+2]=value.to_bytes(2,"little")
    for entry in evidence["byte_evidence"]:
        result=entry["normalized_result"];offset=int(result["address"],16)-0x10000
        assert result["complete"] and result["requested_bytes"]==result["returned_bytes"]
        assert image[offset:offset+result["returned_bytes"]].hex()==result["bytes_hex"],"REA bytes mismatch"
    print(f"Verified {len(scenarios)} DOS ranking sessions, {2*len(scenarios)} snapshots, score controls and report behavior.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence",type=Path,default=ROOT/"research/yt-rankings/dos")
    args=parser.parse_args();check(args.evidence)


if __name__=="__main__":main()
