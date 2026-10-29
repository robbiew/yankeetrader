package game

import (
	"encoding/json"
	"math"
	"testing"
)

func TestBribeRecoveredBoundariesAndDrawOrder(t *testing.T) {
	for _, tc := range []struct {
		name            string
		owner           int
		fighters, offer int64
		planet, hostile bool
		draws           []float64
		reason          string
		combat          bool
	}{
		{"minimum equality", -2, 100, 100, false, false, []float64{.05, .9, 0}, "accepted", false},
		{"threshold equality", -2, 100, 200, false, false, []float64{.5, .5, .5}, "accepted", false},
		{"under threshold", -2, 100, 199, false, false, []float64{.5, .5, .5}, "insulting offer", true},
		{"guaranteed enough money", -2, 100, 300, false, false, []float64{.5, .5, math.Nextafter(1, 0)}, "accepted", false},
		{"five percent hostility", -2, 100, 300, false, false, []float64{.049, .5}, "hostile refusal", true},
		{"weak strict boundary", -2, 99, 300, false, false, []float64{.5, .9, .5}, "accepted", false},
		{"weak hostility", -2, 99, 300, false, false, []float64{.5, .901}, "hostile refusal", true},
		{"equal force not weak", -2, 100, 300, false, false, []float64{.5, .999, .5}, "accepted", false},
		{"previous mercenary casualties", -2, 100, 300, false, true, []float64{.5, .5}, "hostile refusal", true},
		{"planet before hostility", -2, 100, 0, true, true, nil, "planet guard refusal", false},
		{"weak human retaliation", 2, 99, 0, false, false, []float64{.329}, "faction refusal", true},
		{"human strict boundary", 2, 99, 0, false, false, []float64{.33}, "faction refusal", false},
		{"equal human force", 2, 100, 0, false, false, []float64{0}, "faction refusal", false},
		{"xannor unconditional", -1, 100, 0, true, false, []float64{.99}, "faction refusal", true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			i := 0
			reason, fight, err := ResolveBribeDecision(tc.owner, 100, tc.fighters, tc.offer, tc.planet, tc.hostile, func() float64 {
				if i >= len(tc.draws) {
					t.Fatal("unexpected random draw")
				}
				r := tc.draws[i]
				i++
				return r
			})
			if err != nil || reason != tc.reason || fight != tc.combat || i != len(tc.draws) {
				t.Fatal(reason, fight, err, i)
			}
		})
	}
}

func TestBribeRejectsChangedWarningAndInvalidRandomness(t *testing.T) {
	for _, mutate := range []func(*World, *Player){
		func(w *World, p *Player) { p.Credits-- }, func(w *World, p *Player) { p.Fighters-- },
		func(w *World, p *Player) { p.Cloak = .2 }, func(w *World, p *Player) { p.Turns-- },
		func(w *World, p *Player) { p.Sector = 9 }, func(w *World, p *Player) { w.Sectors[8].Defense.Fighters++ },
		func(w *World, p *Player) { w.Sectors[8].Minefield = []MineLayer{{Count: 1}} },
		func(w *World, p *Player) { p.ShipGeneration++ },
	} {
		w, p := setup(t)
		p.Sector = 8
		p.Credits = 1000
		p.Fighters = 100
		w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
		entry, err := w.PrepareBribe(p.ID, 300, false)
		if err != nil {
			t.Fatal(err)
		}
		mutate(w, p)
		before, _ := json.Marshal(w)
		if _, err = w.CommitBribe(entry, false, func() float64 { t.Fatal("stale bribe consumed RNG"); return .5 }, clock); err == nil {
			t.Fatal("stale bribe")
		}
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("stale bribe mutated world")
		}
	}
	for _, bad := range []float64{math.NaN(), math.Inf(1), -1, 1} {
		for badIndex := 1; badIndex <= 3; badIndex++ {
			w, p := setup(t)
			p.Sector = 8
			p.Credits = 1000
			p.Fighters = 100
			w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
			entry, _ := w.PrepareBribe(p.ID, 300, false)
			before, _ := json.Marshal(w)
			i := 0
			_, err := w.CommitBribe(entry, false, func() float64 {
				i++
				if i == badIndex {
					return bad
				}
				return .5
			}, clock)
			after, _ := json.Marshal(w)
			if err == nil || string(before) != string(after) {
				t.Fatal("bad RNG spent money or recruited", badIndex, err)
			}
		}
	}
}

