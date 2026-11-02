package game

import (
	"encoding/json"
	"math"
	"testing"
	"time"
)

func combatEvents(w *World, operation string) []NewsEvent {
	var out []NewsEvent
	for _, e := range w.News {
		if e.Kind == NewsCombat && e.Combat != nil && e.Combat.Operation == operation {
			out = append(out, e)
		}
	}
	return out
}
func TestWeaponNewsThresholdsAndSnapshots(t *testing.T) {
	for _, count := range []int64{9, 10} {
		w, p := plasmaWorld(t, 8)
		w.Sectors[2].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: count}
		firePlasma(t, w, p, 2, 1, func() float64 { return .5 })
		news := combatEvents(w, "plasma-defense")
		if (len(news) == 1) != (count > 9) {
			t.Fatal("threshold", count, news)
		}
		if count > 9 && (news[0].Alias != p.Alias || news[0].Combat.Amount != count || news[0].Combat.Sector != 2) {
			t.Fatal(news)
		}
	}
	w, a := plasmaWorld(t, 8)
	target := plasmaTarget(t, w, 2)
	firePlasma(t, w, a, 2, 1, func() float64 { return .5 })
	news := combatEvents(w, "plasma-ship")
	if len(news) != 1 || news[0].Combat.Target != target.Alias || news[0].Combat.Amount != target.Shields {
		t.Fatal(news, target)
	}
	snapshot := news[0].Combat.Target
	target.Alias = "Renamed"
	if news[0].Combat.Target != snapshot {
		t.Fatal("news changed after rename")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}
func TestCombatNewsMineAndMobilityActualOutcomes(t *testing.T) {
	w, p := setup(t)
	p.Sector = 8
	p.Shields = 10000
	w.Sectors[8].Minefield = []MineLayer{{Owner: p.ID, Count: 1}}
	_, err := w.ResolveMinefield(p.ID, func() float64 { return .5 }, clock)
	if err != nil {
		t.Fatal(err)
	}
	mine := combatEvents(w, "mine-hit")
	if len(mine) != 1 || mine[0].Combat.Amount != p.Shields || mine[0].Combat.Sector != 8 {
		t.Fatal(mine, p)
	}
	w, p, planet := mobilityWorld(t)
	before := p.Fighters
	intent := mobilityEntry(t, w, p, "thrusters", 9, 0)
	out, err := w.CommitPlanetAction(intent, func() float64 { return .999 }, clock)
	if err != nil || !out.Destroyed {
		t.Fatal(out, err)
	}
	news := combatEvents(w, "mobility-explosion")
	if len(news) != 1 || news[0].Combat.Target != planet.Name || news[0].Combat.Amount != before-p.Fighters {
		t.Fatal(news, p)
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}
func TestCombatNewsExhaustionBeforeLaunchMutation(t *testing.T) {
	for _, weapon := range []string{"missile", "plasma"} {
		t.Run(weapon, func(t *testing.T) {
			if weapon == "missile" {
				w, a, _, v := missileWorld(t)
				intent, err := w.PrepareMissile(a.ID, 2, 1, v)
				if err != nil {
					t.Fatal(err)
				}
				w.NextNews = math.MaxUint64 - 1
				before, _ := json.Marshal(w)
				_, err = w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
				if err == nil {
					t.Fatal("exhausted news allowed")
				}
				after, _ := json.Marshal(w)
				if string(before) != string(after) {
					t.Fatal("exhaustion mutated missile world")
				}
			} else {
				w, a := plasmaWorld(t, 8)
				w.NextNews = math.MaxUint64 - 1
				intent, err := w.PreparePlasma(a.ID, 2, 1)
				if err != nil {
					t.Fatal(err)
				}
				before, _ := json.Marshal(w)
				_, err = w.CommitPlasma(intent, func() float64 { return .5 }, clock)
				if err == nil {
					t.Fatal("exhausted news allowed")
				}
				after, _ := json.Marshal(w)
				if string(before) != string(after) {
					t.Fatal("exhaustion mutated plasma world")
				}
			}
		})
	}
}

func TestPlasmaNewsExcludesLazyProductionFromDamage(t *testing.T) {
	w, a := plasmaWorld(t, 8)
	planet := plasmaTestPlanet(w, a.ID)
	// Refresh before damage just as the game does; otherwise ordinary growth can
	// appear as negative reported damage and make a successful launch unsaveable.
	expected := *planet
	now := clock.Add(24 * time.Hour)
	expected.update(now, true)
	intent, err := w.PreparePlasma(a.ID, 2, 1)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitPlasma(intent, func() float64 { return .5 }, now); err != nil {
		t.Fatal(err)
	}
	event := combatEvents(w, "plasma-planet")
	if len(event) != 1 {
		t.Fatal(event)
	}
	c := event[0].Combat
	if c.GroundLoss != expected.Ground-planet.Ground || c.ProductionLoss != productionTotal(expected.Production)-productionTotal(planet.Production) {
		t.Fatal("growth counted as damage", c)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}
