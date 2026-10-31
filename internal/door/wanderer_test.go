package door

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"io"
	"strings"
	"testing"
)

func TestWandererFreshConfirmationAndHiddenReceipt(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, answer := range []string{"y", "Y", "n", "", "y;q", "disconnect"} {
			term := &scripted{lines: []string{answer}}
			s, id, _ := mobilitySession(t, term)
			s.Classic = classic
			if answer == "disconnect" {
				term.lines = nil
			}
			err := s.Store.Update(func(w *game.World) error {
				p := w.Planets[2]
				delete(w.Planets, 2)
				p.ID = 1
				p.Wanderer = true
				w.Planets[1] = p
				w.Sectors[2].Planet = 1
				w.Players[id].PlanetToken = ""
				w.Players[id].LandedPlanet = 0
				return w.Land(id, s.Now())
			})
			if err != nil {
				t.Fatal(err)
			}
			w, _ := s.Store.View()
			pending := []string{"y", "q"}
			calls := 0
			err = s.thrustersWithRandom(w.Players[id].PlanetToken, []string{"3"}, &pending, func() float64 {
				calls++
				if calls == 1 {
					return 0
				}
				return .999
			})
			w, e := s.Store.View()
			if e != nil {
				t.Fatal(e)
			}
			text := term.output.String()
			yes := strings.EqualFold(answer, "y")
			if !strings.Contains(text, "full route budget") || !strings.Contains(text, "random destination is hidden") || len(pending) != 0 {
				t.Fatal(text, pending)
			}
			if !yes {
				if calls != 0 || w.Players[id].Turns != 500 || w.Planets[1].Sector != 2 || strings.Contains(text, "thrusters saved:") || answer == "disconnect" && !errors.Is(err, io.EOF) {
					t.Fatal(answer, text, err)
				}
				continue
			}
			if err != nil || w.Planets[1].Sector != 8 || w.Players[id].Sector != 3 || w.Players[id].Turns != 490 || strings.Count(text, "Planet thrusters saved:") != 1 || !strings.Contains(text, "planet location unknown") || strings.Contains(text, "planet sector 8") || strings.Contains(text, "-> 8") || strings.Contains(text, "Planet destroyed:") {
				t.Fatal(text, err)
			}
		}
	}
}
func TestWandererReceiptKeepsCommittedWarningOnOutputFailure(t *testing.T) {
	warning := &store.DurabilityError{Err: errors.New("sync")}
	out := game.PlanetReceipt{Kind: "thrusters", Vanished: true, Name: "The Wanderer", From: 8, FinalSector: 9, Destination: 10, PlanetSector: 2345, TransportTurns: 10, Hops: 1}
	term := &scripted{}
	s := Session{Terminal: term}
	if err := s.planetActionReceipt(out, warning); !errors.Is(err, warning) || !strings.Contains(term.output.String(), "planet location unknown") || strings.Contains(term.output.String(), "2345") {
		t.Fatal(term.output.String(), err)
	}
	for _, failure := range []error{io.EOF, io.ErrClosedPipe, errors.New("output failure")} {
		s.Terminal = &mobilityOutputFailure{failure: failure}
		if err := s.planetActionReceipt(out, warning); !errors.Is(err, warning) || !errors.Is(err, failure) {
			t.Fatal(err)
		}
	}
	term = &scripted{}
	s.Terminal = term
	abort := errors.New("abort")
	if err := s.planetActionReceipt(out, abort); err != abort || term.output.Len() != 0 {
		t.Fatal("aborted movement receipt", err)
	}
}