func TestBribeCapacityEligibilityAndZeroForce(t *testing.T) {
	w, p := setup(t)
	p.Sector = 8
	p.Credits = 1000
	p.Fighters = MaxQuantity
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 1}
	if _, err := w.PrepareBribe(p.ID, 3, false); err == nil {
		t.Fatal("capacity")
	}
	p.Fighters = 0
	for _, offer := range []int64{-1, 0, 1001} {
		if _, err := w.PrepareBribe(p.ID, offer, false); err == nil {
			t.Fatal("invalid offer", offer)
		}
	}
	entry, _ := w.PrepareBribe(p.ID, 3, false)
	out, err := w.CommitBribe(entry, false, func() float64 { return .5 }, clock)
	if err != nil || out.Joined != 1 || out.Paid != 3 || p.Fighters != 1 || p.Credits != 997 || w.Sectors[8].Defense != nil {
		t.Fatal(out, err, p)
	}
	if _, err = w.CommitBribe(entry, false, func() float64 { t.Fatal("replay RNG"); return 0 }, clock); err == nil {
		t.Fatal("replay")
	}
}

func TestZeroForceHostilityUsesExistingEmergencyEscape(t *testing.T) {
	w, p := setup(t)
	p.Sector = 8
	p.Credits = 1000
	p.Fighters = 0
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
	entry, err := w.PrepareBribe(p.ID, 300, true)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitBribe(entry, true, func() float64 { return .5 }, clock)
	if err != nil || !out.Combat || !out.Defense.Escaped || p.Credits != 1000 || w.Sectors[8].Defense.Fighters != 100 {
		t.Fatal(out, err)
	}
}

func TestAdjacentBribeChargesEntryAndLeavesRefusedDefenseBlocking(t *testing.T) {
	for _, human := range []bool{false, true} {
		w, p := setup(t)
		p.Sector = 7
		p.Turns = 26
		p.Cloak = 1
		p.Credits = 1000
		p.Fighters = 1000
		w.Sectors[7].Warps = []int{8}
		owner := MercenaryOwner
		if human {
			enemy, _ := w.Join("enemy", "Enemy")
			owner = enemy.ID
		}
		w.Sectors[8].Defense = &SectorDefense{Owner: owner, Fighters: 100}
		entry, err := w.PrepareBribeAt(p.ID, 8, 300, false)
		if err != nil {
			t.Fatal(err)
		}
		out, err := w.CommitBribe(entry, false, func() float64 { return .5 }, clock)
		if err != nil || p.Sector != 8 || p.Turns != 25 || p.Cloak != .99 {
			t.Fatal(out, err, p)
		}
		if human {
			if out.Combat || p.Credits != 1000 || !w.HostileDefense(p.ID, 8) {
				t.Fatal(out, p)
			}
			if err = w.Move(p.ID, 7); err == nil {
				t.Fatal("refusal unlocked ordinary movement")
			}
		} else if out.Joined != 100 || p.Credits != 700 || p.Fighters != 1100 || w.Sectors[8].Defense != nil {
			t.Fatal(out, p)
		}
	}
}

func TestAdjacentBribeCannotBypassOriginEncounterOrTurnBudget(t *testing.T) {
	w, p := setup(t)
	p.Sector = 7
	p.Credits = 1000
	p.Fighters = 1000
	w.Sectors[7].Warps = []int{8}
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
	p.Turns = 0
	if _, err := w.PrepareBribeAt(p.ID, 8, 300, false); err == nil {
		t.Fatal("zero-turn entry")
	}
	p.Turns = 500
	if _, err := w.PrepareBribeAt(p.ID, 9, 300, false); err == nil {
		t.Fatal("remote bribe")
	}
	w.Sectors[7].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
	if _, err := w.PrepareBribeAt(p.ID, 8, 300, false); err == nil {
		t.Fatal("origin blockade bypass")
	}
}
