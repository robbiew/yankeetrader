package door

import (
	"fmt"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"io"
	"strings"
	"testing"
	"time"
)

type scripted struct {
	lines  []string
	output strings.Builder
}

func (s *scripted) ReadLine(time.Time) (string, error) {
	if len(s.lines) == 0 {
		return "", io.EOF
	}
	v := s.lines[0]
	s.lines = s.lines[1:]
	return v, nil
}
func (s *scripted) Printf(f string, a ...any) error {
	_, e := fmt.Fprintf(&s.output, f, a...)
	return e
}
func TestPlayableLoopAndReconnect(t *testing.T) {
	now := time.Date(2026, 10, 24, 0, 0, 0, 0, time.UTC)
	st := store.Store{Dir: t.TempDir()}
	w, e := game.New(now, 36, 8)
	if e != nil {
		t.Fatal(e)
	}
	if e = st.Create(w); e != nil {
		t.Fatal(e)
	}
	term := &scripted{lines: []string{"?; i; l; p; equip fighters 1; m 2; p; buy ore 5; m 3; p; sell ore 5; q"}}
	session := Session{disruptionRandom: func() float64 { return .999999 }, Store: st, Terminal: term, Identity: "user:7", Alias: "Trader", Deadline: time.Now().Add(time.Minute), Now: func() time.Time { return now }}
	if e = session.Run(); e != nil {
		t.Fatal(e)
	}
	w, e = st.View()
	if e != nil {
		t.Fatal(e)
	}
	p := w.Players[1]
	if p.Credits != 1005 || p.Fighters != 26 || p.Cargo[0] != 0 || p.Sector != 3 || p.Turns != 495 {
		t.Fatalf("wrong end state: %+v", p)
	}
	term = &scripted{lines: []string{"i;q"}}
	session.Terminal = term
	session.Alias = "New handle"
	if e = session.Run(); e != nil {
		t.Fatal(e)
	}
	w, _ = st.View()
	if len(w.Players) != 1 || w.Players[1].Turns != 495 || w.Players[1].Alias != "New handle" {
		t.Fatal("reconnect duplicates player or restores turns")
	}
	if !strings.Contains(term.output.String(), "Fighters 26") {
		t.Fatal("persisted equipment missing from UI")
	}
}
func TestDisconnectSavesCommittedActionsAndDoesNotSpendOnRejectedTrade(t *testing.T) {
	now := time.Now()
	st := store.Store{Dir: t.TempDir()}
	w, _ := game.New(now, 36, 8)
	_ = st.Create(w)
	term := &scripted{lines: []string{"m 2;p;buy ore -1;buy ore 11;buy ore 3"}}
	s := Session{disruptionRandom: func() float64 { return .999999 }, Store: st, Terminal: term, Identity: "user:1", Alias: "Trader", Deadline: now.Add(time.Minute), Now: func() time.Time { return now }}
	if e := s.Run(); e != nil {
		t.Fatal(e)
	}
	w, e := st.View()
	if e != nil {
		t.Fatal(e)
	}
	p := w.Players[1]
	if p.Credits != 975 || p.Cargo[0] != 3 || p.Turns != 498 {
		t.Fatalf("disconnect accounting: %+v", p)
	}
	if !strings.Contains(term.output.String(), "positive whole quantity") || !strings.Contains(term.output.String(), "not enough") {
		t.Fatal("rejection not shown")
	}
}

func TestPlanetCommandsSaveAndReconnect(t *testing.T) {
	now := time.Now()
	st := store.Store{Dir: t.TempDir()}
	w, _ := game.New(now, 36, 8)
	p, _ := w.Join("planet:1", "Builder")
	p.Credits = 100000
	p.Holds = 100
	p.Cargo = [3]int64{10, 20, 30}
	if e := st.Create(w); e != nil {
		t.Fatal(e)
	}
	term := &scripted{lines: []string{"create New Eden;land;bank 15000;invest 251;transfer cargo;a;planet;leave;m 2;bank 0;q"}}
	session := Session{disruptionRandom: func() float64 { return .999999 }, Store: st, Terminal: term, Identity: "planet:1", Alias: "Builder", Deadline: now.Add(time.Minute), Now: func() time.Time { return now }}
	if e := session.Run(); e != nil {
		t.Fatal(e)
	}
	w, e := st.View()
	if e != nil {
		t.Fatal(e)
	}
	p = w.Players[1]
	planet := w.Planets[2]
	if p.Credits != 59749 || planet.Bank != 15000 || p.Cargo != [3]int64{20, 30, 40} || p.Sector != 2 {
		t.Fatalf("planet UI state: player %+v planet %+v", p, planet)
	}
	if !strings.Contains(term.output.String(), "landing session is no longer current") {
		t.Fatal("bank accepted while away")
	}
	session.Terminal = &scripted{lines: []string{"m 1;land;bank 0;q"}}
	if e = session.Run(); e != nil {
		t.Fatal(e)
	}
	w, _ = st.View()
	if w.Players[1].Credits != 74749 || w.Planets[2].Bank != 0 {
		t.Fatal("planet bank did not survive reconnect")
	}
}
