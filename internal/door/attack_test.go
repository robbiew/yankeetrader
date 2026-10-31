package door

import (
	gd "github.com/robbiew/godoors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"strings"
	"testing"
	"time"
)

func attackSession(t *testing.T, terminal Terminal) (Session, store.Store) {
	t.Helper()
	now := time.Now()
	w, _ := game.New(now, 36, 8)
	a, _ := w.Join("attacker", "Attacker")
	a.Fighters = 100
	a.Cloak = 0
	d, _ := w.Join("victim", "Victim")
	d.Fighters, d.Shields = 0, 0
	d.Mines = 100
	d.Cloak = 0
	d.Credits = 10000
	w.Ports[2].Owner = d.ID
	w.Ports[2].Treasury = 777
	st := store.Store{Dir: t.TempDir()}
	if err := st.Create(w); err != nil {
		t.Fatal(err)
	}
	return Session{disruptionRandom: func() float64 { return .999999 }, Store: st, Terminal: terminal, Identity: "attacker", Alias: "Attacker", Deadline: now.Add(time.Minute)}, st
}

func TestAttackRequiresSeparateExactConfirmation(t *testing.T) {
	for _, answer := range []string{"", "n", "y;q"} {
		t.Run("decline-"+answer, func(t *testing.T) {
			term := &scripted{lines: []string{"attack 2 1;y", answer, "q"}}
			s, st := attackSession(t, term)
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			if w.Players[2].Death != nil || w.Players[1].Fighters != 100 || w.Players[1].Turns != 500 || w.Players[2].Mines != 100 {
				t.Fatal("declined attack changed state")
			}
			if !strings.Contains(term.output.String(), "Attack cancelled.") {
				t.Fatal(term.output.String())
			}
		})
	}
}

func TestConfirmedAttackPublishesSavedOutcomeAndEarthProtection(t *testing.T) {
	term := &scripted{lines: []string{"attack 2 1", "y", "q"}}
	s, st := attackSession(t, term)
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, err := st.View()
	if err != nil {
		t.Fatal(err)
	}
	if w.Players[2].Death == nil || w.Players[2].Mines != 0 || w.Players[1].Turns != 500 || w.Ports[2].Owner != 1 || w.Ports[2].Treasury != 777 {
		t.Fatal("attack outcome missing")
	}
	output := term.output.String()
	if !strings.Contains(output, "Attack saved.") || !strings.Contains(output, "Victim destroyed.") || !strings.Contains(output, "Earth protection safely disposed") {
		t.Fatal(output)
	}
}

func TestAttackRechecksStateAfterConfirmation(t *testing.T) {
	for _, change := range []string{"target moved", "actor moved", "target replaced", "actor replaced", "new team", "target hidden"} {
		t.Run(change, func(t *testing.T) {
			term := &confirmationTerminal{scripted: &scripted{lines: []string{"attack 2 1", "y", "q"}}}
			s, st := attackSession(t, term)
			term.beforeConfirm = func() error {
				return st.Update(func(w *game.World) error {
					switch change {
					case "target moved":
						w.Players[2].Sector = 2
					case "actor moved":
						w.Players[1].Sector = 2
					case "target replaced":
						w.Players[2].ShipGeneration++
					case "actor replaced":
						w.Players[1].ShipGeneration++
					case "new team":
						if err := w.CreateTeam(1, "Team", "ABCD"); err != nil {
							return err
						}
						return w.JoinTeam(2, 1, "ABCD")
					case "target hidden":
						w.Players[2].Cloak = 1
					}
					return nil
				})
			}
			_ = s.Run()
			w, _ := st.View()
			if w.Players[2].Death != nil || w.Players[1].Fighters != 100 || w.Players[2].Credits != 10000 || w.Players[2].Mines != 100 {
				t.Fatal("stale confirmation committed")
			}
			if strings.Contains(term.output.String(), "Attack saved.") {
				t.Fatal("reported unsaved attack")
			}
		})
	}
}

