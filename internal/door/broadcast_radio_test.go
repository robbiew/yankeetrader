package door

import (
	"errors"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/store"
	"io"
	"math"
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestBroadcastRadioComposerLiteralSendAndAbort(t *testing.T) {
	for _, action := range []string{"s", "a", "s;q"} {
		t.Run(action, func(t *testing.T) {
			term := &scripted{lines: []string{"radio all;y;discarded", "ALL; literal/", action, "messages;q"}}
			s, st := radioSession(t, term)
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			if action != "s" {
				if len(w.Radio) != 0 || broadcastNewsCount(w) != 0 {
					t.Fatal("aborted/queued broadcast sent")
				}
				return
			}
			if len(w.Radio) != 3 || w.Players[1].Turns != 500 || broadcastNewsCount(w) != 1 {
				t.Fatal(w.Radio)
			}
			for i, m := range w.Radio {
				if m.To != i+1 || m.Text != "ALL; literal/" {
					t.Fatal(w.Radio)
				}
			}
			out := term.output.String()
			if !strings.Contains(out, "PUBLIC: This exact text and your alias") || !strings.Contains(out, "Public newspaper entry saved.") {
				t.Fatal(out)
			}
			if !strings.Contains(out, "ALL 3 current active accounts (including you)") || !strings.Contains(out, "3 broadcast copies saved.") {
				t.Fatal(out)
			}
			s.Identity, s.Alias = "later", "Later"
			s.Terminal = &scripted{lines: []string{"messages;q"}}
			later := s.Terminal.(*scripted)
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			if strings.Contains(later.output.String(), "ALL; literal/") {
				t.Fatal("future player inherited old broadcast")
			}
		})
	}
}

func TestBroadcastRadioRechecksRosterBeforePreparationAndSend(t *testing.T) {
	for _, at := range []int{1, 2} {
		t.Run(fmt.Sprint(at), func(t *testing.T) {
			term := &radioReadTerminal{scripted: &scripted{lines: []string{"private text", "s"}}}
			s, st := radioSession(t, term)
			w, _ := st.View()
			s.Store = st.ForShip(1, w.Players[1].ShipGeneration, 1)
			term.beforeRead = func(n int) error {
				if n == at {
					return st.Update(func(w *game.World) error { _, err := w.Join("new-recipient", "New"); return err })
				}
				return nil
			}
			pending := []string{"y"}
			if err := s.sendRadio(1, []string{"ALL"}, &pending); err == nil {
				t.Fatal("unconfirmed recipient received broadcast")
			}
			w, _ = st.View()
			if len(w.Radio) != 0 || broadcastNewsCount(w) != 0 {
				t.Fatal("stale broadcast persisted")
			}
		})
	}
}

func broadcastNewsCount(w *game.World) int {
	n := 0
	for _, e := range w.News {
		if e.Kind == game.NewsBroadcast {
			n++
		}
	}
	return n
}

// Actual storage post-replacement failures are exercised by the store suite;
// this injection exercises receipt failure and login termination at that boundary.
type broadcastOutputFailure struct {
	scripted
	failure error
}

func (t *broadcastOutputFailure) Printf(format string, args ...any) error {
	if strings.Contains(format, "broadcast copies") && strings.Contains(format, "saved") {
		return t.failure
	}
	return t.scripted.Printf(format, args...)
}
func TestBroadcastReceiptRetainsWarningAndSessionStops(t *testing.T) {
	for _, failure := range []error{io.EOF, io.ErrClosedPipe, errors.New("output failed")} {
		warning := &store.DurabilityError{Err: errors.New("sync after replacement")}
		term := &broadcastOutputFailure{failure: failure}
		err := (Session{Terminal: term}).broadcastReceipt(3, warning)
		var committed *store.DurabilityError
		if !errors.As(err, &committed) || committed != warning || !errors.Is(err, failure) {
			t.Fatal("lost committed warning", err)
		}
		term = &broadcastOutputFailure{scripted: scripted{lines: []string{"radio all;y", "public text", "s", "radio all;y", "duplicate", "s", "q"}}, failure: errors.Join(warning, failure)}
		s, st := radioSession(t, term)
		err = s.Run()
		if !errors.As(err, &committed) {
			t.Fatal("login continued after warning", err)
		}
		w, e := st.View()
		if e != nil || len(w.Radio) != 3 || broadcastNewsCount(w) != 1 || len(term.lines) != 4 {
			t.Fatal("lost saved send or continued session", e, len(term.lines))
		}
	}
}
func TestBroadcastNewspaperVisibleInBothInterfaces(t *testing.T) {
	for _, classic := range []bool{false, true} {
		term := &scripted{}
		s, st := radioSession(t, term)
		if err := st.Update(func(w *game.World) error {
			address, err := w.FindBroadcastRadioRecipients(1)
			if err != nil {
				return err
			}
			draft, err := w.PrepareBroadcastRadio(1, address, "public; literal/", s.Now())
			if err != nil {
				return err
			}
			_, err = w.CommitBroadcastRadio(draft, s.Now())
			return err
		}); err != nil {
			t.Fatal(err)
		}
		w, _ := st.View()
		s.Store = st.ForShip(2, w.Players[2].ShipGeneration, w.Season)
		s.Classic = classic
		pending := []string{}
		if err := s.newspaper(2, []string{"today"}, &pending); err != nil {
			t.Fatal(err)
		}
		out := term.output.String()
		if !strings.Contains(out, "Navigator [PUBLIC BROADCAST]\r\npublic; literal/") {
			t.Fatal(out)
		}
		w, _ = st.View()
		if !w.Radio[1].Unread {
			t.Fatal("public reading acknowledged private mail")
		}
	}
}

func TestBroadcastJournalFailurePrintsNoSavedReceipt(t *testing.T) {
	term := &radioReadTerminal{scripted: &scripted{lines: []string{"public body", "s"}}}
	s, st := radioSession(t, term)
	w, _ := st.View()
	s.Store = st.ForShip(1, w.Players[1].ShipGeneration, w.Season)
	term.beforeRead = func(n int) error {
		if n == 2 {
			return st.Update(func(w *game.World) error { w.NextNews = math.MaxUint64; return nil })
		}
		return nil
	}
	pending := []string{"y"}
	if err := s.sendRadio(1, []string{"ALL"}, &pending); err == nil {
		t.Fatal("send succeeded with exhausted journal")
	}
	w, _ = st.View()
	if len(w.Radio) != 0 || broadcastNewsCount(w) != 0 || strings.Contains(term.output.String(), "copies saved") {
		t.Fatal("failed save claimed publication", term.output.String())
	}
	if !strings.Contains(term.output.String(), "Public sender: Navigator") {
		t.Fatal("missing actual public alias preview")
	}
}
