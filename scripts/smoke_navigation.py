"""Exercise navigation through real PTY/GoDoors input with a disposable world."""
from pathlib import Path
import errno
import json
import os
import pty
import select
import subprocess
import tempfile
import time

root = Path(__file__).resolve().parents[1]
binary = str(root / "bin/yt")
with tempfile.TemporaryDirectory(prefix="yt-navigation-smoke-") as temp:
    data = Path(temp) / "world"
    subprocess.run([binary,"-data",str(data),"-init","-sectors","8"],check=True,capture_output=True)
    path = data / "world.json"
    world = json.loads(path.read_text())
    for start,end in [(1,2),(2,3),(3,4)]:
        world["Sectors"][str(start)]["Warps"] = [end]
    path.write_text(json.dumps(world))
    master,slave = pty.openpty()
    proc = subprocess.Popen([binary,"-data",str(data),"-local","Navigator"],stdin=slave,stdout=slave,stderr=slave)
    os.close(slave)
    chunks = []
    sent = False
    deadline = time.monotonic()+20
    try:
        while time.monotonic()<deadline:
            if select.select([master],[],[],.1)[0]:
                try:
                    chunk = os.read(master,65536)
                except OSError as err:
                    if err.errno == errno.EIO: break
                    raise
                if not chunk: break
                chunks.append(chunk)
                if not sent and b"> " in b"".join(chunks):
                    os.write(master,b"s;path 1 4;auto 4;n;auto 4;y;i;q\r")
                    sent = True
        proc.wait(timeout=2)
    finally:
        if proc.poll() is None: proc.kill();proc.wait()
        os.close(master)
    transcript = b"".join(chunks).decode().replace("\r","")
    assert proc.returncode == 0,transcript
    for text in ["[ Sensors Activated ]","Sector: 2","Shortest path: [1 2 3 4] | 3 turns.",
                 "Autopilot cancelled.","Moved to sector 4.","Saved. Safe travels"]:
        assert text in transcript,text+"\n"+transcript
    player = json.loads(path.read_text())["Players"]["1"]
    assert (player["Sector"],player["Turns"],player["Credits"]) == (4,497,1005),player
    (root / "evidence/navigation-smoke.txt").write_text(transcript)
    print("PTY/GoDoors navigation passed: sensors, directed path, cancelled and accepted autopilot, exact persisted turn cost.")
