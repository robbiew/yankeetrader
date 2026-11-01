"""Exercise team fanout and private read state through real GoDoors terminals."""
from smoke_arrival_control import without_disruption, reject_disruption
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


@without_disruption
def play(data, alias, commands, classic=False, body=None, action="s", password=None):
    master, slave = pty.openpty()
    options = ["-ascii"] if classic else ["-compact"]
    proc = subprocess.Popen([BINARY, *options, "-data", str(data), "-local", alias],
                            stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    steps = [(b"[ Press any Key ]", b" ")] * 3 if classic else []
    steps += [(b"Main Command (?=Help)?" if classic else b"> ", commands.encode() + b"\r")]
    if password is not None:
        steps += [(b"Team password (4 characters; entered separately): ",password.encode()+b"\r"),
                  (b"Team change saved.",b"1;q\r")]
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
            reject_disruption(output)
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


with tempfile.TemporaryDirectory(prefix="yt-team-radio-smoke-") as temp:
    data=Path(temp)/"world"
    subprocess.run([BINARY,"-data",str(data),"-init","-sectors","8"],check=True,capture_output=True)
    for alias in ("Sender","Member","Visitor"):play(data,alias,"q")
    transcript=play(data,"Sender","team;2;Orion",password="ABCD")
    transcript+=play(data,"Member","team;3;1",password="ABCD")
    path=data/"world.json";before=json.loads(path.read_text())
    text="TEAM RADIO PROBE; literal/"
    out=play(data,"Sender","radio team;y;ignored;s",body=text);transcript+=out
    saved=json.loads(path.read_text())
    assert saved["Version"]==26 and len(saved["Radio"])==2
    assert [m["To"]for m in saved["Radio"]]==[1,2]
    assert all(m["Text"]==text for m in saved["Radio"])
    assert not saved["Radio"][0]["Unread"] and saved["Radio"][1]["Unread"]
    assert saved["Players"]==before["Players"],"Team radio changed resources or membership"
    assert "team Orion (#1)"in out and "  Sender (#1)"in out and "  Member (#2)"in out and "2 team copies saved."in out
    out=play(data,"Visitor","messages;q");transcript+=out;assert text not in out
    # Delivery stays with original recipients after leaving a team.
    transcript+=play(data,"Member","team;4;y;1;q")
    out=play(data,"Member","messages;q");transcript+=out;assert text in out
    saved=json.loads(path.read_text());assert not saved["Radio"][1]["Unread"]
    transcript+=play(data,"Visitor","team;3;1",password="ABCD")
    out=play(data,"Visitor","messages;q");transcript+=out;assert text not in out
    transcript+=play(data,"Sender","radio team;y",body="ABORT TEAM PROBE",action="a")
    assert len(json.loads(path.read_text())["Radio"])==2
    out=play(data,"Sender","c;5;TEAM;y",classic=True,body="CLASSIC TEAM PROBE");transcript+=out
    saved=json.loads(path.read_text());assert len(saved["Radio"])==4
    assert [m["To"]for m in saved["Radio"][-2:]]==[1,3]
    assert "2 team copies saved."in out
    out=play(data,"Member","messages;q");transcript+=out;assert "CLASSIC TEAM PROBE"not in out
    out=play(data,"Visitor","messages;q");transcript+=out;assert "CLASSIC TEAM PROBE"in out
    assert "ABCD"not in transcript
    (ROOT/"evidence/team-radio-smoke.txt").write_text("\n".join(line.rstrip()for line in transcript.splitlines())+"\n")
    print("Team radio PTY passed: real team creation/join, compact/classic sends, independent copies, abort, private history and membership-change delivery.")
