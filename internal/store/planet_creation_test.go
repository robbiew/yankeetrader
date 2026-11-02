package store

import (
	"bytes"
	"encoding/json"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"os"
	"sync"
	"testing"
	"time"
)

func creationStore(t *testing.T) (Store, Store) {
	t.Helper()
	s := create(t)
	if err := s.Update(func(w *game.World) error { w.Players[1].Credits = 50000; w.Players[1].Sector = 8; return nil }); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	return s, s.ForShip(1, w.Players[1].ShipGeneration, w.Season)
}
func TestPlanetCreationAtomicConcurrentRetryAndWarning(t *testing.T) {
	s, b := creationStore(t)
	before, _ := os.ReadFile(s.Dir + "/world.json")
	abort := errors.New("abort")
	if err := b.Update(func(w *game.World) error {
		if e := w.CreatePlanet(1, "Uncommitted", time.Now()); e != nil {
			return e
		}
		return abort
	}); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if !bytes.Equal(before, after) {
		t.Fatal("aborted creation saved")
	}
	b.syncDirectory = func(string) error { return errors.New("sync failure") }
	err := b.CreatePlanet(1, "Saved", 8, time.Now, time.Now().Add(time.Minute))
	var warning *DurabilityError
	if !errors.As(err, &warning) {
		t.Fatal(err)
	}
	b.syncDirectory = nil
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if b.CreatePlanet(1, "Retry", 8, time.Now, time.Now().Add(time.Minute)) == nil {
				t.Error("retry charged again")
			}
		}()
	}
	wg.Wait()
	w, _ := s.View()
	if len(w.News) != 1 || w.News[0].PlanetName != "Saved" || len(w.Planets) != 1 || w.Players[1].Credits != 25000 {
		t.Fatal(w.News, w.Players[1])
	}
}
func TestPlanetCreationStaleAndExpiredSavesNothing(t *testing.T) {
	for _, mode := range []string{"expired", "lock-wait", "location", "generation", "season", "late-expiry"} {
		t.Run(mode, func(t *testing.T) {
			s, b := creationStore(t)
			deadline := time.Now().Add(time.Minute)
			now := time.Now
			switch mode {
			case "expired":
				deadline = time.Now()
			case "location":
				_ = s.Update(func(w *game.World) error { w.Players[1].Sector = 7; return nil })
			case "generation":
				b = b.ForShip(1, 99999, 1)
			case "season":
				b = b.ForShip(1, 0, 99999)
			case "late-expiry":
				deadline = time.Now().Add(time.Second)
				now = func() time.Time { time.Sleep(time.Until(deadline)); return time.Now() }
			}
			before, _ := os.ReadFile(s.Dir + "/world.json")
			var err error
			if mode == "lock-wait" {
				held, release, done := make(chan struct{}), make(chan struct{}), make(chan struct{})
				go func() { _ = s.locked(func() error { close(held); <-release; return nil }); close(done) }()
				<-held
				deadline = time.Now().Add(30 * time.Millisecond)
				result := make(chan error, 1)
				go func() { result <- b.CreatePlanet(1, "Blocked", 8, now, deadline) }()
				time.Sleep(60 * time.Millisecond)
				close(release)
				<-done
				err = <-result
			} else {
				err = b.CreatePlanet(1, "Blocked", 8, now, deadline)
			}
			after, _ := os.ReadFile(s.Dir + "/world.json")
			if err == nil || !bytes.Equal(before, after) {
				t.Fatal("stale/expired creation published", err)
			}
		})
	}
}
func TestPlanetCreationMigrationReadOnlyAndNoBackfill(t *testing.T) {
	s, b := creationStore(t)
	if err := b.CreatePlanet(1, "Historical", 8, time.Now, time.Now().Add(time.Minute)); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	w.Version = 27
	w.News = nil
	raw, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	loaded, err := s.View()
	after, _ := os.ReadFile(path)
	if err != nil || loaded.Version != game.WorldVersion || len(loaded.News) != 0 || !bytes.Equal(raw, after) {
		t.Fatal("read migration rewrote/backfilled", err)
	}
	if err = s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	loaded, _ = s.View()
	if loaded.Version != game.WorldVersion || len(loaded.News) != 0 || loaded.Planets[2].Name != "Historical" {
		t.Fatal(loaded)
	}
}

func TestPlanetCreationRejectsOtherBoundCreator(t *testing.T) {
	s, b := creationStore(t)
	before, _ := os.ReadFile(s.Dir + "/world.json")
	if b.CreatePlanet(2, "Other", 8, time.Now, time.Now().Add(time.Minute)) == nil {
		t.Fatal("bound login created for another identity")
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if !bytes.Equal(before, after) {
		t.Fatal("changed save")
	}
}
