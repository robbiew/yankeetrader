package door

import (
	"github.com/robbiew/yankeetrader/internal/game"
	"strings"
	"testing"
)

func TestMineEntryRequiresFreshAndCurrentWarning(t *testing.T) {
	for _, mode := range []string{"decline", "changed"} {
		t.Run(mode, func(t *testing.T) {
			term := &confirmationTerminal{scripted: &scripted{lines: []string{"m 2;y", "n", "q"}}}
			s, st := navigationSession(t, term)
			if err := st.Update(func(w *game.World) error { w.Sectors[2].Minefield = []game.MineLayer{{Owner: 0, Count: 1}}; return nil }); err != nil {
				t.Fatal(err)
			}
			term.beforeConfirm = func() error { return nil }
			if mode == "changed" {
				term.lines = []string{"m 2", "y", "q"}
				term.beforeConfirm = func() error {
					return st.Update(func(w *game.World) error { w.Sectors[2].Minefield[0].Count = 2; return nil })
				}
			}
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			if w.Players[1].Sector != 1 || w.Players[1].Turns != 500 {
				t.Fatal("stale/declined warning moved ship")
			}
			if mode == "changed" && !strings.Contains(term.output.String(), "confirm again") {
				t.Fatal(term.output.String())
			}
		})
	}
}

func TestAutopilotStopsBeforeMinesAndReportsActualStock(t *testing.T) {
	term := &scripted{lines: []string{"s;auto 4;y;q"}}
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		w.Sectors[2].Minefield = []game.MineLayer{{Owner: 0, Count: 20}}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Sector != 1 || w.Players[1].Turns != 500 {
		t.Fatal("autopilot entered mines")
	}
	if !strings.Contains(term.output.String(), "Sector mines: 20") || !strings.Contains(term.output.String(), "confirm entry manually") {
		t.Fatal(term.output.String())
	}
}
