package door

import (
	"errors"
	"fmt"
	"io"
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func TestFighterTransfersDoNotAdvanceSpies(t *testing.T) {
	s, st := spyDoor(t, &scripted{})
	var token string
	if err := st.Update(func(w *game.World) error {
		if e := w.Dock(1, s.Now()); e != nil {
			return e
		}
		token = w.Players[1].DockToken
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	s.Store = st.ForShip(1, 0, 1)
	if err := s.Store.HireSpies(token, []int{3}, s.Now, s.Deadline); err != nil {
		t.Fatal(err)
	}
	if err := st.Update(func(w *game.World) error {
		w.Players[1].Sector = 8
		w.Sectors[8].Defense = nil
		w.Sectors[8].Minefield = nil
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	for _, reinforce := range []bool{false, true} {
		pending := []string{}
		if err := s.setSectorFighters(1, []string{"1"}, &pending, reinforce); err != nil {
			t.Fatal(err)
		}
	}
	positions, reports, err := s.Store.SpySnapshot(false)
	if err != nil || len(reports) != 0 || len(positions) != 1 || positions[0] != 3 {
		t.Fatal("fighter transfer advanced spy", positions, reports, err)
	}
}

type spyReceiptFailure struct {
	scripted
	failure error
}

func (t *spyReceiptFailure) Printf(f string, args ...any) error {
	rendered := fmt.Sprintf(f, args...)
	if strings.Contains(rendered, "Planet report saved:") || strings.Contains(rendered, "Missile launch saved") {
		return t.failure
	}
	return t.scripted.Printf(f, args...)
}
func TestSpyActionReceiptsPreserveCommittedWarningOnOutputFailure(t *testing.T) {
	for _, failure := range []error{io.EOF, io.ErrClosedPipe, errors.New("terminal failed")} {
		warning := &store.DurabilityError{Err: errors.New("directory sync")}
		s := Session{Terminal: &spyReceiptFailure{failure: failure}}
		err := s.planetReportReceipt(game.PlanetReport{TurnSpent: true, Unavailable: "no planet exists in that sector"}, &game.Player{Turns: 4}, warning)
		var committed *store.DurabilityError
		if !errors.Is(err, failure) || !errors.As(err, &committed) || committed != warning {
			t.Fatal(err)
		}
		err = s.missileReceipt(1, "defenses", game.MissileResult{Primary: game.MissileImpact{Launched: 1}}, warning)
		if !errors.Is(err, failure) || !errors.As(err, &committed) || committed != warning {
			t.Fatal(err)
		}
	}
}
func TestMissingPlanetReportReceiptsInBothInterfaces(t *testing.T) {
	for _, classic := range []bool{false, true} {
		t.Run(fmt.Sprint(classic), func(t *testing.T) {
			lines := []string{"planetreport 7;planetreport 999;portreport 7;q"}
			if classic {
				lines = []string{"", "", "", "c;9;7;9;999;2;7;1;q;y"}
			}
			term := &scripted{lines: lines}
			s, st := reportSession(t, term)
			s.Classic = classic
			before, _ := st.View()
			turns := before.Players[1].Turns
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			out := term.output.String()
			if !strings.Contains(out, "One turn spent: no planet exists in that sector.") || !strings.Contains(out, fmt.Sprintf("Turns remaining: %d", turns-1)) {
				t.Fatal(out)
			}
			after, _ := st.View()
			if after.Players[1].Turns != turns-1 {
				t.Fatal("invalid/port queries charged", out)
			}
		})
	}
}
func TestReportReceiptWarningEndsLoginEvenWithEOF(t *testing.T) {
	warning := &store.DurabilityError{Err: errors.New("committed warning")}
	term := &spyReceiptFailure{scripted: scripted{lines: []string{"planetreport 7", "planetreport 7", "q"}}, failure: errors.Join(warning, io.EOF)}
	s, st := reportSession(t, term)
	err := s.Run()
	var committed *store.DurabilityError
	if !errors.As(err, &committed) {
		t.Fatal("warning swallowed", err)
	}
	w, _ := st.View()
	if w.Players[1].Turns != 499 || len(term.lines) != 2 {
		t.Fatal("login continued after committed receipt warning", w.Players[1].Turns, len(term.lines))
	}
}
func TestUnavailableReportFailedOutputKeepsIntelligenceUnread(t *testing.T) {
	term := &spyReceiptFailure{failure: io.ErrClosedPipe}
	s, st := spyDoor(t, term)
	var token string
	if err := st.Update(func(w *game.World) error {
		if e := w.Dock(1, s.Now()); e != nil {
			return e
		}
		token = w.Players[1].DockToken
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	s.Store = st.ForShip(1, 0, 1)
	if err := s.Store.HireSpies(token, []int{3}, s.Now, time.Now().Add(time.Hour)); err != nil {
		t.Fatal(err)
	}
	pending := []string{}
	if err := s.computerReport(1, "planetreport", []string{"7"}, &pending); !errors.Is(err, io.ErrClosedPipe) {
		t.Fatal(err)
	}
	_, reports, err := s.Store.SpySnapshot(true)
	if err != nil || len(reports) != 1 || !reports[0].Unread {
		t.Fatal("failed receipt acknowledged intelligence", reports, err)
	}
	w, _ := st.View()
	if w.Players[1].Turns != 498 {
		t.Fatal("failed output lost saved turn charge")
	}
}
