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

func overcrowdingStore(t *testing.T) (Store, time.Time) {
	t.Helper()
	at := time.Date(2026, 10, 29, 0, 0, 0, 0, time.UTC)
	now := at.Add(24 * time.Hour)
	w, err := game.New(at, 36, 12)
	if err != nil {
		t.Fatal(err)
	}
	a, _ := w.Join("dock-identity", "Docked")
	b, _ := w.Join("land-identity", "Landed")
	b.Sector = 2
	port := w.Ports[1]
	port.Updated = now
	port.Production = [3]float64{2000000, 500, 501}
	port.Supply = [3]float64{20000000, 5000, 5010}
	for id := 2; id <= 3; id++ {
		p := &game.Planet{ID: id, Sector: id, Owner: b.ID, Name: "Crowded", Updated: now,
			Production: [3]float64{100, 100, 100}, Cargo: [3]float64{1000, 1000, 1000}, Ground: 4000000, Bank: 12345, Fighters: 11, Missiles: 13, Mines: 17, Plasma: 19}
		if id == 3 {
			p.Production = [3]float64{2000000, 0, 0}
			p.Cargo = [3]float64{20000000, 0, 0}
			p.Ground = 100
			p.Name = "Plague"
		}
		w.Planets[id] = p
		w.Sectors[id].Planet = id
	}
	if err = w.Dock(a.ID, now); err != nil {
		t.Fatal(err)
	}
	if err = w.Land(b.ID, now); err != nil {
		t.Fatal(err)
	}
	// Prevent unrelated faction movements while exercising the real full day.
	for _, s := range w.Sectors {
		s.Warps = nil
	}
	st := Store{Dir: t.TempDir()}
	if err = st.Create(w); err != nil {
		t.Fatal(err)
	}
	return st, now
}
func assertOutbreaks(t *testing.T, w *game.World) {
	t.Helper()
	if w.Planets[2].Bank != 6173 || w.Planets[3].Bank != 12345 || w.Planets[2].Ground != 3000000 || w.Planets[3].Ground != 75 {
		t.Fatal("lost or duplicated event assets", w.Planets)
	}
	if len(w.News) < 3 || w.News[0].Kind != game.NewsPortPlague || w.News[0].PortCount != 1 || w.News[1].Kind != game.NewsCivilWar || w.News[2].Kind != game.NewsPlanetPlague {
		t.Fatal("missing or stale public events", w.News)
	}
	if w.Players[1].DockToken != "" || w.Players[2].PlanetToken != "" || w.Planets[2].Owner != 2 || w.Planets[3].Owner != 2 || w.Planets[2].Fighters != 11 {
		t.Fatal("token/title/weapons changed incorrectly")
	}
}
func TestOvercrowdingAtomicAbortValidationConcurrentReloadAndReplay(t *testing.T) {
	st, now := overcrowdingStore(t)
	path := st.Dir + "/world.json"
	before, _ := os.ReadFile(path)
	for _, validation := range []bool{false, true} {
		err := st.Update(func(w *game.World) error {
			w.MaintainWithRandom(now, func() float64 { return .5 })
			assertOutbreaks(t, w)
			if validation {
				w.Planets[2].Bank = -1
				return nil
			}
			return errors.New("abort")
		})
		if err == nil {
			t.Fatal("failed event transaction saved")
		}
		after, _ := os.ReadFile(path)
		if string(after) != string(before) {
			t.Fatal("partial assets/news/date persisted")
		}
	}
	var count atomic.Int32
	var wg sync.WaitGroup
	errs := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- st.Update(func(w *game.World) error {
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
		t.Fatal("duplicate daily damage", count.Load())
	}
	fresh := Store{Dir: st.Dir}
	w, err := fresh.View()
	if err != nil {
		t.Fatal(err)
	}
	assertOutbreaks(t, w)
	raw, _ := json.Marshal(w)
	for _, at := range []time.Time{now, now.Add(time.Hour), now.Add(-24 * time.Hour)} {
		if err = fresh.Update(func(w *game.World) error {
			if w.MaintainWithRandom(at, func() float64 { t.Fatal("replay consumed randomness"); return 0 }) {
				t.Fatal("daily replay")
			}
			return nil
		}); err != nil {
			t.Fatal(err)
		}
	}
	after, _ := fresh.View()
	encoded, _ := json.Marshal(after)
	if string(raw) != string(encoded) {
		t.Fatal("replay changed saved damage/report")
	}
}
func TestOvercrowdingCommittedDurability(t *testing.T) {
	st, now := overcrowdingStore(t)
	st.syncDirectory = func(string) error { return errors.New("sync failed after rename") }
	err := st.Update(func(w *game.World) error { w.MaintainWithRandom(now, func() float64 { return .5 }); return nil })
	var durability *DurabilityError
	if !errors.As(err, &durability) {
		t.Fatal(err)
	}
	fresh := Store{Dir: st.Dir}
	before, err := fresh.View()
	if err != nil {
		t.Fatal(err)
	}
	assertOutbreaks(t, before)
	if err = fresh.Update(func(w *game.World) error {
		w.MaintainWithRandom(now, func() float64 { t.Fatal("committed event repeated"); return 0 })
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	after, _ := fresh.View()
	if !reflect.DeepEqual(before, after) {
		t.Fatal("committed event duplicated")
	}
}
func TestVersion18OvercrowdingMigrationPreservesStateAndRejectsFutureNews(t *testing.T) {
	st, _ := overcrowdingStore(t)
	w, _ := st.View()
	w.Version = 18
	w.Season = 0
	w.GenerationSeed = nil
	raw, _ := json.Marshal(w)
	path := st.Dir + "/world.json"
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	loaded, err := st.View()
	if err != nil || loaded.Version != game.WorldVersion {
		t.Fatal(err)
	}
	original := *loaded
	original.Version = 18
	original.Season = 0
	original.GenerationSeed = nil
	if !reflect.DeepEqual(&original, w) {
		t.Fatal("migration changed assets, sessions or history")
	}
	unchanged, _ := os.ReadFile(path)
	if string(unchanged) != string(raw) {
		t.Fatal("read-only load rewrote legacy save")
	}
	if err = st.Update(func(*game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	saved, _ := st.View()
	if saved.Version != game.WorldVersion {
		t.Fatal("migration not persisted")
	}
	for _, e := range []game.NewsEvent{{Kind: game.NewsPortPlague, PortCount: 1}, {Kind: game.NewsPlanetPlague, PlanetName: "Crowded"}, {Kind: game.NewsCivilWar, PlanetName: "Crowded"}, {Kind: game.NewsLogin, Alias: "Docked", PortCount: 1}} {
		clone := *w
		clone.News = []game.NewsEvent{e}
		clone.News[0].ID = 1
		clone.News[0].At = w.Created
		clone.NextNews = 2
		b, _ := json.Marshal(clone)
		_ = os.WriteFile(path, b, 0600)
		if _, err = st.View(); err == nil {
			t.Fatal("legacy accepted new event data", e)
		}
	}
}
