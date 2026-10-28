"""Probe original DOS rankings in disposable copies; never mount the archive."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def scenarios():
    cases = [("baseline", {}, "C;4;\r~~1")]
    for name, off, value in [("shields",53,100),("fighters",61,100),("holds-eleven",65,11),
        ("holds-twenty",65,20),("ore",69,10),("organics",73,10),("equipment",77,10),
        ("credits",81,1100),("scanner",93,-1),("missiles",97,10),
        ("field101",101,10),("field105",105,10),("stored-score",109,12345),
        ("plasma",113,10),("cached-ports",117,1),("ground",121,10),
        ("cloak",125,1),("mines",129,10)]:
        cases.append((name,{(3,off):value},"C;4;\r~~1"))
    cases += [("dead-target",{(3,45):2},"C;4;\r~~1"),
              ("deployed-fighters",{(152,81):100,(152,85):3},"C;4;\r~~1"),
              ("port-title",{(3152,89):3},"C;4;\r~~1"),
              ("planet-bank",{(4053,73):3,(4053,117):1000000},"C;4;\r~~1"),
              ("team-members",{(2,89):1,(3,89):1,(52,77):2,(52,109):2,(52,117):3},"C;4;\r~~1"),
              ("old-board",{},"C;4;O;1")]
    cases += [("zero-score",{(3,65):0,(3,81):0},"C;4;\r~~1"),
              ("tie-score",{(3,81):9965250},"C;4;\r~~1")]
    return cases


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination",type=Path)
    parser.add_argument("--only",nargs="+")
    parser.add_argument("--dosbox",default="dosbox-staging")
    args=parser.parse_args()
    dest=args.destination.resolve();dest.mkdir(parents=True,exist_ok=False)
    source=ROOT/"archive/analysis/yt-combat/experiments/fixture-team-captain"
    spec=importlib.util.spec_from_file_location("mbf",ROOT/"archive/analysis/yt-maint/experiments.py")
    mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
    source_bytes=(source/"YTDATA.DAT").read_bytes();base=bytearray(source_bytes)
    # Keep account/login metadata intact; change only known scored target fields.
    mbf.put(base,2,89,0)
    for off in (53,61,65,69,73,77,81,89,93,97,109,113,117,121,125,129):mbf.put(base,3,off,0)
    for off,value in {57:200,65:10,81:1000,109:-1}.items():mbf.put(base,3,off,value)
    # Remove all deployed ownership/strength and planet ownership from the baseline.
    for r in range(52,3052):
        for off in (81,85):mbf.put(base,r,off,0)
    for r in range(3052,4052):mbf.put(base,r,89,0)
    for r in range(4052,4152):mbf.put(base,r,73,0)
    base=bytes(base)
    cases=scenarios()
    if args.only:
        if set(args.only)-{c[0] for c in cases}:parser.error("unknown probe")
        cases=[c for c in cases if c[0] in args.only]
    dosbox=shutil.which(args.dosbox)
    if dosbox is None:parser.error("DOSBox Staging not found")
    digest=lambda b:hashlib.sha256(b).hexdigest()

    def run(case):
        name,patch,command=case;d=dest/name;d.mkdir()
        for p in source.iterdir():
            if p.suffix.upper() in (".DAT",".EXE",".DOC",".DEF",".ASC",".ANS"):shutil.copy2(p,d/p.name)
        feeder=ROOT/"archive/analysis/yt-combat/KEYFEED.COM";shutil.copy2(feeder,d/feeder.name)
        # Recognizable stale scoreboard proves OLD reads a file rather than regenerating.
        (d/"YTSCORE.ASC").write_bytes(b"STALE SCOREBOARD PROBE\r\n")
        before=bytearray(base)
        for (r,off),value in patch.items():mbf.put(before,r,off,value)
        before=bytes(before);(d/"YTDATA.DAT").write_bytes(before)
        (d/"KEYS.TXT").write_bytes(b"\r~~~~~\r~"+command.encode()+b"\r~~1\r~~Q;Y\r~~"*8)
        complete=True
        try:
            with (d/"dosbox.log").open("w") as log:
                subprocess.run([dosbox,"--noprimaryconf","--nolocalconf","--set","cpu_cycles=200000","--set","nosound=true","-c",f"mount c {d}","-c","c:","-c","date 10/24/2026","-c","time 00:00:00","-c","keyfeed","-c","local TESTER > game.log","-c","exit"],env={**os.environ,"SDL_VIDEODRIVER":"dummy","SDL_AUDIODRIVER":"dummy"},stdout=log,stderr=subprocess.STDOUT,timeout=130,check=True)
        except subprocess.TimeoutExpired:complete=False
        after=(d/"YTDATA.DAT").read_bytes()
        transcript=(d/"GAME.LOG").read_bytes().decode("cp437").replace("\r\n","\n")
        (d/"transcript.txt").write_text(transcript)
        (d/"scoreboard.txt").write_bytes((d/"YTSCORE.ASC").read_bytes())
        for tag,b in (("before",before),("after",after)):(d/(tag+".dat.gz")).write_bytes(gzip.compress(b,mtime=0))
        retained={"KEYS.TXT","before.dat.gz","after.dat.gz","transcript.txt","scoreboard.txt","dosbox.log"}
        result={"name":name,"complete":complete and "Returning to Yankee Trader" in transcript and "Enter 'O' to see OLD scoreboard" in transcript,"command":command,
          "patches":[[r,o,v] for (r,o),v in patch.items()],"source_sha256":digest(source_bytes),"baseline_sha256":digest(base),
          "before_sha256":digest(before),"after_sha256":digest(after),"executable_sha256":digest((d/"YT.EXE").read_bytes()),"keyfeed_sha256":digest(feeder.read_bytes()),
          "files":{f:digest((d/f).read_bytes()) for f in retained if not f.endswith(".gz")},
          "target_score":mbf.get(after,3,109),"dos_date":"10/24/2026","dos_time":"00:00:00"}
        (d/"result.json").write_text(json.dumps(result,indent=2)+"\n")
        for p in d.iterdir():
            if p.is_file() and p.name not in retained|{"result.json"}:p.unlink()
        print(name,result["complete"],result["target_score"],flush=True)
        return result
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,cases))
    (dest/"results.json").write_text(json.dumps({"scenarios":results},indent=2)+"\n")


if __name__=="__main__":main()
