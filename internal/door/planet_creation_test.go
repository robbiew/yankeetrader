package door

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"io"
	"strings"
	"testing"
)

func TestPlanetCreationClassicNameRetryAndAbort(t *testing.T) {
	for _, mode := range []string{"accept", "decline", "reject-name"} {
		t.Run(mode, func(t *testing.T) {
			s, id := planetSession(t)
			if err := s.Store.Update(func(w *game.World) error { w.Players[id].Sector = 8; return nil }); err != nil {
				t.Fatal(err)
			}
			input := []string{"y", "Rejected", "n", "Accepted", "y"}
			if mode == "decline" {
				input = []string{"n"}
			}
			if mode == "reject-name" {
				input = []string{"y", "Rejected", "n"}
			}
			err := s.classicCreate(id, &input, 100000, 8)
			if mode != "reject-name" && err != nil {
				t.Fatal(err)
			}
			w, _ := s.Store.View()
			if mode == "accept" {
				if len(w.News) != 1 || w.News[0].PlanetName != "Accepted" || w.Players[id].Credits != 75000 {
					t.Fatal(w.News)
				}
			} else if len(w.News) != 0 || w.Players[id].Credits != 100000 {
				t.Fatal("cancel published")
			}
		})
	}
}
func TestPlanetCreationReceiptRetainsCommittedWarning(t *testing.T) {
	for _, classic := range []bool{false, true} {
		s, _ := planetSession(t)
		s.Terminal = &failedCreationReceipt{scripted: &scripted{}}
		warning := &store.DurabilityError{Err: errors.New("directory sync failed")}
		err := s.planetCreationReceipt(warning, "Saved", classic)
		var got *store.DurabilityError
		if !errors.As(err, &got) || !errors.Is(err, io.EOF) {
			t.Fatal(err)
		}
	}
}
func TestPlanetCreationNewsRendersLiteralSnapshot(t *testing.T) {
	s, id := planetSession(t)
	if err := s.Store.Update(func(w *game.World) error {
		w.Players[id].Sector = 8
		return w.CreatePlanet(id, "Literal; planet/", s.Now())
	}); err != nil {
		t.Fatal(err)
	}
	for _, classic := range []bool{false, true} {
		s.Classic = classic
		s.Terminal = &scripted{}
		if err := s.newspaper(id, []string{"today"}, &[]string{}); err != nil {
			t.Fatal(err)
		}
		text := s.Terminal.(*scripted).output.String()
		if !strings.Contains(text, "  -  Trader made a planet: Literal; planet/\r\n") || strings.Contains(text, "25000") || strings.Contains(text, "Sector") {
			t.Fatal(text)
		}
	}
}

type failedCreationReceipt struct{ *scripted }

func (t *failedCreationReceipt) Printf(string, ...any) error { return io.EOF }
