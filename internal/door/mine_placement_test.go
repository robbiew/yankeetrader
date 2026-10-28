package door

import (
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestDropPersistsAcrossReconnectAndTriggersOnlyAfterReentry(t *testing.T) {
	term := &scripted{lines: []string{"d 5", "y", "q"}}
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		p, err := w.Join("nav", "Navigator")
		if err != nil {
			return err
		}
		p.Sector, p.Mines, p.Shields = 8, 10, 1000000
		w.Sectors[8].Warps, w.Sectors[7].Warps = []int{7}, []int{8}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Shields != 1000000 || w.Players[1].Mines != 5 || w.Players[1].MineGraceSector != 8 || w.Sectors[8].Minefield[0].Count != 5 || strings.Contains(term.output.String(), "Mine encounter saved") {
		t.Fatal("deployment detonated before departure", term.output.String())
	}
	// A separate session must retain the departure right, not detonate at login.
	term = &scripted{lines: []string{"i;q"}}
	s.Terminal = term
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ = st.View()
	if w.Players[1].MineGraceSector != 8 || w.Sectors[8].Minefield[0].Count != 5 || strings.Contains(term.output.String(), "Mine encounter saved") {
		t.Fatal("reconnect detonated deployed field")
	}
	term = &scripted{lines: []string{"m 7;m 8", "y", "q"}}
	s.Terminal = term
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ = st.View()
	if w.Players[1].Sector != 8 || w.Players[1].Turns != 498 || w.Players[1].MineGraceSector != 0 || len(w.Sectors[8].Minefield) != 0 || !strings.Contains(term.output.String(), "Mine encounter saved: 5 mines") {
		t.Fatal("reentry bypassed field", term.output.String())
	}
}
