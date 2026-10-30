package store

import (
	"errors"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestBlockedPlanetReportChargeIsAtomicAndRollsBack(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		w.Players[1].Turns = 1
		w.Sectors[2].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 1}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	bound := s.ForShip(1, w.Players[1].ShipGeneration, 1)
	abort := errors.New("aborted report")
	if err := bound.Update(func(w *game.World) error {
		if _, err := w.RemotePlanetReport(1, 2, time.Now()); err != nil {
			return err
		}
		return abort
	}); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	w, _ = s.View()
	if w.Players[1].Turns != 1 {
		t.Fatal("aborted report spent a turn")
	}
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results <- bound.Update(func(w *game.World) error {
				r, err := w.RemotePlanetReport(1, 2, time.Now())
				if err == nil && (r.Available || !r.TurnSpent || r.Details != nil) {
					return errors.New("invalid blocked report")
				}
				return err
			})
		}()
	}
	wg.Wait()
	close(results)
	success := 0
	for err := range results {
		if err == nil {
			success++
		}
	}
	w, err := s.View()
	if err != nil || success != 1 || w.Players[1].Turns != 0 || w.Players[1].Sector != 1 {
		t.Fatalf("concurrent charge: successes %d, world %+v, %v", success, w.Players[1], err)
	}
}
