package door

import (
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"strings"
	"testing"
	"time"
)

func missileSession(t *testing.T, terminal Terminal) (Session, store.Store) {
	t.Helper()
	s, st := navigationSession(t, terminal)
	if err := st.Update(func(w *game.World) error {
		a, err := w.Join(s.Identity, s.Alias)
		if err != nil {
			return err
		}
		a.Missiles = 10
		d, err := w.Join("defender", "Defender")
		if err != nil {
			return err
		}
		d.Sector = 2
		d.Cloak = 0
		d.Fighters, d.Shields = 0, 0
		d.Missiles = 100
		w.Sectors[1].Warps = []int{2}
		w.Sectors[2].Warps = []int{1, 3}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, st
}

func TestMissileLaunchRequiresSeparateConfirmation(t *testing.T) {
	for _, answer := range []string{"", "n", "y;q"} {
		t.Run("decline-"+answer, func(t *testing.T) {
			term := &scripted{lines: []string{"missile 2 1;y", answer, "q"}}
			s, st := missileSession(t, term)
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			if w.Players[1].Turns != 500 || w.Players[1].Missiles != 10 || w.Players[2].Death != nil {
				t.Fatal("cancelled launch changed state")
			}
			if !strings.Contains(term.output.String(), "Missile launch cancelled.") {
				t.Fatal(term.output.String())
			}
		})
	}
}

func TestMissileLaunchSavedReceiptAndDeadTargetCannotRetaliate(t *testing.T) {
	term := &scripted{lines: []string{"missile 2 1", "y", "q"}}
	s, st := missileSession(t, term)
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Turns != 499 || w.Players[2].Death.Cause != "missile" || w.Players[2].Death.Killer != 1 {
		t.Fatal(w.Players[1], w.Players[2])
	}
	output := term.output.String()
	if !strings.Contains(output, "Missile launch saved") || !strings.Contains(output, "Defender destroyed. You recovered") || strings.Contains(output, "Enemy retaliation saved") {
		t.Fatal(output)
	}
}

func TestMissileWarningRechecksTargetAfterWaiting(t *testing.T) {
	term := &confirmationTerminal{scripted: &scripted{lines: []string{"missile 2 1", "y", "q"}}}
	s, st := missileSession(t, term)
	term.beforeConfirm = func() error { return st.Update(func(w *game.World) error { w.Players[2].Sector = 3; return nil }) }
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Missiles != 10 || w.Players[1].Turns != 500 || w.Players[2].Death != nil {
		t.Fatal("stale missile launch")
	}
}

func TestHiddenMissileTargetDoesNotLeakIdentity(t *testing.T) {
	term := &scripted{lines: []string{"missile 2 1", "q"}}
	s, st := missileSession(t, term)
	if err := st.Update(func(w *game.World) error { w.Players[2].Cloak = 1; return nil }); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	if strings.Contains(term.output.String(), "Defender") {
		t.Fatal("hidden target leaked", term.output.String())
	}
}

func TestClassicMissileBindingKeepsFreshConfirmation(t *testing.T) {
	term := &scripted{lines: []string{"", "", "", "!;2;1;y", "n", "q;y"}}
	s, st := missileSession(t, term)
	s.Classic = true
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Missiles != 10 || !strings.Contains(term.output.String(), "Missile launch cancelled.") {
		t.Fatal(term.output.String())
	}
}

func TestExpiredMissileConfirmationDoesNotSpendAmmunition(t *testing.T) {
	term := &confirmationTerminal{scripted: &scripted{lines: []string{"missile 2 1", "y"}}}
	s, st := missileSession(t, term)
	s.Deadline = time.Now().Add(100 * time.Millisecond)
	term.beforeConfirm = func() error { time.Sleep(time.Until(s.Deadline) + 20*time.Millisecond); return nil }
	_ = s.Run()
	w, _ := st.View()
	if w.Players[1].Missiles != 10 || w.Players[1].Turns != 500 || w.Players[2].Death != nil {
		t.Fatal("expired confirmation spent stock")
	}
}

func TestPlanetBombardmentWarningCancellationAndReceipt(t *testing.T) {
	for _, answer := range []string{"n", "y"} {
		t.Run(answer, func(t *testing.T) {
			term := &scripted{lines: []string{"missile 2 2;y", answer, "q"}}
			s, st := missileSession(t, term)
			if err := st.Update(func(w *game.World) error {
				w.Players[2].Sector = 3
				w.Planets[2] = &game.Planet{ID: 2, Sector: 2, Owner: 2, Name: "Target", Updated: s.Now(), Ground: 5000, Production: [3]float64{1, 1, 1}}
				w.Sectors[2].Planet = 2
				return nil
			}); err != nil {
				t.Fatal(err)
			}
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			if !strings.Contains(term.output.String(), "Target; 5000 ground forces; ground-only bombardment") {
				t.Fatal(term.output.String())
			}
			if answer == "n" {
				if w.Planets[2].Ground != 5000 || w.Players[1].Missiles != 10 || w.Players[1].Turns != 500 {
					t.Fatal("declined bombardment saved")
				}
			} else if w.Players[1].Missiles != 8 || w.Players[1].Turns != 499 || !strings.Contains(term.output.String(), "Planet bombardment saved: 2 missiles reached planet 2") {
				t.Fatal(term.output.String())
			}
		})
	}
}
