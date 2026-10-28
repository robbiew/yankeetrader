package store

import (
	"encoding/json"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"math"
	"os"
	"testing"
	"time"
)

func TestMineEntryRollbackAndBoundActionGate(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		w.Players[1].Shields = 10000
		w.Sectors[2].Minefield = []game.MineLayer{{Owner: 0, Count: 2}}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	bound := s.ForShip(1, 0)
	w, _ := s.View()
	entry, err := w.PrepareMineEntry(1, 2)
	if err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(w)
	err = bound.Update(func(w *game.World) error {
		draws := 0
		_, err := w.CommitMineEntry(entry, func() float64 {
			draws++
			if draws > 2 {
				return math.NaN()
			}
			return .5
		}, time.Now())
		return err
	})
	if err == nil {
		t.Fatal("bad RNG accepted")
	}
	after, _ := s.View()
	actual, _ := json.Marshal(after)
	if string(actual) != string(before) {
		t.Fatal("partial mine entry saved")
	}
	if err = s.Update(func(w *game.World) error { w.Players[1].Sector = 2; return nil }); err != nil {
		t.Fatal(err)
	}
	called := false
	err = bound.Update(func(w *game.World) error { called = true; return w.Move(1, 3) })
	if !errors.Is(err, game.ErrMineEncounter) || called {
		t.Fatal("action bypassed unresolved minefield", err)
	}
	out, err := bound.ResolveMines(time.Now(), func() float64 { return .5 })
	if err != nil || out.Spent != 2 {
		t.Fatal(out, err)
	}
	if err = bound.Update(func(w *game.World) error { return w.Move(1, 3) }); err != nil {
		t.Fatal(err)
	}
}

func TestChainedMineDeathAtomicReplayAndReplacement(t *testing.T) {
	s := create(t)
	var intent game.AttackIntent
	if err := s.Update(func(w *game.World) error {
		a := w.Players[1]
		a.Sector = 2
		a.Cloak = 0
		a.Holds = 10
		a.Turns = 37
		a.Fighters = 1
		d, err := w.Join("victim", "Victim")
		if err != nil {
			return err
		}
		d.Sector = 2
		d.Cloak = 0
		d.Fighters, d.Shields = 0, 0
		d.Mines = 100
		w.Ports[2].Owner = d.ID
		w.Ports[2].Treasury = 777
		intent, err = w.PrepareAttack(a.ID, d.ID, 1)
		return err
	}); err != nil {
		t.Fatal(err)
	}
	apply := func(w *game.World) error {
		draws := 0
		_, err := w.CommitAttack(intent, func() float64 {
			draws++
			if draws <= 6 {
				return 0
			}
			return math.Nextafter(1, 0)
		}, time.Now())
		return err
	}
	before, _ := s.View()
	saved, _ := json.Marshal(before)
	if err := s.Update(func(w *game.World) error {
		if err := apply(w); err != nil {
			return err
		}
		return errors.New("aftermath abort")
	}); err == nil {
		t.Fatal("abort accepted")
	}
	after, _ := s.View()
	actual, _ := json.Marshal(after)
	if string(actual) != string(saved) {
		t.Fatal("chain partly saved")
	}
	results := make(chan error, 2)
	for i := 0; i < 2; i++ {
		go func() { results <- s.Update(apply) }()
	}
	wins := 0
	for i := 0; i < 2; i++ {
		if <-results == nil {
			wins++
		}
	}
	if wins != 1 {
		t.Fatal("multiple chains", wins)
	}
	after, _ = s.View()
	if after.Players[1].Death.Cause != "mines" || after.Players[1].Death.Killer != 2 || after.Players[2].Death.Killer != 1 || after.Ports[2].Owner != 0 {
		t.Fatal("chain attribution/estate lost")
	}
	if _, err := s.ForShip(1, 0).View(); !errors.Is(err, game.ErrShipDestroyed) {
		t.Fatal(err)
	}
	if err := s.Update(func(w *game.World) error { return w.LoginShip(1, time.Now()) }); err != nil {
		t.Fatal("false suicide cooldown", err)
	}
	after, _ = s.View()
	if after.Players[1].Turns != 37 || after.Players[1].Sector != 1 {
		t.Fatal("replacement changed budget")
	}
}

func TestVersionSixMineUpgradeAndMalformedState(t *testing.T) {
	s := create(t)
	w, _ := s.View()
	w.Version = 6
	data, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	current, err := s.View()
	if err != nil || current.Version != 10 {
		t.Fatal(current, err)
	}
	unchanged, _ := os.ReadFile(path)
	if string(unchanged) != string(data) {
		t.Fatal("read rewrote upgrade")
	}
	if err = s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	w.Version = 6
	w.Sectors[2].Minefield = []game.MineLayer{{Owner: 0, Count: 1}}
	data, _ = json.Marshal(w)
	os.WriteFile(path, data, 0600)
	if _, err = s.View(); err == nil {
		t.Fatal("legacy mine data accepted")
	}
}

func TestMineDropOverflowRollsBackEntireKillingAttack(t *testing.T) {
	s := create(t)
	var intent game.AttackIntent
	if err := s.Update(func(w *game.World) error {
		a := w.Players[1]
		a.Sector = 2
		a.Cloak = 0
		a.Holds = 1
		a.Fighters = 1
		a.Mines = game.MaxQuantity
		d, err := w.Join("victim", "Victim")
		if err != nil {
			return err
		}
		d.Sector = 2
		d.Cloak = 0
		d.Holds = 1
		d.Fighters, d.Shields = 0, 0
		d.Mines = game.MaxQuantity
		intent, err = w.PrepareAttack(a.ID, d.ID, 1)
		return err
	}); err != nil {
		t.Fatal(err)
	}
	before, _ := s.View()
	saved, _ := json.Marshal(before)
	err := s.Update(func(w *game.World) error {
		_, err := w.CommitAttack(intent, func() float64 { return 0 }, time.Now())
		return err
	})
	if err == nil {
		t.Fatal("overflowing chained drop accepted")
	}
	after, _ := s.View()
	actual, _ := json.Marshal(after)
	if string(actual) != string(saved) {
		t.Fatal("overflow partly committed attack")
	}
}
