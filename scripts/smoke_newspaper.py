"""Exercise public newspaper history through real GoDoors terminals."""
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
def play(data, alias, commands, classic=False, followups=(), page_news=False):
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
    pages = 0
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
            # Opt-in for callers inspecting all public news rather than testing
            # a particular paging choice. Other flows retain explicit steps.
            marker=b"More news? [Enter=more, Q=stop] "
            if page_news and marker in pending:
                pages+=1
                assert pages<=64, "unexpected unbounded newspaper paging"
                pending=pending.split(marker,1)[1]
                os.write(master,b"\r")
                continue
            if step < len(steps) and steps[step][0] in pending:
                marker, answer = steps[step]
                pending = pending.split(marker, 1)[1]
                os.write(master, answer)
                step += 1
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired as error:
            raise AssertionError(('terminal command did not return',step,steps[step:],output.decode(errors='replace'))) from error
        text = output.decode(errors="replace").replace("\r", "")
        assert proc.returncode == 0 and step == len(steps), text
        return text
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)


class UTCDateRollover(Exception):
    pass


class UTCDateGuard:
    def __init__(self, clock):
        self.clock=clock
        self.day=clock().date()

    def check(self):
        if self.clock().date()!=self.day:
            raise UTCDateRollover()

    def run(self, action, *args, **kwargs):
        self.check()
        try:
            return action(*args, **kwargs)
        finally:
            self.check()


def run_on_stable_date(fixture, clock=lambda:datetime.datetime.now(datetime.timezone.utc), attempts=3):
    for _ in range(attempts):
        guard=UTCDateGuard(clock)
        try:
            try:
                result=fixture(guard)
            except Exception:
                guard.check()
                raise
            guard.check()
            return result
        except UTCDateRollover:
            continue
    raise AssertionError("UTC date kept changing; newspaper fixture could not finish on one date")


def run_fixture(guard):
    with tempfile.TemporaryDirectory(prefix="yt-newspaper-smoke-") as temp:
        data=Path(temp)/"world"
        guard.run(subprocess.run,[BINARY,"-data",str(data),"-init","-sectors","8"],check=True,capture_output=True)
        transcript=guard.run(play,data,"Captain","news yesterday;news;q")
        assert "Galactic Newspaper - Yesterday" in transcript and "No news retained for this date." in transcript
        assert "Captain  Logged on" in transcript
        path=data/"world.json";saved=json.loads(path.read_text())
        assert saved["Version"]==28 and len(saved["News"])==1 and saved["NextNews"]==2
        assert saved["Players"]["1"]["Credits"]==1005 and saved["Players"]["1"]["Turns"]==500
        text=guard.run(play,data,"Captain","team;2;News Team",followups=[
            (b"Team password (4 characters; entered separately): ",b"ABCD\r"),
            (b"Team Command? ",b"1;news;q\r")])
        assert "Captain  Created Team 1 -=- News Team" in text and "ABCD" not in text,text
        transcript+=text
        saved=json.loads(path.read_text());assert len(saved["News"])==3 and saved["News"][-1]["Kind"]=="team-created"
        text=guard.run(play,data,"Visitor","news;q")
        assert "Captain  Created Team 1 -=- News Team" in text and "Visitor  Logged on" in text
        transcript+=text
        saved=json.loads(path.read_text());captain=dict(saved["Players"]["1"])
        # Date fixtures validate UTC selection with old history and a fresh login.
        now=guard.clock()
        saved["Created"]=(now-datetime.timedelta(days=2)).isoformat()
        yesterday=(now-datetime.timedelta(days=1)).replace(hour=12,minute=0,second=0,microsecond=0)
        for entry in saved["News"]:entry["At"]=(yesterday+datetime.timedelta(seconds=entry["ID"])).isoformat()
        path.write_text(json.dumps(saved))
        text=guard.run(play,data,"Captain","news yesterday;q");transcript+=text
        assert f"Yesterday ({yesterday.date().isoformat()} UTC)" in text and "Captain  Created Team 1 -=- News Team" in text
        current=json.loads(path.read_text());assert current["Players"]["1"]==captain
        # Real version-11 input has no journal fields. Migration must not invent old events.
        current.pop("NextBattleReport",None)
        for p in current["Players"].values():p.pop("LastActivity",None)
        # Schema 11 predates the explicit Wanderer identity and slot 1.
        mobile=current["Planets"].pop("1",None)
        if mobile: current["Sectors"][str(mobile["Sector"])]["Planet"]=0
        current["Version"]=11; current.pop("Season",None); current.pop("GenerationSeed",None);current.pop("News");current.pop("NextNews")
        current.pop("NextPlanetGeneration",None)
        for planet in current.get("Planets",{}).values(): planet.pop("Generation",None)
        path.write_text(json.dumps(current))
        text=guard.run(play,data,"Captain","news yesterday;q");transcript+=text
        assert "No news retained for this date." in text
        migrated=json.loads(path.read_text());assert migrated["Version"]==28 and len(migrated["News"])==1 and migrated["NextNews"]==2
        text=guard.run(play,data,"Captain","c;8;x;y;8;t;1;q;y",classic=True);transcript+=text
        assert text.count("Do you want to read [T]oday's or [Y]esterday's news?")==3 and "Choose T or Y." in text
        assert "Galactic Newspaper - Today" in text and "Captain  Logged on" in text
        current=json.loads(path.read_text());at=guard.clock()
        current["News"]=[{"ID":i,"At":at.isoformat(),"Kind":"login","Alias":f"VISIBLE{i}"} for i in range(1,11)]
        current["NextNews"]=11;path.write_text(json.dumps(current))
        text=guard.run(play,data,"Captain","news",followups=[(b"More news? [Enter=more, Q=stop] ",b"q\r"),(b"> ",b"q\r")]);transcript+=text
        assert all(f"VISIBLE{i}  Logged on" in text for i in range(1,6)) and "VISIBLE6  Logged on" not in text
        current=json.loads(path.read_text());current["LastMaintenance"]=(now-datetime.timedelta(days=1)).date().isoformat();path.write_text(json.dumps(current))
        for repetition in range(2):
            result=guard.run(subprocess.run,[BINARY,"-data",str(data),"-maint"],check=True,capture_output=True,text=True);transcript+=result.stdout
            if repetition==0:maintained=path.read_bytes()
            else:assert path.read_bytes()==maintained,"same-day maintenance changed public history"
        return transcript


if __name__=="__main__":
    transcript=run_on_stable_date(run_fixture)
    (ROOT/"evidence/newspaper-smoke.txt").write_text("\n".join(line.rstrip() for line in transcript.splitlines())+"\n")
    print("Newspaper PTY passed: compact/classic selection, public events, UTC history, reconnect, secret exclusion, version-11 migration, paging and maintenance replay.")
