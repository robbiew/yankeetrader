package door

import (
	"encoding/json"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"strings"
	"testing"
	"time"
)

func TestNewspaperLoginClassicSelectionAndReconnect(t *testing.T) {
	term := &scripted{lines: []string{"news yesterday;news;q"}}
	s, st := navigationSession(t, term)
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if len(w.News) != 1 || w.News[0].Kind != game.NewsLogin || w.News[0].Alias != "Navigator" || w.NextNews != 2 {
		t.Fatal("compact login not recorded", w.News)
	}
	text := term.output.String()
	if !strings.Contains(text, "Galactic Newspaper - Yesterday") || !strings.Contains(text, "No news retained for this date.") || !strings.Contains(text, "Navigator  Logged on") {
		t.Fatal(text)
	}
	if w.Players[1].Turns != 500 || w.Players[1].Credits != 1005 {
		t.Fatal("newspaper spent resources")
	}
	s.Classic = true
	s.Terminal = &scripted{lines: []string{"", "", "", "c;8;x;y;8;t;1;q;y"}}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ = st.View()
	text = s.Terminal.(*scripted).output.String()
	if len(w.News) != 2 || w.NextNews != 3 || strings.Count(text, "Navigator  Logged on") != 2 || strings.Count(text, "Do you want to read [T]oday's or [Y]esterday's news?") != 3 {
		t.Fatal("classic selection/reconnect mismatch", text, w.News)
	}
}
func TestNewspaperTeamCreationRecordsPublicSnapshot(t *testing.T) {
	term := &scripted{lines: []string{"t;2;News Team", "ABCD", "1;news;q"}}
	s, st := navigationSession(t, term)
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if len(w.News) != 2 || w.News[1].Kind != game.NewsTeamCreated || w.News[1].TeamName != "News Team" {
		t.Fatal(w.News)
	}
	text := term.output.String()
	if !strings.Contains(text, "Navigator  Created Team 1 -=- News Team") {
		t.Fatal(text)
	}
	report, err := w.ReadNewspaper(1, s.Now(), false)
	if err != nil {
		t.Fatal(err)
	}
	encoded, _ := json.Marshal(report)
	if strings.Contains(string(encoded), "ABCD") || strings.Contains(string(encoded), w.Teams[1].PasswordHash) || strings.Contains(string(encoded), "nav\"") {
		t.Fatal("journal exposed private team/account fields", string(encoded))
	}
}
func TestNewspaperPagingStopsAndRechecksShip(t *testing.T) {
	for _, mode := range []string{"stop", "stale", "expiry", "output-failure"} {
		t.Run(mode, func(t *testing.T) {
			term := &radioReadTerminal{scripted: &scripted{lines: []string{"q"}}}
			s, st := navigationSession(t, term)
			if err := st.Update(func(w *game.World) error {
				_, _ = w.Join("nav", "Navigator")
				for i := 0; i < 8; i++ {
					if err := w.RecordLogin(1, s.Now()); err != nil {
						return err
					}
				}
				return nil
			}); err != nil {
				t.Fatal(err)
			}
			s.Store = st.ForShip(1, 0, 1)
			if mode == "stale" {
				term.lines = []string{""}
				term.beforeRead = func(int) error {
					return st.Update(func(w *game.World) error { w.Players[1].ShipGeneration++; return nil })
				}
			}
			if mode == "expiry" {
				s.Deadline = time.Now().Add(-time.Second)
			}
			if mode == "output-failure" {
				s.Terminal = &failNewsTerminal{term.scripted}
			}
			err := s.newspaper(1, []string{"today"}, &[]string{})
			if mode == "stop" {
				if err != nil || strings.Count(term.output.String(), "Navigator  Logged on") != 5 {
					t.Fatal("paging stop failed", err, term.output.String())
				}
			} else if err == nil {
				t.Fatal("stale/expired/disconnected read succeeded", mode)
			}
			if mode == "stale" && strings.Count(term.output.String(), "Navigator  Logged on") != 5 {
				t.Fatal("stale connection read another page")
			}
			w, _ := st.View()
			if len(w.News) != 8 || w.NextNews != 9 || w.Players[1].Turns != 500 {
				t.Fatal("reading changed archive/resources")
			}
		})
	}
}

type failNewsTerminal struct{ *scripted }

