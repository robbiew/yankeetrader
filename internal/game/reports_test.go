package game

import (
	"encoding/json"
	"reflect"
	"testing"
	"time"
)

func reportWorld(t *testing.T) (*World, *Player, *Player) {
	t.Helper()
	w, p := navigationWorld(t)
	other, err := w.Join("reports:other", "Enemy")
	if err != nil {
		t.Fatal(err)
	}
	w.Sectors[102].Planet = 2
	w.Planets[2] = &Planet{ID: 2, Sector: 102, Owner: other.ID, Name: "Test Planet", Updated: w.Created,
		Ground: 12, Bank: 10000, Production: [3]float64{10, 20, 30}, Cargo: [3]float64{40, 50, 60}, Fighters: 70, Missiles: 8, Mines: 9, Plasma: 2}
	return w, p, other
}

func TestRemotePlanetReportVisibility(t *testing.T) {
	// Visibility boundaries come from utility-planet-{report,owned,unguarded,
	// private,guarded}; team sharing follows the modern landing-access policy.
	for _, mode := range []string{"unowned", "own", "unguarded", "private", "team", "missing", "hostile", "friendly-defense"} {
		t.Run(mode, func(t *testing.T) {
			w, p, enemy := reportWorld(t)
			planet := w.Planets[2]
			switch mode {
			case "unowned":
				planet.Owner = 0
			case "own", "friendly-defense":
				planet.Owner = p.ID
			case "unguarded":
				planet.Ground = 0
			case "team":
				p.Team, enemy.Team = 1, 1
				w.Teams[1] = &Team{ID: 1}
			case "missing":
				w.Sectors[102].Planet = 0
				delete(w.Planets, 2)
			case "hostile":
				w.Sectors[102].Defense = &SectorDefense{Owner: enemy.ID, Fighters: 100}
			}
			if mode == "friendly-defense" {
				w.Sectors[102].Defense = &SectorDefense{Owner: p.ID, Fighters: 100}
			}
			before, _ := json.Marshal(w)
			r, err := w.RemotePlanetReport(p.ID, 102, w.Created)
			if err != nil {
				t.Fatal(err)
			}
			if mode == "hostile" {
				if r.Available || !r.TurnSpent || r.Name != "" || r.Ground != 0 || r.Details != nil || p.Turns != 499 || p.Sector != 100 {
					t.Fatalf("blocked query disclosed or moved: %+v, %+v", r, p)
				}
				return
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("free report mutated world")
			}
			if mode == "missing" {
				if r.Available || r.Name != "" || r.Details != nil {
					t.Fatalf("missing planet: %+v", r)
				}
				return
			}
			if !r.Available || r.Name != "Test Planet" || r.Ground != planet.Ground || r.TurnSpent {
				t.Fatalf("wrong public report: %+v", r)
			}
			if mode == "private" {
				if r.Details != nil {
					t.Fatal("private inventory/bank disclosed")
				}
			} else {
				if r.Details == nil || r.Details.Bank != 10000 || r.Details.Missiles != 8 {
					t.Fatalf("accessible details missing: %+v", r)
				}
				r.Details.Bank = 0
				if planet.Bank != 10000 {
					t.Fatal("report aliases stored planet")
				}
			}
		})
	}
}

func TestRemoteReportsProjectWithoutChangingEconomyOrSessions(t *testing.T) {
	w, p, _ := reportWorld(t)
	p.Cargo = [3]int64{10, 20, 30}
	p.DockToken, p.PlanetToken, p.LandedPlanet = "dock", "landing", 2
	port := w.Ports[101]
	port.Coefficient = [3]float64{50, -45, -55}
	before, _ := json.Marshal(w)
	r, err := w.RemotePortReport(p.ID, 101, w.Created)
	if err != nil || !r.Available || r.Prices != [3]int64{10, 44, 62} || r.Cargo != p.Cargo || r.Selling != [3]bool{true, false, false} {
		t.Fatalf("commerce sample: %+v, %v", r, err)
	}
	r, err = w.RemotePortReport(p.ID, 101, w.Created.Add(24*time.Hour))
	if err != nil || r.Supply[0] != 1100 {
		t.Fatalf("projected port growth: %+v, %v", r, err)
	}
	w.Planets[2].Owner = p.ID
	beforePlanet := *w.Planets[2]
	planetReport, err := w.RemotePlanetReport(p.ID, 102, w.Created.Add(24*time.Hour))
	if err != nil || planetReport.Details == nil || planetReport.Details.Bank != 10100 || planetReport.Details.Cargo[0] <= beforePlanet.Cargo[0] {
		t.Fatalf("projected planet growth: %+v, %v", planetReport, err)
	}
	w.Planets[2].Owner = 2
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("reports changed economy, docking, or landing state")
	}
}

