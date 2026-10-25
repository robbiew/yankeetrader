package door

import (
	"errors"
	gd "github.com/robbiew/godoors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"io"
	"strings"
	"testing"
	"time"
)

func navigationSession(t *testing.T, term Terminal) (Session, store.Store) {
	t.Helper()
	now := time.Now()
	w, _ := game.New(now, 36, 8)
	w.Sectors[1].Warps = []int{2}
	w.Sectors[2].Warps = []int{3}
	w.Sectors[3].Warps = []int{4}
	st := store.Store{Dir: t.TempDir()}
	if err := st.Create(w); err != nil {
		t.Fatal(err)
	}
	return Session{Store: st, Terminal: term, Identity: "nav", Alias: "Navigator", Deadline: now.Add(time.Minute), Now: func() time.Time { return now }}, st
}

func TestNavigationCommandsAndConfirmation(t *testing.T) {
	for _, tc := range []struct {
		name   string
		lines  []string
		sector int
		turns  int64
		output string
	}{
		{"accept", []string{"s;path 1 4;auto 4;y;q"}, 4, 497, "Moved to sector 4."},
		{"cancel", []string{"s;path 1 4;auto 4;n;q"}, 1, 500, "Autopilot cancelled."},
		{"default", []string{"auto 4;;q"}, 1, 500, "Autopilot cancelled."},
		{"disconnect-before-confirm", []string{"auto 4"}, 1, 500, "Engage autopilot?"},
		{"separate-confirm", []string{"auto 4", "Y", "q"}, 4, 497, "Moved to sector 4."},
		{"malformed", []string{"s 3;path 1;path bad 4;auto bad;q"}, 1, 500, "use PATH"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			term := &scripted{lines: tc.lines}
			s, st := navigationSession(t, term)
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, err := st.View()
			if err != nil {
				t.Fatal(err)
			}
			p := w.Players[1]
			if p.Sector != tc.sector || p.Turns != tc.turns || !strings.Contains(term.output.String(), tc.output) {
				t.Fatalf("state %+v, output %s", p, term.output.String())
			}
		})
	}
}

type courseTerminal struct {
	*scripted
	afterHop              func() error
	interruptAfter, polls int
}

func (t *courseTerminal) Printf(f string, args ...any) error {
	if strings.HasPrefix(f, "Moved to sector") && t.afterHop != nil {
		return t.afterHop()
	}
	return t.scripted.Printf(f, args...)
}
func (t *courseTerminal) Interrupted() (bool, error) {
	t.polls++
	return t.interruptAfter > 0 && t.polls > t.interruptAfter, nil
}

func TestAutopilotStopsOnDisconnectInterruptAndConcurrentMovement(t *testing.T) {
	for _, mode := range []string{"disconnect", "interrupt", "concurrent-move", "turns-spent", "avoid-suffix"} {
		t.Run(mode, func(t *testing.T) {
			term := &courseTerminal{scripted: &scripted{lines: []string{"auto 4;y;q"}}}
			s, st := navigationSession(t, term)
			switch mode {
			case "disconnect":
				term.afterHop = func() error { return io.ErrClosedPipe }
			case "interrupt":
				term.interruptAfter = 1
			default:
				term.afterHop = func() error {
					return st.Update(func(w *game.World) error {
						if mode == "concurrent-move" {
							w.Players[1].Sector = 8
						} else if mode == "avoid-suffix" {
							return w.SetAvoid(1, 1, 4)
						} else {
							w.Players[1].Turns = 0
						}
						return nil
					})
				}
			}
			err := s.Run()
			if mode == "disconnect" && !errors.Is(err, io.ErrClosedPipe) {
				t.Fatal(err)
			}
			if mode != "disconnect" && err != nil {
				t.Fatal(err)
			}
			w, err := st.View()
			if err != nil {
				t.Fatal(err)
			}
			wantSector, wantTurns := 2, int64(499)
			if mode == "concurrent-move" {
				wantSector = 8
			}
			if mode == "turns-spent" {
				wantTurns = 0
			}
			if p := w.Players[1]; p.Sector != wantSector || p.Turns != wantTurns {
				t.Fatalf("autopilot continued or refunded completed hop: %+v", p)
			}
		})
	}
}

