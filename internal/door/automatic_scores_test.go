package door

import (
	"errors"
	"fmt"
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestCleanLogoutScoreBoundaries(t *testing.T) {
	for _, mode := range []string{"compact-quit", "compact-disconnect", "classic-confirm", "classic-decline", "classic-disconnect"} {
		t.Run(mode, func(t *testing.T) {
			lines := []string{"q"}
			classic := strings.HasPrefix(mode, "classic")
			switch mode {
			case "compact-disconnect":
				lines = []string{"rank old"}
			case "classic-confirm":
				lines = []string{"", "", "", "q;y"}
			case "classic-decline":
				lines = []string{"", "", "", "q;n"}
			case "classic-disconnect":
				lines = []string{"", "", "", "q"}
			}
			term := &scripted{lines: lines}
			s, st := radioSession(t, term)
			s.Classic = classic
			if err := st.Update(func(w *game.World) error { w.Players[1].StoredScore = 777; return nil }); err != nil {
				t.Fatal(err)
			}
			w, _ := st.View()
			fresh, _ := w.PlayerRankings(1, false)
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ = st.View()
			want := int64(777)
			if mode == "compact-quit" || mode == "classic-confirm" {
				for _, r := range fresh.Players {
					if r.ID == 1 {
						want = r.Score
					}
				}
			}
			if w.Players[1].StoredScore != want {
				t.Fatal("wrong logout publication boundary", mode, w.Players[1].StoredScore, want)
			}
			if w.Players[1].Turns != 500 || w.Players[1].Credits != 1005 {
				t.Fatal("logout spent resources")
			}
		})
	}
}

type logoutOutputFailure struct{ *scripted }

func (t *logoutOutputFailure) Printf(format string, args ...any) error {
	if strings.Contains(fmt.Sprintf(format, args...), "Saved. Safe travels") {
		return errors.New("output disconnected after save")
	}
	return t.scripted.Printf(format, args...)
}
func TestLogoutOutputFailureRetainsCommittedScore(t *testing.T) {
	term := &logoutOutputFailure{&scripted{lines: []string{"q"}}}
	s, st := radioSession(t, term)
	if err := s.Run(); err == nil {
		t.Fatal("output failure ignored")
	}
	w, _ := st.View()
	report, _ := w.PlayerRankings(1, false)
	for _, row := range report.Players {
		if w.Players[row.ID].StoredScore != row.Score {
			t.Fatal("successful save lost after output failure")
		}
	}
}
