package store

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"os"
	"testing"
	"time"
)

func TestXannorTurnBonusAtomicRollbackAndPersistence(t *testing.T) {
	st := create(t)
	at := time.Now().UTC()
	if err := st.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Sector = 8
		p.Turns = 100
		p.Fighters = 10000
		p.Shields = 1000000
		p.Cloak = 0
		w.Sectors[8].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 400}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	world, _ := st.View()
	e, err := world.PrepareDefenseFight(1, 8, 10000, false)
	if err != nil {
		t.Fatal(err)
	}
	path := st.Dir + "/world.json"
	before, _ := os.ReadFile(path)
	err = st.Update(func(w *game.World) error {
		out, err := w.CommitDefense(e, func() float64 { return .9 }, at)
		if err != nil {
			return err
		}
		if out.TurnBonus != 2 || w.Players[1].Turns != 102 {
			t.Fatal(out, w.Players[1].Turns)
		}
		return errors.New("injected failure after bonus and news")
	})
	if err == nil {
		t.Fatal("expected rollback")
	}
	after, _ := os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("bonus or newspaper partially saved")
	}
	bound := st.ForShip(1, e.Generation, e.Season)
	out, err := bound.DefenseEncounter(e, func() float64 { return .9 }, at, time.Now().Add(time.Minute))
	if err != nil || out.TurnBonus != 2 {
		t.Fatal(out, err)
	}
	saved, err := (Store{Dir: st.Dir}).View()
	if err != nil || saved.Players[1].Turns != 102 {
		t.Fatal(saved, err)
	}
	count := 0
	for _, n := range saved.News {
		if n.Combat != nil && n.Combat.Operation == "xannor-turn-bonus" {
			count++
			if n.Combat.Amount != 2 || n.Combat.Secondary != 400 {
				t.Fatal(n)
			}
		}
	}
	if count != 1 {
		t.Fatal("missing bonus newspaper", saved.News)
	}
	if _, err = bound.DefenseEncounter(e, func() float64 { t.Fatal("replay RNG"); return 0 }, at, time.Now().Add(time.Minute)); err == nil {
		t.Fatal("replayed bonus")
	}
}
