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

func TestFactionHomeVersionTwelveMigrationAndLegacyIdentityRejection(t *testing.T) {
	s := create(t)
	w, _ := s.View()
	if err := w.RecordLogin(1, w.Created); err != nil {
		t.Fatal(err)
	}
	w.Version = 12
	w.NextBattleReport = 0 // This fixture represents a pre-report save.
	w.Planets[99] = &game.Planet{ID: 99, Sector: 8, Owner: 1, Name: "Mercenary Base", Updated: w.Created, Ground: 123, Bank: 1234}
	w.Sectors[8].Planet = 99
	old, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	if err := os.WriteFile(path, old, 0600); err != nil {
		t.Fatal(err)
	}
	current, err := s.View()
	if err != nil || current.Version != game.WorldVersion || current.Planets[99].Owner != 1 || current.Planets[99].FactionHome != "" || len(current.Planets) != 1 {
		t.Fatal("migration inferred home identity or changed player assets", current, err)
	}
	expected := *w
	expected.Version = game.WorldVersion
	expected.NextBattleReport = 1
	want, _ := json.Marshal(expected)
	got, _ := json.Marshal(current)
	if string(want) != string(got) || len(current.News) != 1 || current.NextNews != 2 {
		t.Fatal("version-12 migration changed existing state or newspaper history")
	}
	unchanged, _ := os.ReadFile(path)
	if string(old) != string(unchanged) {
		t.Fatal("read-only migration rewrote save")
	}
	if err := s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	var persisted game.World
	data, _ := os.ReadFile(path)
	if err := json.Unmarshal(data, &persisted); err != nil || persisted.Version != game.WorldVersion || persisted.Planets[99].Ground != 123 || persisted.Planets[99].Bank != 1234 {
		t.Fatal("migration failed to persist without resource changes", err)
	}
	for _, version := range []int{11, 12} {
		w.Version = version
		w.NextBattleReport = 0 // This fixture represents a pre-report save.
		w.Planets[99].FactionHome = game.MercenaryHome
		bad, _ := json.Marshal(w)
		if err := os.WriteFile(path, bad, 0600); err != nil {
			t.Fatal(err)
		}
		if _, err := s.View(); err == nil {
			t.Fatal("legacy save smuggled faction-home identity", version)
		}
	}
}

func TestMercenaryBaseAtomicCreationConcurrentDailyAndCapture(t *testing.T) {
	s := create(t)
	now := time.Now().Add(24 * time.Hour)
	before, _ := os.ReadFile(s.Dir + "/world.json")
	abort := errors.New("abort after base creation")
	if err := s.Update(func(w *game.World) error { w.Maintain(now); return abort }); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("aborted creation published home record or reference")
	}
	var wg sync.WaitGroup
	errs := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- s.Update(func(w *game.World) error { w.Maintain(now); return nil })
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	w, err := (Store{Dir: s.Dir}).View()
	if err != nil || len(w.Planets) != 1 || w.Planets[99].FactionHome != game.MercenaryHome || w.Planets[99].Bank != 25000000 || w.Sectors[8].Planet != 99 {
		t.Fatal("daily base creation duplicated or not persisted", err)
	}
	before, _ = os.ReadFile(s.Dir + "/world.json")
	if err := s.Update(func(w *game.World) error { w.Planets[99].FactionHome = "unknown"; return nil }); err == nil {
		t.Fatal("invalid faction-home identity was saved")
	}
	after, _ = os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("invalid home update damaged the committed base")
	}
	if err := s.Update(func(w *game.World) error {
		base := w.Planets[99]
		base.Owner, base.Ground, base.Bank = 1, 0, 0
		// Suppress unrelated production while testing captured-home restoration.
		base.Updated = now.Add(48 * time.Hour)
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := s.Update(func(w *game.World) error { w.Maintain(now.Add(24 * time.Hour)); return nil }); err != nil {
		t.Fatal(err)
	}
	w, err = s.View()
	if err != nil || len(w.Planets) != 1 || w.Planets[99].Owner != 1 || w.Planets[99].Ground != 0 || w.Planets[99].Bank != 0 {
		t.Fatal("captured base retitled, refilled or duplicated", err)
	}
}
