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

func TestXannorVersionThirteenMigrationPreservesLegacyAssets(t *testing.T) {
	s := Store{Dir: t.TempDir()}
	w, err := game.New(time.Now(), 36, 12)
	if err != nil {
		t.Fatal(err)
	}
	_, _ = w.Join("captain", "Captain")
	w.Planets[99] = &game.Planet{Generation: uint64(99), ID: 99, Sector: 8, Owner: game.MercenaryOwner, FactionHome: game.MercenaryHome, Name: "Mercenary Base", Ground: 150000, Bank: 25000000, Updated: w.Created}
	w.Sectors[8].Planet = 99
	if err := s.Create(w); err != nil {
		t.Fatal(err)
	}
	w.Version = 13
	w.Season = 0
	w.GenerationSeed = nil
	w.NextBattleReport = 0 // This fixture represents a pre-report save.
	w.Planets[100] = &game.Planet{Generation: uint64(100), ID: 100, Sector: 9, Owner: 1, Name: "Xannoron", Ground: 123, Bank: 456, Updated: w.Created}
	w.Sectors[9].Planet = 100
	if err := w.RecordLogin(1, w.Created); err != nil {
		t.Fatal(err)
	}
	path := s.Dir + "/world.json"
	w.Players[1].LastActivity = "" // Pre-version-18 saves have no activity field.
	old, _ := marshalHistoricalWorld(w)
	if err := os.WriteFile(path, old, 0600); err != nil {
		t.Fatal(err)
	}
	current, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	expected := *w
	expected.Version = game.WorldVersion
	expected.Season = 1
	expected.NextBattleReport = 1
	want, _ := json.Marshal(expected)
	got, _ := json.Marshal(current)
	if string(want) != string(got) || current.Xannor != nil || current.Planets[100].FactionHome != "" {
		t.Fatal("migration inferred HQ/home or changed existing assets/history")
	}
	unchanged, _ := os.ReadFile(path)
	if string(unchanged) != string(old) {
		t.Fatal("read-only migration rewrote save")
	}
	if err := s.Update(func(*game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	var saved game.World
	data, _ := os.ReadFile(path)
	if err := json.Unmarshal(data, &saved); err != nil || saved.Version != game.WorldVersion {
		t.Fatal("version upgrade not persisted", err)
	}
	for _, mode := range []string{"state", "home"} {
		w.Version = 13
		w.Season = 0
		w.GenerationSeed = nil
		w.NextBattleReport = 0 // This fixture represents a pre-report save.
		w.Xannor = nil
		w.Planets[100].FactionHome = ""
		w.Planets[100].Owner = 1
		if mode == "state" {
			w.Xannor = &game.XannorState{HQ: 8}
		} else {
			w.Planets[100].FactionHome = game.XannorHome
			w.Planets[100].Owner = game.XannorOwner
		}
		bad, _ := marshalHistoricalWorld(w)
		if err := os.WriteFile(path, bad, 0600); err != nil {
			t.Fatal(err)
		}
		if _, err := s.View(); err == nil {
			t.Fatal("legacy save smuggled Xannor lifecycle state", mode)
		}
	}
}

func TestXannorAtomicMaintenanceReserveReplayAndCapture(t *testing.T) {
	now := time.Now().UTC()
	w, err := game.New(now, 36, 12)
	if err != nil {
		t.Fatal(err)
	}
	_, _ = w.Join("captain", "Captain")
	w.Xannor = &game.XannorState{HQ: 8, Reserve: game.MaxQuantity}
	w.Sectors[8].Defense = &game.SectorDefense{Owner: 1, Fighters: game.MaxQuantity}
	// A captured home must not move or refill during the sector reclaim battle.
	w.Planets[100] = &game.Planet{Generation: uint64(100), ID: 100, Sector: 8, Owner: 1, FactionHome: game.XannorHome, Name: "Captured", Updated: now.Add(72 * time.Hour)}
	w.Sectors[8].Planet = 100
	s := Store{Dir: t.TempDir()}
	if err := s.Create(w); err != nil {
		t.Fatal(err)
	}
	path := s.Dir + "/world.json"
	before, _ := os.ReadFile(path)
	abort := errors.New("abort HQ phase")
	next := now.Add(24 * time.Hour)
	if err := s.Update(func(w *game.World) error { w.Maintain(next); return abort }); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("aborted HQ phase published partial casualties or home")
	}
	var wg sync.WaitGroup
	errs := make(chan error, 6)
	for i := 0; i < 6; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); errs <- s.Update(func(w *game.World) error { w.Maintain(next); return nil }) }()
	}
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
	if saved.Xannor.HQ != 8 || saved.Xannor.Reserve <= 0 || saved.Sectors[8].Defense.Owner != 1 || saved.Xannor.Reserve+saved.Sectors[8].Defense.Fighters != 2*game.MaxQuantity-250*10000 {
		t.Fatal("unfinished battle lost/duplicated participants or ran more than once")
	}
	p := saved.Planets[100]
	if p.Owner != 1 || p.Sector != 8 || p.Ground != 0 || p.Bank != 0 || p.Name != "Captured" || p.FactionHome != game.XannorHome {
		t.Fatal("captured home mutated", p)
	}
	before, _ = os.ReadFile(path)
	if err := s.Update(func(w *game.World) error {
		if w.Maintain(next) || w.Maintain(now) {
			return errors.New("phase repeated")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	after, _ = os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("daily replay/rollback changed persisted world")
	}
	if err := s.Update(func(w *game.World) error { w.Xannor.HQ = 7; return nil }); err == nil {
		t.Fatal("invalid HQ was published")
	}
	after, _ = os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("validation failure damaged committed reserve")
	}
}
