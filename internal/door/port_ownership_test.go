package door

import (
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"io"
	"strings"
	"testing"
	"time"
)

func ownershipSession(t *testing.T, lines []string) (Session, *scripted) {
	t.Helper()
	now := time.Now()
	w, err := game.New(now, 36, 8)
	if err != nil {
		t.Fatal(err)
	}
	buyer, _ := w.Join("buyer", "Buyer")
	seller, _ := w.Join("seller", "Seller")
	buyer.Sector, buyer.Credits = 2, 100000
	seller.Credits = 2000
	w.Ports[2].Owner, w.Ports[2].Treasury = seller.ID, 777
	st := store.Store{Dir: t.TempDir()}
	if err = st.Create(w); err != nil {
		t.Fatal(err)
	}
	term := &scripted{lines: lines}
	return Session{disruptionRandom: func() float64 { return .999999 }, Store: st, Terminal: term, Identity: "buyer", Alias: "Buyer", Deadline: now.Add(time.Minute), Now: func() time.Time { return now }}, term
}

func TestPortOwnershipCommandsPersistAndReconnect(t *testing.T) {
	s, term := ownershipSession(t, []string{"acquire;y;treasury;$;q"})
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, err := s.Store.View()
	if err != nil {
		t.Fatal(err)
	}
	if w.Players[1].Credits != 99969 || w.Players[2].Credits != 2808 || w.Ports[2].Owner != 1 || w.Ports[2].Treasury != 0 || w.Players[1].Turns != 500 {
		t.Fatal("buyout not saved", w.Players, w.Ports[2])
	}
	for _, want := range []string{"31 credits", "Seller", "Sold!", "personally owned", "Collected 0 credits"} {
		if !strings.Contains(term.output.String(), want) {
			t.Fatal("missing", want, term.output.String())
		}
	}
	term.lines = []string{"b;y;q"}
	if err = s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ = s.Store.View()
	if w.Players[1].Credits != 99969 || !strings.Contains(term.output.String(), "already own") {
		t.Fatal("reconnect/replay changed ownership")
	}
}

func TestPortOwnershipCancellationAndDisconnect(t *testing.T) {
	for _, answer := range []string{"", "n", "eof"} {
		t.Run(answer, func(t *testing.T) {
			lines := []string{answer}
			if answer == "eof" {
				lines = nil
			}
			s, _ := ownershipSession(t, lines)
			pending := []string{}
			err := s.buyPort(1, &pending)
			if answer == "eof" && err != io.EOF {
				t.Fatal(err)
			}
			if answer != "eof" && err != nil {
				t.Fatal(err)
			}
			w, _ := s.Store.View()
			if w.Players[1].Credits != 100000 || w.Players[2].Credits != 2000 || w.Ports[2].Owner != 2 || w.Ports[2].Treasury != 777 {
				t.Fatal("unconfirmed buyout saved")
			}
		})
	}
}

type ownershipChanged struct {
	*scripted
	change func()
}

func (t *ownershipChanged) ReadLine(deadline time.Time) (string, error) {
	t.change()
	return t.scripted.ReadLine(deadline)
}
func TestPortOwnershipRevalidatesAfterConfirmation(t *testing.T) {
	s, term := ownershipSession(t, []string{"y"})
	s.Terminal = &ownershipChanged{term, func() {
		if err := s.Store.Update(func(w *game.World) error { w.Ports[2].Production[0] = 200; return nil }); err != nil {
			t.Fatal(err)
		}
	}}
	pending := []string{}
	if err := s.buyPort(1, &pending); err == nil {
		t.Fatal("changed asking price accepted")
	}
	w, _ := s.Store.View()
	if w.Players[1].Credits != 100000 || w.Ports[2].Owner != 2 {
		t.Fatal("stale confirmation committed")
	}
}

func TestClassicPortOwnershipBindings(t *testing.T) {
	s, term := ownershipSession(t, nil)
	if err := s.Store.Update(func(w *game.World) error { w.Players[1].LastLogin = s.Now().UTC().Format("2006-01-02"); return nil }); err != nil {
		t.Fatal(err)
	}
	s.Classic = true
	term.lines = []string{"", "", "", "b;y;c;12;1;$;q;y"}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	if w.Ports[2].Owner != 1 || w.Players[1].Credits != 99969 {
		t.Fatal("classic B binding failed", term.output.String())
	}
	for _, want := range []string{"personally owned", "Collected 0 credits"} {
		if !strings.Contains(term.output.String(), want) {
			t.Fatal("missing classic command", want, term.output.String())
		}
	}
}
