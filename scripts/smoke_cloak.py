"""Verify saved cloak and hidden/visible sensor output through real GoDoors PTYs."""
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


with tempfile.TemporaryDirectory(prefix="yt-cloak-smoke-") as temp:
    data = Path(temp) / "world"
    subprocess.run([binary,"-data",str(data),"-init","-sectors","8"],check=True,capture_output=True)
    transcript = play(data,b"q\r")
    path = data / "world.json"
    world = json.loads(path.read_text())
    observer = world["Players"]["1"]
    assert observer["Cloak"] == 1
    observer["Cloak"] = .37
    world["Sectors"]["1"]["Warps"] = [2]
    for ident,alias,cloak in [(2,"HiddenPilot",1),(3,"VisiblePilot",0)]:
        ship = dict(observer)
        ship.update(ID=ident,Identity="fixture:"+alias,Alias=alias,Sector=2,Cloak=cloak)
        world["Players"][str(ident)] = ship
    world["NextPlayer"] = 4
    path.write_text(json.dumps(world))
    observed = play(data,b"s;s;i;q\r")
    assert "HiddenPilot" not in observed, observed
    assert observed.count("VisiblePilot") == 2, observed
    assert "Cloak energy: 37%" in observed, observed
    saved = json.loads(path.read_text())
    assert saved["Players"]["1"]["Cloak"] == .37
    assert saved["Players"]["2"]["Cloak"] == 1
    reconnect = play(data,b"s;i;q\r")
    assert "HiddenPilot" not in reconnect and "Cloak energy: 37%" in reconnect
    transcript += observed + reconnect
    (root / "evidence/cloak-smoke.txt").write_text(transcript)
    print("Real PTY cloak persistence, hidden sensors and reconnect checks passed.")