func TestAttackDisconnectAndHiddenTargets(t *testing.T) {
	term := &scripted{lines: []string{"attack 2 1"}}
	s, st := attackSession(t, term)
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[2].Death != nil {
		t.Fatal("disconnect committed")
	}
	if err := st.Update(func(w *game.World) error { w.Players[2].Cloak = 1; return nil }); err != nil {
		t.Fatal(err)
	}
	term = &scripted{lines: []string{"attack 2 1", "q"}}
	s.Terminal = term
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	if strings.Contains(term.output.String(), "Victim") {
		t.Fatal("hidden identity leaked", term.output.String())
	}
}

func TestClassicAttackDialogCancels(t *testing.T) {
	term := &scripted{lines: []string{"2", "1", "n"}}
	s, st := attackSession(t, term)
	s.Classic = true
	w, _ := st.View()
	v, _ := w.NewVisibility(1)
	pending := []string{}
	if err := s.attackShip(1, nil, &pending, v); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(term.output.String(), "Attack Victim with 1 fighters?") {
		t.Fatal(term.output.String())
	}
	w, _ = st.View()
	if w.Players[2].Death != nil {
		t.Fatal("classic declined attack committed")
	}
}

func TestAttackConfirmationDoesNotUseCommandRepeat(t *testing.T) {
	keys := []rune{'y', '/', 13}
	g := &GoDoors{commandMode: true, savedLine: "y", readKey: func(time.Duration) (rune, gd.Key, error) {
		r := keys[0]
		keys = keys[1:]
		if r == 13 {
			return r, gd.KeyEnter, nil
		}
		return r, gd.KeyNone, nil
	}}
	s := Session{disruptionRandom: func() float64 { return .999999 }, Terminal: g, Deadline: time.Now().Add(time.Minute)}
	answer, err := s.readAttackConfirmation()
	if err != nil || answer != "y/" || g.savedLine != "" || !g.commandMode {
		t.Fatal(answer, err, g.savedLine)
	}
}

func TestAttackDrainsQueuedApprovals(t *testing.T) {
	keys := []rune{'y', 13}
	g := &GoDoors{savedLine: "y", pending: []inputKey{{r: 'y'}}}
	g.readKey = func(time.Duration) (rune, gd.Key, error) {
		if len(keys) == 0 {
			return 0, gd.KeyNone, gd.ErrInputTimeout
		}
		r := keys[0]
		keys = keys[1:]
		return r, gd.KeyNone, nil
	}
	if err := g.DiscardTypeahead(); err != nil {
		t.Fatal(err)
	}
	if len(keys) != 0 || len(g.pending) != 0 || g.savedLine != "" {
		t.Fatal("queued approval survived")
	}
}

func TestClassicAReachesFreshAttackConfirmation(t *testing.T) {
	term := &scripted{lines: []string{"", "", "", "a;2;1;y", "n", "q;y"}}
	s, st := attackSession(t, term)
	s.Classic = true
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[2].Death != nil || !strings.Contains(term.output.String(), "Attack cancelled.") {
		t.Fatal(term.output.String())
	}
}

func TestAttackExpiresWhileWaitingForTransactionLock(t *testing.T) {
	term := &confirmationTerminal{scripted: &scripted{lines: []string{"y"}}, reads: 1}
	s, st := attackSession(t, term)
	w, _ := st.View()
	visibility, _ := w.NewVisibility(1)
	s.Deadline = time.Now().Add(time.Second)
	done := make(chan error, 1)
	started := false
	term.beforeConfirm = func() error {
		started = true
		locked := make(chan struct{})
		go func() {
			done <- st.Update(func(w *game.World) error {
				close(locked)
				time.Sleep(time.Until(s.Deadline) + 20*time.Millisecond)
				return nil
			})
		}()
		<-locked
		return nil
	}
	pending := []string{}
	err := s.attackShip(1, []string{"2", "1"}, &pending, visibility)
	if !started {
		t.Fatal("confirmation did not reach lock-wait fixture", err)
	}
	if lockErr := <-done; lockErr != nil {
		t.Fatal(lockErr)
	}
	if err == nil || !strings.Contains(err.Error(), "expired") {
		t.Fatal("expired attack committed", err)
	}
	after, _ := st.View()
	if after.Players[2].Death != nil || after.Players[2].Mines != 100 {
		t.Fatal("expired attack changed state")
	}
}
