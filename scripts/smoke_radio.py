"""Exercise persisted direct radio through real GoDoors terminals."""
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


with tempfile.TemporaryDirectory(prefix="yt-radio-smoke-") as temp:
    data = Path(temp) / "world"
    subprocess.run([BINARY, "-data", str(data), "-init", "-sectors", "8"], check=True, capture_output=True)
    for alias in ("Sender", "Enemy", "Visitor"):
        play(data, alias, "q")
    path = data / "world.json"
    before = json.loads(path.read_text())
    message = "YT RADIO PROBE; literal/"
    transcript = play(data, "Sender", "radio Enemy;y;ignored;s", body=message)
    saved = json.loads(path.read_text())
    assert saved["Version"] == 27 and len(saved["Radio"]) == 1
    assert saved["Radio"][0]["Text"] == message and saved["Radio"][0]["Unread"]
    assert saved["Players"] == before["Players"], "Radio spent assets or turns"
    text = play(data, "Visitor", "messages;q")
    transcript += text
    assert message not in text
    text = play(data, "Enemy", "messages;q")
    transcript += text
    assert "New radio messages:" in text and text.count(message) == 2, text
    assert not json.loads(path.read_text())["Radio"][0]["Unread"]
    text = play(data, "Enemy", "q")
    transcript += text
    assert message not in text and "New radio messages:" not in text
    transcript += play(data, "Sender", "radio Enemy;y", body="ABORTED PROBE", action="a")
    assert len(json.loads(path.read_text())["Radio"]) == 1
    text = play(data, "Sender", "c;5;Enemy;y", classic=True, body="CLASSIC RADIO PROBE")
    transcript += text
    assert "Transmission successful!" in text and "Message to: Enemy * From: Sender" in text
    assert len(json.loads(path.read_text())["Radio"]) == 2
    (ROOT / "evidence/radio-smoke.txt").write_text("\n".join(line.rstrip() for line in transcript.splitlines()) + "\n")
    print("Radio PTY passed: literal body, fresh send/abort, private sent/received history, login delivery, reconnect and classic computer 5/6.")
