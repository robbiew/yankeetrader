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

func radioSession(t *testing.T, term Terminal) (Session, store.Store) {
	t.Helper()
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		_, _ = w.Join("nav", "Navigator")
		_, _ = w.Join("enemy", "Enemy")
		_, _ = w.Join("visitor", "Visitor")
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, st
}

func TestRadioComposerLiteralSendAbortAndHistoryPrivacy(t *testing.T) {
	for _, action := range []string{"s", "a", "s;q"} {
		t.Run(action, func(t *testing.T) {
			term := &scripted{lines: []string{"radio Enemy;y;ignored;S", "hold; then reply/", action, "messages;q"}}
			s, st := radioSession(t, term)
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			if action != "s" {
				if len(w.Radio) != 0 || !strings.Contains(term.output.String(), "Radio cancelled") {
					t.Fatal("stacked send/aborted draft sent a message")
				}
				return
			}
			if len(w.Radio) != 1 || w.Radio[0].Text != "hold; then reply/" || !w.Radio[0].Unread || w.Players[1].Turns != 500 {
				t.Fatal("composer changed literal text/read state or spent turns")
			}
			s.Identity, s.Alias = "visitor", "Visitor"
			visitor := &scripted{lines: []string{"messages;q"}}
			s.Terminal = visitor
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			if strings.Contains(visitor.output.String(), "hold; then reply/") {
				t.Fatal("third party saw message")
			}
			s.Identity, s.Alias = "enemy", "Enemy"
			receiver := &scripted{lines: []string{"messages;q"}}
			s.Terminal = receiver
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ = st.View()
			if w.Radio[0].Unread || strings.Count(receiver.output.String(), "hold; then reply/") != 2 {
				t.Fatal("login/history did not retain delivered message")
			}
			receiver = &scripted{lines: []string{"q"}}
			s.Terminal = receiver
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			if strings.Contains(receiver.output.String(), "hold; then reply/") {
				t.Fatal("acknowledged mail announced again on reconnect")
			}
		})
	}
}

type radioReadTerminal struct {
	*scripted
	reads      int
	beforeRead func(int) error
}

func (t *radioReadTerminal) ReadLine(deadline time.Time) (string, error) {
	t.reads++
	if t.beforeRead != nil {
		if err := t.beforeRead(t.reads); err != nil {
			return "", err
		}
	}
	return t.scripted.ReadLine(deadline)
}

func TestRadioRechecksRecipientAfterComposition(t *testing.T) {
	term := &radioReadTerminal{scripted: &scripted{lines: []string{"private text", "s"}}}
	s, st := radioSession(t, term)
	w, _ := st.View()
	s.Store = st.ForShip(1, w.Players[1].ShipGeneration, 1)
	term.beforeRead = func(n int) error {
		if n == 2 {
			return st.Update(func(w *game.World) error { w.Players[2].Alias = "Changed"; return nil })
		}
		return nil
	}
	pending := []string{"y"}
	if err := s.sendRadio(1, []string{"Enemy"}, &pending); err == nil {
		t.Fatal("stale recipient confirmation sent mail")
	}
	w, _ = st.View()
	if len(w.Radio) != 0 {
		t.Fatal("stale draft persisted")
	}
}

type failingRadioTerminal struct{ *scripted }

func (t *failingRadioTerminal) Printf(format string, args ...any) error {
	if strings.Contains(fmt.Sprintf(format, args...), "private body") {
		return errors.New("disconnected during output")
	}
	return t.scripted.Printf(format, args...)
}

