package store

import (
	"bytes"
	"encoding/json"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"math"
	"os"
	"sync"
	"testing"
	"time"
)

func wandererStore(t *testing.T) (Store, Store, time.Time) {
	t.Helper()
	s, _, now := mobilityStore(t)
	err := s.Update(func(w *game.World) error {
		delete(w.Planets, 2)
		w.Sectors[8].Planet = 0
		if _, e := w.BootstrapWanderer(now, func() float64 { return 7.0 / 32 }); e != nil {
			return e
		}
		p := w.Planets[1]
		p.Owner = 1
		p.Production = [3]float64{}
		p.Ground = 0
		w.Players[1].PlanetToken = ""
		w.Players[1].LandedPlanet = 0
		return w.Land(1, now)
	})
	if err != nil {
		t.Fatal(err)
	}
	return s, s.ForShip(1, 0, 1), now
}
func TestWandererAtomicSplitMovementRollbackAndDurability(t *testing.T) {
	for _, mode := range []string{"rng", "callback", "validation", "durability", "success"} {
		s, b, now := wandererStore(t)
		entry := prepareMobility(t, b, now)
		before := travelBytes(t, s)
		calls := 0
		rng := func() float64 {
			calls++
			if calls == 1 {
				return 0
			}
			if mode == "rng" {
				return math.NaN()
			}
			return .999
		}
		var err error
		var out game.PlanetReceipt
		if mode == "callback" || mode == "validation" {
			err = b.Update(func(w *game.World) error {
				var e error
				out, e = w.CommitPlanetAction(entry, rng, now)
				if e != nil {
					return e
				}
				if mode == "callback" {
					return errors.New("abort after split movement")
				}
				w.Players[1].Credits = -1
				return nil
			})
		} else {
			if mode == "durability" {
				b.syncDirectory = func(string) error { return errors.New("directory sync failed") }
			}
			out, err = b.CommitPlanetAction(entry, rng, func() time.Time { return now }, time.Now().Add(time.Minute))
		}
		if mode == "rng" || mode == "callback" || mode == "validation" {
			if err == nil || !bytes.Equal(before, travelBytes(t, s)) {
				t.Fatal("partial split movement saved", mode, err)
			}
			continue
		}
		var committed *DurabilityError
		if mode == "durability" && !errors.As(err, &committed) || mode == "success" && err != nil || !out.Vanished || out.Hops != 1 || out.TransportTurns != 10 {
			t.Fatal(mode, out, err)
		}
		w, e := s.View()
		if e != nil || w.Planets[1].Sector != 32 || w.Players[1].Sector != 9 || w.Players[1].Turns != 490 || w.Players[1].PlanetToken != "" {
			t.Fatal("split result not persisted", e)
		}
		if _, e = b.CommitPlanetAction(entry, func() float64 { t.Fatal("replay drew"); return 0 }, func() time.Time { return now }, time.Now().Add(time.Minute)); e == nil {
			t.Fatal("replay accepted")
		}
	}
}
func TestWandererMaintenanceAtomicRollbackConcurrentAndWarning(t *testing.T) {
	for _, mode := range []string{"rng", "callback", "validation", "durability"} {
		s, _, now := wandererStore(t)
		before := travelBytes(t, s)
		var receipt game.MaintenanceReceipt
		if mode == "durability" {
			s.syncDirectory = func(string) error { return errors.New("directory sync failed") }
		}
		err := s.Update(func(w *game.World) error {
			var e error
			calls := 0
			receipt, e = w.RunMaintenance(now.Add(24*time.Hour), func() float64 {
				calls++
				if mode == "rng" && calls == 4 {
					return math.NaN()
				}
				return 0
			})
			if e != nil {
				return e
			}
			if mode == "callback" {
				return errors.New("abort after daily phases")
			}
			if mode == "validation" {
				w.Players[1].Credits = -1
			}
			return nil
		})
		if mode != "durability" {
			if err == nil || !bytes.Equal(before, travelBytes(t, s)) {
				t.Fatal("partial daily state saved", mode, err)
			}
			continue
		}
		var committed *DurabilityError
		if !errors.As(err, &committed) || !receipt.Ran {
			t.Fatal(receipt, err)
		}
		after := travelBytes(t, s)
		s.syncDirectory = nil
		if err = s.Update(func(w *game.World) error {
			out, e := w.RunMaintenance(now.Add(24*time.Hour), func() float64 { t.Fatal("daily warning replay drew"); return 0 })
			if out.Ran {
				t.Fatal("daily replay")
			}
			return e
		}); err != nil || !bytes.Equal(after, travelBytes(t, s)) {
			t.Fatal(err)
		}
	}
	s, _, now := wandererStore(t)
	var wg sync.WaitGroup
	outcomes := make(chan game.MaintenanceReceipt, 2)
	errs := make(chan error, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			var out game.MaintenanceReceipt
			e := s.Update(func(w *game.World) error {
				var e error
				out, e = w.RunMaintenance(now.Add(24*time.Hour), func() float64 { return 0 })
				return e
			})
			outcomes <- out
			errs <- e
		}()
	}
	wg.Wait()
	close(outcomes)
	close(errs)
	runs := 0
	for e := range errs {
		if e != nil {
			t.Fatal(e)
		}
	}
	for out := range outcomes {
		if out.Ran {
			runs++
		}
	}
	w, e := s.View()
	if e != nil || runs != 1 || w.Planets[1].Owner != 0 || w.Players[1].Turns != 500 || w.Players[1].PlanetToken != "" {
		t.Fatal(runs, e)
	}
}
func TestWandererReplacementAndDailyMovementInvalidateQuotes(t *testing.T) {
	for _, mode := range []string{"replacement", "daily", "occupancy", "concurrent"} {
		s, a, now := wandererStore(t)
		ea := prepareMobility(t, a, now)
		if mode == "concurrent" {
			b := s.ForShip(1, 0, 1)
			eb := prepareMobility(t, b, now)
			if _, err := b.CommitPlanetAction(eb, func() float64 { return 0 }, func() time.Time { return now }, time.Now().Add(time.Minute)); err != nil {
				t.Fatal(err)
			}
		} else if err := s.Update(func(w *game.World) error {
			switch mode {
			case "replacement":
				old := w.Planets[1]
				w.Sectors[old.Sector].Planet = 0
				delete(w.Planets, 1)
				if _, e := w.BootstrapWanderer(now, func() float64 { return 7.0 / 32 }); e != nil {
					return e
				}
				w.Planets[1].Owner = 1
				w.Planets[1].Production = [3]float64{}
				w.Players[1].PlanetToken = ""
				w.Players[1].LandedPlanet = 0
				return w.Land(1, now)
			case "daily":
				_, e := w.RunMaintenance(now.Add(24*time.Hour), func() float64 { return 0 })
				return e
			case "occupancy":
				w.Planets[2] = &game.Planet{ID: 2, Generation: 2, Sector: 32, Name: "Stationary", Updated: now}
				w.Sectors[32].Planet = 2
			}
			return nil
		}); err != nil {
			t.Fatal(err)
		}
		before := travelBytes(t, s)
		if _, err := a.CommitPlanetAction(ea, func() float64 { t.Fatal("stale confirmation drew", mode); return 0 }, func() time.Time { return now }, time.Now().Add(time.Minute)); err == nil || !bytes.Equal(before, travelBytes(t, s)) {
			t.Fatal(mode, err)
		}
	}
}

