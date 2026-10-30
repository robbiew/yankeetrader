package door

import (
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func reportSession(t *testing.T, term Terminal) (Session, store.Store) {
	t.Helper()
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		if _, err := w.Join("nav", "Navigator"); err != nil {
			return err
		}
		if _, err := w.Join("enemy", "Enemy"); err != nil {
			return err
		}
		w.Ports[2].Name = "Trading Post"
		w.Sectors[3].Planet, w.Sectors[4].Planet = 2, 3
		w.Planets[2] = &game.Planet{ID: 2, Sector: 3, Owner: 2, Name: "Private World", Ground: 12, Bank: 9876543, Updated: s.Now(), Production: [3]float64{1, 2, 3}}
		w.Planets[3] = &game.Planet{ID: 3, Sector: 4, Owner: 1, Name: "Home", Ground: 1, Updated: s.Now(), Production: [3]float64{1, 2, 3}}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, st
}

func TestClassicComputerReportsAndPrivatePlanet(t *testing.T) {
	term := &scripted{lines: []string{"", "", "", "c;2;2;9;3;13;1;q;y"}}
	s, st := reportSession(t, term)
	s.Classic = true
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	text := term.output.String()
	for _, want := range []string{"Commerce report for Trading Post", "Planet: Private World -*- Ground Forces: 12", "Planet: Home", "Sector: 4"} {
		if !strings.Contains(text, want) {
			t.Fatalf("missing %q: %s", want, text)
		}
	}
	if strings.Contains(text, "9876543") || strings.Contains(text, "Credits......") || strings.Contains(text, "not available yet") {
		t.Fatal("private fields disclosed or report unavailable", text)
	}
	w, _ := st.View()
	if w.Players[1].Turns != 500 || w.Players[1].Sector != 1 || w.Players[1].DockToken != "" || w.Players[1].PlanetToken != "" {
		t.Fatal("reports moved, docked, landed, or spent turns")
	}
}

func TestCompactReportsChargeOnlyBlockedPlanetQuery(t *testing.T) {
	term := &scripted{lines: []string{"portreport 2;planetreport 3;myplanets;portreport bad;planetreport 999;planetreport;;q"}}
	s, st := reportSession(t, term)
	if err := st.Update(func(w *game.World) error {
		w.Sectors[2].Defense = &game.SectorDefense{Owner: 2, Fighters: 50}
		w.Sectors[3].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 50}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	text := term.output.String()
	if !strings.Contains(text, "One turn spent") || !strings.Contains(text, "Report cancelled.") || strings.Contains(text, "Private World") || strings.Contains(text, "Trading Post") {
		t.Fatal("blocked reports leaked information or did not account for turn", text)
	}
	w, _ := st.View()
	if w.Players[1].Turns != 499 || w.Players[1].Sector != 1 {
		t.Fatal("invalid, cancelled, or port report spent additional turns")
	}
}

type reportInputTerminal struct {
	*scripted
	beforeInput func()
}

func (term *reportInputTerminal) ReadLine(deadline time.Time) (string, error) {
	if term.beforeInput != nil {
		hook := term.beforeInput
		term.beforeInput = nil
		hook()
	}
	return term.scripted.ReadLine(deadline)
}

func TestPlanetReportRechecksOwnershipAfterSectorPrompt(t *testing.T) {
	term := &reportInputTerminal{scripted: &scripted{lines: []string{"3"}}}
	s, st := reportSession(t, term)
	if err := st.Update(func(w *game.World) error { w.Planets[2].Owner = 1; return nil }); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	s.Store = st.ForShip(1, w.Players[1].ShipGeneration, 1)
	term.beforeInput = func() {
		if err := st.Update(func(w *game.World) error { w.Planets[2].Owner = 2; return nil }); err != nil {
			t.Fatal(err)
		}
	}
	pending := []string{}
	if err := s.computerReport(1, "planetreport", nil, &pending); err != nil {
		t.Fatal(err)
	}
	text := term.output.String()
	if !strings.Contains(text, "Ground Forces: 12") || strings.Contains(text, "9876543") || strings.Contains(text, "Credits......") {
		t.Fatal("stale ownership exposed private report", text)
	}
}
