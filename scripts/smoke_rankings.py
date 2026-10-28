"""Exercise player/team rankings through real GoDoors terminal sessions."""
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


def play(data, alias, commands, classic=False, extra_steps=None):
    master, slave = pty.openpty()
    options = ["-ascii"] if classic else ["-compact"]
    proc = subprocess.Popen([BINARY, *options, "-data", str(data), "-local", alias],
                            stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    steps = [(b"[ Press any Key ]", b" ")] * 3 if classic else []
    steps += [(b"Main Command (?=Help)?" if classic else b"> ", commands.encode() + b"\r")]
    steps += extra_steps or []
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


with tempfile.TemporaryDirectory(prefix="yt-rankings-smoke-") as temp:
    data = Path(temp) / "world"
    subprocess.run([BINARY, "-data", str(data), "-init", "-sectors", "8"], check=True, capture_output=True)
    for alias in ("Captain", "Member", "Third"):
        play(data, alias, "q")
    password_steps = [(b"Team password (4 characters; entered separately): ", b"ABCD\r"),
                      (b"Team change saved.", b"1;q\r")]
    transcript = play(data, "Captain", "team;2;Orion", extra_steps=password_steps)
    transcript += play(data, "Member", "team;3;1", extra_steps=password_steps)
    path = data / "world.json"
    world = json.loads(path.read_text())
    for n, player in world["Players"].items():
        player["StoredScore"] = 666 + 111 * int(n)
    world["Players"]["1"]["Turns"] = 0
    world["Ports"]["2"].update(Owner=1, Treasury=987654)
    world["Sectors"]["3"]["Defense"] = dict(Owner=2, Fighters=100)
    path.write_text(json.dumps(world))
    play(data, "Captain", "q")
    play(data, "Captain", "q;y", classic=True)
    before = json.loads(path.read_text())
    text = play(data, "Captain", "c;4;o;1;q;y", classic=True)
    transcript += text
    assert "Stored scores;" in text and "777" in text and "Orion" in text, text
    actual = json.loads(path.read_text())["Players"]
    assert actual == before["Players"], {n:{k:(before["Players"][n].get(k),v) for k,v in p.items() if before["Players"][n].get(k)!=v} for n,p in actual.items()}

    def score(world, player):
        ports = sum(p["ID"] != 1 and p["Owner"] == player["ID"] for p in world["Ports"].values())
        defenses = sum(s.get("Defense", {}).get("Fighters", 0) for s in world["Sectors"].values()
                       if s.get("Defense", {}).get("Owner") == player["ID"])
        return (50*player["Shields"] + 100*(player["Fighters"]+defenses) + 2500*player["Holds"]
                + sum(a*b for a,b in zip(player["Cargo"], (20,30,40))) + player["Credits"]
                + 1000*player["Missiles"] + 1000000*player["Plasma"] + 50000*ports
                + 750*player["Ground"] + 2500*player["Mines"])

    expected = {n: score(before, p) for n,p in before["Players"].items()}
    text = play(data, "Captain", "c;4;;1;q;y", classic=True)
    transcript += text
    assert "Updated scores saved" in text and "Player Rankings" in text and "Team Rankings" in text, text
    assert re.search(str(expected["1"]+expected["2"]) + r"\s+1\s+Orion", text), text
    assert "987654" not in text and "ABCD" not in text and "local:" not in text, text
    saved = json.loads(path.read_text())
    for n,p in saved["Players"].items():
        assert p["StoredScore"] == expected[n]
        p = {k:v for k,v in p.items() if k != "StoredScore"}
        assert p == {k:v for k,v in before["Players"][n].items() if k != "StoredScore"}
    for key in ("Ports", "Planets", "Sectors", "Teams"):
        assert saved[key] == before[key], key
    text = play(data, "Captain", "rank old;q")
    transcript += text
    assert str(expected["1"]) in text and json.loads(path.read_text())["Players"]["1"]["Turns"] == 0
    saved["Ports"]["2"]["Owner"] = 2
    path.write_text(json.dumps(saved))
    transcript += play(data, "Captain", "rank;q")
    after = json.loads(path.read_text())
    assert after["Players"]["1"]["StoredScore"] == expected["1"] - 50000
    assert after["Players"]["2"]["StoredScore"] == expected["2"] + 50000
    (ROOT / "evidence/rankings-smoke.txt").write_text("\n".join(line.rstrip() for line in transcript.splitlines())+"\n")
    print("Rankings PTY passed: classic option 4, stored/fresh scores, zero turns, team totals, private fields excluded, ownership transfer and saved caches.")