func TestWandererVersion24MigrationIsReadOnlyAndDoesNotMintAssets(t *testing.T) {
	s, _, now := mobilityStore(t)
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	w.Version = 24
	raw, err := json.Marshal(w)
	if err != nil {
		t.Fatal(err)
	}
	path := s.Dir + "/world.json"
	if err = os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	w, err = s.View()
	if err != nil || w.Version != game.WorldVersion || len(w.Planets) != 1 || w.Planets[1] != nil {
		t.Fatal("migration minted assets", err)
	}
	saved, _ := os.ReadFile(path)
	if !bytes.Equal(saved, raw) {
		t.Fatal("view rewrote historical save")
	}
	if err = s.Update(func(w *game.World) error {
		_, e := w.RunMaintenance(now.Add(24*time.Hour), func() float64 { return 0 })
		return e
	}); err != nil {
		t.Fatal(err)
	}
	w, err = s.View()
	if err != nil || !w.Planets[1].Wanderer || w.Planets[1].Updated != now.Add(24*time.Hour) || w.Planets[1].Generation <= 101 {
		t.Fatal("daily migration bootstrap missing or backdated", err)
	}
}

func TestWandererCompetingMoversCommitOnlyOneFeeAndLink(t *testing.T) {
	s, a, now := wandererStore(t)
	b := s.ForShip(1, 0, 1)
	entries := []game.PlanetIntent{prepareMobility(t, a, now), prepareMobility(t, b, now)}
	var wg sync.WaitGroup
	results := make(chan error, 2)
	for i, bound := range []Store{a, b} {
		wg.Add(1)
		go func(i int, bound Store) {
			defer wg.Done()
			_, err := bound.CommitPlanetAction(entries[i], func() float64 { return 0 }, func() time.Time { return now }, time.Now().Add(time.Minute))
			results <- err
		}(i, bound)
	}
	wg.Wait()
	close(results)
	wins := 0
	for err := range results {
		if err == nil {
			wins++
		}
	}
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	links := 0
	for _, sector := range w.Sectors {
		if sector.Planet == 1 {
			links++
		}
	}
	if wins != 1 || links != 1 || w.Planets[1].Sector != 1 || w.Players[1].Sector != 9 || w.Players[1].Turns != 490 || w.Planets[1].Generation != entries[0].Planet.Generation {
		t.Fatal("concurrent split duplicated fee, link or incarnation", wins, links)
	}
}
