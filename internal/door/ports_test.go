package door

import (
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func portSession(t *testing.T, earth bool) (Session, int, string) {
	t.Helper()
	now := time.Date(2026, 10, 24, 0, 0, 0, 0, time.UTC)
	w, err := game.New(now, 36, 8)
	if err != nil {
		t.Fatal(err)
	}
	p, err := w.Join("port-test", "Trader")
	if err != nil {
		t.Fatal(err)
	}
	p.Credits = 10000
	if !earth {
		p.Sector = 2
		w.Ports[2].Coefficient = [3]float64{1, -1, -1}
		w.Ports[2].Supply = [3]float64{1000, 1000, 1000}
	}
	if err = w.Dock(p.ID, now); err != nil {
		t.Fatal(err)
	}
	st := store.Store{Dir: t.TempDir()}
	if err = st.Create(w); err != nil {
		t.Fatal(err)
	}
	return Session{Store: st, Terminal: &scripted{}, Now: func() time.Time { return now }, Deadline: time.Now().Add(time.Minute)}, p.ID, p.DockToken
}

func TestEarthNumberedShop(t *testing.T) {
	s, id, token := portSession(t, true)
	pending := []string{"1", "2", "1", "3", "2", "7", "1", "8", "3", "3", "-1", "3", "1.5", "3", "999999999999999999999999", "3", "", "0"}
	if err := s.classicPort(id, token, &pending); err != nil {
		t.Fatal(err)
	}
	w, err := s.Store.View()
	if err != nil {
		t.Fatal(err)
	}
	p := w.Players[id]
	if p.Credits != 8400 || p.Holds != 11 || p.Fighters != 27 || p.Ground != 1 || p.Shields != 3 || p.Turns != 499 || p.DockToken != "" {
		t.Fatalf("unexpected purchases: %+v", p)
	}
	out := s.Terminal.(*scripted).output.String()
	if !strings.Contains(out, "That item is unavailable") || strings.Count(out, "purchased and saved") != 4 || !strings.Contains(out, "Purchase rejected") {
		t.Fatal(out)
	}
}

func TestCargoAgreementAndDefault(t *testing.T) {
	for _, tc := range []struct {
		name     string
		answers  []string
		quantity int64
	}{
		{"decline", []string{"3", "n"}, 0},
		{"confirmed", []string{"3", "y"}, 3},
		{"defaults", []string{"", ""}, 10},
		{"zero", []string{"0"}, 0},
		{"negative", []string{"-1"}, 0},
		{"fraction", []string{"1.5"}, 0},
		{"overflow", []string{"999999999999999999999999999"}, 0},
		{"too many", []string{"11"}, 0},
	} {
		t.Run(tc.name, func(t *testing.T) {
			s, id, token := portSession(t, false)
			before, _ := s.Store.View()
			price := before.Players[id].DockPrices[0]
			if err := s.classicPort(id, token, &tc.answers); err != nil {
				t.Fatal(err)
			}
			w, err := s.Store.View()
			if err != nil {
				t.Fatal(err)
			}
			p := w.Players[id]
			if p.Cargo[0] != tc.quantity || p.Credits != 10000-tc.quantity*price || p.Turns != 499 || p.DockToken != "" {
				t.Fatalf("unexpected trade: %+v", p)
			}
		})
	}
}

func TestCargoSale(t *testing.T) {
	s, id, token := portSession(t, false)
	if err := s.Store.Update(func(w *game.World) error { w.Ports[2].Coefficient[0] = -1; w.Players[id].Cargo[0] = 5; return nil }); err != nil {
		t.Fatal(err)
	}
	before, _ := s.Store.View()
	price := before.Players[id].DockPrices[0]
	pending := []string{"2", ""}
	if err := s.classicPort(id, token, &pending); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	if w.Players[id].Cargo[0] != 3 || w.Players[id].Credits != 10000+2*price {
		t.Fatal(w.Players[id])
	}
}

type portInput struct {
	scripted
	beforeRead func()
}

func (p *portInput) ReadLine(deadline time.Time) (string, error) {
	if p.beforeRead != nil {
		p.beforeRead()
	}
	return p.scripted.ReadLine(deadline)
}

func TestPortRejectsChangesDuringPrompts(t *testing.T) {
	for _, earth := range []bool{false, true} {
		for _, mode := range []string{"redock", "expired", "credits"} {
			t.Run(mode+map[bool]string{true: "-earth", false: "-cargo"}[earth], func(t *testing.T) {
				s, id, token := portSession(t, earth)
				term := &portInput{}
				s.Terminal = term
				reads := 0
				term.lines = []string{"3", "1"}
				if !earth {
					term.lines = []string{"1", "y"}
				}
				term.beforeRead = func() {
					reads++
					if reads != 2 {
						return
					}
					err := s.Store.Update(func(w *game.World) error {
						switch mode {
						case "redock":
							return w.Dock(id, s.Now())
						case "expired":
							w.Players[id].DockUntil = s.Now()
						case "credits":
							w.Players[id].Credits = 0
						}
						return nil
					})
					if err != nil {
						t.Fatal(err)
					}
				}
				pending := []string{}
				_ = s.classicPort(id, token, &pending)
				w, _ := s.Store.View()
				p := w.Players[id]
				if p.Cargo[0] != 0 || p.Fighters != 25 {
					t.Fatal("stale prompt committed a purchase", p)
				}
				if strings.Contains(term.output.String(), "It's Yours!") || strings.Contains(term.output.String(), "purchased and saved") {
					t.Fatal("false success", term.output.String())
				}
				if mode == "redock" && p.DockToken == "" {
					t.Fatal("cleared the other connection's token")
				}
			})
		}
	}
}

func TestPortDisconnectBeforeCommit(t *testing.T) {
	for _, earth := range []bool{false, true} {
		s, id, token := portSession(t, earth)
		// Supply only a menu choice/quantity: the next input is EOF.
		s.Terminal = &scripted{lines: []string{"3"}}
		pending := []string{}
		if err := s.classicPort(id, token, &pending); err == nil {
			t.Fatal("expected disconnect")
		}
		w, err := s.Store.View()
		if err != nil {
			t.Fatal(err)
		}
		p := w.Players[id]
		if p.Credits != 10000 || p.Cargo[0] != 0 || p.Fighters != 25 || p.Turns != 499 {
			t.Fatalf("disconnect spent assets: %+v", p)
		}
	}
}
