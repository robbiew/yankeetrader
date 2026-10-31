"""Exercise navigation, persistent avoid lists and Ctrl-X through real GoDoors PTYs."""
from smoke_arrival_control import without_disruption, reject_disruption
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


@without_disruption
def play(data, commands, confirmation=None):
    master,slave = pty.openpty()
    proc = subprocess.Popen([binary,'-compact',"-data",str(data),"-local","Navigator"],stdin=slave,stdout=slave,stderr=slave)
    os.close(slave)
    chunks = []
    sent = confirmed = False
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
                reject_disruption(b''.join(chunks))
                text = b"".join(chunks)
                if not sent and b"> " in text:
                    os.write(master,commands)
                    sent = True
                if confirmation is not None and not confirmed and b"Engage autopilot?" in text:
                    os.write(master,confirmation)
                    confirmed = True
        proc.wait(timeout=2)
    finally:
        if proc.poll() is None: proc.kill();proc.wait()
        os.close(master)
    transcript = b"".join(chunks).decode().replace("\r","")
    assert proc.returncode == 0,transcript
    assert "Saved. Safe travels" in transcript,transcript
    return transcript


with tempfile.TemporaryDirectory(prefix="yt-navigation-smoke-") as temp:
    data = Path(temp) / "world"
    subprocess.run([binary,"-data",str(data),"-init","-sectors","8"],check=True,capture_output=True)
    path = data / "world.json"
    world = json.loads(path.read_text())
    for start,warps in {1:[2,5],2:[3],3:[4],4:[1],5:[6],6:[4]}.items():
        world["Sectors"][str(start)]["Warps"] = warps
    path.write_text(json.dumps(world))
    transcript = play(data,b"s;avoid 1 2;avoid;path 1 4;auto 4;n;auto 4;y;i;q\r")
    for text in ["[ Sensors Activated ]","Sector: 2","Slot 1: sector 2",
                 "Shortest path: [1 5 6 4] | 3 turns.","Autopilot cancelled.","Moved to sector 4."]:
        assert text in transcript,text+"\n"+transcript
    player = json.loads(path.read_text())["Players"]["1"]
    assert (player["Sector"],player["Turns"],player["Credits"],player["AvoidSectors"][0]) == (4,497,1005,2),player
    reconnect = play(data,b"avoid;avoid 1 0;avoid;q\r")
    assert "Slot 1: sector 2" in reconnect and "None." in reconnect,reconnect
    transcript += reconnect
    # Confirmation and Ctrl-X are sent together; unrelated queued Q must survive polling.
    interrupted = play(data,b"auto 3\r",b"y\r\x18q\r")
    assert "Autopilot stopped." in interrupted,interrupted
    transcript += interrupted
    player = json.loads(path.read_text())["Players"]["1"]
    assert (player["Sector"],player["Turns"],player["AvoidSectors"][0]) == (4,497,0),player
    (root / "evidence/navigation-smoke.txt").write_text(transcript)
    print("PTY/GoDoors navigation passed: sensors, avoided directed path, cancelled/accepted autopilot, reconnect/clear, Ctrl-X and queued-key preservation; exact persisted turns.")