func TestRadioOutputFailureKeepsMessageUnread(t *testing.T) {
	term := &failingRadioTerminal{scripted: &scripted{}}
	s, st := radioSession(t, term)
	if err := st.Update(func(w *game.World) error {
		address, _ := w.FindRadioRecipient(1, "Enemy")
		draft, _ := w.PrepareRadio(1, address, "private body", s.Now())
		_, err := w.CommitRadio(draft, s.Now())
		return err
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	s.Store = st.ForShip(2, w.Players[2].ShipGeneration, 1)
	if err := s.deliverRadio(2); err == nil {
		t.Fatal("output failure ignored")
	}
	w, _ = st.View()
	if !w.Radio[0].Unread {
		t.Fatal("failed display marked mail read")
	}
	s.Terminal = &scripted{}
	if err := s.deliverRadio(2); err != nil {
		t.Fatal(err)
	}
	w, _ = st.View()
	if w.Radio[0].Unread {
		t.Fatal("successful display was not acknowledged")
	}
}

func TestClassicRadioHistoryComputerOption(t *testing.T) {
	term := &scripted{lines: []string{"", "", "", "c;5;Enemy;y", "DOS RADIO PROBE", "s", "6;1;q;y"}}
	s, st := radioSession(t, term)
	s.Classic = true
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if len(w.Radio) != 1 || !strings.Contains(term.output.String(), "Transmission successful!") || !strings.Contains(term.output.String(), "Message to: Enemy * From: Navigator") {
		t.Fatal("computer 5/6 failed", term.output.String())
	}
}

func TestRadioHistoryPagingLeavesUndisplayedUnread(t *testing.T) {
	term := &scripted{lines: []string{"q"}}
	s, st := radioSession(t, term)
	if err := st.Update(func(w *game.World) error {
		address, _ := w.FindRadioRecipient(1, "Enemy")
		for i := 0; i < 7; i++ {
			d, _ := w.PrepareRadio(1, address, fmt.Sprintf("Page item %d", i), s.Now())
			if _, err := w.CommitRadio(d, s.Now()); err != nil {
				return err
			}
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	s.Store = st.ForShip(2, w.Players[2].ShipGeneration, 1)
	if err := s.radioHistory(2, nil, true); err != nil {
		t.Fatal(err)
	}
	w, _ = st.View()
	unread, _ := w.RadioHistory(2, 0, 20, true)
	if len(unread) != 2 || unread[0].ID != 6 || strings.Contains(term.output.String(), "Page item 5") {
		t.Fatal("paging marked unseen mail read", unread)
	}
	term.lines = []string{""}
	if err := s.radioHistory(2, nil, true); err != nil {
		t.Fatal(err)
	}
	w, _ = st.View()
	unread, _ = w.RadioHistory(2, 0, 20, true)
	if len(unread) != 0 {
		t.Fatal("remaining page was not delivered")
	}
}

func TestTeamRadioComposerSendAbortAndLiteralText(t *testing.T) {
	for _, action := range []string{"s", "a", "s;q"} {
		t.Run(action, func(t *testing.T) {
			term := &scripted{lines: []string{"radio team;y;discarded", "hold; then reply/", action, "messages;q"}}
			s, st := radioSession(t, term)
			if err := st.Update(func(w *game.World) error {
				if err := w.CreateTeam(1, "Orion", "ABCD"); err != nil {
					return err
				}
				return w.JoinTeam(2, 1, "ABCD")
			}); err != nil {
				t.Fatal(err)
			}
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			if action != "s" {
				if len(w.Radio) != 0 {
					t.Fatal("aborted/stacked send delivered copies")
				}
				return
			}
			if len(w.Radio) != 2 || w.Radio[0].To != 1 || w.Radio[1].To != 2 || w.Radio[1].Text != "hold; then reply/" || !w.Radio[1].Unread {
				t.Fatal(w.Radio)
			}
			out := term.output.String()
			if (!strings.Contains(out, "team Orion (#1)") || !strings.Contains(out, "  Navigator (#1)") || !strings.Contains(out, "  Enemy (#2)")) || !strings.Contains(out, "2 team copies saved.") {
				t.Fatal(out)
			}
			if w.Players[1].Turns != 500 {
				t.Fatal("radio charged turns")
			}
		})
	}
}

func TestTeamRadioRejectsRosterChangeDuringComposition(t *testing.T) {
	for _, at := range []int{1, 2} {
		t.Run(fmt.Sprint(at), func(t *testing.T) {
			term := &radioReadTerminal{scripted: &scripted{lines: []string{"private text", "s"}}}
			s, st := radioSession(t, term)
			if err := st.Update(func(w *game.World) error {
				if err := w.CreateTeam(1, "Orion", "ABCD"); err != nil {
					return err
				}
				return w.JoinTeam(2, 1, "ABCD")
			}); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			s.Store = st.ForShip(1, w.Players[1].ShipGeneration, 1)
			term.beforeRead = func(n int) error {
				if n == at {
					return st.Update(func(w *game.World) error { return w.JoinTeam(3, 1, "ABCD") })
				}
				return nil
			}
			pending := []string{"y"}
			if err := s.sendRadio(1, []string{"team"}, &pending); err == nil {
				t.Fatal("new recipient silently added")
			}
			w, _ = st.View()
			if len(w.Radio) != 0 {
				t.Fatal("stale team send persisted")
			}
		})
	}
}
