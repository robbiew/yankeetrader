package game

import (
	"testing"
	"time"
)

func TestEarthAttackConservesAndDisarmsVictimMines(t *testing.T) {
	w, d, a := ownedPortWorld(t)
	a.Sector, d.Sector = 1, 1
	a.Cloak, d.Cloak = 0, 0
	a.Fighters = 100
	d.Fighters, d.Shields = 0, 0
	d.Mines = 100
	a.Mines = 7
	intent, err := w.PrepareAttack(a.ID, d.ID, 1)
	if err != nil {
		t.Fatal(err)
	}
	result, err := w.CommitAttack(intent, func() float64 { return .5 }, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	if !result.Destroyed || result.Salvage.Mines != 50 || result.DisarmedMines != 50 || d.Mines != 0 || a.Mines != 57 {
		t.Fatal(result, d.Mines, a.Mines)
	}
	if w.Sectors[1].Defense != nil {
		t.Fatal("Earth hazard")
	}
	generation := d.ShipGeneration
	if _, err = w.CommitAttack(intent, func() float64 { t.Fatal("replay RNG"); return 0 }, time.Now()); err == nil {
		t.Fatal("replayed aftermath")
	}
	if d.ShipGeneration != generation || a.Mines != 57 {
		t.Fatal("replayed awards")
	}
	if err = w.ReplaceShip(d.ID, time.Now()); err != nil {
		t.Fatal(err)
	}
	if d.Sector != 1 || d.Mines != 0 {
		t.Fatal("unsafe replacement")
	}
	newcomer, err := w.Join("newcomer", "Newcomer")
	if err != nil {
		t.Fatal(err)
	}
	if newcomer.Sector != 1 || newcomer.Turns != 500 || newcomer.Fighters != 25 {
		t.Fatal("unsafe new arrival")
	}
	if err = w.Move(newcomer.ID, w.Sectors[1].Warps[0]); err != nil {
		t.Fatal("spawn exit blocked", err)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestMineBearingTargetCanBeAttackedOutsideEarth(t *testing.T) {
	w, d, a := ownedPortWorld(t)
	a.Sector = d.Sector
	a.Cloak, d.Cloak = 0, 0
	d.Mines = 1
	d.Fighters, d.Shields = 0, 0
	a.Shields = 10000
	intent, err := w.PrepareAttack(a.ID, d.ID, 1)
	if err != nil {
		t.Fatal(err)
	}
	result, err := w.CommitAttack(intent, func() float64 { return .5 }, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	if result.DroppedMines != 1 || result.MineAftermath.Spent != 1 || d.Mines != 0 || len(w.Sectors[2].Minefield) != 0 {
		t.Fatal(result)
	}
}
