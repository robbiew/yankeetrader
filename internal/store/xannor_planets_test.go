package store

import (
	"encoding/json"
	"errors"
	"os"
	"reflect"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func xannorPlanetStore(t *testing.T) (Store, time.Time, string) {
	t.Helper()
	s, next := xannorShipStore(t)
	token := "0123456789abcdef0123456789abcdef"
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Fighters = game.MaxQuantity
		p.Shields = 1
		p.LandedPlanet = 2
		p.PlanetToken = token
		w.Planets[2] = &game.Planet{ID: 2, Sector: 10, Owner: 1, Name: "Condemned", Updated: next.Add(24 * time.Hour), Bank: 1234, Missiles: 5000, Fighters: 1234}
		w.Sectors[10].Planet = 2
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, next, token
}
func TestXannorPlanetAtomicRollbackConcurrentLandingReplayReload(t *testing.T) {
	// Keep this destruction test independent of an unrelated post-assault award.
	s, next, token := xannorPlanetStore(t)
	path := s.Dir + "/world.json"
	before, _ := os.ReadFile(path)
	abort := errors.New("abort destruction")
	if err := s.Update(func(w *game.World) error {
		w.MaintainWithRandom(next, func() float64 { return .49 })
		if w.Planets[2] != nil || w.Players[1].PlanetToken != "" || w.Players[1].BattleReports[0].Planet == nil {
			t.Fatal("fixture did not destroy")
		}
		return abort
	}); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("callback failure committed destruction")
	}
	if err := s.Update(func(w *game.World) error {
		w.MaintainWithRandom(next, func() float64 { return .49 })
		w.NextBattleReport = 0
		return nil
	}); err == nil {
		t.Fatal("invalid destruction committed")
	}
	after, _ = os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("validation failure committed destruction")
	}
	var wg sync.WaitGroup
	errs := make(chan error, 6)
	for i := 0; i < 6; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- s.Update(func(w *game.World) error { w.MaintainWithRandom(next, func() float64 { return .49 }); return nil })
		}()
	}
	// Concurrent landing must either finish before destruction and be revoked, or
	// fail against the absent object. Neither ordering can leave a live old token.
	wg.Add(1)
	go func() {
		defer wg.Done()
		_ = s.ForShip(1, 0).Update(func(w *game.World) error { return w.Land(1, next) })
	}()
	wg.Wait()
	close(errs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	saved, err := (Store{Dir: s.Dir}).View()
	if err != nil {
		t.Fatal(err)
	}
	p := saved.Players[1]
	if saved.Planets[2] != nil || saved.Sectors[10].Planet != 0 || p.Death != nil || p.ShipGeneration != 0 || p.PlanetToken != "" || p.LandedPlanet != 0 || p.Missiles != 0 || p.Credits != 1005 {
		t.Fatal("cleanup or collateral assets", p)
	}
	count, news := 0, 0
	for _, r := range p.BattleReports {
		if r.Planet != nil {
			count++
			if !r.Destroyed || !r.Unread || r.Planet.Name != "Condemned" {
				t.Fatal("bad persisted owner report")
			}
		}
	}
	for _, e := range saved.News {
		if e.Kind == game.NewsXannorPlanet {
			news++
			if e.Outcome != "destroyed" {
				t.Fatal("bad public outcome")
			}
		}
	}
	if count != 1 || news != 1 {
		t.Fatal("duplicated/lost outcomes", count, news)
	}
	if err := s.ForShip(1, 0).Update(func(w *game.World) error { return w.Bank(1, token, 0, next) }); err == nil {
		t.Fatal("pending bank confirmation survived")
	}
	before, _ = os.ReadFile(path)
	if err := s.Update(func(w *game.World) error {
		if w.MaintainWithRandom(next, func() float64 { return .49 }) || w.MaintainWithRandom(next.Add(-time.Hour), func() float64 { return .49 }) {
			t.Fatal("replayed")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	after, _ = os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("replay altered aftermath")
	}
}
func TestXannorPlanetCommittedDurabilityFailureDoesNotReplay(t *testing.T) {
	s, next, _ := xannorPlanetStore(t)
	s.syncDirectory = func(string) error { return errors.New("directory sync") }
	err := s.Update(func(w *game.World) error { w.MaintainWithRandom(next, func() float64 { return .49 }); return nil })
	var committed *DurabilityError
	if !errors.As(err, &committed) {
		t.Fatal("expected committed error", err)
	}
	normal := Store{Dir: s.Dir}
	before, _ := normal.View()
	if err := normal.Update(func(w *game.World) error {
		if w.MaintainWithRandom(next, func() float64 { return .49 }) {
			t.Fatal("replayed committed destruction")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	after, _ := normal.View()
	if before.Planets[2] != nil || !reflect.DeepEqual(before, after) {
		t.Fatal("durability retry changed outcome")
	}
}
func TestVersionFifteenPlanetMigrationPreservesShipHistoryUntilWrite(t *testing.T) {
	s, _ := xannorShipStore(t)
	w, _ := s.View()
	w.Version = 15
	w.Players[1].BattleReports = []game.BattleReport{{ID: 1, At: w.Created, Sector: 10, XannorLost: 3, Unread: true}}
	w.NextBattleReport = 2
	raw, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	migrated, err := s.View()
	if err != nil || migrated.Version != game.WorldVersion || !reflect.DeepEqual(w.Players[1].BattleReports, migrated.Players[1].BattleReports) {
		t.Fatal("migration lost ship history", err)
	}
	unchanged, _ := os.ReadFile(path)
	if string(raw) != string(unchanged) {
		t.Fatal("read-only migration rewrote save")
	}
	if err := s.Update(func(*game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	saved, _ := s.View()
	if saved.Version != game.WorldVersion {
		t.Fatal("upgrade not saved")
	}
}
