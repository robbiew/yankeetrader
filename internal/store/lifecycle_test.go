package store

import (
	"encoding/json"
	"errors"
	"os"
	"os/exec"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestLifecycleWorker(t *testing.T) {
	if os.Getenv("YT_LIFECYCLE_WORKER") == "" {
		return
	}
	s := Store{Dir: os.Getenv("YT_LIFECYCLE_DIR")}
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		return w.RecordDeath(game.DeathContext{Victim: 1, Generation: p.ShipGeneration, Sector: p.Sector, Killer: 2, Cause: "combat"}, time.Now())
	}); err != nil {
		t.Fatal(err)
	}
	if os.Getenv("YT_LIFECYCLE_DEATH_ONLY") == "1" {
		return
	}
	if err := s.Update(func(w *game.World) error { return w.ReplaceShip(1, time.Now()) }); err != nil {
		t.Fatal(err)
	}
}

func TestShipGenerationRejectsOldProcessSessionAfterReplacement(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error { _, err := w.Join("killer", "Killer"); w.Players[1].Turns = 37; return err }); err != nil {
		t.Fatal(err)
	}
	old := s.ForShip(1, 0)
	cmd := exec.Command(os.Args[0], "-test.run=^TestLifecycleWorker$")
	cmd.Env = append(os.Environ(), "YT_LIFECYCLE_WORKER=1", "YT_LIFECYCLE_DIR="+s.Dir)
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatal(err, string(out))
	}
	if _, err := old.View(); !errors.Is(err, game.ErrShipChanged) {
		t.Fatal("old process session could read replacement", err)
	}
	called := false
	if err := old.Update(func(w *game.World) error { called = true; w.Players[1].Credits = 999999; return nil }); !errors.Is(err, game.ErrShipChanged) || called {
		t.Fatal("stale callback executed", err, called)
	}
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	if w.Players[1].ShipGeneration != 2 || w.Players[1].Credits != 1005 || w.Players[1].Turns != 37 {
		t.Fatal("replacement overwritten", w.Players[1])
	}
	fresh := s.ForShip(1, 2)
	if err = fresh.Update(func(w *game.World) error { return w.Move(1, 2) }); err != nil {
		t.Fatal(err)
	}
}

func TestFailedDeathTransactionRollsBackAttributionAndInvalidation(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error { _, err := w.Join("killer", "Killer"); return err }); err != nil {
		t.Fatal(err)
	}
	before, _ := os.ReadFile(s.Dir + "/world.json")
	if err := s.Update(func(w *game.World) error {
		if err := w.RecordDeath(game.DeathContext{Victim: 1, Sector: 1, Killer: 2, Cause: "combat"}, time.Now()); err != nil {
			return err
		}
		return errors.New("settlement aborted")
	}); err == nil {
		t.Fatal("missing abort")
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("failed settlement partly saved death")
	}
	if _, err := s.ForShip(1, 0).View(); err != nil {
		t.Fatal("failed death invalidated session", err)
	}
}

func TestVersionThreeUpgradePreservesTeamAndAssets(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		w.Players[1].Credits = 100000
		w.Players[1].AvoidSectors = []int{2, 3}
		w.Ports[2].Owner, w.Ports[2].Treasury = 1, 777
		if err := w.CreatePlanet(1, "Home", time.Now()); err != nil {
			return err
		}
		return w.CreateTeam(1, "Orion", "ABCD")
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	hash := w.Teams[1].PasswordHash
	w.NextRadio = 0
	w.Version = 3
	for _, p := range w.Players {
		p.Cloak = 0
	}
	b, err := json.Marshal(w)
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(s.Dir+"/world.json", b, 0600); err != nil {
		t.Fatal(err)
	}
	upgraded, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	p := upgraded.Players[1]
	if upgraded.Version != 11 || p.ShipGeneration != 0 || p.Death != nil || p.Team != 1 || upgraded.Teams[1].PasswordHash != hash || upgraded.Teams[1].Captain != 1 || upgraded.Planets[2].Owner != 1 || upgraded.Ports[2].Treasury != 777 || len(p.AvoidSectors) != 2 || p.Credits != 75000 {
		t.Fatal("v3 data changed during upgrade")
	}
	disk, _ := os.ReadFile(s.Dir + "/world.json")
	if string(disk) != string(b) {
		t.Fatal("read-only upgrade rewrote old save")
	}
	if err = s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	current, err := s.View()
	if err != nil || current.Version != 11 {
		t.Fatal("upgrade not persisted", err)
	}
}
