package door

import (
	"errors"
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestRankingsCommandsPublishAndReadStoredScores(t *testing.T) {
	for _, mode := range []string{"compact", "old", "classic", "classic-old"} {
		t.Run(mode, func(t *testing.T) {
			lines := []string{"rank;q"}
			if mode == "old" {
				lines = []string{"rank old;q"}
			}
			classic := strings.HasPrefix(mode, "classic")
			if classic {
				command := "c;4;;1;q;y"
				if mode == "classic-old" {
					command = "c;4;o;1;q;y"
				}
				lines = []string{"", "", "", command}
			}
			term := &scripted{lines: lines}
			s, st := radioSession(t, term)
			s.Classic = classic
			if err := st.Update(func(w *game.World) error {
				w.Players[1].StoredScore = 777
				w.Players[2].StoredScore = 888
				w.Players[3].StoredScore = 999
				return nil
			}); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			expected, _ := w.PlayerRankings(1, false)
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ = st.View()
			old := strings.HasSuffix(mode, "old")
			if !strings.Contains(term.output.String(), "Player Rankings") || !strings.Contains(term.output.String(), "Team Rankings") {
				t.Fatal(term.output.String())
			}
			if old && (!strings.Contains(term.output.String(), "Stored scores;") || !strings.Contains(term.output.String(), "777")) {
				t.Fatal("old view did not use stored score")
			}
			// Both updated and OLD sessions publish current scores on clean quit.
			for _, row := range expected.Players {
				if w.Players[row.ID].StoredScore != row.Score {
					t.Fatal("logout refresh was not saved")
				}
			}

			if w.Players[1].Turns != 500 || w.Players[1].Credits != 1005 {
				t.Fatal("rankings spent resources")
			}
		})
	}
}

func TestRankingsPagingStopsForInvalidatedSession(t *testing.T) {
	term := &radioReadTerminal{scripted: &scripted{lines: []string{""}}}
	s, st := navigationSession(t, term)
	if err := st.Update(func(w *game.World) error {
		for i := 0; i < 15; i++ {
			if _, err := w.Join(fmt.Sprint(i), fmt.Sprintf("Caller%02d", i)); err != nil {
				return err
			}
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	s.Store = st.ForShip(1, w.Players[1].ShipGeneration)
	term.beforeRead = func(n int) error {
		return st.Update(func(w *game.World) error {
			return w.RecordDeath(game.DeathContext{Victim: 1, Generation: w.Players[1].ShipGeneration, Sector: w.Players[1].Sector, Cause: "hazard"}, s.Now())
		})
	}
	pending := []string{"q"}
	if err := s.rankings(1, nil, &pending); !errors.Is(err, game.ErrShipDestroyed) && !errors.Is(err, game.ErrShipChanged) {
		t.Fatal("invalidated session continued", err)
	}
	if len(pending) != 1 || strings.Contains(term.output.String(), "Caller14") {
		t.Fatal("paging consumed commands or disclosed a later page")
	}
}

func TestRankingsExpiredSessionCannotPublish(t *testing.T) {
	s, st := radioSession(t, &scripted{})
	w, _ := st.View()
	s.Store = st.ForShip(1, w.Players[1].ShipGeneration)
	s.Deadline = time.Now().Add(-time.Second)
	pending := []string{}
	if err := s.rankings(1, nil, &pending); err == nil {
		t.Fatal("expired refresh")
	}
	w, _ = st.View()
	if w.Players[1].StoredScore != 0 {
		t.Fatal("expired refresh persisted")
	}
}
