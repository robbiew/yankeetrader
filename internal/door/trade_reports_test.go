package door

import (
	"reflect"
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func tradeReportSession(t *testing.T, term Terminal) (Session, store.Store) {
	t.Helper()
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		p, err := w.Join("nav", "Navigator")
		if err != nil {
			return err
		}
		p.Sector, p.Turns = 7, 0
		for _, sector := range w.Sectors {
			sector.Warps = nil
		}
		for _, sector := range []int{7, 2, 3, 4, 5} {
			w.Sectors[sector].Warps = []int{map[int]int{7: 2, 2: 3, 3: 4, 4: 5, 5: 7}[sector]}
		}
		for id := range w.Ports {
			if id > 3 {
				w.Sectors[w.Ports[id].Sector].Port = 0
				delete(w.Ports, id)
			}
		}
		w.Ports[2].Name, w.Ports[3].Name = "First Market", "Second Market"
		w.Ports[2].Coefficient = [3]float64{50, -45, -55}
		w.Ports[3].Coefficient = [3]float64{-50, 50, -55}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, st
}

func TestClassicNearestAndTradeComputerCommands(t *testing.T) {
	term := &scripted{lines: []string{"", "", "", "c;14;3;S;16;17;1;q;y"}}
	s, st := tradeReportSession(t, term)
	s.Classic = true
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	text := term.output.String()
	for _, want := range []string{"Your action: [B] Buy or [S] Sell?", "Distance: 2 | Sector: 3 | Second Market", "S ore @ 30", "Return: 4", "Spread: 49 credits/unit of each", "no accessible cargo trading port in your sector"} {
		if !strings.Contains(text, want) {
			t.Fatalf("missing %q: %s", want, text)
		}
	}
	if strings.Contains(text, "not available yet") || strings.Contains(text, "Sector: 2 | First Market") {
		t.Fatal("computer dispatch or selling filter failed", text)
	}
	w, _ := st.View()
	if w.Players[1].Sector != 7 || w.Players[1].Turns != 0 || w.Players[1].Credits != 1005 {
		t.Fatal("free computer reports moved/spent")
	}
}

func TestCompactTradeReportsAndInvalidFiltersAreFree(t *testing.T) {
	term := &scripted{lines: []string{"nearest ore sell;pairs;profits;nearest team;nearest ore;profits bad;q"}}
	s, st := tradeReportSession(t, term)
	if err := st.Update(func(w *game.World) error { w.Players[1].Sector = 2; return nil }); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	text := term.output.String()
	if strings.Count(text, "Spread: 49 credits/unit of each") != 2 || !strings.Contains(text, "Approach: 0 warps") || !strings.Contains(text, "don't belong to a team") || !strings.Contains(text, "use NEAREST") || !strings.Contains(text, "without arguments") {
		t.Fatal(text)
	}
	w, _ := st.View()
	if w.Players[1].Turns != 0 || w.Players[1].Credits != 1005 || w.Players[1].DockToken != "" || w.Players[1].PlanetToken != "" {
		t.Fatal("report changed player resources or authorizations")
	}
}

func TestTradeReportPagingRefreshesAccessAndPreservesQueuedCommands(t *testing.T) {
	term := &reportInputTerminal{scripted: &scripted{lines: []string{""}}}
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		if _, err := w.Join("nav", "Navigator"); err != nil {
			return err
		}
		if _, err := w.Join("enemy", "Enemy"); err != nil {
			return err
		}
		w.Sectors[1].Warps = []int{2, 3, 4, 5, 6, 7, 8}
		w.Ports[8].Name = "Hidden Market"
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	s.Store = st.ForShip(1, w.Players[1].ShipGeneration, 1)
	term.beforeInput = func() {
		if err := st.Update(func(w *game.World) error {
			w.Sectors[8].Defense = &game.SectorDefense{Owner: 2, Fighters: 50}
			return nil
		}); err != nil {
			t.Fatal(err)
		}
	}
	pending := []string{"i", "q"}
	if err := s.tradeReport(1, "nearest", nil, &pending); err != nil {
		t.Fatal(err)
	}
	text := term.output.String()
	if !strings.Contains(text, "More results?") || strings.Contains(text, "Hidden Market") || !reflect.DeepEqual(pending, []string{"i", "q"}) {
		t.Fatal("paging exposed stale data or consumed queued commands", text, pending)
	}
}

func TestNearestReadsAuthoritativeStateAfterFilterPrompt(t *testing.T) {
	term := &reportInputTerminal{scripted: &scripted{lines: []string{"s"}}}
	s, st := tradeReportSession(t, term)
	s.Classic = true
	if err := st.Update(func(w *game.World) error { _, err := w.Join("enemy", "Enemy"); return err }); err != nil {
		t.Fatal(err)
	}
	term.beforeInput = func() {
		if err := st.Update(func(w *game.World) error {
			w.Sectors[3].Defense = &game.SectorDefense{Owner: 2, Fighters: 50}
			return nil
		}); err != nil {
			t.Fatal(err)
		}
	}
	pending := []string{"3"}
	if err := s.tradeReport(1, "nearest", nil, &pending); err != nil {
		t.Fatal(err)
	}
	if text := term.output.String(); strings.Contains(text, "Second Market") || !strings.Contains(text, "No matching accessible") {
		t.Fatal("filter prompt leaked a newly guarded market", text)
	}
}
