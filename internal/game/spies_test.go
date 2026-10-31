package game

import (
	"encoding/json"
	"math"
	"os"
	"reflect"
	"strings"
	"testing"
	"time"
)

func spyWorld(t *testing.T) (*World, *Player, *SpyNetwork) {
	t.Helper()
	w, p := navigationWorld(t)
	p.Sector = 1
	p.Credits = 2000000
	w.Sectors[1].Warps = []int{100}
	w.Sectors[100].Warps = []int{1}
	w.Sectors[101].Warps = []int{102}
	w.Sectors[102].Warps = []int{101}
	if err := w.Dock(p.ID, w.Created); err != nil {
		t.Fatal(err)
	}
	return w, p, NewSpyNetwork(p.ID, p.ShipGeneration, 1)
}
func TestSpiesMatchDOSSupportedCases(t *testing.T) {
	raw, err := os.ReadFile("../../research/yt-spies/expected.json")
	if err != nil {
		t.Fatal(err)
	}
	var cases map[string]struct {
		Locations []int
		Reports   int
		Turns     int64
	}
	if err = json.Unmarshal(raw, &cases); err != nil {
		t.Fatal(err)
	}
	for name, gold := range cases {
		t.Run(name, func(t *testing.T) {
			w, p, n := spyWorld(t)
			switch name {
			case "populated":
				w.Sectors[101].Minefield = []MineLayer{{Count: 7}}
				w.Sectors[101].Planet = 2
				w.Planets[2] = &Planet{Generation: uint64(2), ID: 2, Sector: 101, Name: "Test Planet", Ground: 12, Updated: w.Created, Bank: 12345, Cargo: [3]float64{1, 2, 3}, Fighters: 1000}
			case "defenders":
				enemy, _ := w.Join("enemy", "Enemy")
				w.Sectors[101].Defense = &SectorDefense{Owner: enemy.ID, Fighters: 42}
			case "same-sector":
				// Original self-loops are not valid Go worlds; model the equivalent
				// unchanged hunt location using the explicit zero-warp safety policy.
				w.Sectors[101].Warps = nil
				w.Sectors[101].Minefield = []MineLayer{{Count: 7}}
			case "cloak":
				enemy, _ := w.Join("enemy", "Enemy")
				enemy.Sector = 101
				enemy.Cloak = 1
			}
			if err := n.Hire(w, p.DockToken, []int{101}, w.Created); err != nil {
				t.Fatal(err)
			}
			locations := []int{101}
			for i := 0; i < 2; i++ {
				if name != "list-only" && name != "status" {
					to := 100
					if i == 1 {
						to = 1
					}
					if err := w.Move(p.ID, to); err != nil {
						t.Fatal(err)
					}
					before, _ := json.Marshal(w)
					if err := n.Advance(w, w.Created, func() float64 { return 0 }); err != nil {
						t.Fatal(err)
					}
					after, _ := json.Marshal(w)
					if string(before) != string(after) {
						t.Fatal("intelligence mutated world")
					}
				} else if name == "status" {
					if _, err := w.Scan(p.ID); err != nil {
						t.Fatal(err)
					}
				}
				positions, _ := n.Locations(w)
				locations = append(locations, positions[0])
			}
			reports, _ := n.Reports(w, false)
			if !reflect.DeepEqual(locations, gold.Locations) || len(reports) != gold.Reports || p.Turns != gold.Turns || p.Credits != 1667000 {
				t.Fatalf("locations %v reports %+v player %+v", locations, reports, p)
			}
			if name == "populated" && (reports[0].Mines != 7 || reports[0].Planet != "Test Planet" || reports[0].Ground != 12) {
				t.Fatal(reports)
			}
			if name == "defenders" && (reports[0].DefenseFighters != 42 || reports[0].DefenseOwner != "Enemy") {
				t.Fatal(reports)
			}
		})
	}
}
func TestSpyHireRejectsAtomically(t *testing.T) {
	for _, mode := range []string{"invalid-sector", "zero", "four", "funds", "stale-token", "expired-dock", "wrong-port", "generation", "death", "bad-time", "cap"} {
		t.Run(mode, func(t *testing.T) {
			w, p, n := spyWorld(t)
			sectors := []int{101, 102}
			token := p.DockToken
			now := w.Created
			switch mode {
			case "invalid-sector":
				sectors = []int{101, 9999}
			case "zero":
				sectors = nil
			case "four":
				sectors = []int{1, 2, 3, 4}
			case "funds":
				p.Credits = SpyPrice
			case "stale-token":
				token = "stale"
			case "expired-dock":
				now = p.DockUntil
			case "wrong-port":
				p.Sector = 2
			case "generation":
				p.ShipGeneration++
			case "death":
				p.Death = &Death{}
			case "bad-time":
				now = time.Time{}
			case "cap":
				if err := n.Hire(w, token, []int{1, 2}, now); err != nil {
					t.Fatal(err)
				}
			}
			before, _ := json.Marshal(w)
			state := n.Clone()
			if err := n.Hire(w, token, sectors, now); err == nil {
				t.Fatal("invalid hire accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) || !reflect.DeepEqual(state, n) {
				t.Fatal("failed hire changed state")
			}
		})
	}
}
func TestSpyStagingVisibilityAndBoundedHistory(t *testing.T) {
	w, p, n := spyWorld(t)
	if err := n.Hire(w, p.DockToken, []int{101, 102}, w.Created); err != nil {
		t.Fatal(err)
	}
	w.Sectors[101].Minefield = []MineLayer{{Count: 7}}
	w.Sectors[102].Defense = &SectorDefense{Owner: p.ID, Fighters: 30}
	before := n.Clone()
	calls := 0
	if err := n.Advance(w, w.Created, func() float64 {
		calls++
		if calls == 2 {
			return math.NaN()
		}
		return 0
	}); err == nil || !reflect.DeepEqual(before, n) {
		t.Fatal("partial RNG failure changed network")
	}
	for i := 0; i < 40; i++ {
		if err := n.Advance(w, w.Created, func() float64 { return 0 }); err != nil {
			t.Fatal(err)
		}
	}
	reports, _ := n.Reports(w, false)
	// Only one finding sector means revisits are suppressed, even after empty searches.
	if len(reports) != 2 {
		t.Fatal(reports)
	}
	if err := n.Acknowledge(w, reports[0].ID); err != nil {
		t.Fatal(err)
	}
	unread, _ := n.Reports(w, true)
	if len(unread) != 1 {
		t.Fatal(unread)
	}
	// Findings in both sectors replace last-reported locations and grow history.
	w.Sectors[102].Defense.Owner = XannorOwner
	for i := 0; i < 40; i++ {
		if err := n.Advance(w, w.Created, func() float64 { return 0 }); err != nil {
			t.Fatal(err)
		}
	}
	reports, _ = n.Reports(w, false)
	if len(reports) != SpyHistoryLimit || reports[0].ID <= 2 {
		t.Fatal("history not bounded")
	}
	reports[0].Planet = "tampered"
	locations, _ := n.Locations(w)
	locations[0] = 999
	again, _ := n.Reports(w, false)
	positions, _ := n.Locations(w)
	if again[0].Planet == "tampered" || positions[0] == 999 {
		t.Fatal("snapshot aliases private state")
	}
	p.ShipGeneration++
	if _, err := n.Reports(w, false); err == nil {
		t.Fatal("stale ship read intelligence")
	}
	if _, err := n.Locations(w); err == nil {
		t.Fatal("stale ship read spies")
	}
}

func TestSpyPlanetProjectionAndForeignOwnerLabels(t *testing.T) {
	w, p, n := spyWorld(t)
	enemy, _ := w.Join("enemy-private-account", "Enemy")
	enemy.Team = 1
	w.Teams[1] = &Team{ID: 1, Name: "Orion", PasswordHash: "secret"}
	w.Sectors[101].Planet = 2
	w.Planets[2] = &Planet{Generation: uint64(2), ID: 2, Sector: 101, Name: "Private Planet", Owner: enemy.ID, Updated: w.Created, Ground: 100, Bank: 10000, Fighters: 123456, Missiles: 9876}
	w.Sectors[101].Defense = &SectorDefense{Owner: enemy.ID, Fighters: 42}
	if err := n.Hire(w, p.DockToken, []int{101}, w.Created); err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(w)
	if err := n.Advance(w, w.Created.Add(24*time.Hour), func() float64 { return 0 }); err != nil {
		t.Fatal(err)
	}
	reports, _ := n.Reports(w, false)
	if len(reports) != 1 || reports[0].Ground != 102 || reports[0].DefenseOwner != "Enemy * Team: Orion" {
		t.Fatal(reports)
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("spy projection changed remote planet")
	}
	encoded, _ := json.Marshal(reports)
	for _, private := range []string{"Bank", "Missiles", "PasswordHash", "Identity", "enemy-private-account", "123456", "9876", "secret"} {
		if strings.Contains(string(encoded), private) {
			t.Fatal("private data in spy projection", string(encoded))
		}
	}
	for _, owner := range []int{MercenaryOwner, XannorOwner} {
		other := NewSpyNetwork(p.ID, p.ShipGeneration, 1)
		if err := other.Hire(w, p.DockToken, []int{101}, w.Created); err != nil {
			t.Fatal(err)
		}
		w.Sectors[101].Defense.Owner = owner
		if err := other.Advance(w, w.Created, func() float64 { return 0 }); err != nil {
			t.Fatal(err)
		}
		report, _ := other.Reports(w, false)
		if report[0].DefenseOwner != map[int]string{MercenaryOwner: "Mercenaries", XannorOwner: "The Xannor"}[owner] {
			t.Fatal(report)
		}
	}
}
