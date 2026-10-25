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

func planetSession(t *testing.T) (Session, int) {
	t.Helper()
	now := time.Date(2026, 10, 24, 0, 0, 0, 0, time.UTC)
	w, err := game.New(now, 36, 8)
	if err != nil {
		t.Fatal(err)
	}
	p, err := w.Join("planet-test", "Trader")
	if err != nil {
		t.Fatal(err)
	}
	p.Credits = 100000
	p.Holds = 100
	p.Cargo = [3]int64{10, 20, 30}
	p.Fighters = 10000
	p.Missiles = 7
	p.Mines = 8
	p.Plasma = 9
	p.Ground = 15
	p.Sector = 2
	planet := &game.Planet{ID: 2, Sector: 2, Owner: p.ID, Name: "Test Planet", Updated: now, Production: [3]float64{10, 20, 30}, Cargo: [3]float64{100, 200, 300}, Fighters: 600, Missiles: 70, Mines: 80, Plasma: 90, Ground: 100}
	w.Planets[2] = planet
	w.Sectors[2].Planet = 2
	st := store.Store{Dir: t.TempDir()}
	if err = st.Create(w); err != nil {
		t.Fatal(err)
	}
	return Session{Store: st, Terminal: &scripted{}, Now: func() time.Time { return now }, Deadline: time.Now().Add(time.Minute)}, p.ID
}

func TestClassicPlanetTransactionsAndLeave(t *testing.T) {
	s, id := planetSession(t)
	pending := []string{"?", "t", "f", "123", "b", "15000", "$", "251", "f", "90", "d", "1", "5", "l"}
	if err := s.classicLand(id, &pending); err != nil {
		t.Fatal(err)
	}
	w, err := s.Store.View()
	if err != nil {
		t.Fatal(err)
	}
	p := w.Players[id]
	planet := w.Planets[2]
	if p.Credits != 84749 || planet.Bank != 15000 || p.Fighters != 9877 || int64(planet.Fighters) != 723 || p.Ground != 25 || planet.Ground != 90 || p.Cargo[0] != 15 || int64(planet.Cargo[0]) != 95 || p.Turns != 500 || p.PlanetToken != "" {
		t.Fatalf("wrong final state p=%+v planet=%+v", p, planet)
	}
	if planet.Production[0] != 11.004 {
		t.Fatal("investment lost fractions", planet.Production)
	}
	if !strings.Contains(s.Terminal.(*scripted).output.String(), "Planet command (?=help) [A]?") {
		t.Fatal("missing planet prompt")
	}
}

func TestPlanetDefaultTakeAllAndDeposit(t *testing.T) {
	s, id := planetSession(t)
	pending := []string{"", "t", "c", "t", "b", "t", "s", "t", "m", "l"}
	if err := s.classicLand(id, &pending); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	p := w.Players[id]
	planet := w.Planets[2]
	if p.Cargo != [3]int64{} || p.Plasma != 0 || p.Missiles != 0 || p.Mines != 0 || p.Fighters != 10600 || int64(planet.Plasma) != 99 || int64(planet.Missiles) != 77 || int64(planet.Mines) != 88 {
		t.Fatalf("transfer conservation p=%+v planet=%+v", p, planet)
	}
}

func TestPlanetRejectedInputsStayInMenu(t *testing.T) {
	s, id := planetSession(t)
	pending := []string{"b", "-1", "b", "1.5", "b", "9999999999999999999999", "b", "100001", "$", "100001", "f", "116", "1", "41", "t", "f", "10001", "l"}
	if err := s.classicLand(id, &pending); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	p := w.Players[id]
	planet := w.Planets[2]
	if p.Credits != 100000 || planet.Bank != 0 || p.Cargo != [3]int64{10, 20, 30} || p.Fighters != 10000 || planet.Ground != 100 || p.PlanetToken != "" {
		t.Fatalf("rejected inputs mutated state: %+v %+v", p, planet)
	}
}

func TestPlanetPromptRechecksSessionAndPermission(t *testing.T) {
	for _, mode := range []string{"reland", "move", "access", "funds"} {
		t.Run(mode, func(t *testing.T) {
			s, id := planetSession(t)
			reads := 0
			term := &portInput{scripted: scripted{lines: []string{"b", "1000", "l"}}}
			s.Terminal = term
			term.beforeRead = func() {
				reads++
				if reads != 2 {
					return
				}
				err := s.Store.Update(func(w *game.World) error {
					switch mode {
					case "reland":
						return w.Land(id, s.Now())
					case "move":
						return w.Move(id, 3)
					case "access":
						other, err := w.Join("other", "Other")
						if err != nil {
							return err
						}
						w.Planets[2].Owner = other.ID
					case "funds":
						w.Players[id].Credits = 0
					}
					return nil
				})
				if err != nil {
					t.Fatal(err)
				}
			}
			pending := []string{}
			err := s.classicLand(id, &pending)
			if mode != "funds" && err == nil {
				t.Fatal("stale session accepted")
			}
			w, _ := s.Store.View()
			if w.Planets[2].Bank != 0 {
				t.Fatal("stale prompt moved credits")
			}
			if mode == "reland" && w.Players[id].PlanetToken == "" {
				t.Fatal("cleared another connection's token")
			}
		})
	}
}

