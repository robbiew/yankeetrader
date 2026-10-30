package store

import (
	"encoding/json"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"math"
	"testing"
	"time"
)

func TestDefenseBoundGateRollbackAndExpiredConfirmation(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		w.Players[1].Sector = 8
		w.Sectors[8].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 1}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	bound := s.ForShip(1, 0, 1)
	called := false
	if err := bound.Update(func(w *game.World) error { called = true; w.Players[1].Credits++; return nil }); !errors.Is(err, game.ErrDefenseEncounter) || called {
		t.Fatal(err, called)
	}
	w, _ := s.View()
	entry, err := w.PrepareDefenseFight(1, 8, 1, false)
	if err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(w)
	// Current hazards must be resolved before a current-sector battle.
	if err = s.Update(func(w *game.World) error { w.Sectors[8].Minefield = []game.MineLayer{{Count: 1}}; return nil }); err != nil {
		t.Fatal(err)
	}
	w, _ = s.View()
	entry.Mines = append([]game.MineLayer(nil), w.Sectors[8].Minefield...)
	// Current mines must resolve first, even through this dedicated entry point.
	if _, err = bound.DefenseEncounter(entry, func() float64 { return .5 }, time.Now(), time.Now().Add(time.Hour)); !errors.Is(err, game.ErrMineEncounter) {
		t.Fatal(err)
	}
	if err = s.Update(func(w *game.World) error { w.Sectors[8].Minefield = nil; return nil }); err != nil {
		t.Fatal(err)
	}
	entry.Mines = nil
	if _, err = bound.DefenseEncounter(entry, func() float64 { return math.NaN() }, time.Now(), time.Now().Add(time.Hour)); err == nil {
		t.Fatal("bad RNG")
	}
	w, _ = s.View()
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("failed encounter saved")
	}
	if _, err = bound.DefenseEncounter(entry, func() float64 { t.Fatal("expired RNG"); return 0 }, time.Now(), time.Now().Add(-time.Second)); err == nil {
		t.Fatal("expired confirmation")
	}
	if _, err = s.DefenseEncounter(entry, func() float64 { return .5 }, time.Now(), time.Now().Add(time.Hour)); err == nil {
		t.Fatal("unbound encounter")
	}
	out, err := bound.DefenseEncounter(entry, func() float64 { return .5 }, time.Now(), time.Now().Add(time.Hour))
	if err != nil || out.Battle.DefenderLosses != 1 {
		t.Fatal(out, err)
	}
	if err = bound.Update(func(w *game.World) error { w.Players[1].Credits++; return nil }); err != nil {
		t.Fatal(err)
	}
	w, _ = s.View()
	if w.Sectors[8].Defense != nil {
		t.Fatal("cleared defense restored")
	}
}

func TestDefenseVictoryAndMineFailureRollbackTogether(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Sector = 7
		p.Fighters = 10001
		p.Shields = 10000
		owner, err := w.Join("owner", "Owner")
		if err != nil {
			return err
		}
		w.Sectors[7].Warps = []int{8}
		w.Sectors[8].Defense = &game.SectorDefense{Owner: owner.ID, Fighters: 1000}
		w.Sectors[8].Minefield = []game.MineLayer{{Owner: owner.ID, Count: 1}}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	entry, err := w.PrepareDefenseFight(1, 8, 10001, true)
	if err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(w)
	// Surrender needs no draw; invalid mine RNG follows the entry and transfers.
	if _, err = s.ForShip(1, 0, 1).DefenseEncounter(entry, func() float64 { return math.NaN() }, time.Now(), time.Now().Add(time.Hour)); err == nil {
		t.Fatal("invalid aftermath")
	}
	w, _ = s.View()
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("entry/surrender saved despite failed mine aftermath")
	}
}
