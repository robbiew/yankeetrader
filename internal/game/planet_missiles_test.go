package game

import (
	"encoding/json"
	"math"
	"os"
	"testing"
	"time"
)

func planetMissileWorld(t *testing.T) (*World, *Player, *Planet, *Visibility) {
	w, a, d, v := missileWorld(t)
	d.Sector = 3
	planet := &Planet{ID: 2, Sector: 2, Owner: d.ID, Name: "Target", Updated: clock, Ground: 5000, Production: [3]float64{100, 200, 300}, Cargo: [3]float64{10, 20, 30}, Bank: 10000}
	w.Planets[2] = planet
	w.Sectors[2].Planet = 2
	return w, a, planet, v
}
func TestPlanetMissileInterceptionAndGroundOnlyImpact(t *testing.T) {
	w, a, p, v := planetMissileWorld(t)
	w.Sectors[2].Defense = &SectorDefense{Owner: p.Owner, Fighters: 1000}
	w.Sectors[2].Minefield = []MineLayer{{Owner: p.Owner, Count: 1}}
	before := *p
	intent, err := w.PrepareMissile(a.ID, 2, 4, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || out.Primary.SectorMissiles != 1 || out.Primary.MinesDestroyed != 1 || out.Primary.PlanetMissiles != 2 || out.Primary.GroundBefore != 5000 || out.Primary.GroundAfter != 4975 || out.Counter.Launched != 0 {
		t.Fatal(out, err)
	}
	before.Ground = 4975
	if *p != before || a.Missiles != 6 || a.Turns != 499 {
		t.Fatal("non-ground asset changed", p, a)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}
func TestPlanetMissileLazyGrowthAndNoUnusedProductionShots(t *testing.T) {
	w, a, p, v := planetMissileWorld(t)
	intent, err := w.PrepareMissile(a.ID, 2, 2, v)
	if err != nil {
		t.Fatal(err)
	}
	now := clock.Add(24 * time.Hour)
	want := *p
	want.update(now, true)
	initial := want.Ground
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, now)
	if err != nil || out.Primary.GroundBefore != initial || p.Ground != initial-25 || !p.Updated.Equal(now) {
		t.Fatal(out, p, err)
	}
	want.Ground -= 25
	if *p != want {
		t.Fatal("bombardment changed non-ground assets")
	}
}
func TestPlanetMissilePreflightAndStaleSnapshots(t *testing.T) {
	for _, mode := range []string{"own", "team", "mixed", "changed ground", "changed bank", "changed owner", "changed production", "removed"} {
		t.Run(mode, func(t *testing.T) {
			w, a, p, v := planetMissileWorld(t)
			count := int64(1)
			switch mode {
			case "own":
				p.Owner = a.ID
			case "team":
				a.Team = 1
				w.Players[p.Owner].Team = 1
			case "mixed":
				w.Players[p.Owner].Sector = 2
			}
			before, _ := json.Marshal(w)
			intent, err := w.PrepareMissile(a.ID, 2, count, v)
			if mode == "own" || mode == "team" || mode == "mixed" {
				if err == nil {
					t.Fatal("unsupported bombardment")
				}
				after, _ := json.Marshal(w)
				if string(before) != string(after) {
					t.Fatal("preflight mutation")
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			switch mode {
			case "changed ground":
				p.Ground++
			case "changed bank":
				p.Bank++
			case "changed owner":
				p.Owner = 0
			case "changed production":
				p.Production[0]++
			case "removed":
				delete(w.Planets, p.ID)
				w.Sectors[2].Planet = 0
			}
			before, _ = json.Marshal(w)
			_, err = w.CommitMissile(intent, v, func() float64 { t.Fatal("stale launch sampled"); return 0 }, clock)
			if err == nil {
				t.Fatal("stale bombardment accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("stale launch mutation")
			}
		})
	}
}

func TestPlanetMissileProductionDamageAndDestruction(t *testing.T) {
	t.Run("partial clamps and caps each warehouse", func(t *testing.T) {
		w, a, p, v := planetMissileWorld(t)
		p.Ground = 25
		p.Production = [3]float64{1, 10000, 1}
		p.Cargo = [3]float64{10, 100000, 10}
		p.Bank = 0
		intent, err := w.PrepareMissile(a.ID, 2, 10, v)
		if err != nil {
			t.Fatal(err)
		}
		draws := 0
		out, err := w.CommitMissile(intent, v, func() float64 { draws++; return .5 }, clock)
		if err != nil {
			t.Fatal(err)
		}
		if out.Primary.GroundMissiles != 2 || out.Primary.ProductionMissiles != 8 || out.Primary.PlanetMissiles != 10 || draws != 26 {
			t.Fatal(out.Primary, "draws", draws)
		}
		if p.Production != [3]float64{0, 2000, 0} || p.Cargo != [3]float64{0, 20000, 0} || out.Primary.PlanetDestroyed {
			t.Fatal("unexpected production or warehouse result", p, out.Primary)
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	})
	t.Run("destruction atomically revokes all landing sessions", func(t *testing.T) {
		w, a, p, v := planetMissileWorld(t)
		p.Ground = 25
		p.Production = [3]float64{1, 1, 1}
		ownerCredits := w.Players[p.Owner].Credits
		attackerCredits := a.Credits
		landed, err := w.Join("landed", "Landed")
		if err != nil {
			t.Fatal(err)
		}
		landed.Sector, landed.LandedPlanet, landed.PlanetToken = 2, 2, "0123456789abcdef0123456789abcdef"
		intent, err := w.PrepareMissile(a.ID, 2, 10, v)
		if err != nil {
			t.Fatal(err)
		}
		out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
		if err != nil {
			t.Fatal(err)
		}
		if !out.Primary.PlanetDestroyed || w.Planets[2] != nil || w.Sectors[2].Planet != 0 || landed.PlanetToken != "" || landed.LandedPlanet != 0 {
			t.Fatal(out.Primary, w.Sectors[2], landed)
		}
		if landed.Sector != 2 || landed.Death != nil || a.Death != nil || w.Players[p.Owner].Death != nil || a.Credits != attackerCredits || w.Players[p.Owner].Credits != ownerCredits {
			t.Fatal("planet destruction affected a ship, owner or account", landed, a, w.Players[p.Owner])
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	})
}

func TestProductionBombardmentPreservesCachedOreEligibility(t *testing.T) {
	production := [3]float64{100, 1, 1}
	budget := maxMissileRounds
	used, rates, _, destroyed, err := resolveMissileProduction(3, production, [3]float64{}, func() float64 { return .99 }, &budget)
	if err != nil {
		t.Fatal(err)
	}
	if used != 3 || rates != [3]float64{} || !destroyed {
		t.Fatal("positive entry ore must keep the production loop eligible", used, rates, destroyed)
	}
	production = [3]float64{0, 1, 1}
	budget = maxMissileRounds
	used, rates, _, destroyed, err = resolveMissileProduction(3, production, [3]float64{}, func() float64 { return .99 }, &budget)
	if err != nil {
		t.Fatal(err)
	}
	if used != 1 || rates != [3]float64{} || !destroyed {
		t.Fatal("zero entry ore should stop when both live secondary rates exhaust", used, rates, destroyed)
	}
}
func TestGroundMissileBoundsFractionalRoundingAndRNG(t *testing.T) {
	remaining, err := ResolveMissileGround(2, 50, func() float64 { return .01 })
	if err != nil || remaining != 49 {
		t.Fatal(remaining, err)
	} // .25+.25, floor only once
	remaining, err = ResolveMissileGround(1, 25, func() float64 { return .999 })
	if err != nil || remaining != 0 {
		t.Fatal(remaining, err)
	} // last round can floor ground to zero
	for _, r := range []float64{math.NaN(), math.Inf(1), -1, 1} {
		if _, err = ResolveMissileGround(1, 25, func() float64 { return r }); err == nil {
			t.Fatal(r)
		}
	}
	if _, err = ResolveMissileGround(2, 25, func() float64 { t.Fatal("unsafe volley draw"); return 0 }); err == nil {
		t.Fatal("production overrun")
	}
}
func TestGroundMissileResearchFixtures(t *testing.T) {
	var rows []struct {
		Name                        string
		Missiles, Ground, Remaining int64
		Draw                        float64
	}
	data, err := os.ReadFile("testdata/planet-ground-missiles.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(data, &rows); err != nil {
		t.Fatal(err)
	}
	for _, row := range rows {
		t.Run(row.Name, func(t *testing.T) {
			got, err := ResolveMissileGround(row.Missiles, row.Ground, func() float64 { return row.Draw })
			if err != nil || got != row.Remaining {
				t.Fatal(got, row, err)
			}
		})
	}
}
