package store

import (
	"errors"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestHumanDefenseDesertionDailyPersistenceAndRollback(t *testing.T) {
	s := create(t) // Only sector 8 is outside the protected Union, so no route.
	if err := s.Update(func(w *game.World) error {
		w.Sectors[8].Defense = &game.SectorDefense{Owner: 1, Fighters: 50}
		w.Ports[2].Treasury = 90
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	now := time.Now().Add(24 * time.Hour)
	before, _ := os.ReadFile(s.Dir + "/world.json")
	abort := errors.New("abort after daily ownership changes")
	if err := s.Update(func(w *game.World) error { w.Maintain(now); return abort }); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("aborted daily update published ownership, tax, scores or date")
	}
	if err := s.Update(func(w *game.World) error { w.Maintain(now); w.Ports[2].Treasury = -1; return nil }); err == nil {
		t.Fatal("invalid daily save accepted")
	}
	after, _ = os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("failed validation partly published daily update")
	}
	var wg sync.WaitGroup
	errs := make(chan error, 8)
	runs := make(chan bool, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- s.Update(func(w *game.World) error { runs <- w.Maintain(now); return nil })
		}()
	}
	wg.Wait()
	close(errs)
	close(runs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	count := 0
	for ran := range runs {
		if ran {
			count++
		}
	}
	w, err := (Store{Dir: s.Dir}).View()
	if err != nil {
		t.Fatal(err)
	}
	d := w.Sectors[8].Defense
	// Either random outcome is valid; exact thresholds are tested with a
	// controlled stream in game. Persistence must preserve the chosen outcome.
	if count != 1 || d.Fighters != 50 || (d.Owner != 1 && d.Owner != game.MercenaryOwner) || w.Ports[2].Treasury != 81 {
		t.Fatal("daily action replay, invalid owner or force/tax loss", count, d)
	}
	owned, err := w.OwnSectorFighters(1)
	if err != nil || (len(owned) == 1) != (d.Owner == 1) {
		t.Fatal("owned-fighter report disagrees with saved daily ownership", owned, err)
	}
	before, _ = os.ReadFile(s.Dir + "/world.json")
	if err := s.Update(func(w *game.World) error {
		if w.Maintain(now) || w.Maintain(now.Add(-24*time.Hour)) {
			return errors.New("maintenance repeated")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	after, _ = os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("same-day/rollback update rerolled desertion")
	}
}