func (t *failNewsTerminal) Printf(f string, args ...any) error {
	if strings.Contains(f, "Logged on") {
		return errors.New("output disconnected")
	}
	return t.scripted.Printf(f, args...)
}
func TestExpiredAndAbortedLoginDoesNotPublishNews(t *testing.T) {
	term := &scripted{lines: []string{"q"}}
	s, st := navigationSession(t, term)
	s.Deadline = time.Now().Add(-time.Second)
	if err := s.Run(); err == nil {
		t.Fatal("expired login succeeded")
	}
	w, _ := st.View()
	if len(w.News) != 0 || len(w.Players) != 0 {
		t.Fatal("expired login wrote public history")
	}
	term = &scripted{}
	s, st = navigationSession(t, term)
	s.Classic = true
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ = st.View()
	if len(w.News) != 0 || len(w.Players) != 0 {
		t.Fatal("aborted registration wrote public history")
	}
}

func TestNewspaperPageLockWaitCannotOutliveSession(t *testing.T) {
	term := &radioReadTerminal{scripted: &scripted{lines: []string{""}}}
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		_, _ = w.Join("nav", "Navigator")
		for i := 0; i < 8; i++ {
			if err := w.RecordLogin(1, s.Now()); err != nil {
				return err
			}
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	s.Store = st.ForShip(1, 0, 1)
	s.Deadline = time.Now().Add(500 * time.Millisecond)
	holderDone := make(chan error, 1)
	term.beforeRead = func(int) error {
		held := make(chan struct{})
		release := make(chan struct{})
		go func() { holderDone <- st.Update(func(*game.World) error { close(held); <-release; return nil }) }()
		<-held
		go func() { time.Sleep(time.Until(s.Deadline) + 20*time.Millisecond); close(release) }()
		return nil
	}
	err := s.newspaper(1, []string{"today"}, &[]string{})
	select {
	case holderErr := <-holderDone:
		if holderErr != nil {
			t.Fatal(holderErr)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("page never reached lock contention")
	}
	if err == nil || !strings.Contains(err.Error(), "session time expired") || strings.Count(term.output.String(), "Navigator  Logged on") != 5 {
		t.Fatal("lock wait let an expired reader see another page", err, term.output.String())
	}
}

func TestDailyMaintenanceNewsRendersWithoutPrivateLocation(t *testing.T) {
	term := &scripted{}
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		_, _ = w.Join("nav", "Navigator")
		w.News = []game.NewsEvent{{ID: 1, At: s.Now().UTC(), Kind: game.NewsSuperPlanet, Alias: "Winner"}, {ID: 2, At: s.Now().UTC(), Kind: game.NewsRetirement, Alias: "Retired"}}
		w.NextNews = 3
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	s.Store = st.ForShip(1, 0, 1)
	if err := s.newspaper(1, []string{"today"}, &[]string{}); err != nil {
		t.Fatal(err)
	}
	text := term.output.String()
	if !strings.Contains(text, "Winner  Won a PLANET in the SUPER LOTTERY!") || !strings.Contains(text, "Retired  Retired after inactivity") || strings.Contains(text, "sector") {
		t.Fatal(text)
	}
}

func TestOvercrowdingNewsRendersActualEventsWithoutPrivateAssets(t *testing.T) {
	for _, classic := range []bool{false, true} {
		term := &scripted{}
		s, st := navigationSession(t, term)
		s.Classic = classic
		if err := st.Update(func(w *game.World) error {
			p, _ := w.Join("nav", "Navigator")
			p.Sector = 1
			now := s.Now()
			w.LastMaintenance = now.Add(-24 * time.Hour).UTC().Format("2006-01-02")
			port := w.Ports[1]
			port.Updated = now
			port.Production = [3]float64{2000000, 500, 500}
			w.Planets[2] = &game.Planet{ID: 2, Sector: 2, Owner: p.ID, Name: "Plague World", Updated: now, Production: [3]float64{2000000, 0, 0}, Bank: 12345}
			w.Planets[3] = &game.Planet{ID: 3, Sector: 3, Owner: p.ID, Name: "Civil World", Updated: now, Ground: 4000000, Bank: 12345}
			w.Sectors[2].Planet = 2
			w.Sectors[3].Planet = 3
			w.MaintainWithRandom(now, func() float64 { return .5 })
			return nil
		}); err != nil {
			t.Fatal(err)
		}
		s.Store = st.ForShip(1, 0, 1)
		if err := s.newspaper(1, []string{"today"}, &[]string{}); err != nil {
			t.Fatal(err)
		}
		text := term.output.String()
		for _, want := range []string{"Ports struck by plague: 1.", "Plague struck Plague World.", "Civil war erupted on Civil World."} {
			if !strings.Contains(text, want) {
				t.Fatal("missing event", want, text)
			}
		}
		for _, secret := range []string{"12345", "6172", "6173", "4000000", "sector", "nav", "credits", "ground"} {
			if strings.Contains(text, secret) {
				t.Fatal("private event data leaked", secret, text)
			}
		}
	}
}
