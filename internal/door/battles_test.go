package door

import (
	"errors"
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func battleSession(t *testing.T, term Terminal) (Session, store.Store) {
	t.Helper()
	s, st := radioSession(t, term)
	if err := st.Update(func(w *game.World) error {
		w.Players[1].BattleReports = []game.BattleReport{{ID: 1, At: s.Now().UTC(), Sector: 8, XannorLost: 17, FightersLost: 23, ShieldsLost: 31, Unread: true}}
		w.NextBattleReport = 2
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, st
}

func TestPrivateBattleReportsCompactClassicHistoryAndPrivacy(t *testing.T) {
	for _, classic := range []bool{false, true} {
		term := &scripted{lines: []string{"battles;q"}}
		s, st := battleSession(t, term)
		s.Classic = classic
		if classic {
			term.lines = []string{"", "", "", "battles;q;y"}
		}
		if err := s.Run(); err != nil {
			t.Fatal(err, term.output.String())
		}
		if strings.Count(term.output.String(), "Xannor lost 17 fighters. You lost 23 fighters and 31 shields.") != 2 {
			t.Fatal("login/history missed private report", term.output.String())
		}
		w, _ := st.View()
		if w.Players[1].BattleReports[0].Unread {
			t.Fatal("displayed report unread")
		}
		s.Store = st
		s.Identity, s.Alias = "visitor", "Visitor"
		s.Classic = false
		other := &scripted{lines: []string{"battles;news;q"}}
		s.Terminal = other
		if err := s.Run(); err != nil {
			t.Fatal(err)
		}
		if strings.Contains(other.output.String(), "Xannor lost 17") || !strings.Contains(other.output.String(), "No retained battle reports") {
			t.Fatal("private counts exposed to visitor")
		}
	}
}

type battleOutputFailure struct{ *scripted }

func (t *battleOutputFailure) Printf(format string, args ...any) error {
	if strings.Contains(fmt.Sprintf(format, args...), "Private Xannor battle report") {
		return errors.New("output disconnected")
	}
	return t.scripted.Printf(format, args...)
}
func TestBattleReportOutputFailureAndStaleGenerationRemainUnread(t *testing.T) {
	term := &battleOutputFailure{&scripted{}}
	s, st := battleSession(t, term)
	w, _ := st.View()
	s.Store = st.ForShip(1, w.Players[1].ShipGeneration)
	if err := s.battleReports(1, true); err == nil {
		t.Fatal("output failure hidden")
	}
	w, _ = st.View()
	if !w.Players[1].BattleReports[0].Unread {
		t.Fatal("failed output consumed report")
	}
	// A report snapshot cannot be printed or acknowledged by a stale session.
	snapshot := w.Players[1].BattleReports[0]
	if err := st.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Sector = 8
		return w.RecordDeath(game.DeathContext{Victim: 1, Generation: p.ShipGeneration, Sector: 8, Cause: "xannor", Killer: game.XannorOwner}, s.Now())
	}); err != nil {
		t.Fatal(err)
	}
	s.Terminal = &scripted{}
	if err := s.displayBattle(snapshot); err == nil {
		t.Fatal("dead session printed private report")
	}
	w, _ = st.View()
	if !w.Players[1].BattleReports[0].Unread {
		t.Fatal("stale session consumed report")
	}
}

func TestBattleReportsStopBeforeUndisplayedPageAndAfterDeadline(t *testing.T) {
	term := &scripted{lines: []string{"q"}}
	s, st := battleSession(t, term)
	if err := st.Update(func(w *game.World) error {
		for i := 2; i <= 7; i++ {
			w.Players[1].BattleReports = append(w.Players[1].BattleReports, game.BattleReport{ID: uint64(i), At: s.Now().UTC(), Sector: 8, Unread: true})
		}
		w.NextBattleReport = 8
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	s.Store = st.ForShip(1, 0)
	if err := s.battleReports(1, false); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].BattleReports[4].Unread || !w.Players[1].BattleReports[5].Unread {
		t.Fatal("unseen report acknowledged")
	}
	s.Deadline = time.Now().Add(-time.Second)
	if err := s.battleReports(1, true); err == nil {
		t.Fatal("expired session printed report")
	}
	w, _ = st.View()
	if !w.Players[1].BattleReports[5].Unread {
		t.Fatal("expired session consumed report")
	}
}
