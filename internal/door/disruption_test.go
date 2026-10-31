package door

import (
	"errors"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"io"
	"strings"
	"testing"
	"time"
)

func doorArrivalRandom(t *testing.T, values ...float64) func() float64 {
	t.Helper()
	i := 0
	return func() float64 {
		if i == len(values) {
			t.Fatal("unexpected login/arrival draw")
			return 0
		}
		v := values[i]
		i++
		return v
	}
}
func TestDisruptionStartupAndQueuedCourseStopBothInterfaces(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, mode := range []string{"startup", "move", "auto"} {
			t.Run(fmt.Sprint(classic, mode), func(t *testing.T) {
				lines := []string{}
				if classic {
					lines = []string{"", "", ""}
				}
				cmd := "m 2;i;q"
				if mode == "auto" {
					cmd = "auto 3;y;i;q"
				}
				if mode == "startup" {
					cmd = "q"
				}
				lines = append(lines, cmd, "q")
				if classic {
					lines = append(lines, "y")
				}
				term := &scripted{lines: lines}
				s, st := navigationSession(t, term)
				s.Classic = classic
				if e := st.Update(func(w *game.World) error {
					p, _ := w.Join("nav", "Navigator")
					if mode == "startup" {
						p.Sector = 2
						p.Turns = 0
						p.Cloak = .5
					}
					return nil
				}); e != nil {
					t.Fatal(e)
				}
				s.disruptionRandom = doorArrivalRandom(t, 0, 0, 0, 0, .99, 0, 0)
				if e := s.Run(); e != nil {
					t.Fatal(e)
				}
				w, e := st.View()
				if e != nil {
					t.Fatal(e)
				}
				p := w.Players[1]
				text := term.output.String()
				if strings.Count(text, "Forced warp saved:") != 1 || !strings.Contains(text, "Disruption arrival saved:") || p.Sector != 8 || p.WarpSequence != 1 {
					t.Fatal(p, text)
				}
				if mode == "startup" {
					if p.Turns != 0 || p.Cloak != .5 {
						t.Fatal(p)
					}
				} else if p.Turns != 499 || strings.Contains(text, "Moved to sector 3.") {
					t.Fatal(p, text)
				}
			})
		}
	}
}

type failedArrivalTerminal struct {
	scripted
	err error
}

func (t *failedArrivalTerminal) Printf(format string, args ...any) error {
	if strings.Contains(format, "Forced warp saved:") {
		return t.err
	}
	return t.scripted.Printf(format, args...)
}
func TestDisruptionReceiptFailureRetainsCommittedWarning(t *testing.T) {
	for _, output := range []error{io.EOF, io.ErrClosedPipe, errors.New("terminal failed")} {
		for _, warning := range []bool{false, true} {
			term := &failedArrivalTerminal{err: output}
			s, st := navigationSession(t, term)
			if e := st.Update(func(w *game.World) error { p, _ := w.Join("nav", "Navigator"); p.Sector = 2; return nil }); e != nil {
				t.Fatal(e)
			}
			w, _ := st.View()
			s.Store = st.ForShip(1, 0, w.Season)
			if e := s.Store.StartDisruption(doorArrivalRandom(t, 0, 0, 0, 0, .99, 0, 0), time.Now, s.Deadline); e != nil {
				t.Fatal(e)
			}
			var actionErr error
			if warning {
				actionErr = &store.DurabilityError{Err: errors.New("sync")}
			}
			pending := []string{"pay again"}
			handled, e := s.finishArrival(actionErr, &pending)
			var committed *store.DurabilityError
			if !handled || !errors.Is(e, output) || errors.As(e, &committed) != warning || len(pending) != 0 {
				t.Fatal(e)
			}
			if warning && sessionInputEnd(e) == nil {
				t.Fatal("EOF discarded committed warning")
			}
			saved, _ := st.View()
			if saved.Players[1].WarpSequence != 1 {
				t.Fatal("receipt retried warp")
			}
		}
	}
}

func TestStartupMinesWithoutBlackHoleStillReportFatalSave(t *testing.T) {
	term := &scripted{lines: []string{"q"}}
	s, st := navigationSession(t, term)
	if e := st.Update(func(w *game.World) error {
		p, _ := w.Join("nav", "Navigator")
		p.Sector = 2
		p.Cloak = 0
		p.Holds = 1
		p.Shields = 0
		p.Fighters = 0
		p.Mines = 0
		w.Sectors[2].Minefield = []game.MineLayer{{Owner: 0, Count: 1}}
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	i := 0
	s.disruptionRandom = func() float64 {
		i++
		if i <= 2 {
			return .999999
		}
		return .5
	}
	err := s.Run()
	text := term.output.String()
	if !errors.Is(err, game.ErrShipDestroyed) || !strings.Contains(text, "Mine encounter saved:") || !strings.Contains(text, "destroyed by unowned mines") || strings.Contains(text, "Forced warp saved:") {
		t.Fatal(err, text)
	}
	saved, e := st.View()
	if e != nil || saved.Players[1].Death == nil {
		t.Fatal(e)
	}
}
