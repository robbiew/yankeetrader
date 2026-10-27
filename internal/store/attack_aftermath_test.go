package store

import (
	"encoding/json"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"testing"
	"time"
)

func TestEarthAttackAftermathRollbackAndConcurrentClaims(t *testing.T) {
	s := create(t)
	var intent game.AttackIntent
	if err := s.Update(func(w *game.World) error {
		a, err := w.Join("attacker", "Attacker")
		if err != nil {
			return err
		}
		a.Fighters = 100
		a.Cloak = 0
		d := w.Players[1]
		d.Cloak = 0
		d.Fighters, d.Shields = 0, 0
		d.Mines = 100
		d.Turns = 37
		intent, err = w.PrepareAttack(a.ID, d.ID, 1)
		return err
	}); err != nil {
		t.Fatal(err)
	}
	oldSession := s.ForShip(1, 0)
	before, _ := s.View()
	saved, _ := json.Marshal(before)
	apply := func(w *game.World) error {
		_, err := w.CommitAttack(intent, func() float64 { return .5 }, time.Now())
		return err
	}
	if err := s.Update(func(w *game.World) error {
		if err := apply(w); err != nil {
			return err
		}
		return errors.New("later phase failed")
	}); err == nil {
		t.Fatal("abort accepted")
	}
	after, _ := s.View()
	actual, _ := json.Marshal(after)
	if string(actual) != string(saved) {
		t.Fatal("aftermath rollback lost resources")
	}
	results := make(chan error, 2)
	for i := 0; i < 2; i++ {
		go func() { results <- s.Update(apply) }()
	}
	successes := 0
	for i := 0; i < 2; i++ {
		if <-results == nil {
			successes++
		}
	}
	if successes != 1 {
		t.Fatal("multiple settlements", successes)
	}
	after, _ = s.View()
	if after.Players[1].Mines != 0 || after.Players[2].Mines != 50 || after.Sectors[1].Defense != nil {
		t.Fatal("wrong mine conservation or spawn hazard")
	}
	if _, err := oldSession.View(); !errors.Is(err, game.ErrShipDestroyed) {
		t.Fatal("victim session not invalidated", err)
	}
	if err := s.Update(func(w *game.World) error { return w.LoginShip(1, time.Now()) }); err != nil {
		t.Fatal(err)
	}
	after, _ = s.View()
	if after.Players[1].Sector != 1 || after.Players[1].Turns != 37 || after.Players[1].Mines != 0 {
		t.Fatal("unsafe replacement or turn refill")
	}
	if _, err := oldSession.View(); !errors.Is(err, game.ErrShipChanged) {
		t.Fatal("old session regained access", err)
	}
}
