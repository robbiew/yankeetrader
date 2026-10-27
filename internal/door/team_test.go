package door

import (
	"strings"
	"testing"
	"time"

	gd "github.com/robbiew/godoors"
	"github.com/robbiew/yankeetrader/internal/game"
)

func TestTeamMenuCreateReconnectAndQuit(t *testing.T) {
	for _, classic := range []bool{false, true} {
		t.Run(map[bool]string{false: "compact", true: "classic"}[classic], func(t *testing.T) {
			s, term := ownershipSession(t, nil)
			s.Classic = classic
			if classic {
				if err := s.Store.Update(func(w *game.World) error { w.Players[1].LastLogin = s.Now().UTC().Format("2006-01-02"); return nil }); err != nil {
					t.Fatal(err)
				}
				term.lines = []string{"", "", "", "t;2;Orion", "ABCD", "9;Traders;1;q;y"}
			} else {
				term.lines = []string{"team;2;Orion", "ABCD", "9;Traders;1;q"}
			}
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			w, err := s.Store.View()
			if err != nil || w.Teams[1].Name != "Traders" || w.Players[1].Team != 1 {
				t.Fatal(w, err, term.output.String())
			}
			if strings.Contains(term.output.String(), "ABCD") || strings.Contains(term.output.String(), "$2a$") {
				t.Fatal("team password leaked")
			}
			if classic {
				term.lines = []string{"", "", "", "t;4;y;1;q;y"}
			} else {
				term.lines = []string{"team;4;y;1;q"}
			}
			if err = s.Run(); err != nil {
				t.Fatal(err)
			}
			w, _ = s.Store.View()
			if len(w.Teams) != 0 || w.Players[1].Team != 0 || w.Players[1].Credits != 100000 {
				t.Fatal("leave not saved", w)
			}
		})
	}
}

func TestTeamMenuDisconnectDoesNotCreatePartialTeam(t *testing.T) {
	s, _ := ownershipSession(t, []string{"team;2;Orion"})
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	if len(w.Teams) != 0 || w.Players[1].Team != 0 {
		t.Fatal("partial team created before password")
	}
}

func TestTeamMenuRechecksCaptainAfterInput(t *testing.T) {
	s, term := ownershipSession(t, []string{"9", "Hijacked", "1"})
	if err := s.Store.Update(func(w *game.World) error { return w.CreateTeam(1, "Orion", "ABCD") }); err != nil {
		t.Fatal(err)
	}
	reads := 0
	s.Terminal = &ownershipChanged{term, func() {
		reads++
		if reads == 2 {
			if err := s.Store.Update(func(w *game.World) error { return w.LeaveTeam(1, 1) }); err != nil {
				t.Fatal(err)
			}
		}
	}}
	pending := []string{}
	if err := s.teamMenu(1, &pending); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	if len(w.Teams) != 0 || !strings.Contains(term.output.String(), "only the current team captain") {
		t.Fatal("stale captain authorized", term.output.String())
	}
}

func TestSecretInputDoesNotEnterCommandRepeatBuffer(t *testing.T) {
	keys := []inputKey{{r: 'A'}, {r: 'b'}, {r: 'C'}, {r: 'd'}, {k: gd.KeyEnter}}
	g := &GoDoors{commandMode: true, savedLine: "i", readKey: func(time.Duration) (rune, gd.Key, error) { k := keys[0]; keys = keys[1:]; return k.r, k.k, nil }}
	value, err := g.ReadSecret(time.Now().Add(time.Second))
	if err != nil || value != "AbCd" || g.savedLine != "i" {
		t.Fatal("password entered history", value, err, g.savedLine)
	}
}
