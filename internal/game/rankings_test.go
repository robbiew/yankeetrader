package game

import (
	"encoding/json"
	"os"
	"strings"
	"testing"
)

func rankRow(t *testing.T, r Rankings, id int) PlayerRank {
	t.Helper()
	for _, row := range r.Players {
		if row.ID == id {
			return row
		}
	}
	t.Fatal("missing row")
	return PlayerRank{}
}

func TestRankingsRecoveredDOSWeights(t *testing.T) {
	data, err := os.ReadFile("../../research/yt-rankings/expected.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixtures map[string]struct {
		Score   int64
		Patches [][3]int64
	}
	if err = json.Unmarshal(data, &fixtures); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"baseline", "shields", "fighters", "holds-eleven", "holds-twenty", "ore", "organics", "equipment", "credits", "missiles", "plasma", "ground", "cloak", "mines", "stored-score", "field101", "field105", "zero-score"} {
		t.Run(name, func(t *testing.T) {
			w, caller := setup(t)
			p, _ := w.Join("private:target", "Enemy")
			p.Shields, p.Fighters, p.Holds, p.Credits, p.Missiles, p.Cloak = 0, 0, 10, 1000, 0, 0
			for _, patch := range fixtures[name].Patches {
				var field *int64
				switch patch[1] {
				case 53:
					field = &p.Shields
				case 61:
					field = &p.Fighters
				case 65:
					field = &p.Holds
				case 69:
					field = &p.Cargo[0]
				case 73:
					field = &p.Cargo[1]
				case 77:
					field = &p.Cargo[2]
				case 81:
					field = &p.Credits
				case 97:
					field = &p.Missiles
				case 109:
					field = &p.StoredScore
				case 113:
					field = &p.Plasma
				case 121:
					field = &p.Ground
				case 125:
					p.Cloak = float64(patch[2])
				case 129:
					field = &p.Mines
				}
				if field != nil {
					*field = patch[2]
				}
			}
			before, _ := json.Marshal(w)
			report, err := w.PlayerRankings(caller.ID, false)
			if err != nil || rankRow(t, report, p.ID).Score != fixtures[name].Score {
				t.Fatal(name, report, err)
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("query changed world")
			}
			public, _ := json.Marshal(report)
			if strings.Contains(string(public), "private:") || strings.Contains(string(public), "Password") {
				t.Fatal("private account exposed")
			}
		})
	}
}

func TestRankingsOwnershipTeamsDeadAndCaches(t *testing.T) {
	w, a := setup(t)
	b, _ := w.Join("b", "Enemy")
	c, _ := w.Join("c", "Third")
	a.StoredScore = 777
	b.StoredScore = -1
	c.StoredScore = 888
	a.Team, b.Team, c.Team = 1, 1, 2
	w.Teams[1] = &Team{ID: 1, Name: "Orion"}
	w.Teams[2] = &Team{ID: 2, Name: "Other"}
	w.Ports[2].Owner = b.ID
	w.Sectors[3].Defense = &SectorDefense{Owner: b.ID, Fighters: 100}
	b.Death = &Death{}
	before, _ := json.Marshal(w)
	report, err := w.PlayerRankings(a.ID, true)
	if err != nil {
		t.Fatal(err)
	}
	if rankRow(t, report, b.ID).Score != 0 || rankRow(t, report, a.ID).Score != 777 {
		t.Fatal("stored/dead scores", report)
	}
	if _, err := w.PlayerRankings(b.ID, false); err != ErrShipDestroyed {
		t.Fatal("dead caller", err)
	}
	b.Death = nil
	report, _ = w.PlayerRankings(a.ID, false)
	base := rankRow(t, report, a.ID).Score
	if rankRow(t, report, b.ID).Score != base+60000 || rankRow(t, report, b.ID).Ports != 1 {
		t.Fatal("current title/defense not counted", report)
	}
	w.Ports[2].Owner = a.ID
	w.Sectors[3].Defense.Owner = a.ID
	b.Team = 2
	report, err = w.RefreshRankings(a.ID)
	if err != nil {
		t.Fatal(err)
	}
	if rankRow(t, report, a.ID).Score != base+60000 || rankRow(t, report, b.ID).Score != base {
		t.Fatal("stale titles", report)
	}
	for _, row := range report.Players {
		if w.Players[row.ID].StoredScore != row.Score {
			t.Fatal("cache mismatch")
		}
	}
	for _, team := range report.Teams {
		want := base + 60000
		if team.ID == 2 {
			want = 2 * base
		}
		if team.Score != want {
			t.Fatal("membership total", team, want)
		}
	}
	// Restore intentional test changes and caches; publishing changes nothing else.
	w.Ports[2].Owner = b.ID
	w.Sectors[3].Defense.Owner = b.ID
	b.Team = 1
	b.Death = &Death{}
	a.StoredScore, b.StoredScore, c.StoredScore = 777, -1, 888
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("ranking changed assets")
	}
}

func TestRankingsBoundsTiesAndZero(t *testing.T) {
	w, a := setup(t)
	b, _ := w.Join("b", "Enemy")
	a.StoredScore, b.StoredScore = 0, 0
	r, _ := w.PlayerRankings(a.ID, true)
	if r.Players[0].ID != a.ID || r.Players[0].Percent != "0.00%" || r.Players[1].Percent != "0.00%" {
		t.Fatal(r)
	}
	a.StoredScore, b.StoredScore = -2, -1
	r, _ = w.PlayerRankings(a.ID, true)
	if r.Players[0].ID != b.ID || r.Players[1].Percent != "0.00%" {
		t.Fatal(r)
	}
	a.Credits = MaxMoney
	a.Plasma = MaxQuantity
	r, err := w.RefreshRankings(a.ID)
	if err != nil || rankRow(t, r, a.ID).Score != MaxMoney || a.StoredScore != MaxMoney {
		t.Fatal("score cap", r, err)
	}
	if rankPercent(MaxMoney-1, MaxMoney) != "99.99%" || rankPercent(MaxMoney, MaxMoney) != "100.00%" {
		t.Fatal("percentage overflow")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestRankingsPublishedCacheSizesMissileRetaliation(t *testing.T) {
	w, p := setup(t)
	p.Plasma = 3
	p.StoredScore = 0
	if _, err := w.RefreshRankings(p.ID); err != nil {
		t.Fatal(err)
	}
	volley, err := RetaliationVolley(p.StoredScore, 100, func() float64 { return 0 })
	if err != nil || volley != 31 {
		t.Fatal("retaliation did not use published real score", p.StoredScore, volley, err)
	}
}

func TestRankingsTeamPercentBeyondIndividualSaveBound(t *testing.T) {
	w, p := setup(t)
	w.Teams[1] = &Team{ID: 1, Name: "Large"}
	w.Teams[2] = &Team{ID: 2, Name: "Small"}
	p.Team = 1
	p.StoredScore = MaxMoney
	for i := 0; i < 4; i++ {
		other, err := w.Join("member"+string(rune('a'+i)), "Player"+string(rune('a'+i)))
		if err != nil {
			t.Fatal(err)
		}
		other.StoredScore = MaxMoney
		other.Team = 1
		if i == 3 {
			other.Team = 2
		}
	}
	r, err := w.PlayerRankings(p.ID, true)
	if err != nil || len(r.Teams) != 2 || r.Teams[0].Score != 4*MaxMoney || r.Teams[0].Percent != "100.00%" || r.Teams[1].Percent != "25.00%" {
		t.Fatal("team aggregate/percentage overflow", r, err)
	}
}
