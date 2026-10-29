package door

import (
	"errors"
	"fmt"
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func planetReportSession(t *testing.T, term Terminal) (Session, store.Store) {
	t.Helper()
	s, st := battleSession(t, term)
	if err := st.Update(func(w *game.World) error {
		r := &w.Players[1].BattleReports[0]
		r.FightersLost = 0
		r.ShieldsLost = 0
		r.Destroyed = true
		r.Planet = &game.PlanetBattleReport{ID: 2, Name: "Lost Eden", GroundBefore: 3, ProductionBefore: [3]float64{.1, .2, .3}, CargoBefore: [3]float64{1, 2, 3}, Neutralized: true}
		w.News = []game.NewsEvent{{ID: 1, At: s.Now().UTC(), Kind: game.NewsXannorPlanet, PlanetName: "Lost Eden", Outcome: "destroyed"}}
		w.NextNews = 2
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, st
}
func TestPlanetOwnerReportDeliveryHistoryAndPublicPrivacy(t *testing.T) {
	for _, classic := range []bool{false, true} {
		term := &scripted{lines: []string{"battles;q"}}
		s, st := planetReportSession(t, term)
		s.Classic = classic
		if classic {
			term.lines = []string{"", "", "", "battles;q;y"}
		}
		if err := s.Run(); err != nil {
			t.Fatal(err, term.output.String())
		}
		text := term.output.String()
		if strings.Count(text, "Lost Eden: Xannor lost 17 fighters; ground 3 -> 0.") != 2 || !strings.Contains(text, "Planet destroyed.") || strings.Contains(text, "Your ship was destroyed") {
			t.Fatal("planet report mislabeled/missing", text)
		}
		w, _ := st.View()
		if w.Players[1].BattleReports[0].Unread {
			t.Fatal("delivered report unread")
		}
		s.Store = st
		s.Identity = "visitor"
		s.Alias = "Visitor"
		s.Classic = false
		other := &scripted{lines: []string{"battles;news;q"}}
		s.Terminal = other
		if err := s.Run(); err != nil {
			t.Fatal(err)
		}
		text = other.output.String()
		if !strings.Contains(text, "Xannor assault on Lost Eden: destroyed.") || strings.Contains(text, "ground 3") || strings.Contains(text, "Production 0.100") || strings.Contains(text, "Private Xannor") || strings.Contains(text, "Sector 8") {
			t.Fatal("public journal leaked private battle details", text)
		}
	}
}

type planetOutputFailure struct{ *scripted }

func (t *planetOutputFailure) Printf(format string, args ...any) error {
	if strings.Contains(fmt.Sprintf(format, args...), "Private Xannor planetary report") {
		return errors.New("disconnect")
	}
	return t.scripted.Printf(format, args...)
}
func TestPlanetReportDisconnectRemainsUnread(t *testing.T) {
	s, st := planetReportSession(t, &planetOutputFailure{&scripted{}})
	s.Store = st.ForShip(1, 0)
	if err := s.battleReports(1, true); err == nil {
		t.Fatal("output failure hidden")
	}
	w, _ := st.View()
	if !w.Players[1].BattleReports[0].Unread {
		t.Fatal("failed output acknowledged")
	}
}
