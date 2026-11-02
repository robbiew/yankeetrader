"""Bounded Wanderer initialization, hidden split transport and daily receipts in PTYs."""
import copy
import datetime
import json
import re
import subprocess
import tempfile
from pathlib import Path
from smoke_newspaper import BINARY, play, run_on_stable_date


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix="yt-wanderer-smoke-") as temp:
        root=Path(temp);seed=root/"seed"
        guard.run(subprocess.run,[BINARY,"-data",str(seed),"-init","-sectors","32"],check=True,capture_output=True)
        fresh=json.loads((seed/"world.json").read_text());planet=fresh["Planets"]["1"]
        assert fresh["Version"]==28 and planet["Wanderer"] and planet["Bank"]==250000 and planet["Owner"]==0
        assert planet["Production"]==[5000]*3 and planet["Cargo"]==[0]*3 and planet["Generation"]>=101
        assert all(planet[key]==0 for key in ("Ground","Fighters","Missiles","Mines","Plasma"))
        assert fresh["Sectors"][str(planet["Sector"])]["Planet"]==1
        guard.run(play,seed,"Mover","q")
        original=json.loads((seed/"world.json").read_text());p=original["Players"]["1"]
        p.update(Sector=8,Fighters=10000,Shields=1000000,Turns=500)
        original["Sectors"][str(planet["Sector"])]["Planet"]=0
        original["Sectors"]["8"]["Planet"]=1
        original["Sectors"]["8"]["Warps"]=[9];original["Sectors"]["9"]["Warps"]=[10]
        original["Planets"]["1"].update(Sector=8,Owner=1,Production=[0]*3,Ground=1)
        for classic in (False,True):
            for mode in ("move","cancel","budget","collision"):
                data=root/f"{classic}-{mode}";data.mkdir();path=data/"world.json";w=copy.deepcopy(original)
                if mode=="budget":w["Players"]["1"]["Turns"]=19
                if mode=="collision":
                    w["Planets"]["2"]=dict(Generation=2,ID=2,Sector=9,Owner=0,Name="Stationary",Updated=w["Created"],Production=[0]*3,Cargo=[0]*3,Fighters=0,Missiles=0,Mines=0,Plasma=0,Ground=0,Bank=17)
                    w["Sectors"]["9"]["Planet"]=2
                path.write_text(json.dumps(w))
                main=b"Main Command (?=Help)?" if classic else b"> "
                followups=[]
                if classic:followups=[(b"Planet command (?=help) [A]? ",b"!\r"),(b"destination (blank cancels): ",b"10\r")]
                if mode!="budget":followups += [(b"Engage? [y/N] ",b"n\r" if mode=="cancel" else b"y\r")]
                followups += [(main,b"q;y\r" if classic else b"leave;q\r")]
                text=guard.run(play,data,"Mover","l" if classic else "land;thrust 10",classic=classic,followups=followups)
                saved=json.loads(path.read_text());ship=saved["Players"]["1"];mobile=saved["Planets"].get("1")
                if mode in ("cancel","budget"):
                    assert mobile["Sector"]==8 and ship["Sector"]==8 and ship["Turns"]==(19 if mode=="budget" else 500) and "thrusters saved:" not in text,text
                    if mode=="budget":assert "not enough turns" in text,text
                else:
                    assert text.count("Planet thrusters saved:")==1 and "full route budget" in text,text
                    if mode=="collision" or mobile is None:
                        assert mobile is None and ship["Sector"]==8 and ship["Turns"]==500 and "Planet destroyed: true" in text,text
                        if mode=="collision":assert saved["Planets"]["2"]==w["Planets"]["2"]
                    else:
                        assert ship["Sector"]==9 and ship["Turns"]==490 and mobile["Generation"]==w["Planets"]["1"]["Generation"],text
                        assert "completed 1 hops, sector 8 -> 9" in text and "planet location unknown" in text and "planet sector " not in text,text
                        # The known ship sector may naturally equal the planet's random sector;
                        # only the private destination field must stay out of the receipt.
                        receipt=text.split("Planet thrusters saved:",1)[1].split("All landing grants revoked.",1)[0]
                        assert not re.search(r"planet (?:sector|destination) \d",receipt),receipt
                before=(ship["Sector"],ship["Turns"],ship["Fighters"])
                guard.run(play,data,"Mover","q;y" if classic else "q",classic=classic)
                reloaded=json.loads(path.read_text())["Players"]["1"]
                assert before==(reloaded["Sector"],reloaded["Turns"],reloaded["Fighters"])
                print(f"Wanderer {'classic' if classic else 'compact'} {mode}: passed")
        # Quiet protected sectors hold the finite set for an admin daily move.
        data=root/"maintenance";data.mkdir();path=data/"world.json";w=copy.deepcopy(original)
        yesterday=guard.clock()-datetime.timedelta(days=1)
        w["Created"]=yesterday.isoformat();w["LastMaintenance"]=yesterday.date().isoformat()
        for port in w["Ports"].values():port["Updated"]=guard.clock().isoformat()
        w["Planets"]["1"].update(Bank=0,Updated=guard.clock().isoformat())
        # No mobile factions are seeded, and retained positive ground prevents
        # accidental neutral planetary destruction by any newly bootstrapped group.
        w["Planets"]["1"]["Ground"]=1000000
        path.write_text(json.dumps(w))
        result=guard.run(subprocess.run,[BINARY,"-data",str(data),"-maint"],check=True,capture_output=True)
        saved=json.loads(path.read_text());mobile=saved["Planets"]["1"]
        assert mobile["Owner"]==0 and mobile["Bank"]==250000 and mobile["Generation"]==w["Planets"]["1"]["Generation"]
        assert "Wanderer maintenance saved:" in result.stdout.decode() and "sector" not in result.stdout.decode().lower()
        before=path.read_bytes();again=guard.run(subprocess.run,[BINARY,"-data",str(data),"-maint"],check=True,capture_output=True)
        assert "already current" in again.stdout.decode() and path.read_bytes()==before
    print("Wanderer PTY passed: clean schema25 bootstrap; classic/compact full-budget refusal, fresh cancellation, one paid edge, hidden destination, collision, reconnect and once-daily neutralization/refill receipt.")


if __name__=="__main__":run_on_stable_date(exercise)
