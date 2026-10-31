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
			err := s.ForShip(1, 0, 1).Update(func(w *game.World) error {
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
		go func() { results <- s.ForShip(1, 0, 1).Update(apply) }()
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
	if _, err := s.ForShip(1, 0, 1).View(); !errors.Is(err, game.ErrShipDestroyed) {
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
	w.NextRadio = 0
	w.Version = 7
	w.Season = 0
	w.GenerationSeed = nil
	w.NextBattleReport = 0 // This fixture represents a pre-report save.
	w.NextNews = 0
	w.Players[1].StoredScore = 0
	data, _ := marshalHistoricalWorld(w)
	path := s.Dir + "/world.json"
	os.WriteFile(path, data, 0600)
	upgraded, err := s.View()
	if err != nil || upgraded.Version != game.WorldVersion || upgraded.Players[1].StoredScore != 0 {
		t.Fatal(upgraded, err)
	}
	actual, _ := os.ReadFile(path)
	if string(actual) != string(data) {
		t.Fatal("read-only upgrade rewrote save")
	}
	if err = s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	w.NextRadio = 0
	w.Version = 7
	w.Season = 0
	w.GenerationSeed = nil
	w.NextBattleReport = 0 // This fixture represents a pre-report save.
	w.NextNews = 0
	w.Players[1].StoredScore = 1
	data, _ = marshalHistoricalWorld(w)
	os.WriteFile(path, data, 0600)
	if _, err = s.View(); err == nil {
		t.Fatal("malformed legacy score accepted")
	}
}

func TestVersionEightUpgradeAcceptsZeroPlanetProduction(t *testing.T) {
	s := create(t)
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	w.NextRadio = 0
	w.Version = 8
	w.Season = 0
	w.GenerationSeed = nil
	w.NextBattleReport = 0 // This fixture represents a pre-report save.
	w.NextNews = 0
	w.Players[1].Credits = 100000
	if err = w.CreatePlanet(1, "Zero", time.Now()); err != nil {
		t.Fatal(err)
	}
	w.Planets[2].Production = [3]float64{0, 20, 0}
	w.Planets[2].Cargo = [3]float64{0, 200, 0}
	data, _ := marshalHistoricalWorld(w)
	path := s.Dir + "/world.json"
	if err = os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	upgraded, err := s.View()
	if err != nil || upgraded.Version != game.WorldVersion || upgraded.Planets[2].Production != [3]float64{0, 20, 0} {
		t.Fatal(upgraded, err)
	}
	disk, _ := os.ReadFile(path)
	if string(disk) != string(data) {
		t.Fatal("read-only upgrade rewrote save")
	}
	if err = s.Update(func(*game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	upgraded, err = s.View()
	if err != nil || upgraded.Version != game.WorldVersion || upgraded.Planets[2].Production[0] != 0 {
		t.Fatal(upgraded, err)
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
	err := s.ForShip(1, 0, 1).Update(func(w *game.World) error {
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

func TestPlanetBombardmentRollbackIncludesInterceptionAndLazyUpdate(t *testing.T) {
	s, _, v := missileStore(t)
	now := time.Now().UTC()
	if err := s.Update(func(w *game.World) error {
		w.Players[2].Sector = 3
		w.Planets[2] = &game.Planet{Generation: uint64(2), ID: 2, Sector: 2, Owner: 2, Name: "Target", Updated: now.Add(-time.Hour), Ground: 25, Production: [3]float64{1, 1, 1}, Bank: 0}
		w.Sectors[2].Planet = 2
		landed, err := w.Join("landed", "Landed")
		if err != nil {
			return err
		}
		landed.Sector, landed.LandedPlanet, landed.PlanetToken = 2, 2, "0123456789abcdef0123456789abcdef"
		w.Sectors[2].Defense = &game.SectorDefense{Owner: 2, Fighters: 1}
		w.Sectors[2].Minefield = []game.MineLayer{{Owner: 2, Count: 1}}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	before, _ := s.View()
	intent, err := before.PrepareMissile(1, 2, 6, v)
	if err != nil {
		t.Fatal(err)
	}
	saved, _ := json.Marshal(before)
	draws := 0
	err = s.ForShip(1, 0, 1).Update(func(w *game.World) error {
		_, err := w.CommitMissile(intent, v, func() float64 {
			draws++
			if draws > 2 {
				return math.NaN()
			}
			return .5
		}, now)
		return err
	})
	if err == nil || draws != 3 {
		t.Fatal(err, draws)
	}
	after, _ := s.View()
	actual, _ := json.Marshal(after)
	if string(saved) != string(actual) {
		t.Fatal("partial planetary launch saved")
	}
	err = s.ForShip(1, 0, 1).Update(func(w *game.World) error {
		_, err := w.CommitMissile(intent, v, func() float64 { return .5 }, now)
		if err != nil {
			return err
		}
		return errors.New("late abort after planetary destruction")
	})
	if err == nil {
		t.Fatal("late-aborted destruction was saved")
	}
	after, _ = s.View()
	actual, _ = json.Marshal(after)
	if string(saved) != string(actual) {
		t.Fatal("late abort persisted planet destruction")
	}
	err = s.ForShip(1, 0, 1).Update(func(w *game.World) error {
		_, err := w.CommitMissile(intent, v, func() float64 { return .5 }, now)
		return err
	})
	if err != nil {
		t.Fatal(err)
	}
	after, _ = s.View()
	if after.Players[1].Missiles != 4 || after.Players[1].Turns != 36 || after.Sectors[2].Defense != nil || len(after.Sectors[2].Minefield) != 0 || after.Planets[2] != nil || after.Sectors[2].Planet != 0 || after.Players[3].PlanetToken != "" || after.Players[3].LandedPlanet != 0 {
		t.Fatal("launch consequences missing", after.Planets[2], after.Players[3])
	}
}
