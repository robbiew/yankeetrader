package door

import (
	"errors"
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
)

func destroyAndReplace(t *testing.T, s Session, id int) {
	t.Helper()
	if err := s.Store.Update(func(w *game.World) error {
		p := w.Players[id]
		w.Players[2].Sector = p.Sector
		return w.RecordDeath(game.DeathContext{Victim: id, Generation: p.ShipGeneration, Sector: p.Sector, Killer: 2, Cause: "combat"}, s.Now())
	}); err != nil {
		t.Fatal(err)
	}
	if err := s.Store.Update(func(w *game.World) error { return w.ReplaceShip(id, s.Now()) }); err != nil {
		t.Fatal(err)
	}
}

func TestPromptCannotSpendFromReplacementShip(t *testing.T) {
	s, term := ownershipSession(t, []string{"acquire", "y", "m 3;q"})
	reads := 0
	s.Terminal = &ownershipChanged{term, func() {
		reads++
		if reads == 2 {
			destroyAndReplace(t, s, 1)
		}
	}}
	err := s.Run()
	if !errors.Is(err, game.ErrShipChanged) {
		t.Fatal("old prompt survived replacement", err, term.output.String())
	}
	w, _ := s.Store.View()
	p := w.Players[1]
	if p.Sector != 1 || p.Credits != 1005 || p.Turns != 500 || w.Ports[2].Owner != 2 || w.Players[2].Credits != 2000 {
		t.Fatal("old command chain changed replacement", p, w.Ports[2])
	}
	if strings.Contains(term.output.String(), "Sold!") {
		t.Fatal("stale purchase announced")
	}
}

func TestTeamPromptCannotCreateTeamForReplacementShip(t *testing.T) {
	s, term := ownershipSession(t, []string{"team;2;Ghost", "ABCD", "1;q"})
	reads := 0
	s.Terminal = &ownershipChanged{term, func() {
		reads++
		if reads == 2 {
			destroyAndReplace(t, s, 1)
		}
	}}
	if err := s.Run(); !errors.Is(err, game.ErrShipChanged) {
		t.Fatal("nested team prompt survived", err)
	}
	w, _ := s.Store.View()
	if len(w.Teams) != 0 || w.Players[1].Credits != 1005 {
		t.Fatal("old team prompt committed")
	}
}

func TestFreshLoginReplacesDeadShipWithoutRefillingTurns(t *testing.T) {
	for _, classic := range []bool{false, true} {
		t.Run(map[bool]string{true: "classic", false: "compact"}[classic], func(t *testing.T) {
			s, term := ownershipSession(t, nil)
			if err := s.Store.Update(func(w *game.World) error {
				w.Players[1].Turns = 37
				w.Players[2].Sector = 2
				w.Players[1].LastLogin = s.Now().UTC().Format("2006-01-02")
				return w.RecordDeath(game.DeathContext{Victim: 1, Sector: 2, Killer: 2, Cause: "retaliation"}, s.Now())
			}); err != nil {
				t.Fatal(err)
			}
			s.Classic = classic
			if classic {
				term.lines = []string{"", "", "", "q;y"}
			} else {
				term.lines = []string{"i;q"}
			}
			if err := s.Run(); err != nil {
				t.Fatal(err, term.output.String())
			}
			w, _ := s.Store.View()
			p := w.Players[1]
			if p.Death != nil || p.Sector != 1 || p.Turns != 37 || p.ShipGeneration != 2 {
				t.Fatal("login replacement failed", p)
			}
			if !strings.Contains(term.output.String(), "replacement ship has been built. Remaining turns: 37") {
				t.Fatal("replacement not explained", term.output.String())
			}
		})
	}
}

func TestIdleDeadSessionStopsBeforeNextCommand(t *testing.T) {
	s, term := ownershipSession(t, []string{"m 3;acquire;y;q"})
	s.Terminal = &ownershipChanged{term, func() {
		if err := s.Store.Update(func(w *game.World) error {
			w.Players[2].Sector = 2
			return w.RecordDeath(game.DeathContext{Victim: 1, Sector: 2, Killer: 2, Cause: "combat"}, s.Now())
		}); err != nil {
			t.Fatal(err)
		}
	}}
	if err := s.Run(); !errors.Is(err, game.ErrShipDestroyed) {
		t.Fatal("dead session acted", err)
	}
	w, _ := s.Store.View()
	if w.Players[1].Sector != 0 || w.Players[1].Turns != 500 || w.Ports[2].Owner != 2 {
		t.Fatal("dead session moved or spent")
	}
}
