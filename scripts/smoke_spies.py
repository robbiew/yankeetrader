"""Exercise session spies through real classic and compact GoDoors terminals."""
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


def play(data, alias, commands, classic=False, body=None, action="s"):
    master, slave = pty.openpty()
    options = ["-ascii"] if classic else ["-compact"]
    proc = subprocess.Popen([BINARY, *options, "-data", str(data), "-local", alias],
                            stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    steps = [(b"[ Press any Key ]", b" ")] * 3 if classic else []
    steps += [(b"Main Command (?=Help)?" if classic else b"> ", commands.encode() + b"\r")]
    if body is not None:
        steps += [(b"blank cancels): ", body.encode() + b"\r"),
                  (b"[S] Send [A] Abort -=> ", action.encode() + b"\r"),
                  (b"saved." if action == "s" else b"Radio cancelled.",
                   b"6;1;q;y\r" if classic else b"messages;q\r")]
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


with tempfile.TemporaryDirectory(prefix="yt-spies-smoke-") as temp:
    data=Path(temp)/"world"
    subprocess.run([BINARY,"-data",str(data),"-init","-sectors","8"],check=True,capture_output=True)
    play(data,"Trader","q")
    path=data/"world.json"
    world=json.loads(path.read_text())
    player=world["Players"]["1"]
    player["Credits"]=2000000
    world["Sectors"]["1"]["Warps"]=[2]
    world["Sectors"]["8"]["Warps"]=[]
    world["Sectors"]["8"]["Minefield"]=[{"Count":7}]
    world["Sectors"]["8"]["Defense"]={"Owner":-1,"Fighters":42}
    path.write_text(json.dumps(world))
    transcript=play(data,"Trader","p;hire 8;spies;s;spies;m 2;spies;intel;q")
    assert transcript.count("RADIO MESSAGE FROM SPY #1")==2,transcript
    assert "SECTOR HAS 7 MINES" in transcript and "Fighters in sector: 42 (Belong to The Xannor)" in transcript
    saved=json.loads(path.read_text())
    assert saved["Players"]["1"]["Credits"]==1667000 and saved["Players"]["1"]["Turns"]==498
    assert saved["Version"]==25 and not saved.get("Radio")
    text=play(data,"Trader","spies;intel;q")
    assert "You do not have any spies!" in text and "No intelligence reports this login." in text
    transcript+=text
    saved=json.loads(path.read_text());saved["Players"]["1"]["Sector"]=1
    path.write_text(json.dumps(saved))
    text=play(data,"Trader","p;9;1;8;0;c;15;1;m;2;c;15;1;intel;q;y",classic=True)
    assert "Hire how many spies?" in text and "Start spy # 1 in what sector?" in text,text
    assert text.count("RADIO MESSAGE FROM SPY #1")==2 and text.count("Spy # 1 will hunt in sector 8.")==3,text
    transcript+=text
    final=json.loads(path.read_text())
    assert final["Players"]["1"]["Credits"]==1334000 and final["Players"]["1"]["Turns"]==496
    (ROOT/"evidence/spies-smoke.txt").write_text("\n".join(line.rstrip() for line in transcript.splitlines())+"\n")
    print("Spies PTY passed: Earth hiring, computer 15, compact commands, reports/history, resources, reconnect isolation and zero-warp safety.")