func TestRemoteReportDenialAndInvalidRequests(t *testing.T) {
	w, p, enemy := reportWorld(t)
	w.Sectors[101].Defense = &SectorDefense{Owner: enemy.ID, Fighters: 1}
	w.Sectors[102].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 1}
	p.Turns = 0
	before, _ := json.Marshal(w)
	r, err := w.RemotePortReport(p.ID, 101, w.Created)
	if err != nil || r.Available || r != (PortReport{}) {
		t.Fatalf("port denial should be free and empty: %+v, %v", r, err)
	}
	if _, err = w.RemotePlanetReport(p.ID, 102, w.Created); err == nil {
		t.Fatal("blocked report overdrew turns")
	}
	for _, sector := range []int{0, 9999} {
		if _, err = w.RemotePortReport(p.ID, sector, w.Created); err == nil {
			t.Fatal("invalid port sector accepted")
		}
		if _, err = w.RemotePlanetReport(p.ID, sector, w.Created); err == nil {
			t.Fatal("invalid planet sector accepted")
		}
	}
	if _, err = w.RemotePlanetReport(999, 102, w.Created); err == nil {
		t.Fatal("missing actor accepted")
	}
	if _, err = w.RemotePortReport(p.ID, 101, time.Time{}); err == nil {
		t.Fatal("invalid time accepted")
	}
	if earth, err := w.RemotePortReport(p.ID, 1, w.Created); err != nil || earth.Available {
		t.Fatal("Earth service represented as a remote cargo market")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("denied/invalid requests mutated world")
	}
	// Absence and a guarded port use the same unavailable response.
	w.Sectors[101].Port = 0
	r, err = w.RemotePortReport(p.ID, 101, w.Created)
	if err != nil || r.Available {
		t.Fatal("absent port reported")
	}
}

func TestRemotePlanetReportTeamAccessRevokedImmediately(t *testing.T) {
	w, p, owner := reportWorld(t)
	p.Team, owner.Team = 1, 1
	w.Teams[1] = &Team{ID: 1}
	shared, err := w.RemotePlanetReport(p.ID, 102, w.Created)
	if err != nil || shared.Details == nil {
		t.Fatal("current teammate could not see shared planet", err)
	}
	owner.Team = 0
	private, err := w.RemotePlanetReport(p.ID, 102, w.Created)
	if err != nil || !private.Available || private.Details != nil || private.Name != "Test Planet" {
		t.Fatalf("departed owner's private report stayed accessible: %+v, %v", private, err)
	}
}

func TestRemotePlanetReportChecksRegeneratedGroundBeforeDisclosure(t *testing.T) {
	for _, access := range []string{"foreign", "owner", "team", "unowned"} {
		t.Run(access, func(t *testing.T) {
			w, p, owner := reportWorld(t)
			w.Planets[2].Ground = 0
			switch access {
			case "owner":
				w.Planets[2].Owner = p.ID
			case "team":
				p.Team, owner.Team = 1, 1
				w.Teams[1] = &Team{ID: 1}
			case "unowned":
				w.Planets[2].Owner = 0
			}
			before, _ := json.Marshal(w)
			r, err := w.RemotePlanetReport(p.ID, 102, w.Created.Add(24*time.Hour))
			if err != nil || !r.Available || r.Ground != 1 {
				t.Fatalf("regenerated public ground: %+v, %v", r, err)
			}
			if access == "foreign" {
				if r.Details != nil {
					t.Fatal("regenerated foreign defenses did not protect bank/inventory")
				}
			} else if r.Details == nil || r.Details.Ground != 1 {
				t.Fatal("accessible report lost projected details")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("permission projection changed the stored world")
			}
		})
	}
}

func TestOwnPlanetFinderDoesNotIncludeTeamOrForeignPlanets(t *testing.T) {
	w, p, enemy := reportWorld(t)
	w.Planets[2].Owner = p.ID
	w.Planets[3] = &Planet{ID: 3, Name: "Earlier", Sector: 101, Owner: p.ID}
	w.Planets[4] = &Planet{ID: 4, Name: "Shared", Sector: 103, Owner: enemy.ID}
	p.Team, enemy.Team = 1, 1
	got, err := w.OwnPlanets(p.ID)
	want := []PlanetLocation{{Name: "Earlier", ID: 3, Sector: 101}, {Name: "Test Planet", ID: 2, Sector: 102}}
	if err != nil || !reflect.DeepEqual(got, want) {
		t.Fatalf("own planet list: %+v, %v", got, err)
	}
	w.Planets[2].Owner, w.Planets[3].Owner = enemy.ID, enemy.ID
	if got, err = w.OwnPlanets(p.ID); err != nil || len(got) != 0 {
		t.Fatal("foreign ownership remained in personal list")
	}
}
