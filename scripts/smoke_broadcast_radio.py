"""Exercise explicit ALL broadcasts through compact/classic GoDoors terminals."""
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
def play(data, alias, commands, classic=False, body=None, action="s", password=None, page_news=False):
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
                   b"1;q;y\r" if classic else b"q\r")]
    if page_news:
        steps += [(b"Computer command (?=help)?" if classic else b"> ", b"1;q;y\r" if classic else b"q\r")]
    pages = 0
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
            marker = b"More news? [Enter=more, Q=stop] "
            if page_news and marker in pending:
                pages += 1
                assert pages <= 64, "unbounded newspaper paging"
                pending = pending.split(marker, 1)[1]
                os.write(master, b"\r")
                continue
            if step < len(steps) and steps[step][0] in pending:
                marker, answer = steps[step]
                pending = pending.split(marker, 1)[1]
                os.write(master, answer)
                step += 1
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired as error:
            raise AssertionError(("terminal did not return", step, steps[step:], output.decode(errors="replace"))) from error
        text = output.decode(errors="replace").replace("\r", "")
        assert proc.returncode == 0 and step == len(steps), text
        return text
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)


with tempfile.TemporaryDirectory(prefix="yt-broadcast-smoke-")as temp:
    data=Path(temp)/"world"
    subprocess.run([BINARY,"-data",str(data),"-init","-sectors","8"],check=True,capture_output=True)
    for alias in ("Sender","Able","Baker"):play(data,alias,"q")
    path=data/"world.json";before=json.loads(path.read_text())
    message="ALL BROADCAST; literal/"
    transcript=play(data,"Sender","radio ALL;y;ignored;s",body=message)
    saved=json.loads(path.read_text())
    assert saved["Version"]==27 and len(saved["Radio"])==3
    assert [m["To"]for m in saved["Radio"]]==[1,2,3]
    assert all(m["Text"]==message for m in saved["Radio"])
    assert "ALL 3 current active accounts (including you)"in transcript and "3 broadcast copies saved."in transcript
    news=[e for e in saved["News"] if e["Kind"]=="radio-broadcast"]
    assert len(news)==1 and news[0]["BroadcastText"]==message and news[0]["Alias"]=="Sender"
    assert "PUBLIC: This exact text and your alias" in transcript and "Public newspaper entry saved." in transcript
    assert saved["Players"]==before["Players"],"Broadcast changed assets or turns"
    out=play(data,"Able","messages;q");transcript+=out;assert out.count(message)==2,out
    saved=json.loads(path.read_text());assert not saved["Radio"][1]["Unread"] and saved["Radio"][2]["Unread"]
    out=play(data,"Able","q");transcript+=out;assert message not in out
    out=play(data,"Baker","messages;q");transcript+=out;assert out.count(message)==2,out
    out=play(data,"Later","messages;q");transcript+=out;assert message not in out
    transcript+=play(data,"Sender","radio all;y",body="ABORT BROADCAST",action="a")
    assert len(json.loads(path.read_text())["Radio"])==3
    assert len([e for e in json.loads(path.read_text())["News"] if e["Kind"]=="radio-broadcast"])==1
    out=play(data,"Sender","c;5;ALL;y",classic=True,body="CLASSIC BROADCAST");transcript+=out
    saved=json.loads(path.read_text());assert len(saved["Radio"])==7
    assert [m["To"]for m in saved["Radio"][-4:]]==[1,2,3,4]
    assert "4 broadcast copies saved."in out
    out=play(data,"Later","messages;q");transcript+=out;assert "CLASSIC BROADCAST"in out and message not in out
    for classic in (False,True):
        out=play(data,"Later","news today" if not classic else "c;8;t",classic=classic,page_news=True)
        transcript+=out
        assert "Sender [PUBLIC BROADCAST]"in out and message in out and "CLASSIC BROADCAST"in out,out
        assert "ABORT BROADCAST"not in out,out
    news=[e for e in json.loads(path.read_text())["News"]if e["Kind"]=="radio-broadcast"]
    assert len(news)==2,"Reconnect or reading duplicated publication"
    (ROOT/"evidence/broadcast-radio-smoke.txt").write_text("\n".join(line.rstrip()for line in transcript.splitlines())+"\n")
    print("Broadcast PTY passed: explicit compact/classic ALL confirmation, literal body, abort, private copies, independent reads, no repeats, later-account private isolation and public newspaper publication in both interfaces.")
