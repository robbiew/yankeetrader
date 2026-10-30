package door

import (
	"errors"
	"fmt"
	"io"
	"math"
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func cloakSession(t *testing.T, term *scripted) (Session, int, string) {
	t.Helper()
	s, id, token := portSession(t, true)
	s.Terminal = term
	if err := s.Store.Update(func(w *game.World) error {
		p := w.Players[id]
		p.Cloak = 0
		p.Credits = 1000000
		target, e := w.Join("hidden", "Hidden")
		if e != nil {
			return e
		}
		target.Sector = 2
		target.Cloak = 1
		w.Sectors[1].Warps = []int{2}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	s.Store = s.Store.ForShip(id, 0)
	w, _ := s.Store.View()
	s.visibility, _ = w.NewVisibility(id)
	return s, id, token
}
func TestCloakDoorPurchaseReceiptsAndDefaults(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, cash := range []int64{999, 1000, 1001} {
			term := &scripted{}
			s, id, token := cloakSession(t, term)
			s.Classic = classic
			if err := s.Store.Update(func(w *game.World) error { w.Players[id].Credits = cash; return nil }); err != nil {
				t.Fatal(err)
			}
			var err error
			if classic {
				err = s.earthShop(id, token, &[]string{"1", "1", "0"})
			} else {
				err = s.buyCloak(token, 1)
			}
			w, _ := s.Store.View()
			p := w.Players[id]
			text := term.output.String()
			if cash < 1000 {
				if p.Credits != cash || p.Cloak != 0 || strings.Contains(text, "purchased and saved") {
					t.Fatal("poor receipt", err, text)
				}
				continue
			}
			if err != nil || p.Credits != cash-1000 || p.Cloak != .01 || p.Turns != 499 || strings.Count(text, fmt.Sprintf("credits spent: 1000. Balance: %d.", cash-1000)) != 1 {
				t.Fatal("receipt", err, text)
			}
		}
	}
	for _, tc := range []struct {
		cloak       float64
		cash, spent int64
		after       float64
	}{{.9, 10000, 10000, 1}, {0, 1999, 1000, .01}, {1, 10000, 0, 1}} {
		term := &scripted{}
		s, id, token := cloakSession(t, term)
		_ = s.Store.Update(func(w *game.World) error { w.Players[id].Cloak = tc.cloak; w.Players[id].Credits = tc.cash; return nil })
		if err := s.earthShop(id, token, &[]string{"1", "", "0"}); err != nil {
			t.Fatal(err)
		}
		w, _ := s.Store.View()
		p := w.Players[id]
		if p.Credits != tc.cash-tc.spent || math.Abs(p.Cloak-tc.after) > 1e-12 || strings.Contains(term.output.String(), "purchased and saved") != (tc.spent > 0) {
			t.Fatal("classic default", term.output.String())
		}
	}
	term := &scripted{lines: []string{"0", "0"}}
	s, id, token := cloakSession(t, term)
	_ = s.Store.Update(func(w *game.World) error { w.Players[id].Cloak = .9; return nil })
	if err := s.earthShop(id, token, &[]string{"1", "11", "10"}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	if w.Players[id].Credits != 1000000 || !strings.Contains(term.output.String(), "cannot exceed") || strings.Contains(term.output.String(), "purchased and saved") {
		t.Fatal("queued correction bought", term.output.String())
	}
}
func TestAntiCloakDoorFreshReceiptRepeatAndInfo(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, answer := range []string{"y", "n", "", "y;q"} {
			term := &scripted{lines: []string{answer, "0"}}
			s, id, token := cloakSession(t, term)
			s.Classic = classic
			var err error
			if classic {
				err = s.earthShop(id, token, &[]string{"6", "y", "0"})
			} else {
				err = s.activateAntiCloak(token, nil, &[]string{"y", "q"})
			}
			w, _ := s.Store.View()
			p := w.Players[id]
			text := term.output.String()
			if answer != "y" {
				if err != nil || p.Credits != 1000000 || s.visibility.AntiCloakActivations() != 0 || strings.Contains(text, "activation saved") {
					t.Fatal("false activation", err, text)
				}
				continue
			}
			if err != nil || p.Credits != 500000 || s.visibility.AntiCloakActivations() != 1 || !strings.Contains(text, "Credits spent: 500000. Balance: 500000. Newly revealed: 1.") || !strings.Contains(text, "2: Hidden is revealed to this login.") {
				t.Fatal("saved activation receipt", err, text)
			}
			term.lines = []string{"y"}
			if err = s.activateAntiCloak(token, nil, &[]string{}); err != nil {
				t.Fatal(err)
			}
			if !strings.Contains(term.output.String(), "Balance: 0. Newly revealed: 0.") {
				t.Fatal("empty repeat receipt", term.output.String())
			}
			w, _ = s.Store.View()
			if w.Players[id].Cloak != 0 || w.Players[2].Cloak != 1 || w.Players[id].Turns != 499 {
				t.Fatal("persistent energy modified")
			}
			if err = s.classicInfo(w, id, false); err != nil {
				t.Fatal(err)
			}
			if !strings.Contains(term.output.String(), "Anti-cloak active for this login") || strings.Contains(term.output.String(), "FAIL") {
				t.Fatal("misleading info", term.output.String())
			}
		}
	}
}
func TestCloakDoorExpiredAndDisconnectedNoSuccess(t *testing.T) {
	for _, mode := range []string{"deadline", "eof", "poor", "args"} {
		term := &scripted{lines: []string{"y"}}
		s, id, token := cloakSession(t, term)
		if mode == "eof" {
			term.lines = nil
		}
		if mode == "poor" {
			_ = s.Store.Update(func(w *game.World) error { w.Players[id].Credits = 499999; return nil })
		}
		args := []string{}
		if mode == "args" {
			args = []string{"1"}
		}
		if mode == "deadline" {
			at := s.Now()
			calls := 0
			s.Deadline = time.Now().Add(30 * time.Millisecond)
			s.Now = func() time.Time {
				calls++
				if calls == 2 {
					time.Sleep(50 * time.Millisecond)
				}
				return at
			}
		}
		before, _ := s.Store.View()
		cash := before.Players[id].Credits
		err := s.activateAntiCloak(token, args, &[]string{"y"})
		after, _ := s.Store.View()
		if err == nil || after.Players[id].Credits != cash || s.visibility.AntiCloakActivations() != 0 || strings.Contains(term.output.String(), "activation saved") {
			t.Fatal(mode, err, term.output.String())
		}
		if mode == "eof" && !errors.Is(err, io.EOF) {
			t.Fatal(err)
		}
	}
}
