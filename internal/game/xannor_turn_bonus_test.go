package game

import (
	"encoding/json"
	"testing"
)

func TestXannorTurnBonusFloorAndDailyCap(t *testing.T) {
	for _, tc := range []struct{ destroyed, turns, want int64 }{
		{0, 0, 0}, {199, 0, 0}, {200, 0, 1}, {399, 0, 1}, {400, 0, 2},
		{400, 499, 1}, {400, 500, 0}, {1000000, 0, 500}, {200, -1, 0}, {200, 501, 0},
	} {
		if got := xannorTurnBonus(XannorOwner, tc.destroyed, tc.turns); got != tc.want {
			t.Fatalf("kills%d turns%d: %d want%d", tc.destroyed, tc.turns, got, tc.want)
		}
	}
	for _, owner := range []int{MercenaryOwner, 0, 1, 2} {
		if got := xannorTurnBonus(owner, 1000000, 0); got != 0 {
			t.Fatal("non-Xannor bonus", owner, got)
		}
	}
}

func xannorTurnWorld(t *testing.T, owner int, defenders, turns int64) (*World, *Player, DefenseIntent) {
	t.Helper()
	w, p := setup(t)
	p.Sector = 8
	p.Fighters = 10000
	p.Shields = 1000000
	p.Turns = turns
	p.Cloak = 0
	w.Sectors[8].Defense = &SectorDefense{Owner: owner, Fighters: defenders}
	e, err := w.PrepareDefenseFight(p.ID, 8, p.Fighters, false)
	if err != nil {
		t.Fatal(err)
	}
	return w, p, e
}
func TestXannorTurnBonusConfirmedBattleAndReplay(t *testing.T) {
	for _, kills := range []int64{199, 200, 399, 400} {
		w, p, e := xannorTurnWorld(t, XannorOwner, kills, 100)
		out, err := w.CommitDefense(e, func() float64 { return .9 }, clock)
		want := kills / 200
		if err != nil || out.TurnBonus != want || p.Turns != 100+want {
			t.Fatal(kills, out, err, p.Turns)
		}
		entries := combatEvents(w, "xannor-turn-bonus")
		if want == 0 && len(entries) != 0 || want > 0 && (len(entries) != 1 || entries[0].Combat.Amount != want || entries[0].Combat.Secondary != kills || entries[0].Combat.Sector != 8) {
			t.Fatal(entries)
		}
		before, _ := json.Marshal(w)
		if _, err = w.CommitDefense(e, func() float64 { t.Fatal("replay drew RNG"); return 0 }, clock); err == nil {
			t.Fatal("replay accepted")
		}
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("replay changed world")
		}
		if err = w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}
func TestXannorTurnBonusPartialLossEscapesWithCreditedTurns(t *testing.T) {
	w, p, e := xannorTurnWorld(t, XannorOwner, 1000, 100)
	p.Fighters = 500
	e.Fighters = 500
	draw := 0
	out, err := w.CommitDefense(e, func() float64 {
		draw++
		if draw <= 12 {
			return .9
		}
		return 0
	}, clock)
	if err != nil || !out.Escaped || out.Battle.Defenders == 0 || out.Battle.DefenderLosses < 200 || out.TurnBonus != out.Battle.DefenderLosses/200 || p.Turns != 100+out.TurnBonus {
		t.Fatal(out, err, p.Turns)
	}
	if len(combatEvents(w, "xannor-turn-bonus")) != 1 {
		t.Fatal(w.News)
	}
}
func TestXannorTurnBonusExcludedOwnersAndWeapons(t *testing.T) {
	w, p := setup(t)
	other, _ := w.Join("enemy", "Enemy")
	for _, owner := range []int{MercenaryOwner, other.ID} {
		w, p, e := xannorTurnWorld(t, owner, 400, 100)
		if owner > 0 {
			_, _ = w.Join("enemy", "Enemy")
		}
		out, err := w.CommitDefense(e, func() float64 { return .9 }, clock)
		if err != nil || out.TurnBonus != 0 || p.Turns != 100 || len(combatEvents(w, "xannor-turn-bonus")) != 0 {
			t.Fatal(owner, out, err)
		}
	}
	w, p = plasmaWorld(t, 8)
	p.Turns = 100
	w.Sectors[2].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 400}
	firePlasma(t, w, p, 2, 1, func() float64 { return .5 })
	if p.Turns != 99 || len(combatEvents(w, "xannor-turn-bonus")) != 0 {
		t.Fatal("plasma granted turn bonus")
	}
	w, p, _, v := missileWorld(t)
	p.Turns = 100
	w.Sectors[2].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 400}
	e, err := w.PrepareMissile(p.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitMissile(e, v, func() float64 { return .5 }, clock); err != nil {
		t.Fatal(err)
	}
	if p.Turns != 99 || len(combatEvents(w, "xannor-turn-bonus")) != 0 {
		t.Fatal("missile granted turn bonus")
	}
}

func TestXannorTurnBonusEntryCapAndFatalMineAftermath(t *testing.T) {
	w, p, _ := xannorTurnWorld(t, XannorOwner, 400, 500)
	p.Sector = 7
	p.Shields = 0
	p.Holds = 1
	other, _ := w.Join("mine-owner", "Mine Owner")
	w.Sectors[7].Warps = []int{8}
	w.Sectors[8].Minefield = []MineLayer{{Owner: other.ID, Count: 1}}
	e, err := w.PrepareDefenseFight(p.ID, 8, p.Fighters, false)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitDefense(e, func() float64 { return .9 }, clock)
	if err != nil || out.TurnBonus != 1 || p.Death == nil || !out.Mines.Destroyed || p.Turns != 500 {
		t.Fatal(out, err, p)
	}
	entries := combatEvents(w, "xannor-turn-bonus")
	if len(entries) != 1 || entries[0].Combat.Amount != 1 || entries[0].Combat.Secondary != 400 {
		t.Fatal(entries)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestXannorTurnBonusNewsValidationAndMigration(t *testing.T) {
	w, p, e := xannorTurnWorld(t, XannorOwner, 400, 100)
	if _, err := w.CommitDefense(e, func() float64 { return .9 }, clock); err != nil {
		t.Fatal(err)
	}
	entries := combatEvents(w, "xannor-turn-bonus")
	if len(entries) != 1 {
		t.Fatal(entries)
	}
	payload := entries[0].Combat
	payload.Amount = 3
	if w.Validate() == nil {
		t.Fatal("bonus exceeds casualty formula")
	}
	payload.Amount = 2
	w.Version = 31
	if w.Upgrade() == nil {
		t.Fatal("legacy bonus accepted")
	}
	w.News = nil
	w.NextNews = 1
	turns := p.Turns
	if err := w.Upgrade(); err != nil || w.Version != WorldVersion || p.Turns != turns || len(w.News) != 0 {
		t.Fatal("migration changed balance/history", err)
	}
}
