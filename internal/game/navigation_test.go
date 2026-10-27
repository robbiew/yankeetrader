package game

import (
	"encoding/json"
	"os"
	"reflect"
	"strings"
	"testing"
	"time"
)

func navigationWorld(t *testing.T) (*World, *Player) {
	t.Helper()
	w, err := New(time.Now(), 36, 111)
	if err != nil {
		t.Fatal(err)
	}
	for _, s := range w.Sectors {
		s.Warps = nil
	}
	for id, warps := range map[int][]int{100: {101, 102, 103, 104, 105, 106}, 101: {107}, 102: {108}, 103: {100}, 104: {100}, 105: {100}, 106: {100}, 107: {109}, 108: {109}, 109: {110}, 110: {100}} {
		w.Sectors[id].Warps = warps
	}
	p, err := w.Join("navigation:1", "Navigator")
	if err != nil {
		t.Fatal(err)
	}
	p.Sector = 100
	return w, p
}

func TestSensorsLocalPublicAndFree(t *testing.T) {
	w, p := navigationWorld(t)
	p.Turns = 0
	other, _ := w.Join("secret-identity", "Visitor")
	other.Sector, other.Fighters, other.Shields = 103, 42, 7
	other.Cloak = 0
	w.Sectors[100].Warps = []int{103, 101, 102}
	w.Ports[101].Name = "Test Port"
	w.Ports[101].Coefficient = [3]float64{-50, 50, -50}
	p.Credits = 100000
	if err := w.Move(other.ID, 100); err != nil {
		t.Fatal(err)
	}
	if err := w.CreatePlanet(p.ID, "Test Planet", time.Now()); err != nil {
		t.Fatal(err)
	}
	planet := w.Planets[2]
	w.Sectors[100].Planet = 0
	w.Sectors[102].Planet = planet.ID
	planet.Sector, planet.Ground = 102, 12
	other.Sector = 103
	before, _ := json.Marshal(w)
	reports, err := w.Scan(p.ID)
	if err != nil {
		t.Fatal(err)
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("sensors mutated state")
	}
	if len(reports) != 3 || reports[0].Sector != 103 || len(reports[0].Ships) != 1 || reports[0].Ships[0].Fighters != 42 || reports[0].Ships[0].Shields != 7 || reports[1].PortName != "Test Port" || !reflect.DeepEqual(reports[1].Selling, []string{"organics"}) || reports[2].PlanetName != "Test Planet" || reports[2].Ground != 12 {
		t.Fatalf("incorrect scan: %+v", reports)
	}
	b, _ := json.Marshal(reports)
	if string(b) == "" || strings.Contains(string(b), "secret-identity") {
		t.Fatal("private identity exposed")
	}
	reports[0].Warps[0] = 1
	if w.Sectors[103].Warps[0] != 100 {
		t.Fatal("returned warp aliases world")
	}
	if _, err := w.Scan(999); err == nil {
		t.Fatal("accepted missing player")
	}
}

func TestNavigationDOSRoutesAndTurnAccounting(t *testing.T) {
	w, p := navigationWorld(t)
	for _, tc := range []struct {
		from, to int
		want     []int
	}{
		{100, 110, []int{100, 101, 107, 109, 110}},
		{101, 100, []int{101, 107, 109, 110, 100}},
	} {
		got, err := w.Path(tc.from, tc.to)
		if err != nil || !reflect.DeepEqual(got, tc.want) {
			t.Fatalf("route %d->%d: %v, %v", tc.from, tc.to, got, err)
		}
	}
	if p.Turns != 500 || p.Sector != 100 {
		t.Fatal("pathfinding spends turns or moves ship")
	}
	path, err := w.Course(p.ID, 110)
	if err != nil {
		t.Fatal(err)
	}
	p.DockToken, p.PlanetToken, p.LandedPlanet = "old-dock", "old-planet", 2
	for hop := 1; hop < len(path); hop++ {
		if err := w.FollowCourse(p.ID, path[hop-1:]); err != nil {
			t.Fatal(err)
		}
	}
	if p.Sector != 110 || p.Turns != 496 || p.DockToken != "" || p.PlanetToken != "" || p.LandedPlanet != 0 {
		t.Fatalf("course state: %+v", p)
	}
	for _, tc := range [][2]int{{0, 100}, {100, 111}, {100, 100}, {100, 1}} {
		if _, err := w.Path(tc[0], tc[1]); err == nil {
			t.Fatalf("accepted invalid/unreachable path %v", tc)
		}
	}
}

