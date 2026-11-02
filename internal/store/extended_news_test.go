package store

import (
	"bytes"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"testing"
)

func TestExtendedNewsCommitsWithDeathAndRollsBackWithAction(t *testing.T) {
	s, _, at := genesisStore(t)
	before := travelBytes(t, s)
	failure := errors.New("reject enclosing transaction")
	err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		if e := w.RecordDeath(game.DeathContext{Victim: 1, Generation: p.ShipGeneration, Sector: p.Sector, Cause: "hazard"}, at); e != nil {
			return e
		}
		if len(w.News) != 1 || w.News[0].Combat == nil || w.News[0].Combat.Operation != "ship-death" {
			t.Fatal("missing staged event")
		}
		return failure
	})
	if !errors.Is(err, failure) || !bytes.Equal(before, travelBytes(t, s)) {
		t.Fatal("rolled back action leaked news", err)
	}
	if err = s.Update(func(w *game.World) error {
		p := w.Players[1]
		return w.RecordDeath(game.DeathContext{Victim: 1, Generation: p.ShipGeneration, Sector: p.Sector, Cause: "hazard"}, at)
	}); err != nil {
		t.Fatal(err)
	}
	fresh, err := (Store{Dir: s.Dir}).View()
	if err != nil || fresh.Players[1].Death == nil || len(fresh.News) != 1 || fresh.News[0].Combat.Operation != "ship-death" {
		t.Fatal("death/news not saved together", err)
	}
}
