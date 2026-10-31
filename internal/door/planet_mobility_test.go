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

func mobilitySession(t *testing.T, term Terminal) (Session, int, string) {
	t.Helper()
	s, id := planetSession(t)
	if err := s.Store.Update(func(w *game.World) error {
		w.Planets[2].Ground = 10
		w.Planets[2].Production = [3]float64{}
		return w.Land(id, s.Now())
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	token := w.Players[id].PlanetToken
	s.Store = s.Store.ForShip(id, 0, 1)
	s.Terminal = term
	return s, id, token
}
func TestPlanetThrusterDoorFreshConfirmationAndReceipt(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, answer := range []string{"y", "Y", "n", "", "y;q"} {
			term := &scripted{lines: []string{answer}}
			s, id, token := mobilitySession(t, term)
			s.Classic = classic
			pending := []string{"y", "q"}
			calls := 0
			err := s.thrustersWithRandom(token, []string{"3"}, &pending, func() float64 { calls++; return 0 })
			w, e := s.Store.View()
			if err != nil || e != nil || len(pending) != 0 {
				t.Fatal(err, e, pending)
			}
			yes := strings.EqualFold(answer, "y")
			text := term.output.String()
			if !yes {
				if calls != 0 || w.Players[id].Sector != 2 || strings.Contains(text, "thrusters saved:") {
					t.Fatal(text)
				}
				continue
			}
			if w.Players[id].Sector != 3 || w.Planets[2].Sector != 3 || w.Players[id].Turns != 490 || w.Players[id].PlanetToken != "" || !strings.Contains(text, "completed 1 hops, sector 2 -> 3") || !strings.Contains(text, "Transport 10 turns; aftermath 0; total 10; remaining 490") {
				t.Fatal(text, w.Players[id])
			}
		}
	}
}
func TestPlanetGroundDoorStrictQuantityAndExactReceipts(t *testing.T) {
	for _, quantity := range []string{"10", "0", "", "1.9", "-1", "999999999999999999999999"} {
		term := &scripted{lines: []string{"y", quantity, "y"}}
		s, id, _ := mobilitySession(t, term)
		if err := s.Store.Update(func(w *game.World) error {
			enemy, _ := w.Join("enemy", "Enemy")
			w.Planets[2].Owner = enemy.ID
			w.Players[id].PlanetToken = ""
			w.Players[id].LandedPlanet = 0
			return nil
		}); err != nil {
			t.Fatal(err)
		}
		pending := []string{}
		calls := 0
		token, err := s.forceLandingWithRandom(id, &pending, func() float64 {
			calls++
			if calls%2 == 1 {
				return 0
			}
			return .99
		})
		w, e := s.Store.View()
		if e != nil {
			t.Fatal(e)
		}
		text := term.output.String()
		if quantity != "10" {
			if calls != 0 || w.Players[id].Ground != 15 || strings.Contains(text, "Ground action saved") {
				t.Fatal(text, err)
			}
			continue
		}
		if err != nil || token == "" || w.Planets[2].Owner != id || w.Planets[2].Ground != 10 || w.Players[id].Ground != 5 || !strings.Contains(text, "Committed 10; attackers lost 0; retreated without refund 0; defenders lost 10; garrison 10; carried ground remaining 5") {
			t.Fatal(text, token, err)
		}
	}
}
func TestPlanetDoorDisconnectAndStaleConfirmation(t *testing.T) {
	for _, mode := range []string{"disconnect", "replace", "deadline"} {
		term := &portInput{scripted: scripted{lines: []string{"y"}}}
		s, id, token := mobilitySession(t, term)
		if mode == "disconnect" {
			term.lines = nil
		} else {
			term.beforeRead = func() {
				if mode == "deadline" {
					s.Deadline = s.Now()
					return
				}
				err := s.Store.Update(func(w *game.World) error { w.Planets[2].Ground++; return nil })
				if err != nil {
					t.Fatal(err)
				}
			}
		}
		pending := []string{"y"}
		calls := 0
		// Store's wall deadline is captured by value; expiry itself is exercised at
		// store level. This mode instead drives the session clock past quote lifetime.
		if mode == "deadline" {
			clock := s.Now()
			s.Now = func() time.Time { return clock }
			term.beforeRead = func() { clock = clock.Add(game.PlanetActionLifetime) }
		}
		err := s.thrustersWithRandom(token, []string{"3"}, &pending, func() float64 { calls++; return 0 })
		w, e := s.Store.View()
		if err == nil || e != nil || calls != 0 || w.Players[id].Turns != 500 {
			t.Fatal(mode, err, e, calls)
		}
	}
}
func TestPlanetReceiptRetainsCommittedWarningOnOutputFailure(t *testing.T) {
	for _, kind := range []string{"thrusters", "assault"} {
		for _, output := range []error{nil, io.EOF, io.ErrClosedPipe, errors.New("write failed")} {
			term := &mobilityOutputFailure{failure: output}
			s := Session{Terminal: term}
			warning := &store.DurabilityError{Err: errors.New("directory sync failed")}
			err := s.planetActionReceipt(game.PlanetReceipt{Kind: kind, Name: "Mobile", Hops: 1, TurnsSpent: 10}, warning)
			var committed *store.DurabilityError
			if !errors.As(err, &committed) || output != nil && !errors.Is(err, output) {
				t.Fatal(err)
			}
		}
	}
}

type mobilityOutputFailure struct {
	scripted
	failure error
}

func (t *mobilityOutputFailure) Printf(f string, a ...any) error {
	if strings.Contains(f, " saved") {
		return t.failure
	}
	return t.scripted.Printf(f, a...)
}

func TestCompactThrusterCancellationKeepsLeaveHandle(t *testing.T) {
	s, id := planetSession(t)
	s.Identity = "planet-test"
	s.Alias = "Trader"
	term := &scripted{lines: []string{"land;thrust 3;y", "n", "leave;q"}}
	s.Terminal = term
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, err := s.Store.View()
	if err != nil || w.Players[id].PlanetToken != "" || w.Players[id].LandedPlanet != 0 || w.Players[id].Turns != 500 || w.Players[id].Sector != 2 {
		t.Fatal(err, w.Players[id])
	}
	if strings.Contains(term.output.String(), "Planet thrusters saved:") {
		t.Fatal(term.output.String())
	}
}

type mobilityReceiptHook struct {
	scripted
	afterReceipt func()
}

func (t *mobilityReceiptHook) Printf(f string, a ...any) error {
	err := t.scripted.Printf(f, a...)
	if strings.Contains(f, "Ground action saved") && t.afterReceipt != nil {
		hook := t.afterReceipt
		t.afterReceipt = nil
		hook()
	}
	return err
}
func TestCompactCaptureRevalidatesGrantAfterReceipt(t *testing.T) {
	s, id := planetSession(t)
	admin := s.Store
	if err := admin.Update(func(w *game.World) error {
		enemy, _ := w.Join("enemy", "Enemy")
		w.Planets[2].Owner = enemy.ID
		w.Planets[2].Ground = 1
		w.Players[id].Ground = 1000000
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	term := &mobilityReceiptHook{scripted: scripted{lines: []string{"land", "y", "1000000", "y", "q"}}}
	term.afterReceipt = func() {
		if err := admin.Update(func(w *game.World) error {
			// Another caller's completed move/capture can revoke the grant between the
			// receipt and the status display. No stale ID dereference is authorized.
			w.Players[id].PlanetToken = ""
			w.Players[id].LandedPlanet = 0
			return nil
		}); err != nil {
			t.Fatal(err)
		}
	}
	s.Terminal = term
	s.Identity = "planet-test"
	s.Alias = "Trader"
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(term.output.String(), "land again; this landing session is no longer current") {
		t.Fatal(term.output.String())
	}
}
