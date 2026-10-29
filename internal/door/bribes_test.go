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

func bribeSession(t *testing.T, terminal Terminal) (Session, store.Store) {
	t.Helper()
	s, st := navigationSession(t, terminal)
	if err := st.Update(func(w *game.World) error {
		p, e := w.Join("nav", "Navigator")
		if e != nil {
			return e
		}
		p.Sector = 8
		p.Credits = 10000
		p.Fighters = 1000
		w.Sectors[8].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 100}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, st
}

func TestBribeRejectsStackedConfirmationsAndMalformedOffers(t *testing.T) {
	for _, lines := range [][]string{
		{"bribe 300;y", "n", "q"}, {"bribe 300", "y;q", "q"}, {"bribe 300", "y/", "q"},
		{"bribe", "", "q"}, {"bribe 0;bribe -1;bribe 1.5;bribe abc;bribe 10001;q"},
		{"bribe 300"},
	} {
		term := &scripted{lines: lines}
		s, st := bribeSession(t, term)
		if err := s.Run(); err != nil && !errors.Is(err, io.EOF) {
			t.Fatal(err)
		}
		w, _ := st.View()
		if w.Players[1].Credits != 10000 || w.Players[1].Fighters != 1000 || w.Sectors[8].Defense.Fighters != 100 {
			t.Fatal("unconfirmed bribe changed resources", term.output.String())
		}
	}
}

type bribeTerminal struct {
	*scripted
	before func() error
}

func (t *bribeTerminal) Printf(f string, args ...any) error {
	if strings.HasPrefix(f, "Attempt bribery") && t.before != nil {
		if err := t.before(); err != nil {
			return err
		}
		t.before = nil
	}
	return t.scripted.Printf(f, args...)
}
func TestBribeConfirmationRechecksAuthoritativeWorldAndDeadline(t *testing.T) {
	for _, expire := range []bool{false, true} {
		term := &bribeTerminal{scripted: &scripted{lines: []string{"bribe 300", "y", "q"}}}
		s, st := bribeSession(t, term)
		expected := int64(101)
		if expire {
			s.Deadline = time.Now().Add(500 * time.Millisecond)
			expected = 100
		}
		term.before = func() error {
			if expire {
				time.Sleep(time.Until(s.Deadline) + 20*time.Millisecond)
				return nil
			}
			return st.Update(func(w *game.World) error { w.Sectors[8].Defense.Fighters++; return nil })
		}
		err := s.Run()
		if err != nil && !expire {
			t.Fatal(err)
		}
		w, _ := st.View()
		if w.Players[1].Credits != 10000 || w.Sectors[8].Defense.Fighters != expected || strings.Contains(term.output.String(), "Bribe saved:") {
			t.Fatal("stale or expired confirmation committed", term.output.String())
		}
		if !expire && !strings.Contains(term.output.String(), "confirm again") {
			t.Fatal(term.output.String())
		}
	}
}

func TestClassicBPreservesAcquisitionOutsideEncounter(t *testing.T) {
	// During a hostile encounter B becomes BRIBE; blank cancels before randomness.
	term := &scripted{lines: []string{"", "", "", "b", "", "q;y"}}
	s, st := bribeSession(t, term)
	s.Classic = true
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Credits != 10000 || !strings.Contains(term.output.String(), "Bribe cancelled.") {
		t.Fatal(term.output.String())
	}
	// Existing port-ownership tests cover ordinary B acquisition, which retains
	// its original dispatcher branch whenever there is no current hostile group.
}
