package door

import (
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestPendingXannorRevengeIsPrivateInBothInfoModes(t *testing.T) {
	for _, classic := range []bool{false, true} {
		term := &scripted{lines: []string{"i;q"}}
		s, st := radioSession(t, term)
		if err := st.Update(func(w *game.World) error {
			w.Xannor = &game.XannorState{HQ: 8, Revenge: &game.XannorRevengeTarget{Player: 1, Generation: w.Players[1].ShipGeneration}}
			return nil
		}); err != nil {
			t.Fatal(err)
		}
		s.Classic = classic
		if classic {
			term.lines = []string{"", "", "", "i;q;y"}
		}
		if err := s.Run(); err != nil {
			t.Fatal(err, term.output.String())
		}
		if !strings.Contains(term.output.String(), "Xannor revenge pending for this ship.") {
			t.Fatal("pending status absent", classic, term.output.String())
		}
		w, _ := st.View()
		if !w.HasXannorRevenge(1) {
			t.Fatal("info consumed pending revenge")
		}
		other := &scripted{lines: []string{"i;news;q"}}
		s.Terminal, s.Store, s.Classic, s.Identity, s.Alias = other, st, false, "visitor", "Visitor"
		if err := s.Run(); err != nil {
			t.Fatal(err)
		}
		if strings.Contains(other.output.String(), "revenge pending") {
			t.Fatal("other caller/public journal leaked target")
		}
	}
}
