package door

import (
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestDefenseConfirmationRejectsChangedGroup(t *testing.T) {
	term := &confirmationTerminal{scripted: &scripted{lines: []string{"breach 8 10001", "y", "y", "q"}}}
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		if _, err := w.Join("nav", "Navigator"); err != nil {
			return err
		}
		w.Players[1].Sector = 7
		w.Players[1].Fighters = 10001
		w.Sectors[7].Warps = []int{8}
		owner, err := w.Join("owner", "Owner")
		if err != nil {
			return err
		}
		w.Sectors[8].Defense = &game.SectorDefense{Owner: owner.ID, Fighters: 1000}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	term.beforeConfirm = func() error {
		return st.Update(func(w *game.World) error { w.Sectors[8].Defense.Fighters++; return nil })
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Sector != 7 || w.Players[1].Fighters != 10001 || w.Players[1].Turns != 500 || !strings.Contains(term.output.String(), "confirm again") {
		t.Fatal(term.output.String())
	}
}

func TestCurrentHostileDefenseAllowsDecliningFleeAndQuitting(t *testing.T) {
	term := &scripted{lines: []string{"f 0;flee;y", "n", "q"}}
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		if _, err := w.Join("nav", "Navigator"); err != nil {
			return err
		}
		w.Players[1].Sector = 8
		w.Sectors[8].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 1000}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Sector != 8 || w.Sectors[8].Defense.Fighters != 1000 || !strings.Contains(term.output.String(), "Defense encounter cancelled.") {
		t.Fatal(term.output.String())
	}
}