func TestPlanetDisconnectDoesNotCommitPrompt(t *testing.T) {
	for _, choice := range []string{"b", "$", "f", "1", "t"} {
		t.Run(choice, func(t *testing.T) {
			s, id := planetSession(t)
			s.Terminal = &scripted{lines: []string{choice}}
			pending := []string{}
			if err := s.classicLand(id, &pending); !errors.Is(err, io.EOF) {
				t.Fatal("expected disconnect", err)
			}
			w, _ := s.Store.View()
			p := w.Players[id]
			if p.Credits != 100000 || p.Cargo != [3]int64{10, 20, 30} || w.Planets[2].Bank != 0 || p.Ground != 15 {
				t.Fatal("disconnect spent assets", p)
			}
		})
	}
}

func TestPlanetCreationConfirmation(t *testing.T) {
	for _, mode := range []string{"yes", "no", "disconnect", "moved"} {
		t.Run(mode, func(t *testing.T) {
			s, id := planetSession(t)
			if err := s.Store.Update(func(w *game.World) error { delete(w.Planets, 2); w.Sectors[2].Planet = 0; return nil }); err != nil {
				t.Fatal(err)
			}
			pending := []string{"y", "New Eden", "y"}
			if mode == "no" {
				pending = []string{"n"}
			}
			if mode == "disconnect" {
				pending = []string{"y", "New Eden"}
			}
			if mode == "moved" {
				term := &portInput{scripted: scripted{lines: []string{"y", "New Eden", "y"}}}
				s.Terminal = term
				pending = nil
				reads := 0
				term.beforeRead = func() {
					reads++
					if reads == 3 {
						if err := s.Store.Update(func(w *game.World) error { return w.Move(id, 3) }); err != nil {
							t.Fatal(err)
						}
					}
				}
			}
			_ = s.classicLand(id, &pending)
			w, _ := s.Store.View()
			if mode == "yes" {
				if w.Players[id].Credits != 75000 || w.Planets[2] == nil || w.Planets[2].Name != "New Eden" {
					t.Fatal("creation failed", w.Players[id])
				}
			} else if w.Players[id].Credits != 100000 || len(w.Planets) != 0 {
				t.Fatal("unconfirmed creation committed")
			}
		})
	}
}

func TestPlanetCancelZeroAndDefaultQuantities(t *testing.T) {
	for _, tc := range []struct {
		name                    string
		commands                []string
		cash, bank, ore, ground int64
	}{
		{"cancel bank", []string{"b", "", "l"}, 100000, 10000, 10, 15},
		{"withdraw all", []string{"b", "0", "l"}, 110000, 0, 10, 15},
		{"default cargo", []string{"1", "", "l"}, 100000, 10000, 50, 15},
		{"cancel cargo", []string{"1", "0", "l"}, 100000, 10000, 10, 15},
		{"remove garrison", []string{"f", "0", "l"}, 100000, 10000, 10, 115},
		{"one credit", []string{"$", "1", "l"}, 99999, 10000, 10, 15},
		{"unavailable", []string{"n", "!", "l"}, 100000, 10000, 10, 15},
	} {
		t.Run(tc.name, func(t *testing.T) {
			s, id := planetSession(t)
			if err := s.Store.Update(func(w *game.World) error { w.Planets[2].Bank = 10000; return nil }); err != nil {
				t.Fatal(err)
			}
			if err := s.classicLand(id, &tc.commands); err != nil {
				t.Fatal(err)
			}
			w, _ := s.Store.View()
			p := w.Players[id]
			planet := w.Planets[2]
			if p.Credits != tc.cash || planet.Bank != tc.bank || p.Cargo[0] != tc.ore || p.Ground != tc.ground {
				t.Fatalf("wrong state %+v %+v", p, planet)
			}
			if tc.name == "remove garrison" && (planet.Owner != 0 || planet.Ground != 0) {
				t.Fatal("garrison release failed", planet)
			}
		})
	}
}

func TestPlanetCommittedActionSurvivesDisconnect(t *testing.T) {
	s, id := planetSession(t)
	s.Terminal = &scripted{lines: []string{"b", "1000"}}
	pending := []string{}
	if err := s.classicLand(id, &pending); !errors.Is(err, io.EOF) {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	if w.Players[id].Credits != 99000 || w.Planets[2].Bank != 1000 {
		t.Fatal("completed action lost on disconnect")
	}
}

func TestPlanetLeavePreservesNewLanding(t *testing.T) {
	s, id := planetSession(t)
	term := &portInput{scripted: scripted{lines: []string{"l"}}, beforeRead: func() {
		if err := s.Store.Update(func(w *game.World) error { return w.Land(id, s.Now()) }); err != nil {
			t.Fatal(err)
		}
	}}
	s.Terminal = term
	pending := []string{}
	if err := s.classicLand(id, &pending); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	if w.Players[id].PlanetToken == "" {
		t.Fatal("cleared the replacement session")
	}
}

func TestPlanetReportLegacyDisplayDoesNotChangeMoney(t *testing.T) {
	planet := game.Planet{Production: [3]float64{10, 20, 30}, Ground: 100, Bank: 10000}
	if got := planetRates(planet); got != [9]int64{11, 20, 30, 80, 0, 0, 99, 1, 0} {
		t.Fatal("DOS displayed production rates", got)
	}
	if planet.Bank != 10000 {
		t.Fatal("report modified spendable money")
	}
}
