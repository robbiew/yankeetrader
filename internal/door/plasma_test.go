package door

import (
	"errors"
	"io"
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func plasmaSession(t *testing.T, term Terminal) (Session, store.Store) {
	t.Helper()
	s, st := navigationSession(t, term)
	if e := st.Update(func(w *game.World) error {
		a, e := w.Join(s.Identity, s.Alias)
		if e != nil {
			return e
		}
		a.Plasma = 10
		a.Fighters = 0
		a.Shields = 1_000_000
		a.Cloak = 0
		d, e := w.Join("private-target", "SECRET ALIAS")
		if e != nil {
			return e
		}
		d.Sector = 2
		d.Cloak = 1
		d.Fighters = 0
		d.Shields = 1_000_000
		d.Mines = 0
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	s.Store = st.ForShip(1, 0, 1)
	return s, st
}
func TestPlasmaBothInterfacesRequireExactFreshConfirmation(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, answer := range []string{"y", "Y", "n", "", "y;q"} {
			t.Run(map[bool]string{true: "classic", false: "compact"}[classic]+"/"+answer, func(t *testing.T) {
				term := &scripted{lines: []string{answer}}
				s, st := plasmaSession(t, term)
				s.Classic = classic
				pending := []string{"y", "q"}
				calls := 0
				e := s.launchPlasmaWithRandom([]string{"2", "1"}, &pending, func() float64 { calls++; return .5 })
				if e != nil || len(pending) != 0 {
					t.Fatal(e, pending)
				}
				w, e := st.View()
				if e != nil {
					t.Fatal(e)
				}
				accepted := strings.EqualFold(answer, "y")
				if accepted {
					if w.Players[1].Plasma != 9 || w.Players[1].Turns != 499 || w.Players[2].Shields >= 1_000_000 || !strings.Contains(term.output.String(), "Plasma launch saved: 1 bolts, 1 turn.") {
						t.Fatal(term.output.String())
					}
				} else {
					if w.Players[1].Plasma != 10 || w.Players[1].Turns != 500 || calls != 0 || strings.Contains(term.output.String(), "Plasma launch saved:") {
						t.Fatal("cancel spent or false receipt")
					}
				}
				if strings.Contains(term.output.String(), "SECRET ALIAS") || strings.Contains(term.output.String(), "private-target") {
					t.Fatal("concealed identity leaked")
				}
			})
		}
	}
}
func TestPlasmaCompactAndClassicDispatchAndPrompts(t *testing.T) {
	for _, classic := range []bool{false, true} {
		lines := []string{"plasma 2 1;y", "y", "q"}
		if classic {
			lines = []string{"", "", "", "+;2;1;y", "y", "q;y"}
		}
		term := &scripted{lines: lines}
		s, st := plasmaSession(t, term)
		s.Classic = classic
		if e := s.Run(); e != nil {
			t.Fatal(e)
		}
		w, e := st.View()
		if e != nil || w.Players[1].Plasma != 9 || w.Players[1].Turns != 499 {
			t.Fatal(e)
		}
		if strings.Count(term.output.String(), "Plasma launch saved:") != 1 || strings.Contains(term.output.String(), "SECRET ALIAS") {
			t.Fatal(term.output.String())
		}
	}
}
func TestPlasmaRejectsInputsExpiryAndEOFWithoutSpending(t *testing.T) {
	for _, mode := range []string{"blank", "count-blank", "fraction", "over-limit", "negative", "bad-sector", "args", "eof", "expired", "nil-rng", "bad-rng"} {
		t.Run(mode, func(t *testing.T) {
			term := &scripted{lines: []string{"y"}}
			s, st := plasmaSession(t, term)
			args := []string{"2", "1"}
			rng := func() float64 { return .5 }
			switch mode {
			case "blank":
				args = nil
				term.lines = []string{""}
			case "count-blank":
				args = nil
				term.lines = []string{"2", ""}
			case "fraction":
				args[1] = "1.5"
			case "over-limit":
				args[1] = "65"
			case "negative":
				args[1] = "-1"
			case "bad-sector":
				args[0] = "9"
			case "args":
				args = []string{"2"}
			case "eof":
				term.lines = nil
			case "expired":
				s.Deadline = time.Now().Add(-time.Second)
			case "nil-rng":
				rng = nil
			case "bad-rng":
				rng = func() float64 { return -1 }
			}
			e := s.launchPlasmaWithRandom(args, &[]string{}, rng)
			if mode != "blank" && e == nil {
				t.Fatal("expected rejection", mode)
			}
			w, err := st.View()
			if err != nil || w.Players[1].Plasma != 10 || w.Players[1].Turns != 500 || strings.Contains(term.output.String(), "Plasma launch saved:") {
				t.Fatal(e, err, term.output.String())
			}
		})
	}
}
func TestPlasmaConfirmationRechecksHiddenState(t *testing.T) {
	term := &confirmationTerminal{scripted: &scripted{lines: []string{"plasma 2 1", "y", "q"}}}
	s, st := plasmaSession(t, term)
	term.beforeConfirm = func() error { return st.Update(func(w *game.World) error { w.Players[2].Shields--; return nil }) }
	if e := s.Run(); e != nil {
		t.Fatal(e)
	}
	w, e := st.View()
	if e != nil || w.Players[1].Plasma != 10 || w.Players[1].Turns != 500 || strings.Contains(term.output.String(), "Plasma launch saved:") {
		t.Fatal(e, term.output.String())
	}
	if strings.Contains(term.output.String(), "SECRET ALIAS") {
		t.Fatal("stale hidden state disclosed")
	}
}
func TestPlasmaSelfDeathEndsSessionAfterSavedReceipt(t *testing.T) {
	term := &scripted{lines: []string{"plasma 1 1", "y", "plasma 2 1", "y", "q"}}
	s, st := plasmaSession(t, term)
	if e := st.Update(func(w *game.World) error { w.Players[1].Shields = 1; w.Players[1].Mines = 3; return nil }); e != nil {
		t.Fatal(e)
	}
	e := s.Run()
	if !errors.Is(e, game.ErrShipDestroyed) {
		t.Fatal(e)
	}
	w, e := st.View()
	if e != nil || w.Players[1].Death.Cause != "plasma" || w.Players[1].Turns != 499 || w.Players[1].Mines != 0 || len(w.Sectors[1].Minefield) != 0 {
		t.Fatal(e)
	}
	out := term.output.String()
	if strings.Count(out, "Plasma launch saved:") != 1 || !strings.Contains(out, "Wreck mines dropped/disarmed: 0/3") || !strings.Contains(out, "this login has ended") || !strings.Contains(out, "next UTC midnight") {
		t.Fatal(out)
	}
}

type plasmaOutputFailure struct {
	scripted
	failure error
}

func (t *plasmaOutputFailure) Printf(format string, args ...any) error {
	if e := t.scripted.Printf(format, args...); e != nil {
		return e
	}
	if strings.Contains(format, "Plasma launch saved:") {
		return t.failure
	}
	return nil
}
func TestPlasmaReceiptPreservesCommittedWarningWithOutputErrors(t *testing.T) {
	for _, failure := range []error{io.EOF, io.ErrClosedPipe, errors.New("write failed")} {
		terminal := &plasmaOutputFailure{failure: failure}
		s, _ := plasmaSession(t, terminal)
		warning := &store.DurabilityError{Err: errors.New("directory sync failed")}
		e := s.plasmaReceipt(game.PlasmaResult{Launched: 1, TurnsSpent: 1}, warning)
		var committed *store.DurabilityError
		if !errors.Is(e, failure) || !errors.As(e, &committed) || !errors.As(sessionInputEnd(e), &committed) {
			t.Fatal("committed warning lost", e)
		}
	}
	term := &plasmaOutputFailure{scripted: scripted{lines: []string{"plasma 2 1", "y", "plasma 2 1", "y", "q"}}, failure: &store.DurabilityError{Err: errors.New("committed warning")}}
	s, st := plasmaSession(t, term)
	var warning *store.DurabilityError
	if e := s.Run(); !errors.As(e, &warning) {
		t.Fatal(e)
	}
	w, e := st.View()
	if e != nil || w.Players[1].Plasma != 9 || strings.Count(term.output.String(), "Plasma launch saved:") != 1 {
		t.Fatal(e, term.output.String())
	}
}
