"""Exercise automatic score publication through real GoDoors and maintenance CLI."""
from pathlib import Path
import datetime
import errno
import json
import os
import pty
import re
import select
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
BINARY = str(ROOT / "bin/yt")


def play(data, alias, commands, classic=False):
    master, slave = pty.openpty()
    options = ["-ascii"] if classic else ["-compact"]
    proc = subprocess.Popen([BINARY, *options, "-data", str(data), "-local", alias],
                            stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    steps = [(b"[ Press any Key ]", b" ")] * 3 if classic else []
    steps += [(b"Main Command (?=Help)?" if classic else b"> ", commands.encode() + b"\r")]
    output = pending = b""
    step = 0
    deadline = time.monotonic() + 20
    try:
        while time.monotonic() < deadline:
            if not select.select([master], [], [], .1)[0]:
                continue
            try:
                chunk = os.read(master, 65536)
            except OSError as err:
                if err.errno == errno.EIO:
                    break
                raise
            if not chunk:
                break
            output += chunk
            pending += chunk
            if step < len(steps) and steps[step][0] in pending:
                marker, answer = steps[step]
                pending = pending.split(marker, 1)[1]
                os.write(master, answer)
                step += 1
        proc.wait(timeout=2)
        text = output.decode(errors="replace").replace("\r", "")
        assert proc.returncode == 0 and step == len(steps), text
        return text
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)


def scores(world):
    result = {}
    for n,p in world["Players"].items():
        ports = sum(port["ID"] != 1 and port["Owner"] == p["ID"] for port in world["Ports"].values())
        defenses = sum(s.get("Defense", {}).get("Fighters", 0) for s in world["Sectors"].values()
                       if s.get("Defense", {}).get("Owner") == p["ID"])
        result[n] = (p["Credits"] + 50*p["Shields"] + 100*(p["Fighters"]+defenses)
            + 2500*p["Holds"] + sum(a*b for a,b in zip(p["Cargo"], (20,30,40)))
            + 1000*p["Missiles"] + 1000000*p["Plasma"] + 50000*ports
            + 750*p["Ground"] + 2500*p["Mines"])
    return result


def assert_scores(world):
    expected=scores(world)
    assert all(p["StoredScore"] == expected[n] for n,p in world["Players"].items())


with tempfile.TemporaryDirectory(prefix="yt-auto-scores-") as temp:
    data=Path(temp)/"world"
    subprocess.run([BINARY,"-data",str(data),"-init","-sectors","8"],check=True,capture_output=True)
    play(data,"Captain","q")
    play(data,"Enemy","q")
    play(data,"Captain","q;y",classic=True)
    path=data/"world.json"
    world=json.loads(path.read_text())
    world["Players"]["1"]["Credits"]=100000
    world["Ports"]["2"]["Owner"]=1
    world["Sectors"]["3"]["Defense"]=dict(Owner=2,Fighters=50)
    for p in world["Players"].values():p["StoredScore"]=777
    path.write_text(json.dumps(world))
    transcript=play(data,"Captain","q")
    saved=json.loads(path.read_text());assert_scores(saved)
    for n,p in saved["Players"].items():
        assert {k:v for k,v in p.items() if k!="StoredScore"} == {k:v for k,v in world["Players"][n].items() if k!="StoredScore"}
    for p in saved["Players"].values():p["StoredScore"]=888
    path.write_text(json.dumps(saved))
    transcript+=play(data,"Captain","q;y",classic=True)
    saved=json.loads(path.read_text());assert_scores(saved)
    # Exercise the operator maintenance command, including its replay guard.
    saved["LastMaintenance"]=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=1)).date().isoformat()
    for p in saved["Players"].values():p["StoredScore"]=999;p["Turns"]=17
    path.write_text(json.dumps(saved))
    result=subprocess.run([BINARY,"-data",str(data),"-maint"],check=True,capture_output=True,text=True)
    transcript+=result.stdout
    maintained=json.loads(path.read_text());assert_scores(maintained)
    assert all(p["Turns"]==500 for p in maintained["Players"].values())
    assert all(p["Credits"]==saved["Players"][n]["Credits"] for n,p in maintained["Players"].items())
    result=subprocess.run([BINARY,"-data",str(data),"-maint"],check=True,capture_output=True,text=True)
    transcript+=result.stdout
    assert json.loads(path.read_text())==maintained,"same-day replay changed state"
    transcript+=play(data,"Captain","rank old;q")
    assert "Stored scores;" in transcript
    (ROOT/"evidence/automatic-scores-smoke.txt").write_text("\n".join(line.rstrip() for line in transcript.splitlines())+"\n")
    print("Automatic scores PTY/CLI passed: compact/classic logout, current ownership/defenses, maintenance, same-day replay and cached reconnect.")
