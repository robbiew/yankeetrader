package game

import (
	"encoding/json"
	"math"
	"testing"
	"time"
)

func TestCloakDetectionStrictThresholdAndSessionLifetime(t *testing.T) {
	w, p := navigationWorld(t)
	target, _ := w.Join("hidden", "Hidden")
	target.Sector = 103
	target.Cloak = .5
	v, _ := w.NewVisibility(p.ID)
	before, _ := json.Marshal(w)
	for i, r := range []float64{.5, .6} {
		reports, err := w.ScanVisible(p.ID, v, func() float64 { return r })
		if err != nil {
			t.Fatal(err)
		}
		count := 0
		for _, report := range reports {
			for _, ship := range report.Ships {
				count++
				if !ship.Revealed {
					t.Fatal("first detection missing shimmer")
				}
			}
		}
		if count != i {
			t.Fatal("strict threshold", r, count)
		}
	}
	reports, err := w.ScanVisible(p.ID, v, func() float64 { t.Fatal("already revealed ship drew again"); return 0 })
	if err != nil {
		t.Fatal(err)
	}
	for _, report := range reports {
		for _, ship := range report.Ships {
			if ship.Revealed {
				t.Fatal("repeated shimmer")
			}
		}
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("scan changed saved world")
	}
	fresh, _ := w.NewVisibility(p.ID)
	reports, _ = w.ScanVisible(p.ID, fresh, func() float64 { return 0 })
	for _, report := range reports {
		if len(report.Ships) > 0 {
			t.Fatal("reveal leaked across sessions")
		}
	}
	target.ShipGeneration++
	reports, _ = w.ScanVisible(p.ID, v, func() float64 { return 0 })
	for _, report := range reports {
		if len(report.Ships) > 0 {
			t.Fatal("replacement inherited reveal")
		}
	}
	p.ShipGeneration++
	if _, err = w.ScanVisible(p.ID, v, func() float64 { return .9 }); err == nil {
		t.Fatal("stale observer accepted")
	}
}

func TestCloakVisibilityErrorIsAtomicAndBoundToObserver(t *testing.T) {
	w, p := navigationWorld(t)
	one, _ := w.Join("one", "One")
	two, _ := w.Join("two", "Two")
	one.Sector, two.Sector = 103, 103
	one.Cloak, two.Cloak = .5, .5
	v, _ := w.NewVisibility(p.ID)
	draws := 0
	_, err := w.ScanVisible(p.ID, v, func() float64 {
		draws++
		if draws == 1 {
			return .9
		}
		return math.NaN()
	})
	if err == nil || len(v.revealed) != 0 {
		t.Fatal("partial reveal cached", err)
	}
	if _, err = w.ScanVisible(one.ID, v, func() float64 { return .9 }); err == nil {
		t.Fatal("another observer used cache")
	}
	one.Cloak = 1
	two.Cloak = 0
	reports, err := w.ScanVisible(p.ID, v, func() float64 { return math.Nextafter(1, 0) })
	if err != nil {
		t.Fatal(err)
	}
	for _, report := range reports {
		for _, ship := range report.Ships {
			if ship.ID == one.ID || ship.Revealed {
				t.Fatal("full cloak detected or uncloaked shimmer")
			}
		}
	}
}

func TestCloakTurnDecayAndReplacement(t *testing.T) {
	w, p := navigationWorld(t)
	p.Turns = 476
	if err := w.Move(p.ID, 103); err != nil {
		t.Fatal(err)
	}
	if p.Cloak != .99 || p.Turns != 475 {
		t.Fatal(p.Cloak, p.Turns)
	}
	if err := w.Move(p.ID, 100); err != nil {
		t.Fatal(err)
	}
	if p.Cloak != .99 {
		t.Fatal("decayed away from boundary")
	}
	p.Turns = 1
	p.Cloak = .005
	if err := w.Dock(p.ID, time.Now()); err != nil {
		t.Fatal(err)
	}
	if p.Cloak != 0 || p.Turns != 0 {
		t.Fatal("zero boundary clamp", p.Cloak, p.Turns)
	}
	if err := w.RecordDeath(DeathContext{Victim: p.ID, Generation: p.ShipGeneration, Sector: p.Sector, Cause: "hazard"}, time.Now()); err != nil {
		t.Fatal(err)
	}
	if err := w.ReplaceShip(p.ID, time.Now()); err != nil {
		t.Fatal(err)
	}
	if p.Cloak != 1 || p.Turns != 0 {
		t.Fatal("replacement cloak or turn refill")
	}
	for _, n := range []float64{-.01, 1.01, math.NaN(), math.Inf(1)} {
		p.Cloak = n
		if w.Validate() == nil {
			t.Fatal("invalid cloak", n)
		}
	}
}

func TestVisibleAttackRequiresCurrentDetection(t *testing.T) {
	w, d, a := ownedPortWorld(t)
	a.Sector = d.Sector
	a.Cloak = 1
	d.Cloak = .5
	a.Fighters = 10
	d.Fighters = 1
	d.Shields = 1
	v, _ := w.NewVisibility(a.ID)
	if _, err := w.PrepareVisibleAttack(a.ID, d.ID, 1, v); err == nil {
		t.Fatal("hidden target offered")
	}
	intent, _ := w.PrepareAttack(a.ID, d.ID, 1)
	if _, err := w.CommitAttack(intent, func() float64 { t.Fatal("hidden attack drew randomness"); return 0 }, time.Now()); err == nil {
		t.Fatal("hidden attack")
	}
	// Detection comes from an adjacent scan, then remains valid on entering that sector.
	a.Sector = 1
	w.Sectors[1].Warps = []int{d.Sector}
	if _, err := w.ScanVisible(a.ID, v, func() float64 { return .9 }); err != nil {
		t.Fatal(err)
	}
	a.Sector = d.Sector
	candidates, err := w.VisibleAttackCandidates(a.ID, v)
	if err != nil || len(candidates) != 1 {
		t.Fatal(candidates, err)
	}
	intent, err = w.PrepareVisibleAttack(a.ID, d.ID, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	// .4 would kill the committed fighter without cloak; full attacker cloak wins this round.
	draws := 0
	result, err := w.CommitVisibleAttack(intent, v, func() float64 {
		draws++
		if draws == 1 {
			return .4
		}
		return 0
	}, time.Now())
	if err != nil || !result.Destroyed || result.AttackerLosses != 0 {
		t.Fatal(result, err)
	}
}
