package store

import (
	"errors"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestConcurrentCreditSalvageClaimsPayOnce(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		_, err := w.Join("killer", "Killer")
		if err != nil {
			return err
		}
		w.Players[1].Credits = 12345
		w.Players[1].Fighters = 0
		w.Players[1].Shields = 0
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	before, _ := s.View()
	initial := before.Players[1].Credits + before.Players[2].Credits
	ctx := game.DeathContext{Victim: 1, Sector: 1, Killer: 2, Cause: "combat"}
	var wg sync.WaitGroup
	errs := make(chan error, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- s.Update(func(w *game.World) error { return w.SettleCreditSalvage(ctx, 6689, time.Now()) })
		}()
	}
	wg.Wait()
	close(errs)
	paid := 0
	for err := range errs {
		if err == nil {
			paid++
		}
	}
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	if paid != 1 || w.Players[2].Credits != 7694 || w.Players[1].Credits != 5656 || w.Players[1].Death == nil || w.Players[1].Credits+w.Players[2].Credits != initial {
		t.Fatal("salvage paid twice or lost money", paid, w.Players)
	}
	if _, err = s.ForShip(1, 0, 1).View(); !errors.Is(err, game.ErrShipDestroyed) {
		t.Fatal("victim session survived settlement", err)
	}
}

func TestDamageAndCreditSalvageRollBackTogether(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		_, err := w.Join("enemy", "Enemy")
		w.Players[1].Credits = 12345
		w.Players[1].Fighters = 10
		w.Players[1].Shields = 10
		w.Players[2].Fighters = 1000
		return err
	}); err != nil {
		t.Fatal(err)
	}
	apply := func(w *game.World) error {
		// Deliberately choose a deterministic duel. A future attack handler must
		// also verify cloak, weapons, confirmation and complete estate settlement.
		result, err := game.ResolveShipDuel(100, w.Players[1].Fighters, w.Players[1].Shields, 0, func() float64 { return .49 })
		if err != nil {
			return err
		}
		w.Players[2].Fighters -= result.AttackerLosses
		w.Players[1].Fighters, w.Players[1].Shields = result.DefenderFighters, result.DefenderShields
		if !result.Destroyed {
			return errors.New("test duel did not kill")
		}
		return w.SettleCreditSalvage(game.DeathContext{Victim: 1, Sector: 1, Killer: 2, Cause: "combat"}, 6689, time.Now())
	}
	if err := s.Update(func(w *game.World) error {
		if err := apply(w); err != nil {
			return err
		}
		return errors.New("future estate phase aborted")
	}); err == nil {
		t.Fatal("missing transaction abort")
	}
	w, _ := s.View()
	if w.Players[1].Death != nil || w.Players[1].Fighters != 10 || w.Players[1].Shields != 10 || w.Players[2].Fighters != 1000 || w.Players[2].Credits != 1005 {
		t.Fatal("partial combat settlement saved")
	}
	if err := s.ForShip(2, 0, 1).Update(apply); err != nil {
		t.Fatal(err)
	}
	w, _ = s.View()
	if w.Players[1].Death == nil || w.Players[1].Fighters != 0 || w.Players[1].Shields != 0 || w.Players[2].Credits != 7694 {
		t.Fatal("combat settlement incomplete")
	}
}