func TestAutopilotRejectsInsufficientTurnsAndStaleCourse(t *testing.T) {
	w, p := navigationWorld(t)
	p.Turns = 3
	if _, err := w.Course(p.ID, 110); err == nil {
		t.Fatal("accepted course beyond turn budget")
	}
	if p.Sector != 100 || p.Turns != 3 {
		t.Fatal("rejected course mutated player")
	}
	p.Turns = 4
	if _, err := w.Course(p.ID, 110); err != nil {
		t.Fatal(err)
	}
	p.Sector = 102
	if err := w.FollowCourse(p.ID, []int{100, 101, 107, 109, 110}); err == nil {
		t.Fatal("stale course accepted")
	}
	p.Sector = 100
	if err := w.FollowCourse(p.ID, []int{100, 110}); err == nil {
		t.Fatal("nonadjacent hop accepted")
	}
	if p.Sector != 100 || p.Turns != 4 {
		t.Fatal("rejected hop mutated player")
	}
	p.Turns = 0
	if err := w.Move(p.ID, 101); err == nil {
		t.Fatal("move accepted without turns")
	}
	p.Turns = 1
	if err := w.Move(p.ID, 101); err != nil {
		t.Fatal(err)
	}
	if p.Turns != 0 || p.Sector != 101 {
		t.Fatal("last turn movement incorrect")
	}
}

// The compact fixture comes from the preserved DOS before/after saves and logs.
func TestDOSNavigationGolden(t *testing.T) {
	var fixture struct {
		Graph     map[int][]int
		Scenarios []struct {
			Name         string `json:"name"`
			Route        []int  `json:"route"`
			TurnsBefore  int64  `json:"turns_before"`
			TurnsAfter   int64  `json:"turns_after"`
			SectorBefore int    `json:"sector_before"`
			SectorAfter  int    `json:"sector_after"`
		}
	}
	data, err := os.ReadFile("testdata/dos-navigation.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	if len(fixture.Scenarios) != 13 {
		t.Fatal("incomplete DOS fixture")
	}
	for _, tc := range fixture.Scenarios {
		t.Run(tc.Name, func(t *testing.T) {
			w, p := navigationWorld(t)
			for sector, warps := range fixture.Graph {
				w.Sectors[sector].Warps = warps
			}
			p.Sector, p.Turns = tc.SectorBefore, tc.TurnsBefore
			var err error
			switch tc.Name {
			case "sensors", "sensors-zero":
				_, err = w.Scan(p.ID)
			case "move", "move-last", "move-zero":
				err = w.Move(p.ID, 101)
			case "move-invalid":
				err = w.Move(p.ID, 110)
			case "autopilot":
				var path []int
				path, err = w.Course(p.ID, 110)
				if err == nil {
					for i := 1; i < len(path); i++ {
						if err = w.FollowCourse(p.ID, path[i-1:]); err != nil {
							break
						}
					}
				}
			case "autopilot-short":
				_, err = w.Course(p.ID, 110)
			case "autopilot-cancel":
				_, err = w.Course(p.ID, 110)
			case "path", "path-reverse":
				var path []int
				path, err = w.Path(tc.Route[0], tc.Route[len(tc.Route)-1])
				if !reflect.DeepEqual(path, tc.Route) {
					t.Fatalf("DOS route %v, Go route %v", tc.Route, path)
				}
			case "path-same":
				_, err = w.Path(100, 100)
			case "path-unreachable":
				_, err = w.Path(100, 111)
			default:
				t.Fatal("unhandled fixture", tc.Name)
			}
			rejects := tc.Name == "move-zero" || tc.Name == "move-invalid" || tc.Name == "autopilot-short" || tc.Name == "path-same" || tc.Name == "path-unreachable"
			if (err != nil) != rejects {
				t.Fatalf("unexpected result: %v", err)
			}
			if p.Sector != tc.SectorAfter || p.Turns != tc.TurnsAfter {
				t.Fatalf("Go state %+v differs from DOS sector %d/turns %d", p, tc.SectorAfter, tc.TurnsAfter)
			}
		})
	}
}