type confirmationTerminal struct {
	*scripted
	beforeConfirm func() error
	reads         int
}

func (t *confirmationTerminal) ReadLine(deadline time.Time) (string, error) {
	t.reads++
	if t.reads == 2 {
		if err := t.beforeConfirm(); err != nil {
			return "", err
		}
	}
	return t.scripted.ReadLine(deadline)
}
func TestAutopilotConfirmationRechecksTurnBudget(t *testing.T) {
	term := &confirmationTerminal{scripted: &scripted{lines: []string{"auto 4", "y", "q"}}}
	s, st := navigationSession(t, term)
	term.beforeConfirm = func() error { return st.Update(func(w *game.World) error { w.Players[1].Turns = 2; return nil }) }
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Sector != 1 || w.Players[1].Turns != 2 || !strings.Contains(term.output.String(), "not enough turns") {
		t.Fatal("course starts with insufficient turns after confirmation")
	}
}

func TestAutopilotPollPreservesOtherKeys(t *testing.T) {
	keys := []rune{'i', 13, 24}
	g := &GoDoors{readKey: func(time.Duration) (rune, gd.Key, error) {
		if len(keys) == 0 {
			return 0, gd.KeyNone, gd.ErrInputTimeout
		}
		r := keys[0]
		keys = keys[1:]
		k := gd.KeyNone
		if r == 13 {
			k = gd.KeyEnter
		}
		return r, k, nil
	}}
	stop, err := g.Interrupted()
	if err != nil || !stop || len(g.pending) != 2 || g.pending[0].r != 'i' || g.pending[1].k != gd.KeyEnter {
		t.Fatalf("poll discarded typed input: %+v %v %v", g.pending, stop, err)
	}
	stop, err = g.Interrupted()
	if stop || err != nil {
		t.Fatal("timeout treated as interrupt")
	}
}

func TestSensorEarthSellsEquipment(t *testing.T) {
	term := &scripted{}
	if err := showSensors(term, []game.SensorReport{{Sector: 1, PortID: 1, PortName: "Earth"}}); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(term.output.String(), "Earth | Selling: ship equipment") {
		t.Fatal(term.output.String())
	}
}

func TestAvoidCommandsPersistAcrossReconnect(t *testing.T) {
	term := &scripted{lines: []string{"avoid 1 2;avoid;path 1 4;auto 4;n;q"}}
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		w.Sectors[1].Warps = []int{2, 5}
		w.Sectors[5].Warps = []int{6}
		w.Sectors[6].Warps = []int{4}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	for _, text := range []string{"Slot 1: sector 2", "Shortest path: [1 5 6 4]", "Autopilot cancelled"} {
		if !strings.Contains(term.output.String(), text) {
			t.Fatal("missing output", text, term.output.String())
		}
	}
	w, _ := st.View()
	if w.Players[1].Turns != 500 || w.Players[1].AvoidSectors[0] != 2 {
		t.Fatal("avoid not saved or edit charged turns")
	}
	term = &scripted{lines: []string{"avoid;auto 4;y;avoid 1 0;avoid;q"}}
	s.Terminal = term
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ = st.View()
	p := w.Players[1]
	if p.Sector != 4 || p.Turns != 497 || p.AvoidSectors[0] != 0 || len(w.Players) != 1 {
		t.Fatalf("avoid reconnect state: %+v", p)
	}
	if !strings.Contains(term.output.String(), "Slot 1: sector 2") || !strings.Contains(term.output.String(), "None.") {
		t.Fatal("list/clear not shown")
	}
}

func TestAvoidChangedDuringAutopilotConfirmation(t *testing.T) {
	term := &confirmationTerminal{scripted: &scripted{lines: []string{"auto 4", "y", "q"}}}
	s, st := navigationSession(t, term)
	term.beforeConfirm = func() error { return st.Update(func(w *game.World) error { return w.SetAvoid(1, 1, 4) }) }
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Sector != 1 || w.Players[1].Turns != 500 || !strings.Contains(term.output.String(), "avoid list") {
		t.Fatal("stale confirmed course accepted", term.output.String())
	}
}
