package game

import (
	"encoding/json"
	"math"
	"testing"
)

func TestCloakPurchasingLimitsCreditsAndNoScoreBonus(t *testing.T) {
	for _, tc := range []struct {
		cloak        float64
		cash, points int64
		ok           bool
	}{
		{0, 999, 1, false}, {0, 1000, 1, true}, {0, 1001, 1, true}, {.37, 10000, 10, true},
		{.9, 10000, 10, true}, {.9, MaxMoney, 11, false}, {1, MaxMoney, 1, false},
		{0, MaxMoney, 0, false}, {0, MaxMoney, -1, false}, {0, MaxMoney, math.MaxInt64, false},
		{.995, MaxMoney, 1, false}, {.8, MaxMoney, 20, true},
	} {
		w, p := setup(t)
		p.Cloak = tc.cloak
		p.Credits = tc.cash
		p.StoredScore = 123
		if err := w.Dock(p.ID, clock); err != nil {
			t.Fatal(err)
		}
		before, _ := json.Marshal(w)
		old := w.rankingSnapshot(false).Players[0].Score
		err := w.Equip(p.ID, p.DockToken, "cloak", tc.points, clock)
		if (err == nil) != tc.ok {
			t.Fatalf("%+v: %v", tc, err)
		}
		if !tc.ok {
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("refused purchase mutated")
			}
			continue
		}
		if p.Credits != tc.cash-tc.points*CloakPointPrice || math.Abs(p.Cloak-math.Min(1, tc.cloak+float64(tc.points)/100)) > 1e-12 || p.StoredScore != 123 || p.Turns != 499 || w.Ports[1].Treasury != 0 {
			t.Fatal("purchase accounting", tc, p)
		}
		wantScore := old - tc.points*CloakPointPrice
		if tc.cash == MaxMoney {
			wantScore = MaxMoney
		}
		if w.rankingSnapshot(false).Players[0].Score != wantScore {
			t.Fatal("cloak asset bonus")
		}
		if err = w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
	w, p := setup(t)
	p.Cloak = .9
	p.Credits = MaxMoney
	_ = w.Dock(p.ID, clock)
	limit, err := w.CloakPurchaseLimit(p.ID, p.DockToken, clock)
	if err != nil || limit != 10 {
		t.Fatal(limit, err)
	}
	p.Cloak = 0
	p.Credits = 1999
	limit, err = w.CloakPurchaseLimit(p.ID, p.DockToken, clock)
	if err != nil || limit != 1 {
		t.Fatal(limit, err)
	}
	token := p.DockToken
	if _, err = w.CloakPurchaseLimit(p.ID, token, p.DockUntil); err == nil {
		t.Fatal("expired quote")
	}
	if err = w.Equip(p.ID, "wrong", "cloak", 1, clock); err == nil {
		t.Fatal("wrong docking token")
	}
	p.Sector = 2
	if err = w.Equip(p.ID, token, "cloak", 1, clock); err == nil {
		t.Fatal("remote cloak")
	}
}

func TestAntiCloakPaidScopeRepeatsIncarnationsAndNormalDecay(t *testing.T) {
	w, p := setup(t)
	p.Credits = 3 * AntiCloakPrice
	p.Cloak = 1
	p.StoredScore = 987
	a, _ := w.Join("a", "Hidden")
	a.Sector = 2
	a.Cloak = 1
	b, _ := w.Join("b", "Distant")
	b.Sector = 8
	b.Cloak = .5
	zero, _ := w.Join("z", "Uncloaked")
	zero.Cloak = 0
	_ = w.Dock(p.ID, clock)
	v, _ := w.NewVisibility(p.ID)
	observer, _ := w.NewVisibility(p.ID)
	for i, want := range []int{2, 0} {
		e, err := w.PrepareAntiCloak(p.ID, p.DockToken, v, clock)
		if err != nil {
			t.Fatal(err)
		}
		out, err := w.CommitAntiCloak(e, v, clock)
		if err != nil || len(out.Revealed) != want || out.Spent != AntiCloakPrice || out.Balance != int64(2-i)*AntiCloakPrice || p.Cloak != 1 || a.Cloak != 1 || b.Cloak != .5 || p.StoredScore != 987 || p.Turns != 499 || w.Ports[1].Treasury != 0 {
			t.Fatal("activation accounting", out, err)
		}
		if _, err = w.CommitAntiCloak(e, v, clock); err == nil {
			t.Fatal("model replay")
		}
	}
	if v.AntiCloakActivations() != 2 || observer.sees(a) || !v.sees(a) || !v.sees(b) {
		t.Fatal("login isolation")
	}
	fresh, _ := w.NewVisibility(p.ID)
	if fresh.sees(a) || fresh.AntiCloakActivations() != 0 {
		t.Fatal("reconnect inherited activation")
	}
	a.ShipGeneration++
	if v.sees(a) {
		t.Fatal("replacement inherited reveal")
	}
	later, _ := w.Join("later", "Later")
	if v.sees(later) {
		t.Fatal("future ship inherited reveal")
	}
	p.Turns = 476
	p.spendTurn()
	if p.Turns != 475 || math.Abs(p.Cloak-.99) > 1e-12 {
		t.Fatal("activation suspended normal decay")
	}
	if _, err := w.PrepareAntiCloak(p.ID, p.DockToken, observer, clock); err != nil {
		t.Fatal(err)
	}
	p.ShipGeneration++
	if _, err := w.PrepareAntiCloak(p.ID, p.DockToken, v, clock); err == nil {
		t.Fatal("stale observer")
	}
}

func TestAntiCloakStaleQuotesAndStagedRollback(t *testing.T) {
	for _, mutate := range []func(*World, *Player){
		func(w *World, p *Player) { p.Credits-- }, func(w *World, p *Player) { p.Cloak = .5 },
		func(w *World, p *Player) { p.Turns-- }, func(w *World, p *Player) { p.DockUntil = p.DockUntil.AddDate(0, 0, 1) },
		func(w *World, p *Player) { w.LastMaintenance = "2026-10-25" },
	} {
		w, p := setup(t)
		p.Credits = 1000000
		_ = w.Dock(p.ID, clock)
		v, _ := w.NewVisibility(p.ID)
		e, err := w.PrepareAntiCloak(p.ID, p.DockToken, v, clock)
		if err != nil {
			t.Fatal(err)
		}
		mutate(w, p)
		before, _ := json.Marshal(w)
		if _, err = w.CommitAntiCloak(e, v, clock); err == nil {
			t.Fatal("stale quote")
		}
		after, _ := json.Marshal(w)
		if string(before) != string(after) || v.AntiCloakActivations() != 0 {
			t.Fatal("stale quote mutated")
		}
	}
	w, p := setup(t)
	p.Credits = AntiCloakPrice
	_ = w.Dock(p.ID, clock)
	v, _ := w.NewVisibility(p.ID)
	e, _ := w.PrepareAntiCloak(p.ID, p.DockToken, v, clock)
	staged, finish := v.StageAntiCloak()
	out, err := w.CommitAntiCloak(e, staged, clock)
	finish(false)
	if err != nil || len(out.Revealed) != 0 || v.AntiCloakActivations() != 0 {
		t.Fatal("staging", out, err)
	}
	// The world debit above is only a model operation; Store rollback also discards it.
}
