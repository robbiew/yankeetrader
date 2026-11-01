package game

import (
	"encoding/json"
	"math"
	"reflect"
	"testing"
)

func TestSpyShipDetectionSnapshotAndGeneration(t *testing.T) {
	w, p, n := spyWorld(t)
	target, _ := w.Join("private-identity", "Enemy")
	target.Sector = 101
	target.Cloak = .5
	target.Team = 7
	target.Fighters = 42
	target.Shields = 10
	w.Sectors[101].Warps = nil
	if err := n.Hire(w, p.DockToken, []int{101}, w.Created); err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(w)
	// The exact-tie policy is deliberately conservative, not a DOS RNG claim.
	if err := n.Advance(w, w.Created, func() float64 { return .5 }); err != nil {
		t.Fatal(err)
	}
	r, _ := n.Reports(w, false)
	if len(r) != 0 {
		t.Fatal(r)
	}
	if err := n.Advance(w, w.Created, func() float64 { return .6 }); err != nil {
		t.Fatal(err)
	}
	r, _ = n.Reports(w, false)
	if len(r) != 1 || len(r[0].Ships) != 1 || r[0].Ships[0] != (SpyShip{Alias: "Enemy", Team: 7, Fighters: 42, Shields: 10, Shimmering: true}) {
		t.Fatal(r)
	}
	r[0].Ships[0].Alias = "tampered"
	copy := n.Clone()
	copy.reports[0].Ships[0].Alias = "also tampered"
	again, _ := n.Reports(w, false)
	if again[0].Ships[0].Alias != "Enemy" {
		t.Fatal(again)
	}
	// A second scan can use only this network's generation-bound detection.
	n.lastReported[0] = 0
	if err := n.Advance(w, w.Created, nil); err != nil {
		t.Fatal(err)
	}
	r, _ = n.Reports(w, false)
	if len(r) != 2 || r[1].Ships[0].Shimmering {
		t.Fatal(r)
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("spy mutated saved world")
	}
	target.ShipGeneration++
	n.lastReported[0] = 0
	if err := n.Advance(w, w.Created, func() float64 { return 0 }); err != nil {
		t.Fatal(err)
	}
	r, _ = n.Reports(w, false)
	if len(r) != 2 {
		t.Fatal("replacement inherited detection", r)
	}
	fresh := NewSpyNetwork(p.ID, p.ShipGeneration, w.Season)
	if err := fresh.Hire(w, p.DockToken, []int{101}, w.Created); err != nil {
		t.Fatal(err)
	}
	if err := fresh.Advance(w, w.Created, func() float64 { return 0 }); err != nil {
		t.Fatal(err)
	}
	r, _ = fresh.Reports(w, false)
	if len(r) != 0 {
		t.Fatal("login inherited detection", r)
	}
}

func TestSpyDetectionLateFailureRollsBack(t *testing.T) {
	for _, bad := range []float64{math.NaN(), math.Inf(1), -1, 1} {
		w, p, n := spyWorld(t)
		target, _ := w.Join("enemy", "Enemy")
		target.Sector = 101
		target.Cloak = .5
		if err := n.Hire(w, p.DockToken, []int{101}, w.Created); err != nil {
			t.Fatal(err)
		}
		before := n.Clone()
		draw := 0
		err := n.Advance(w, w.Created, func() float64 {
			draw++
			if draw == 1 {
				return .9
			}
			return bad
		})
		if err == nil || !reflect.DeepEqual(n, before) {
			t.Fatalf("late invalid draw published state: %v", err)
		}
	}
}

func TestSpyDisruptionAndShipEligibility(t *testing.T) {
	w, p, n := spyWorld(t)
	if err := w.BindDisruption(Disruption{Player: p.ID, Generation: p.ShipGeneration, Season: w.Season, Locations: [2]int{101, 102}}, nil, nil); err != nil {
		t.Fatal(err)
	}
	p.Sector = 101
	dead, _ := w.Join("dead", "Dead")
	dead.Sector = 101
	dead.Death = &Death{}
	// The observer is excluded even when sharing the spy's sector.
	if err := n.Hire(w, p.DockToken, []int{101}, w.Created); err == nil {
		t.Fatal("hired away from Earth")
	}
	p.Sector = 1
	if err := n.Hire(w, p.DockToken, []int{101}, w.Created); err != nil {
		t.Fatal(err)
	}
	p.Sector = 101
	if err := n.Advance(w, w.Created, func() float64 { return 0 }); err != nil {
		t.Fatal(err)
	}
	r, _ := n.Reports(w, false)
	if len(r) != 1 || !r[0].Disruption || len(r[0].Ships) != 0 {
		t.Fatal(r)
	}
	// A different login must not see this observer's private disruption pair.
	p.Sector = 1
	other, _ := w.Join("other-login", "Other")
	other.Sector = 1
	other.Credits = SpyPrice
	if err := w.Dock(other.ID, w.Created); err != nil {
		t.Fatal(err)
	}
	fresh := NewSpyNetwork(other.ID, other.ShipGeneration, w.Season)
	if err := fresh.Hire(w, other.DockToken, []int{101}, w.Created); err != nil {
		t.Fatal(err)
	}
	if err := fresh.Advance(w, w.Created, func() float64 { return 0 }); err != nil {
		t.Fatal(err)
	}
	private, _ := fresh.Reports(w, false)
	if len(private) != 0 {
		t.Fatal("disruption pair leaked to another login", private)
	}
}

func TestSpyShipOrderFullCloakAndSharedDetection(t *testing.T) {
	w, p, n := spyWorld(t)
	first, _ := w.Join("first-private", "First")
	first.Sector = 101
	first.Cloak = .5
	first.Team = p.Team
	second, _ := w.Join("second-private", "Second")
	second.Sector = 101
	second.Cloak = 0
	hidden, _ := w.Join("hidden-private", "Hidden")
	hidden.Sector = 101
	hidden.Cloak = 1
	w.Sectors[101].Warps = nil
	if err := n.Hire(w, p.DockToken, []int{101, 101}, w.Created); err != nil {
		t.Fatal(err)
	}
	draws := 0
	if err := n.Advance(w, w.Created, func() float64 { draws++; return .9 }); err != nil {
		t.Fatal(err)
	}
	reports, _ := n.Reports(w, false)
	if len(reports) != 2 || draws != 3 {
		t.Fatal(reports, draws)
	}
	for i, r := range reports {
		if len(r.Ships) != 2 || r.Ships[0].Alias != "First" || r.Ships[1].Alias != "Second" || r.Ships[0].Shimmering != (i == 0) {
			t.Fatal(reports)
		}
	}
}
