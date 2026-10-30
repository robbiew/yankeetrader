"""Genesis confirmation, atomic new-season state and history through real terminals."""
import copy
import json
import subprocess
import tempfile
from pathlib import Path
from smoke_newspaper import BINARY, play, run_on_stable_date


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix="yt-genesis-smoke-") as temp:
        root = Path(temp)
        seed = root / "seed"
        guard.run(subprocess.run, [BINARY, "-data", str(seed), "-init", "-sectors", "32"], check=True, capture_output=True)
        guard.run(play, seed, "Winner", "q")
        original = json.loads((seed / "world.json").read_text())
        original["GenesisPorts"] = 20
        original["LotteryDailyLimit"] = 0
        for n in range(2, 22):
            original["Ports"][str(n)]["Owner"] = 1
        original["Players"]["1"]["StoredScore"] = 999999999
        for value in (-1, 0, 19, 20, 300, 301):
            configured = root / ("config-" + str(value))
            result = guard.run(subprocess.run, [BINARY, "-data", str(configured), "-init", "-sectors", "32", "-genesis-ports", str(value)], capture_output=True)
            valid = value in (0, 20, 300)
            assert (result.returncode == 0) == valid, (value, result.stderr)
            assert (configured / "world.json").exists() == valid
            if valid:
                config = json.loads((configured / "world.json").read_text())
                assert config["GenesisPorts"] == value and config["Season"] == 1
        invalid_mode = guard.run(subprocess.run, [BINARY, "-data", str(seed), "-maint", "-genesis-ports", "0"], capture_output=True)
        assert invalid_mode.returncode != 0 and b"only supported with -init" in invalid_mode.stderr
        for classic in (False, True):
            data = root / str(classic)
            data.mkdir()
            path = data / "world.json"
            world = copy.deepcopy(original)
            path.write_text(json.dumps(world))
            command_prompt = b"Main Command (?=Help)?" if classic else b"> "
            # Queued destructive answer is discarded. Lowercase and chained
            # confirmation also cancel; only a separately entered literal works.
            text = guard.run(play, data, "Winner", "g;GENESIS;q", classic=classic, followups=[
                (b"Type GENESIS to confirm this reset (blank cancels): ", b"genesis\r"),
                (command_prompt, b"g\r"),
                (b"Type GENESIS to confirm this reset (blank cancels): ", b"GENESIS;q\r"),
                (command_prompt, b"g\r"),
                (b"Type GENESIS to confirm this reset (blank cancels): ", b"GENESIS\r"),
            ])
            assert text.count("Genesis cancelled; universe unchanged.") == 2, text
            assert text.count("Genesis saved: Winner won season 1 with 20 ports (required 20)") == 1, text
            assert "ENTIRE universe" in text and "This login has ended; reconnect to join." in text, text
            saved = json.loads(path.read_text())
            assert saved["Version"] == 23 and saved["Season"] == 2 and saved["Players"] == {} and saved["NextPlayer"] == 1
            assert saved["Teams"] == {} and not saved.get("Radio") and not saved.get("News")
            assert len(saved["Planets"]) == 2 and saved["Xannor"]["HQ"] > 7
            assert saved["LotteryDailyLimit"] == 0 and saved["GenesisPorts"] == 20 and "GenerationSeed" in saved
            assert all(p["Owner"] == 0 and p["Treasury"] == 0 for p in saved["Ports"].values())
            assert all(not s.get("Minefield") and not s.get("Defense") for s in saved["Sectors"].values())
            result = saved["SeasonResults"][0]
            assert set(result) == {"Season", "Started", "Ended", "Winner", "Player", "Ports", "Threshold", "Score"}
            assert result["Season"] == 1 and result["Winner"] == "Winner" and result["Ports"] == 20 and result["Score"] != 999999999
            # Initialization is complete even though same-day maintenance skips.
            before = path.read_bytes()
            maintained = guard.run(subprocess.run, [BINARY, "-data", str(data), "-maint"], check=True, capture_output=True)
            assert "already current" in maintained.stdout.decode(), maintained.stdout
            assert json.loads(path.read_text()) == json.loads(before)
            guard.run(play, data, "New Person", "q")  # register the first new caller
            history = guard.run(play, data, "New Person", "seasons;q;y" if classic else "seasons;q", classic=classic)
            assert "Season 1: Winner (#1); 20 ports / 20 required" in history, history
            current = json.loads(path.read_text())
            assert current["Players"]["1"]["Alias"] == "New Person" and current["Season"] == 2 and len(current["SeasonResults"]) == 1
            denied = guard.run(play, data, "New Person", "g;q;y" if classic else "g;q", classic=classic)
            assert "you own 0 (20 short)" in denied and "Type GENESIS to confirm" not in denied, denied
    print("Genesis PTY passed: compact/classic queued/lowercase/chained cancellation, exact fresh reset, one receipt and logout, fully bootstrapped state, zero-disabled lottery retained, public winner history, new login and replay refusal.")


if __name__ == "__main__":
    run_on_stable_date(exercise)
