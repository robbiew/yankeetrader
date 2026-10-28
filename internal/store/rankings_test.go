package store

import (
	"errors"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestRankingsAtomicPublicationRollbackAndSessionGuard(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error { _, err := w.Join("enemy", "Enemy"); return err }); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	bound := s.ForShip(1, w.Players[1].ShipGeneration)
	before, _ := os.ReadFile(s.Dir + "/world.json")
	abort := errors.New("rollback")
	err := bound.Update(func(w *game.World) error {
		if _, err := w.RefreshRankings(1); err != nil {
			return err
		}
		return abort
	})
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if !errors.Is(err, abort) || string(before) != string(after) {
		t.Fatal("partial cache persisted", err)
	}
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func(owner int) {
			defer wg.Done()
			results <- s.Update(func(w *game.World) error {
				w.Ports[2].Owner = owner
				report, err := w.RefreshRankings(1)
				if err != nil {
					return err
				}
				for _, row := range report.Players {
					wantPorts := 0
					if row.ID == owner {
						wantPorts = 1
					}
					if row.Ports != wantPorts || w.Players[row.ID].StoredScore != row.Score {
						return errors.New("incoherent ownership/cache")
					}
				}
				return nil
			})
		}(1 + i%2)
	}
	wg.Wait()
	close(results)
	for err := range results {
		if err != nil {
			t.Fatal(err)
		}
	}
	w, _ = s.View()
	report, _ := w.PlayerRankings(1, false)
	for _, row := range report.Players {
		if w.Players[row.ID].StoredScore != row.Score {
			t.Fatal("cache from another snapshot")
		}
	}
	if err := s.Update(func(w *game.World) error {
		return w.RecordDeath(game.DeathContext{Victim: 1, Generation: w.Players[1].ShipGeneration, Sector: w.Players[1].Sector, Cause: "hazard"}, time.Now())
	}); err != nil {
		t.Fatal(err)
	}
	called := false
	if err := bound.Update(func(w *game.World) error { called = true; _, err := w.RefreshRankings(1); return err }); err == nil || called {
		t.Fatal("stale session refreshed replacement/dead scores", err)
	}
}
