package door

import (
	"fmt"
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
				if len(w.Radio) != 0 {
					t.Fatal("aborted/queued broadcast sent")
				}
				return
			}
			if len(w.Radio) != 3 || w.Players[1].Turns != 500 {
				t.Fatal(w.Radio)
			}
			for i, m := range w.Radio {
				if m.To != i+1 || m.Text != "ALL; literal/" {
					t.Fatal(w.Radio)
				}
			}
			out := term.output.String()
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
			if len(w.Radio) != 0 {
				t.Fatal("stale broadcast persisted")
			}
		})
	}
}
