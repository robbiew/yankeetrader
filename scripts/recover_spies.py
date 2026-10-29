"""Probe original DOS spies in disposable copies; never mount the archive."""
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
    hire="P;9;1;101\r~~~~\r~~0;"
    return [("list-only",{},hire+"C;15;1;C;15;1"),
      ("status",{},hire+"S;C;15;1;S;C;15;1"),
      ("move",{},hire+"M;100;C;15;1;M;1;C;15;1"),
      ("populated",{(152,129):7,(152,93):2,(4053,73):3,(4053,77):12,(3,57):101},hire+"M;100;C;15;1;M;1;C;15;1"),
      ("defenders",{(152,81):42,(152,85):3},hire+"M;100;C;15;1;M;1;C;15;1"),
      ("same-sector",{(152,41):101,(152,129):7},hire+"M;100;C;15;1;M;1;C;15;1"),
      ("cloak",{(3,57):101,(3,125):1},hire+"M;100;C;15;1;M;1;C;15;1") ]


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
    for off,value in {57:1,81:2000000,89:0,125:0}.items():mbf.put(base,2,off,value)
    mbf.put(base,52,65,1)
    # Deterministic two-sector spy route, isolated from caller travel.
    for sector,destination in [(100,1),(101,102),(102,101)]:
        r=51+sector;base[(r-1)*137:r*137]=bytes(137)
        mbf.put(base,r,41,destination)
    mbf.put(base,52,41,100)
    mbf.put(base,3,57,200)
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
        # Retain the exit-generated scoreboard as an auxiliary output.
        (d/"YTSCORE.ASC").write_bytes(b"STALE SCOREBOARD PROBE\r\n")
        before=bytearray(base)
        for (r,off),value in patch.items():mbf.put(before,r,off,value)
        before=bytes(before);(d/"YTDATA.DAT").write_bytes(before)
        (d/"KEYS.TXT").write_bytes(b"\r~~~~~\r~"+command.encode()+b"\r~~~~"+b"\rQ;Y\r~~"*24)
        complete=True
        try:
            with (d/"dosbox.log").open("w") as log:
                subprocess.run([dosbox,"--noprimaryconf","--nolocalconf","--set","cpu_cycles=200000","--set","nosound=true","-c",f"mount c {d}","-c","c:","-c","date 10/24/2026","-c","time 00:00:00","-c","keyfeed","-c","local TESTER > game.log","-c","exit"],env={**os.environ,"SDL_VIDEODRIVER":"dummy","SDL_AUDIODRIVER":"dummy"},stdout=log,stderr=subprocess.STDOUT,timeout=130,check=True)
        except subprocess.TimeoutExpired:complete=False
        after=(d/"YTDATA.DAT").read_bytes()
        transcript=(d/"GAME.LOG").read_bytes().decode("cp437").replace("\\r\\n","\n")
        (d/"transcript.txt").write_text(transcript)
        (d/"scoreboard.txt").write_bytes((d/"YTSCORE.ASC").read_bytes())
        for tag,b in (("before",before),("after",after)):(d/(tag+".dat.gz")).write_bytes(gzip.compress(b,mtime=0))
        retained={"KEYS.TXT","before.dat.gz","after.dat.gz","transcript.txt","scoreboard.txt","dosbox.log"}
        result={"name":name,"complete":complete and "Returning to Yankee Trader" in transcript and transcript.count("Spy # 1 will hunt in sector")==3,"command":command,
          "patches":[[r,o,v] for (r,o),v in patch.items()],"source_sha256":digest(source_bytes),"baseline_sha256":digest(base),
          "before_sha256":digest(before),"after_sha256":digest(after),"executable_sha256":digest((d/"YT.EXE").read_bytes()),"keyfeed_sha256":digest(feeder.read_bytes()),
          "files":{f:digest((d/f).read_bytes()) for f in retained if not f.endswith(".gz")},
          "actor_turns":mbf.get(after,2,49),"dos_date":"10/24/2026","dos_time":"00:00:00"}
        (d/"result.json").write_text(json.dumps(result,indent=2)+"\n")
        for p in d.iterdir():
            if p.is_file() and p.name not in retained|{"result.json"}:p.unlink()
        print(name,result["complete"],result["actor_turns"],flush=True)
        return result
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,cases))
    (dest/"results.json").write_text(json.dumps({"scenarios":results},indent=2)+"\n")


if __name__=="__main__":main()
