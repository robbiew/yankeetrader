package store

import (
	"encoding/json"
	"errors"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestFullSalvageWorker(t *testing.T) {
	if os.Getenv("YT_SALVAGE_WORKER") == "" {
		return
	}
	s := Store{Dir: os.Getenv("YT_SALVAGE_DIR")}.ForShip(2, 0)
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		_, err := w.SettleShipSalvage(game.DeathContext{Victim: 1, Generation: p.ShipGeneration, Sector: p.Sector, Killer: 2, Cause: "combat"}, func() float64 { return .5 }, time.Now())
		return err
	}); err != nil {
		t.Fatal(err)
	}
}

func TestFullSalvageAndEstateAtomicAcrossConcurrentClaims(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		_, err := w.Join("killer", "Killer")
		if err != nil {
			return err
		}
		p := w.Players[1]
		p.Credits, p.Holds, p.Fighters, p.Shields = 10000, 100, 10, 10
		p.Cargo = [3]int64{11, 23, 37}
		p.Missiles, p.Plasma, p.Ground, p.Mines = 100, 100, 100, 100
		w.Players[2].Fighters = 1000
		w.Ports[2].Owner, w.Ports[2].Treasury = 1, 777
		w.Sectors[3].Defense = &game.SectorDefense{Owner: 1, Fighters: 123}
		return w.CreateTeam(1, "Orion", "ABCD")
	}); err != nil {
		t.Fatal(err)
	}
	apply := func(w *game.World) error {
		p := w.Players[1]
		result, err := game.ResolveShipDuel(100, p.Fighters, p.Shields, 0, func() float64 { return .49 })
		if err != nil {
			return err
		}
		w.Players[2].Fighters -= result.AttackerLosses
		p.Fighters, p.Shields = result.DefenderFighters, result.DefenderShields
		_, err = w.SettleShipSalvage(game.DeathContext{Victim: 1, Generation: 0, Sector: 1, Killer: 2, Cause: "combat"}, func() float64 { return .5 }, time.Now())
		return err
	}
	before, _ := os.ReadFile(s.Dir + "/world.json")
	if err := s.Update(func(w *game.World) error {
		if err := apply(w); err != nil {
			return err
		}
		return errors.New("future aftermath aborted")
	}); err == nil {
		t.Fatal("missing rollback")
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("damage, reward or estate partly saved")
	}
	var wg sync.WaitGroup
	results := make(chan error, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); results <- s.ForShip(2, 0).Update(apply) }()
	}
	wg.Wait()
	close(results)
	success := 0
	for err := range results {
		if err == nil {
			success++
		}
	}
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	p, k := w.Players[1], w.Players[2]
	if success != 1 || p.Death == nil || k.Credits != 6005 || p.Credits != 5000 || k.Holds != 60 || p.Holds != 50 || w.Ports[2].Owner != 2 || w.Ports[2].Treasury != 777 || p.Team != 0 || len(w.Teams) != 0 || w.Sectors[3].Defense.Owner != game.MercenaryOwner {
		t.Fatal("duplicate/incomplete salvage", success, p, k)
	}
	if _, err = s.ForShip(1, 0).View(); !errors.Is(err, game.ErrShipDestroyed) {
		t.Fatal("victim session survived", err)
	}
}

func TestVersionFourUpgradeKeepsExistingDeadAccountsAndEstate(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		_, err := w.Join("enemy", "Enemy")
		if err != nil {
			return err
		}
		w.Ports[2].Owner, w.Ports[2].Treasury = 1, 777
		return w.RecordDeath(game.DeathContext{Victim: 1, Sector: 1, Killer: 2, Cause: "combat"}, time.Now())
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	w.Version = 4
	for _, p := range w.Players {
		p.Cloak = 0
	}
	// Simulate the legacy, already-committed death policy. Upgrading must not
	// award loot, replay deaths or silently transfer previously saved property.
	w.Ports[2].Owner = 1
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
	if upgraded.Version != 7 || upgraded.Players[1].Death == nil || upgraded.Players[1].ShipGeneration != 1 || upgraded.Ports[2].Owner != 1 || upgraded.Ports[2].Treasury != 777 || upgraded.Players[2].Credits != 1005 {
		t.Fatal("upgrade replayed an old death")
	}
	disk, _ := os.ReadFile(s.Dir + "/world.json")
	if string(disk) != string(b) {
		t.Fatal("read-only upgrade changed disk")
	}
	if err = s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	// Defenses must persist across reloads in the current format.
	if err = s.Update(func(w *game.World) error {
		w.Sectors[3].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 123}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	current, err := s.View()
	if err != nil || current.Sectors[3].Defense.Fighters != 123 {
		t.Fatal("defenses not persisted", err)
	}
}
