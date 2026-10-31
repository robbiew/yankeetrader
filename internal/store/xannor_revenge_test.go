package store

import (
	"errors"
	"os"
	"reflect"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func revengeStore(t *testing.T) (Store, time.Time, game.DefenseIntent) {
	t.Helper()
	s, next := xannorShipStore(t)
	var entry game.DefenseIntent
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Sector, p.Fighters = 7, 10000
		w.Sectors[7].Warps = []int{8}
		var err error
		entry, err = w.PrepareDefenseFight(1, 8, 10000, false)
		return err
	}); err != nil {
		t.Fatal(err)
	}
	return s, next, entry
}
func TestXannorRevengeQueueAtomicRollbackConcurrentAndStaleCommit(t *testing.T) {
	s, next, entry := revengeStore(t)
	path := s.Dir + "/world.json"
	before, _ := os.ReadFile(path)
	abort := errors.New("abort HQ victory")
	if err := s.Update(func(w *game.World) error {
		if _, err := w.CommitDefense(entry, func() float64 { return .9 }, next.Add(-24*time.Hour)); err != nil {
			return err
		}
		if !w.HasXannorRevenge(1) || w.Sectors[8].Defense != nil {
			t.Fatal("fixture did not queue")
		}
		return abort
	}); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("failed callback persisted revenge")
	}
	if err := s.Update(func(w *game.World) error {
		_, err := w.CommitDefense(entry, func() float64 { return .9 }, next.Add(-24*time.Hour))
		if err != nil {
			return err
		}
		w.NextNews = 0
		return nil
	}); err == nil {
		t.Fatal("invalid state saved")
	}
	after, _ = os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("validation failure persisted revenge")
	}
	results := make(chan error, 2)
	var wg sync.WaitGroup
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := s.ForShip(1, entry.Generation, 1).DefenseEncounter(entry, func() float64 { return .9 }, next.Add(-24*time.Hour), time.Now().Add(time.Minute))
			results <- err
		}()
	}
	wg.Wait()
	close(results)
	wins := 0
	for err := range results {
		if err == nil {
			wins++
		}
	}
	if wins != 1 {
		t.Fatal("duplicate HQ settlement", wins)
	}
	saved, err := (Store{Dir: s.Dir}).View()
	if err != nil || !saved.HasXannorRevenge(1) || saved.Sectors[8].Defense != nil || saved.Players[1].Credits != 1005+game.XannorHQBonus {
		t.Fatal("queue/force roundtrip", err)
	}
	before, _ = os.ReadFile(path)
	if _, err := s.ForShip(1, entry.Generation, 1).DefenseEncounter(entry, func() float64 { t.Fatal("stale fight drew"); return 0 }, next, time.Now().Add(time.Minute)); err == nil {
		t.Fatal("stale victory replayed")
	}
	after, _ = os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("stale command rewrote queue")
	}
}
func pendingRevengeStore(t *testing.T) (Store, time.Time) {
	t.Helper()
	s, next, entry := revengeStore(t)
	if _, err := s.ForShip(1, entry.Generation, 1).DefenseEncounter(entry, func() float64 { return .9 }, next.Add(-24*time.Hour), time.Now().Add(time.Minute)); err != nil {
		t.Fatal(err)
	}
	// A later returning fighter makes the HQ stable; a full route passes the
	// revenge victim and returns home even when the final HQ override wins.
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Sector, p.Fighters, p.Shields, p.Cloak = 10, game.MaxQuantity, 1, 0
		w.Sectors[8].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 1}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, next
}
func TestXannorRevengeConsumptionConcurrentReplayAndDurability(t *testing.T) {
	for _, durability := range []bool{false, true} {
		s, next := pendingRevengeStore(t)
		path := s.Dir + "/world.json"
		before, _ := os.ReadFile(path)
		abort := errors.New("abort consumed revenge")
		if err := s.Update(func(w *game.World) error {
			w.MaintainWithRandom(next, func() float64 { return .5 })
			if w.Xannor.Revenge != nil {
				t.Fatal("not consumed")
			}
			return abort
		}); !errors.Is(err, abort) {
			t.Fatal(err)
		}
		after, _ := os.ReadFile(path)
		if string(before) != string(after) {
			t.Fatal("failed maintenance consumed target")
		}
		if durability {
			s.syncDirectory = func(string) error { return errors.New("directory sync") }
			err := s.Update(func(w *game.World) error { w.MaintainWithRandom(next, func() float64 { return .5 }); return nil })
			var committed *DurabilityError
			if !errors.As(err, &committed) {
				t.Fatal("expected committed error", err)
			}
		} else {
			var wg sync.WaitGroup
			errs := make(chan error, 5)
			for i := 0; i < 5; i++ {
				wg.Add(1)
				go func() {
					defer wg.Done()
					errs <- s.Update(func(w *game.World) error {
						w.MaintainWithRandom(next, func() float64 { return .5 })
						return w.LoginShip(1, next)
					})
				}()
			}
			wg.Wait()
			close(errs)
			for err := range errs {
				if err != nil {
					t.Fatal(err)
				}
			}
		}
		normal := Store{Dir: s.Dir}
		saved, err := normal.View()
		if err != nil {
			t.Fatal(err)
		}
		if saved.Xannor.Revenge != nil || saved.Players[1].Death != nil || len(saved.Players[1].BattleReports) != 1 || saved.Players[1].Cloak != 0 {
			t.Fatal("consumption/detection/repeated battle")
		}
		snapshot := *saved.Players[1]
		before, _ = os.ReadFile(path)
		if err := normal.Update(func(w *game.World) error {
			if w.MaintainWithRandom(next, func() float64 { return .5 }) || w.Maintain(next.Add(-time.Hour)) {
				t.Fatal("daily replay")
			}
			return nil
		}); err != nil {
			t.Fatal(err)
		}
		after, _ = os.ReadFile(path)
		if string(before) != string(after) {
			t.Fatal("daily replay changed force/report")
		}
		reloaded, _ := normal.View()
		if !reflect.DeepEqual(snapshot, *reloaded.Players[1]) {
			t.Fatal("reload altered aftermath")
		}
	}
}
func TestXannorRevengeDeathReplacementAndVersionSixteenMigration(t *testing.T) {
	s, next := pendingRevengeStore(t)
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		return w.RecordDeath(game.DeathContext{Victim: 1, Generation: p.ShipGeneration, Sector: p.Sector, Cause: "hazard"}, next)
	}); err != nil {
		t.Fatal(err)
	}
	if err := s.Update(func(w *game.World) error { return w.LoginShip(1, next) }); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	if w.Xannor.Revenge != nil || w.HasXannorRevenge(1) {
		t.Fatal("replacement inherited revenge")
	}
	w.Version = 16
	w.Season = 0
	w.GenerationSeed = nil
	// A genuine old save predates the new victory announcement.
	w.News = nil
	raw, _ := marshalHistoricalWorld(w)
	path := s.Dir + "/world.json"
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	upgraded, err := s.View()
	if err != nil || upgraded.Version != game.WorldVersion || !reflect.DeepEqual(w.Players, upgraded.Players) || !reflect.DeepEqual(w.Xannor, upgraded.Xannor) {
		t.Fatal("migration lost assets/state", err)
	}
	unchanged, _ := os.ReadFile(path)
	if string(raw) != string(unchanged) {
		t.Fatal("read-only migration wrote")
	}
	if err := s.Update(func(*game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	upgraded, _ = s.View()
	if upgraded.Version != game.WorldVersion {
		t.Fatal("migration not saved")
	}
	upgraded.Version = 16
	upgraded.Season = 0
	upgraded.GenerationSeed = nil
	upgraded.Xannor.Revenge = &game.XannorRevengeTarget{Player: 1, Generation: upgraded.Players[1].ShipGeneration}
	raw, _ = marshalHistoricalWorld(upgraded)
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := s.View(); err == nil {
		t.Fatal("legacy future revenge accepted")
	}
}

func TestMissileHQRevengeRollsBackOnLaterVolleyFailure(t *testing.T) {
	s, next, _ := revengeStore(t)
	var intent game.MissileIntent
	var visibility *game.Visibility
	if err := s.Update(func(w *game.World) error {
		w.Players[1].Missiles = 2
		w.Sectors[8].Warps = []int{9}
		var err error
		visibility, err = w.NewVisibility(1)
		if err != nil {
			return err
		}
		intent, err = w.PrepareMissile(1, 9, 2, visibility)
		return err
	}); err != nil {
		t.Fatal(err)
	}
	path := s.Dir + "/world.json"
	before, _ := os.ReadFile(path)
	// The first missile clears HQ and queues revenge, but the surviving volley
	// encounters the fixture's future-dated hostile planet. The error must abort
	// the complete launch, including both missile consumption and new target.
	err := s.Update(func(w *game.World) error {
		_, err := w.CommitMissile(intent, visibility, func() float64 { return .9 }, next.Add(-24*time.Hour))
		return err
	})
	if err == nil {
		t.Fatal("expected later planet clock failure")
	}
	after, _ := os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("failed volley persisted HQ defeat/revenge")
	}
	w, _ := s.View()
	if w.Xannor.Revenge != nil || w.Sectors[8].Defense.Fighters != 1 || w.Players[1].Missiles != 2 {
		t.Fatal("partial missile settlement")
	}
}
