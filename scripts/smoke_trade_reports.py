"""Real terminal nearest-port filters and directed trade forecasts; no trades."""
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

ROOT = Path(__file__).resolve().parents[1]
BINARY = str(ROOT / "bin/yt")


@without_disruption
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


with tempfile.TemporaryDirectory(prefix="yt-trade-reports-") as temp:
    data = Path(temp) / "world"
    subprocess.run([BINARY, "-data", str(data), "-init", "-sectors", "8"], check=True, capture_output=True)
    play(data, "Caller", "q")
    play(data, "Owner", "q")
    path = data / "world.json"
    world = json.loads(path.read_text())
    world["Players"]["1"].update(Sector=7, Turns=0)
    for sector in world["Sectors"].values():
        sector["Warps"] = []
    for start, end in {7: 2, 2: 3, 3: 4, 4: 5, 5: 7}.items():
        world["Sectors"][str(start)]["Warps"] = [end]
    for port_id in list(world["Ports"]):
        if int(port_id) > 3:
            world["Sectors"][str(world["Ports"][port_id]["Sector"])]["Port"] = 0
            del world["Ports"][port_id]
    # Controlled Go quotes match the captured DOS 10/44 and 30/15 sample;
    # existing Go pricing stays authoritative rather than importing DOS prices.
    world["Ports"]["2"].update(Name="First Market", Coefficient=[50, -45, -55])
    world["Ports"]["3"].update(Name="Second Market", Coefficient=[-50, 50, -55])
    path.write_text(json.dumps(world))
    play(data, "Caller", "q")
    baseline = json.loads(path.read_text())

    text = play(data, "Caller", "c;14;A;14;3;S;16;17;1;q;y", classic=True)
    transcript = text
    for want in ["Distance: 1 | Sector: 2 | First Market", "Distance: 2 | Sector: 3 | Second Market", "S ore @ 30", "Spread: 49 credits/unit of each", "Return: 4", "no accessible cargo trading port in your sector"]:
        assert want in text, text
    saved = json.loads(path.read_text())
    assert saved["Players"]["1"]["Turns"] == 0 and saved["Players"]["1"]["Sector"] == 7
    assert saved["Ports"] == baseline["Ports"]

    world = saved
    world["Players"]["1"].update(Sector=2, Holds=100)
    path.write_text(json.dumps(world))
    text = play(data, "Caller", "pairs;profits;nearest team;q")
    transcript += text
    assert text.count("Spread: 49 credits/unit of each") == 2 and "Approach: 0 warps" in text, text
    assert "don't belong to a team" in text, text

    world = json.loads(path.read_text())
    world["Sectors"]["3"]["Warps"] = [2, 4]
    path.write_text(json.dumps(world))
    text = play(data, "Caller", "profits;q")
    transcript += text
    assert "Spread: 49 credits/unit of each" in text and "Return: 1" in text, text

    world = json.loads(path.read_text())
    world["Sectors"]["3"]["Warps"] = [4]
    world["Players"]["1"]["AvoidSectors"] = [4]
    path.write_text(json.dumps(world))
    text = play(data, "Caller", "profits;nearest;q")
    transcript += text
    assert "No matching accessible" in text and "Spread:" not in text and "Second Market" in text, text

    world = json.loads(path.read_text())
    world["Players"]["1"]["AvoidSectors"] = []
    world["Sectors"]["3"]["Defense"] = dict(Owner=2, Fighters=50)
    path.write_text(json.dumps(world))
    text = play(data, "Caller", "nearest ore sell;pairs;profits;q")
    transcript += text
    assert "Second Market" not in text and "Spread:" not in text, text
    assert text.count("No matching accessible") == 3, text
    saved = json.loads(path.read_text())
    assert saved["Ports"] == baseline["Ports"]
    assert saved["Players"]["1"]["Credits"] == 1005 and saved["Players"]["1"]["Turns"] == 0
    assert saved["Players"]["1"]["Sector"] == 2 and not saved["Players"]["1"]["DockToken"]
    (ROOT / "evidence/trade-reports-smoke.txt").write_text(transcript)
    print("Trade reports PTY passed: computer 14/16/17, player-side filters, 49-credit spread independent of holds, directed return distance, avoids, guarded markets and zero-turn/account conservation.")
