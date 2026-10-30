package game

import (
	"encoding/json"
	"math/rand"
	"reflect"
	"testing"
)

func revengeFight(t *testing.T, owner, sector int, missiles bool) (*World, *Player) {
	t.Helper()
	w := mobileWorld(t, 12)
	p, _ := w.Join("captain", "Captain")
	p.Sector, p.Fighters, p.Missiles = 7, 10000, 1
	w.Sectors[7].Warps = []int{sector}
	w.Sectors[sector].Warps = []int{7}
	w.Sectors[sector].Defense = &SectorDefense{Owner: owner, Fighters: 1}
	if missiles {
		v, _ := w.NewVisibility(p.ID)
		intent, err := w.PrepareMissile(p.ID, sector, 1, v)
		if err != nil {
			t.Fatal(err)
		}
		if _, err = w.CommitMissile(intent, v, func() float64 { return .9 }, clock); err != nil {
			t.Fatal(err)
		}
	} else {
		intent, err := w.PrepareDefenseFight(p.ID, sector, 10000, true)
		if err != nil {
			t.Fatal(err)
		}
		if _, err = w.CommitDefense(intent, func() float64 { return .9 }, clock); err != nil {
			t.Fatal(err)
		}
	}
	return w, p
}
func TestXannorRevengeQueuesOnlyActualHQVictory(t *testing.T) {
	for _, missiles := range []bool{false, true} {
		for _, tc := range []struct {
			owner, sector int
			want          bool
		}{{XannorOwner, 8, true}, {XannorOwner, 9, false}, {MercenaryOwner, 8, false}, {2, 8, false}} {
			// Owner2 is a real unrelated account, never an inferred faction owner.
			w := mobileWorld(t, 12)
			p, _ := w.Join("captain", "Captain")
			_, _ = w.Join("owner", "Owner")
			p.Sector, p.Fighters, p.Missiles = 7, 10000, 1
			w.Sectors[7].Warps = []int{tc.sector}
			w.Sectors[tc.sector].Warps = []int{7}
			w.Sectors[tc.sector].Defense = &SectorDefense{Owner: tc.owner, Fighters: 1}
			if missiles {
				v, _ := w.NewVisibility(p.ID)
				intent, e := w.PrepareMissile(p.ID, tc.sector, 1, v)
				if e != nil {
					t.Fatal(e)
				}
				if _, e = w.CommitMissile(intent, v, func() float64 { return .9 }, clock); e != nil {
					t.Fatal(e)
				}
			} else {
				intent, e := w.PrepareDefenseFight(p.ID, tc.sector, 10000, true)
				if e != nil {
					t.Fatal(e)
				}
				if _, e = w.CommitDefense(intent, func() float64 { return .9 }, clock); e != nil {
					t.Fatal(e)
				}
			}
			if w.HasXannorRevenge(p.ID) != tc.want || w.Sectors[tc.sector].Defense != nil {
				t.Fatal("incorrect revenge producer", tc, missiles)
			}
			wantCredits := int64(1005)
			if tc.want {
				wantCredits += XannorHQBonus
			}
			if p.Credits != wantCredits {
				t.Fatal("HQ reward eligibility")
			}
			validMobile(t, w)
		}
	}
	w, p := revengeFight(t, XannorOwner, 8, false)
	other, _ := w.Join("other", "Other")
	other.Sector = 9
	w.queueXannorRevenge(other.ID, 8, XannorOwner)
	if w.HasXannorRevenge(p.ID) || !w.HasXannorRevenge(other.ID) {
		t.Fatal("latest committed victory did not replace pending target")
	}
	w.queueXannorRevenge(p.ID, 9, XannorOwner)
	if !w.HasXannorRevenge(other.ID) {
		t.Fatal("ordinary kill cleared another target")
	}
}
func TestXannorRevengePartialFightAndStaleConfirmation(t *testing.T) {
	w := mobileWorld(t, 12)
	p, _ := w.Join("one", "One")
	p.Sector, p.Fighters = 7, 10
	w.Sectors[7].Warps = []int{8}
	w.Sectors[8].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 2}
	entry, err := w.PrepareDefenseFight(p.ID, 8, 1, false)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitDefense(entry, func() float64 { return 0 }, clock); err != nil {
		t.Fatal(err)
	}
	if w.Xannor.Revenge != nil || w.Sectors[8].Defense.Fighters != 2 {
		t.Fatal("HQ loss queued revenge")
	}
	p.Sector, p.Fighters = 7, 10
	entry, err = w.PrepareDefenseFight(p.ID, 8, 10, false)
	if err != nil {
		t.Fatal(err)
	}
	w.Sectors[8].Defense.Owner = MercenaryOwner
	if _, err = w.CommitDefense(entry, func() float64 { t.Fatal("stale defense drew"); return 0 }, clock); err == nil || w.Xannor.Revenge != nil {
		t.Fatal("stale HQ warning queued")
	}
}
func TestXannorRevengeLifetimeConsumptionAndProtectedTargets(t *testing.T) {
	for _, mode := range []string{"living", "protected", "dead", "generation", "missing", "no-force", "one-sector"} {
		w := mobileWorld(t, 12)
		p, _ := w.Join("one", "One")
		p.Sector = 10
		w.queueXannorRevenge(p.ID, 8, XannorOwner)
		switch mode {
		case "protected":
			p.Sector = 7
		case "dead":
			if err := w.RecordDeath(DeathContext{Victim: p.ID, Sector: 10, Cause: "hazard"}, clock); err != nil {
				t.Fatal(err)
			}
			if w.Xannor.Revenge != nil {
				t.Fatal("death retained pending target")
			}
			if err := w.ReplaceShip(p.ID, clock); err != nil {
				t.Fatal(err)
			}
		case "generation":
			p.ShipGeneration++
		case "missing":
			delete(w.Players, p.ID)
		case "no-force":
			w.xannorActions(clock, func() float64 { t.Fatal("empty phase drew"); return 0 })
		case "one-sector":
			for id := 9; id <= 12; id++ {
				delete(w.Sectors, id)
				delete(w.Ports, id)
			}
			p.Sector = 8
			w.xannorActions(clock, func() float64 { t.Fatal("one eligible sector retried"); return 0 })
		}
		if mode == "no-force" || mode == "one-sector" {
			if w.Xannor.Revenge != nil {
				t.Fatal("unavailable force/route retained revenge")
			}
			continue
		}
		revenge, sector := w.consumeXannorRevenge()
		if (mode == "living") != revenge || mode == "living" && sector != 10 || w.Xannor.Revenge != nil {
			t.Fatal("consumption", mode, revenge, sector)
		}
		if again, _ := w.consumeXannorRevenge(); again {
			t.Fatal("repeated consumption")
		}
	}
}
func TestXannorCandidateBoundEagerDrawsAndSharedPreference(t *testing.T) {
	for _, revenge := range []bool{false, true} {
		w := mobileWorld(t, 12)
		one, _ := w.Join("one", "One")
		two, _ := w.Join("two", "Two")
		one.Sector, two.Sector = 1, 2
		ids := []int{8, 9, 10, 11, 12}
		preferred := 0
		draws := 0
		target := w.xannorTarget(2, 9, ids, 12, 0, 0, &preferred, revenge, func() float64 { draws++; return 0 })
		attempts := 1
		if revenge {
			attempts = 25
		}
		if target != 8 || draws != 1+attempts*3 || preferred != 0 {
			t.Fatal("unbounded or lazy candidate draws", revenge, draws)
		}
		preferred = 11
		draws = 0
		w.xannorTarget(2, 9, ids, 12, 0, 0, &preferred, revenge, func() float64 { draws++; return 0 })
		if draws != 2 || preferred != 11 {
			t.Fatal("retained preference scanned players/retried")
		}
	}
	// Revenge still consumes the detection draw when accepting a hidden player.
	w := mobileWorld(t, 12)
	p, _ := w.Join("one", "One")
	p.Sector, p.Cloak = 10, 1
	for _, revenge := range []bool{false, true} {
		preferred := 0
		draws := 0
		got := w.xannorTarget(2, 9, []int{8, 9, 10, 11, 12}, 12, 0, 0, &preferred, revenge, func() float64 { draws++; return .5 })
		if draws != 3 || (revenge && got != 10) || (!revenge && preferred != 0) {
			t.Fatal("selection cloak bypass/draw", revenge, got, draws)
		}
	}
	// Candidate equality rejects; the separate ship .33 equality accepts.
	p.Cloak = .5
	preferred := 0
	w.xannorTarget(2, 9, []int{8, 9, 10, 11, 12}, 12, 0, 0, &preferred, false, mobileRNG(t, .99, .5, .5))
	if preferred != 0 {
		t.Fatal("candidate equality accepted")
	}
	p.Fighters, p.Shields = 500, 0
	force, work, pursuit := int64(500), 100, 0
	w.xannorShips(10, &force, &work, &pursuit, clock, func() float64 { return p.Cloak - .33 })
	if len(p.BattleReports) != 1 {
		t.Fatal("interception equality rejected")
	}
}
func TestXannorRevengeGroupOverridesAndSeededConservation(t *testing.T) {
	w := mobileWorld(t, 12)
	for _, slot := range []int{2, 15, 16, 19, 20} {
		for _, revenge := range []bool{false, true} {
			pref := 10
			got := w.xannorTarget(slot, 9, []int{8, 9, 10, 11, 12}, 12, 0, 0, &pref, revenge, mobileRNG(t, 0, 0))
			want := 10
			if slot == 20 || revenge && slot > 15 {
				want = 12
			}
			if got != want {
				t.Fatal("override", slot, revenge, got)
			}
			got = w.xannorTarget(slot, 9, []int{8, 9, 10, 11, 12}, 12, 4000, 1, &pref, revenge, mobileRNG(t, 0, 0))
			if got != 8 {
				t.Fatal("low HQ must win")
			}
		}
	}
	for seed := int64(0); seed < 32; seed++ {
		rng := rand.New(rand.NewSource(seed))
		w := mobileWorld(t, 32)
		p, _ := w.Join("one", "One")
		p.Sector = 1
		p.StoredScore = rng.Int63n(3000000)
		for id := 8; id <= 32; id++ {
			w.Sectors[id].Warps = nil
			if rng.Intn(3) != 0 {
				mobileGroup(w, id, []int64{1, 100, MaxQuantity}[rng.Intn(3)])
			}
		}
		w.queueXannorRevenge(p.ID, 8, XannorOwner)
		p.Sector = 7 // consumed, never entered
		before := xannorForce(w)
		draws := 0
		w.xannorActions(clock, func() float64 { draws++; return rng.Float64() })
		if xannorForce(w) != before || w.Xannor.Revenge != nil || draws > 136 {
			t.Fatal("seeded replay/force", seed, draws)
		}
		validMobile(t, w)
	}
}
func TestXannorRevengeMigrationAndInvalidTargets(t *testing.T) {
	w, p := revengeFight(t, XannorOwner, 8, false)
	for _, mode := range []string{"legacy", "missing", "dead", "generation"} {
		raw, _ := json.Marshal(w)
		var candidate World
		_ = json.Unmarshal(raw, &candidate)
		switch mode {
		case "legacy":
			candidate.Version = 16
		case "missing":
			candidate.Xannor.Revenge.Player = 50
		case "dead":
			candidate.Players[p.ID].Death = &Death{}
		case "generation":
			candidate.Xannor.Revenge.Generation++
		}
		if mode == "legacy" {
			if candidate.Upgrade() == nil {
				t.Fatal("legacy future revenge accepted")
			}
		} else if candidate.Validate() == nil {
			t.Fatal("invalid revenge target accepted", mode)
		}
	}
	old := mobileWorld(t, 12)
	old.Version = 16
	before := *old.Xannor
	if err := old.Upgrade(); err != nil || old.Version != WorldVersion || !reflect.DeepEqual(before, *old.Xannor) {
		t.Fatal("v16 migration invented revenge", err)
	}
}

func TestMissileHQPartialDamageQueuesOnlyFinishingVolley(t *testing.T) {
	w := mobileWorld(t, 12)
	p, _ := w.Join("one", "One")
	p.Sector, p.Missiles = 7, 2
	w.Sectors[7].Warps = []int{8}
	w.Sectors[8].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 5000}
	visibility, _ := w.NewVisibility(p.ID)
	for volley := 0; volley < 2; volley++ {
		entry, err := w.PrepareMissile(p.ID, 8, 1, visibility)
		if err != nil {
			t.Fatal(err)
		}
		if _, err = w.CommitMissile(entry, visibility, func() float64 { return .9 }, clock); err != nil {
			t.Fatal(err)
		}
		if volley == 0 {
			if w.Xannor.Revenge != nil || w.Sectors[8].Defense == nil || w.Sectors[8].Defense.Fighters != 500 {
				t.Fatal("partial impact queued revenge")
			}
		} else if !w.HasXannorRevenge(p.ID) || w.Sectors[8].Defense != nil {
			t.Fatal("finishing volley did not queue")
		}
	}
	validMobile(t, w)
}
