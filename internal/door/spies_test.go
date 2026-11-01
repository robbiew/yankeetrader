package door

import (
	"errors"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"strings"
	"testing"
	"time"
)

func spyDoor(t *testing.T, term Terminal) (Session, store.Store) {
	t.Helper()
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		p, _ := w.Join("nav", "Navigator")
		p.Credits = 2000000
		w.Sectors[3].Warps = nil
		w.Sectors[3].Minefield = []game.MineLayer{{Count: 7}}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, st
}
func TestSpyCommandsHireReportHistoryAndReconnect(t *testing.T) {
	term := &scripted{lines: []string{"p;hire 3;spies;s;spies;m 2;spies;intel;q"}}
	s, st := spyDoor(t, term)
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	output := term.output.String()
	if strings.Count(output, "RADIO MESSAGE FROM SPY #1") != 2 || !strings.Contains(output, "SECTOR HAS 7 MINES") || strings.Count(output, "Spy # 1 will hunt in sector 3.") != 4 {
		t.Fatal(output)
	}
	w, _ := st.View()
	if p := w.Players[1]; p.Credits != 1667000 || p.Turns != 498 || p.Sector != 2 {
		t.Fatal(p)
	}
	if len(w.Radio) != 0 {
		t.Fatal("spy history mixed into durable radio")
	}
	term = &scripted{lines: []string{"spies;intel;q"}}
	s.Terminal = term
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(term.output.String(), "You do not have any spies!") || !strings.Contains(term.output.String(), "No intelligence reports this login.") {
		t.Fatal(term.output.String())
	}
}
func TestClassicEarthSpiesAndComputer15(t *testing.T) {
	term := &scripted{lines: []string{"", "", "", "p;9;1;3;0;c;15;1;m;2;c;15;1;q;y"}}
	s, st := spyDoor(t, term)
	s.Classic = true
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	output := term.output.String()
	if !strings.Contains(output, "Hire how many spies?") || !strings.Contains(output, "Start spy # 1 in what sector?") || strings.Count(output, "Spy # 1 will hunt in sector 3.") != 3 || strings.Count(output, "RADIO MESSAGE FROM SPY #1") != 1 {
		t.Fatal(output)
	}
	w, _ := st.View()
	if w.Players[1].Credits != 1667000 || w.Players[1].Turns != 498 {
		t.Fatal(w.Players[1])
	}
}

type failedSpyTerminal struct{ *scripted }

func (t *failedSpyTerminal) Printf(f string, args ...any) error {
	if strings.Contains(fmt.Sprintf(f, args...), "MINES") {
		return errors.New("output disconnected")
	}
	return t.scripted.Printf(f, args...)
}
func TestSpyOutputFailurePreservesUnreadAndStaleReadRejects(t *testing.T) {
	term := &failedSpyTerminal{&scripted{}}
	s, st := spyDoor(t, term)
	var token string
	if err := st.Update(func(w *game.World) error {
		if err := w.Dock(1, s.Now()); err != nil {
			return err
		}
		token = w.Players[1].DockToken
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	s.Store = st.ForShip(1, 0, 1)
	if err := s.Store.HireSpies(token, []int{3}, s.Now, s.Deadline); err != nil {
		t.Fatal(err)
	}
	if err := s.Store.UpdateWithSpies(func(w *game.World) error { return w.Move(1, 2) }, s.Now(), s.Deadline); err != nil {
		t.Fatal(err)
	}
	if err := s.intelligence(true); err == nil {
		t.Fatal("output failure ignored")
	}
	_, reports, _ := s.Store.SpySnapshot(true)
	if len(reports) != 1 {
		t.Fatal("failed output acknowledged")
	}
	replacement := &scripted{}
	s.Terminal = replacement
	if err := s.intelligence(true); err != nil {
		t.Fatal(err)
	}
	_, reports, _ = s.Store.SpySnapshot(true)
	if len(reports) != 0 {
		t.Fatal("successful output not acknowledged")
	}
	if err := st.Update(func(w *game.World) error { w.Players[1].ShipGeneration++; return nil }); err != nil {
		t.Fatal(err)
	}
	replacement.output.Reset()
	if err := s.intelligence(false); err == nil || replacement.output.Len() != 0 {
		t.Fatal("stale login read history")
	}
}
func TestExpiredSpyHireAfterPromptDoesNotCharge(t *testing.T) {
	s, st := spyDoor(t, &scripted{})
	var token string
	if err := st.Update(func(w *game.World) error {
		if err := w.Dock(1, s.Now()); err != nil {
			return err
		}
		token = w.Players[1].DockToken
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	s.Store = st.ForShip(1, 0, 1)
	s.Deadline = time.Now().Add(-time.Second)
	pending := []string{"1", "3"}
	if err := s.hireSpies(token, nil, &pending); err == nil {
		t.Fatal("expired purchase accepted")
	}
	w, _ := st.View()
	locations, _, _ := s.Store.SpySnapshot(false)
	if w.Players[1].Credits != 2000000 || len(locations) != 0 {
		t.Fatal("expired prompt charged account")
	}
}

func TestIntelligencePagingAcknowledgesOnlyDisplayedReports(t *testing.T) {
	term := &scripted{lines: []string{"q"}}
	s, st := spyDoor(t, term)
	var token string
	if err := st.Update(func(w *game.World) error {
		w.Sectors[3].Warps = []int{8}
		w.Sectors[8].Warps = []int{3}
		w.Sectors[8].Minefield = []game.MineLayer{{Count: 9}}
		if err := w.Dock(1, s.Now()); err != nil {
			return err
		}
		token = w.Players[1].DockToken
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	s.Store = st.ForShip(1, 0, 1)
	if err := s.Store.HireSpies(token, []int{3, 8}, s.Now, s.Deadline); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 5; i++ {
		if err := s.Store.UpdateWithSpies(func(w *game.World) error { return w.Dock(1, s.Now()) }, s.Now(), s.Deadline); err != nil {
			t.Fatal(err)
		}
	}
	if err := s.intelligence(false); err != nil {
		t.Fatal(err)
	}
	_, unread, err := s.Store.SpySnapshot(true)
	if err != nil || len(unread) != 5 || strings.Count(term.output.String(), "RADIO MESSAGE FROM SPY") != 5 {
		t.Fatal("page acknowledged undisplayed reports", len(unread), err)
	}
}

func TestSpyShipIntelligenceOutput(t *testing.T) {
	term := &scripted{lines: []string{"p;hire 3;m 2;intel;q"}}
	s, st := spyDoor(t, term)
	if err := st.Update(func(w *game.World) error {
		p, e := w.Join("enemy-private-identity", "Enemy")
		if e != nil {
			return e
		}
		p.Sector = 3
		p.Cloak = 0
		p.Fighters = 42
		p.Shields = 10
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	out := term.output.String()
	if strings.Count(out, "Enemy - Team: 0 - Fighters: 42 - Shields: 10") != 2 || strings.Contains(out, "enemy-private-identity") {
		t.Fatal(out)
	}
}
