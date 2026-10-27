package store

import (
	"encoding/json"
	"github.com/robbiew/yankeetrader/internal/game"
	"math"
	"testing"
	"time"
)

func TestConfirmedAttackSettlesOnceAndRollsBackLootFailure(t *testing.T) {
	for _, fail := range []bool{false, true} {
		t.Run(map[bool]string{false: "settled", true: "loot failure"}[fail], func(t *testing.T) {
			s := create(t)
			var intent game.AttackIntent
			if err := s.Update(func(w *game.World) error {
				a, err := w.Join("attacker", "Attacker")
				if err != nil {
					return err
				}
				a.Fighters = 100
				d := w.Players[1]
				d.Fighters = 1
				d.Shields = 1
				d.Credits = 10000
				w.Ports[2].Owner = d.ID
				w.Ports[2].Treasury = 777
				intent, err = w.PrepareAttack(a.ID, d.ID, 10)
				return err
			}); err != nil {
				t.Fatal(err)
			}
			before, err := s.View()
			if err != nil {
				t.Fatal(err)
			}
			saved, _ := json.Marshal(before)
			draws := 0
			apply := func(w *game.World) error {
				_, err := w.CommitAttack(intent, func() float64 {
					draws++
					if fail && draws > 2 {
						return math.NaN()
					}
					if draws == 1 {
						return .49
					}
					if draws == 2 {
						return 0
					}
					return .5
				}, time.Now())
				return err
			}
			err = s.Update(apply)
			after, loadErr := s.View()
			if loadErr != nil {
				t.Fatal(loadErr)
			}
			if fail {
				actual, _ := json.Marshal(after)
				if err == nil || string(saved) != string(actual) {
					t.Fatal("failed loot did not roll back whole attack", err)
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if after.Players[1].Death == nil || after.Ports[2].Owner != 2 || after.Ports[2].Treasury != 777 || after.Players[2].Credits != 6005 {
				t.Fatal("missing atomic rewards")
			}
			if err = s.Update(apply); err == nil {
				t.Fatal("replayed kill")
			}
		})
	}
}

func TestConcurrentConfirmedKillsHaveOneWinner(t *testing.T) {
	s := create(t)
	var intent game.AttackIntent
	if err := s.Update(func(w *game.World) error {
		a, err := w.Join("attacker", "Attacker")
		if err != nil {
			return err
		}
		a.Fighters = 100
		w.Players[1].Fighters = 1
		w.Players[1].Shields = 1
		intent, err = w.PrepareAttack(a.ID, 1, 10)
		return err
	}); err != nil {
		t.Fatal(err)
	}
	results := make(chan error, 2)
	for i := 0; i < 2; i++ {
		go func() {
			draws := 0
			results <- s.Update(func(w *game.World) error {
				_, err := w.CommitAttack(intent, func() float64 {
					draws++
					if draws == 1 {
						return .49
					}
					if draws == 2 {
						return 0
					}
					return .5
				}, time.Now())
				return err
			})
		}()
	}
	successes := 0
	for i := 0; i < 2; i++ {
		if <-results == nil {
			successes++
		}
	}
	if successes != 1 {
		t.Fatalf("%d successful kills", successes)
	}
}
