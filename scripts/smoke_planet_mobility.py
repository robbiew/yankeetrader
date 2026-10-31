"""Planet thrusters and player forced landing through real classic/compact PTYs."""
import copy
import json
import subprocess
import tempfile
from pathlib import Path
from smoke_newspaper import BINARY, play, run_on_stable_date


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix="yt-planet-mobility-") as temp:
        root=Path(temp);seed=root/"seed"
        guard.run(subprocess.run,[BINARY,"-data",str(seed),"-init","-sectors","32"],check=True,capture_output=True)
        guard.run(play,seed,"Mover","q")
        original=json.loads((seed/"world.json").read_text())
        p=original["Players"]["1"];p.update(Sector=8,Credits=100000,Ground=1000000,Fighters=10000,Shields=1000000)
        original["Sectors"]["8"]["Warps"]=[9];original["Sectors"]["9"]["Warps"]=[10]
        # Canonical whole-second timestamps keep exact untouched-target checks
        # independent of Go trimming trailing fractional-second zeroes.
        original["Planets"]["2"]=dict(Generation=2,ID=2,Sector=8,Owner=1,Name="Mobile",Updated=guard.clock().replace(microsecond=0).isoformat().replace("+00:00","Z"),Production=[0,0,0],Cargo=[0,0,0],Fighters=0,Missiles=0,Mines=0,Plasma=0,Ground=1,Bank=0)
        original["Sectors"]["8"]["Planet"]=2
        for classic in (False,True):
            for mode in ("move","collision","assault","adoption","cancel"):
                data=root/f"{classic}-{mode}";data.mkdir();path=data/"world.json"
                w=copy.deepcopy(original)
                if mode=="collision":
                    target=copy.deepcopy(w["Planets"]["2"]);target.update(ID=3,Generation=3,Sector=10,Name="Stationary")
                    w["Planets"]["3"]=target;w["Sectors"]["10"]["Planet"]=3
                if mode=="assault":
                    enemy=copy.deepcopy(p);enemy.update(ID=2,Identity="local:Enemy",Alias="Enemy",Sector=11)
                    w["Players"]["2"]=enemy;w["NextPlayer"]=3;w["Planets"]["2"]["Owner"]=2
                if mode=="adoption":w["Planets"]["2"]["Owner"]=0
                path.write_text(json.dumps(w))
                main=b"Main Command (?=Help)?" if classic else b"> "
                quit_keys=b"q;y\r" if classic else b"leave;q\r"
                followups=[]
                if mode in ("assault","adoption"):
                    if mode=="assault":followups += [(b"Do you wish to try to force a landing? [y/N] ",b"y\r"),(b"(0/blank cancels): ",b"1000000\r")]
                    followups += [(b"[y/N] ",b"y\r")]
                    followups += [(b"Planet command (?=help) [A]? ",b"l;q;y\r")] if classic else [(main,quit_keys)]
                    command="l" if classic else "land"
                else:
                    command="l" if classic else "land;thrust 10"
                    if classic:followups += [(b"Planet command (?=help) [A]? ",b"!\r"),(b"destination (blank cancels): ",b"10\r")]
                    followups += [(b"Engage? [y/N] ",b"n\r" if mode=="cancel" else b"y\r"),(main,quit_keys)]
                text=guard.run(play,data,"Mover",command,classic=classic,followups=followups)
                saved=json.loads(path.read_text());ship=saved["Players"]["1"]
                assert saved["Version"]==25 and saved["NextPlanetGeneration"]>=101,text
                if mode=="cancel":assert ship["Sector"]==8 and ship["Turns"]==500 and saved["Planets"]["2"]["Sector"]==8 and "thrusters saved:" not in text,text
                elif mode in ("move","collision"):
                    assert text.count("Planet thrusters saved:")==1,text
                    planet=saved["Planets"].get("2")
                    if mode=="collision" or planet is None:
                        assert planet is None and "Planet destroyed: true" in text,text
                        # Natural stress may destroy the moving planet before the
                        # intended collision; both are physical committed outcomes.
                        assert ship["Sector"] in (8,9) and ship["Turns"]==500-10*(ship["Sector"]-8),text
                    else:assert ship["Sector"]==10 and ship["Turns"]==480 and planet["Sector"]==10,text
                    if mode=="collision":assert saved["Planets"]["3"]==w["Planets"]["3"],text
                else:
                    assert text.count("Ground action saved")==1 and saved["Planets"]["2"]["Owner"]==1 and ship["Turns"]==500,text
                    assert ship["Ground"]==(0 if mode=="assault" else 1000000),text
                    news=[e for e in saved["News"] if e["Kind"]=="player-planet-assault"]
                    assert len(news)==1 and news[0]["Outcome"]==("captured" if mode=="assault" else "adopted"),news
                assert not ship["PlanetToken"],ship
                # Reconnect has no pending confirmation and cannot repay/repeat.
                before=(ship["Turns"],ship["Ground"],ship["Fighters"])
                guard.run(play,data,"Mover","q;y" if classic else "q",classic=classic)
                reloaded=json.loads(path.read_text())["Players"]["1"]
                assert before==(reloaded["Turns"],reloaded["Ground"],reloaded["Fighters"])
                print(f"planet mobility {'classic' if classic else 'compact'} {mode}: passed")

if __name__=="__main__":run_on_stable_date(exercise)
