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

func missileStore(t *testing.T) (Store, game.MissileIntent, *game.Visibility) {
	t.Helper()
	s := create(t)
	var intent game.MissileIntent
	var v *game.Visibility
	if err := s.Update(func(w *game.World) error {
		a := w.Players[1]
		a.Missiles = 10
		a.StoredScore = 500000
		a.Turns = 37
		a.Mines = 100
		d, err := w.Join("defender", "Defender")
		if err != nil {
			return err
		}
		d.Sector = 2
		d.Cloak = 0
		d.Fighters, d.Shields = game.MaxQuantity, game.MaxQuantity
		d.Missiles = 6
		w.Sectors[1].Warps = []int{2}
		w.Sectors[2].Warps = []int{1, 3}
		w.Ports[2].Owner = a.ID
		w.Ports[2].Treasury = 777
		v, err = w.NewVisibility(1)
		if err != nil {
			return err
		}
		intent, err = w.PrepareMissile(1, 2, 1, v)
		return err
	}); err != nil {
		t.Fatal(err)
	}
	return s, intent, v
}

func TestMissileRetaliationRollbackAfterDamageAndSettlement(t *testing.T) {
	for _, mode := range []string{"invalid counter RNG", "later abort"} {
		t.Run(mode, func(t *testing.T) {
			s, intent, v := missileStore(t)
			before, _ := s.View()
			saved, _ := json.Marshal(before)
			err := s.ForShip(1, 0).Update(func(w *game.World) error {
				draws := 0
				_, err := w.CommitMissile(intent, v, func() float64 {
					draws++
					if mode == "invalid counter RNG" && draws > 3 {
						return math.NaN()
					}
					return .99
				}, time.Now())
				if err != nil {
					return err
				}
				return errors.New("later settlement phase aborted")
			})
			if err == nil {
				t.Fatal("failed volley accepted")
			}
			after, _ := s.View()
			actual, _ := json.Marshal(after)
			if string(actual) != string(saved) {
				t.Fatal("partial missile transaction saved")
			}
		})
	}
}

func TestConcurrentRetaliationDeathSettlesOnceAndKeepsBudget(t *testing.T) {
	s, intent, v := missileStore(t)
	apply := func(w *game.World) error {
		_, err := w.CommitMissile(intent, v, func() float64 { return .99 }, time.Now())
		return err
	}
	results := make(chan error, 2)
	for i := 0; i < 2; i++ {
		go func() { results <- s.ForShip(1, 0).Update(apply) }()
	}
	wins := 0
	for i := 0; i < 2; i++ {
		if <-results == nil {
			wins++
		}
	}
	if wins != 1 {
		t.Fatal("multiple killing counter volleys", wins)
	}
	w, _ := s.View()
	if w.Players[1].Death.Cause != "retaliation" || w.Players[1].Death.Killer != 2 || w.Players[1].Turns != 36 || w.Players[2].Missiles != 8 || w.Ports[2].Owner != 2 {
		t.Fatal(w.Players[1], w.Players[2])
	}
	// One shot defeats the ship; the remaining five selected missiles dissipate.
	// The defender then salvages eight of the attacker's nine unlaunched missiles.
	// No recursive response consumes more stock.
	if _, err := s.ForShip(1, 0).View(); !errors.Is(err, game.ErrShipDestroyed) {
		t.Fatal(err)
	}
	if err := s.Update(func(w *game.World) error { return w.LoginShip(1, time.Now()) }); err != nil {
		t.Fatal("false suicide cooldown", err)
	}
	w, _ = s.View()
	if w.Players[1].Turns != 36 || w.Players[1].StoredScore != 500000 {
		t.Fatal("replacement changed budget/score")
	}
}

func TestStoredScorePersistenceAndVersionSevenUpgrade(t *testing.T) {
	s, _, _ := missileStore(t)
	w, err := s.View()
	if err != nil || w.Players[1].StoredScore != 500000 {
		t.Fatal(w, err)
	}
	w.Version = 7
	w.Players[1].StoredScore = 0
	data, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	os.WriteFile(path, data, 0600)
	upgraded, err := s.View()
	if err != nil || upgraded.Version != 8 || upgraded.Players[1].StoredScore != 0 {
		t.Fatal(upgraded, err)
	}
	actual, _ := os.ReadFile(path)
	if string(actual) != string(data) {
		t.Fatal("read-only upgrade rewrote save")
	}
	if err = s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	w.Version = 7
	w.Players[1].StoredScore = 1
	data, _ = json.Marshal(w)
	os.WriteFile(path, data, 0600)
	if _, err = s.View(); err == nil {
		t.Fatal("malformed legacy score accepted")
	}
}

func TestMissileSalvageCapacityFailureRestoresLaunchAndVictim(t *testing.T) {
	s, intent, v := missileStore(t)
	if err := s.Update(func(w *game.World) error {
		w.Players[1].Credits = game.MaxMoney
		w.Players[2].Credits = 10000
		w.Players[2].Fighters, w.Players[2].Shields = 1, 1
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	before, _ := s.View()
	saved, _ := json.Marshal(before)
	err := s.ForShip(1, 0).Update(func(w *game.World) error {
		_, err := w.CommitMissile(intent, v, func() float64 { return .5 }, time.Now())
		return err
	})
	if err == nil {
		t.Fatal("overflowing loot accepted")
	}
	after, _ := s.View()
	actual, _ := json.Marshal(after)
	if string(actual) != string(saved) {
		t.Fatal("capacity failure partly saved launch")
	}
}
