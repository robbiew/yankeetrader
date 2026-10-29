"""Exercise public newspaper history through real GoDoors terminals."""
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


def play(data, alias, commands, classic=False, followups=()):
    master, slave = pty.openpty()
    options = ["-ascii"] if classic else ["-compact"]
    proc = subprocess.Popen([BINARY, *options, "-data", str(data), "-local", alias],
                            stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    steps = [(b"[ Press any Key ]", b" ")] * 3 if classic else []
    steps += [(b"Main Command (?=Help)?" if classic else b"> ", commands.encode() + b"\r")]
    steps += list(followups)
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


with tempfile.TemporaryDirectory(prefix="yt-newspaper-smoke-") as temp:
    data=Path(temp)/"world"
    subprocess.run([BINARY,"-data",str(data),"-init","-sectors","8"],check=True,capture_output=True)
    transcript=play(data,"Captain","news yesterday;news;q")
    assert "Galactic Newspaper - Yesterday" in transcript and "No news retained for this date." in transcript
    assert "Captain  Logged on" in transcript
    path=data/"world.json";saved=json.loads(path.read_text())
    assert saved["Version"]==12 and len(saved["News"])==1 and saved["NextNews"]==2
    assert saved["Players"]["1"]["Credits"]==1005 and saved["Players"]["1"]["Turns"]==500
    text=play(data,"Captain","team;2;News Team",followups=[
        (b"Team password (4 characters; entered separately): ",b"ABCD\r"),
        (b"Team Command? ",b"1;news;q\r")])
    assert "Captain  Created Team 1 -=- News Team" in text and "ABCD" not in text,text
    transcript+=text
    saved=json.loads(path.read_text());assert len(saved["News"])==3 and saved["News"][-1]["Kind"]=="team-created"
    text=play(data,"Visitor","news;q")
    assert "Captain  Created Team 1 -=- News Team" in text and "Visitor  Logged on" in text
    transcript+=text
    saved=json.loads(path.read_text());captain=dict(saved["Players"]["1"])
    # Date fixtures validate UTC selection with old history and a fresh login.
    now=datetime.datetime.now(datetime.timezone.utc)
    saved["Created"]=(now-datetime.timedelta(days=2)).isoformat()
    yesterday=(now-datetime.timedelta(days=1)).replace(hour=12,minute=0,second=0,microsecond=0)
    for entry in saved["News"]:entry["At"]=(yesterday+datetime.timedelta(seconds=entry["ID"])).isoformat()
    path.write_text(json.dumps(saved))
    text=play(data,"Captain","news yesterday;q");transcript+=text
    assert f"Yesterday ({yesterday.date().isoformat()} UTC)" in text and "Captain  Created Team 1 -=- News Team" in text
    current=json.loads(path.read_text());assert current["Players"]["1"]==captain
    # Real version-11 input has no journal fields. Migration must not invent old events.
    current["Version"]=11;current.pop("News");current.pop("NextNews")
    path.write_text(json.dumps(current))
    text=play(data,"Captain","news yesterday;q");transcript+=text
    assert "No news retained for this date." in text
    migrated=json.loads(path.read_text());assert migrated["Version"]==12 and len(migrated["News"])==1 and migrated["NextNews"]==2
    text=play(data,"Captain","c;8;x;y;8;t;1;q;y",classic=True);transcript+=text
    assert text.count("Do you want to read [T]oday's or [Y]esterday's news?")==3 and "Choose T or Y." in text
    assert "Galactic Newspaper - Today" in text and "Captain  Logged on" in text
    current=json.loads(path.read_text());at=datetime.datetime.now(datetime.timezone.utc)
    current["News"]=[{"ID":i,"At":at.isoformat(),"Kind":"login","Alias":f"VISIBLE{i}"} for i in range(1,11)]
    current["NextNews"]=11;path.write_text(json.dumps(current))
    text=play(data,"Captain","news",followups=[(b"More news? [Enter=more, Q=stop] ",b"q\r"),(b"> ",b"q\r")]);transcript+=text
    assert all(f"VISIBLE{i}  Logged on" in text for i in range(1,6)) and "VISIBLE6  Logged on" not in text
    current=json.loads(path.read_text());current["LastMaintenance"]=(now-datetime.timedelta(days=1)).date().isoformat();path.write_text(json.dumps(current))
    for repetition in range(2):
        result=subprocess.run([BINARY,"-data",str(data),"-maint"],check=True,capture_output=True,text=True);transcript+=result.stdout
        if repetition==0:maintained=path.read_bytes()
        else:assert path.read_bytes()==maintained,"same-day maintenance changed public history"
    (ROOT/"evidence/newspaper-smoke.txt").write_text("\n".join(line.rstrip() for line in transcript.splitlines())+"\n")
    print("Newspaper PTY passed: compact/classic selection, public events, UTC history, reconnect, secret exclusion, version-11 migration, paging and maintenance replay.")
