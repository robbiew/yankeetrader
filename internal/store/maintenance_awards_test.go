package store

import (
	"encoding/json"
	"errors"
	"os"
	"reflect"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func dailyAwardStore(t *testing.T) (Store, time.Time) {
	t.Helper()
	at := time.Date(2026, 12, 20, 0, 0, 0, 0, time.UTC)
	now := at.AddDate(0, 0, 14)
	w, err := game.New(at, 36, 12)
	if err != nil {
		t.Fatal(err)
	}
	p, _ := w.Join("retired-identity", "Retiring")
	q, _ := w.Join("visitor-identity", "Visitor")
	p.LastLogin = at.Format("2006-01-02")
	if err = w.RecordDeath(game.DeathContext{Victim: p.ID, Generation: p.ShipGeneration, Sector: 1, Cause: "hazard"}, at); err != nil {
		t.Fatal(err)
	}
	w.Ports[2].Owner = p.ID
	w.Ports[2].Treasury = 900
	w.Planets[2] = &game.Planet{ID: 2, Sector: 9, Owner: p.ID, Name: "Estate", Updated: at, Ground: 99, Bank: 1000000}
	w.Sectors[9].Planet = 2
	w.Xannor = &game.XannorState{HQ: 8}
	w.Sectors[8].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 1}
	for _, spec := range []struct {
		id, sector, owner int
		home, name        string
	}{{99, 11, -2, game.MercenaryHome, "Mercenary Base"}, {100, 12, -1, game.XannorHome, "Xannoron"}} {
		w.Planets[spec.id] = &game.Planet{ID: spec.id, Sector: spec.sector, Owner: spec.owner, FactionHome: spec.home, Name: spec.name, Updated: now, Ground: 1, Bank: 1}
		w.Sectors[spec.sector].Planet = spec.id
	}
	for _, sector := range w.Sectors {
		sector.Warps = nil
	}
	draft, err := w.PrepareRadio(q.ID, game.RadioAddress{ID: p.ID, Alias: p.Alias}, "Identity-bound private history", at)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitRadio(draft, at); err != nil {
		t.Fatal(err)
	}
	s := Store{Dir: t.TempDir()}
	if err = s.Create(w); err != nil {
		t.Fatal(err)
	}
	return s, now
}
func TestMaintenanceAwardRetirementAtomicRollbackValidationAndConcurrency(t *testing.T) {
	s, now := dailyAwardStore(t)
	path := s.Dir + "/world.json"
	before, _ := os.ReadFile(path)
	abort := errors.New("abort daily update")
	for _, validation := range []bool{false, true} {
		err := s.Update(func(w *game.World) error {
			if !w.MaintainWithRandom(now, func() float64 { return .5 }) {
				t.Fatal("fixture skipped")
			}
			if w.Players[1].RetiredAt.IsZero() || w.Planets[50] == nil || len(w.Radio) != 2 {
				t.Fatal("incomplete fixture", w.Planets, w.Radio)
			}
			if validation {
				w.NextNews = 0
				return nil
			}
			return abort
		})
		if err == nil {
			t.Fatal("failed daily update saved")
		}
		after, _ := os.ReadFile(path)
		if string(before) != string(after) {
			t.Fatal("partial retirement/award persisted")
		}
	}
	var count atomic.Int32
	var wg sync.WaitGroup
	errs := make(chan error, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- s.Update(func(w *game.World) error {
				if w.MaintainWithRandom(now, func() float64 { return .5 }) {
					count.Add(1)
				}
				return nil
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
	if count.Load() != 1 {
		t.Fatal("daily transaction repeated", count.Load())
	}
	w, err := (Store{Dir: s.Dir}).View()
	if err != nil {
		t.Fatal(err)
	}
	if w.Players[1].RetiredAt.IsZero() || w.Planets[2].Owner != 0 || w.Planets[50].Owner != 2 || w.Sectors[10].Planet != 50 || len(w.Radio) != 2 || w.Radio[1].System != "super-planet" || len(w.News) != 2 {
		t.Fatal("daily roundtrip", w.News, w.Radio)
	}
	if w.Planets[50].Fighters != 0 || w.Planets[50].Updated != now {
		t.Fatal("award got same-day catch-up")
	}
	// The old bound session cannot read after retirement or fresh reactivation.
	if _, err = s.ForShip(1, 0).View(); err == nil {
		t.Fatal("destroyed session survived")
	}
	if err = s.Update(func(w *game.World) error { return w.LoginShip(1, now) }); err != nil {
		t.Fatal(err)
	}
	w, err = s.View()
	if err != nil {
		t.Fatal(err)
	}
	history, err := w.RadioHistory(1, 0, 20, false)
	if err != nil || len(history) != 1 || history[0].FromAlias != "Visitor" {
		t.Fatal("private history lost/misattributed", err, history)
	}
	if _, err = s.ForShip(1, 0).View(); err == nil {
		t.Fatal("pre-retirement session gained fresh ship")
	}
	other, err := w.RadioHistory(2, 0, 20, false)
	if err != nil || len(other) != 2 {
		t.Fatal(other, err)
	}
}
func TestMaintenanceAwardRetirementCommittedDurabilityAndReplay(t *testing.T) {
	s, now := dailyAwardStore(t)
	s.syncDirectory = func(string) error { return errors.New("injected directory sync") }
	err := s.Update(func(w *game.World) error { w.MaintainWithRandom(now, func() float64 { return .5 }); return nil })
	var committed *DurabilityError
	if !errors.As(err, &committed) {
		t.Fatal(err)
	}
	fresh := Store{Dir: s.Dir}
	before, err := fresh.View()
	if err != nil {
		t.Fatal(err)
	}
	if before.Players[1].RetiredAt.IsZero() || before.Planets[50] == nil {
		t.Fatal("rename not committed")
	}
	if err = fresh.Update(func(w *game.World) error {
		if w.MaintainWithRandom(now, func() float64 { t.Fatal("replay draw"); return 0 }) {
			t.Fatal("replay ran")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	after, _ := fresh.View()
	if !reflect.DeepEqual(before, after) {
		t.Fatal("committed maintenance repeated")
	}
}
func TestVersion17RetirementAwardMigrationReadOnlyAndRejection(t *testing.T) {
	s, _ := dailyAwardStore(t)
	w, _ := s.View()
	w.Version = 17
	raw, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	upgraded, err := s.View()
	if err != nil || upgraded.Version != 18 || !reflect.DeepEqual(upgraded.Players, w.Players) || !reflect.DeepEqual(upgraded.Radio, w.Radio) {
		t.Fatal("migration altered accounts/history", err)
	}
	unchanged, _ := os.ReadFile(path)
	if string(unchanged) != string(raw) {
		t.Fatal("read-only migration wrote")
	}
	if err = s.Update(func(*game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	saved, _ := s.View()
	if saved.Version != 18 {
		t.Fatal("migration not saved")
	}
	for _, edit := range []func(*game.World){func(w *game.World) { w.Players[1].RetiredAt = w.Created.AddDate(0, 0, 14) }, func(w *game.World) { w.Radio[0].System = "super-planet" }, func(w *game.World) { w.News = []game.NewsEvent{{Kind: game.NewsRetirement}} }} {
		var old game.World
		_ = json.Unmarshal(raw, &old)
		edit(&old)
		b, _ := json.Marshal(old)
		_ = os.WriteFile(path, b, 0600)
		if _, err = s.View(); err == nil {
			t.Fatal("future maintenance fields accepted in legacy world")
		}
	}
}

func TestPostAssaultAwardCannotReviveOldLanding(t *testing.T) {
	s, next, oldToken := xannorPlanetStore(t)
	if err := s.Update(func(w *game.World) error { w.MaintainWithRandom(next, func() float64 { return .5 }); return nil }); err != nil {
		t.Fatal(err)
	}
	saved, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	if saved.Planets[2] != nil || saved.Planets[50] == nil || saved.Sectors[10].Planet != 50 || saved.Players[1].PlanetToken != "" {
		t.Fatal("post-assault award/order", saved.Planets)
	}
	if saved.Planets[50].Fighters != 0 || saved.Planets[50].Bank != 500000 || saved.Planets[50].Updated != next {
		t.Fatal("new award inherited old estate")
	}
	if err = s.ForShip(1, 0).Update(func(w *game.World) error { return w.Bank(1, oldToken, 0, next) }); err == nil {
		t.Fatal("old landing reached newly awarded planet")
	}
}
