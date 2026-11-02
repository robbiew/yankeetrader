package game

import (
	"encoding/json"
	"math"
	"testing"
)

func TestFighterWreckMinesNewsUsesDeployedRemainder(t *testing.T) {
	for _, test := range []struct {
		name   string
		sector int
		mines  int64
		want   int64
	}{
		{"non-Earth", 2, 3, 2}, {"Earth-disarmed", 1, 3, 0}, {"no-mines", 2, 0, 0},
	} {
		t.Run(test.name, func(t *testing.T) {
			w, d, a := ownedPortWorld(t)
			a.Sector, d.Sector = test.sector, test.sector
			a.Cloak, d.Cloak = 0, 0
			d.Mines = test.mines
			d.Fighters, d.Shields = 0, 0
			a.Shields = 10000
			intent, err := w.PrepareAttack(a.ID, d.ID, 1)
			if err != nil {
				t.Fatal(err)
			}
			result, err := w.CommitAttack(intent, func() float64 { return .5 }, clock)
			if err != nil {
				t.Fatal(err)
			}
			count := 0
			for _, event := range w.News {
				if event.Kind == NewsCombat && event.Combat.Operation == "wreck-mines" {
					count++
					if event.Alias != d.Alias || event.Combat.Sector != test.sector || event.Combat.Amount != test.want || event.Combat.Amount != result.DroppedMines {
						t.Fatal(event, result)
					}
				}
			}
			expected := 0
			if test.want > 0 {
				expected = 1
			}
			if count != expected {
				t.Fatal("wrong wreck publication count", count)
			}
			before, _ := json.Marshal(w)
			if _, err = w.CommitAttack(intent, func() float64 { t.Fatal("replay reached RNG"); return 0 }, clock); err == nil {
				t.Fatal("replayed kill")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("replay mutated or republished")
			}
		})
	}
}

func TestFighterNewsReservationPrecedesDuelDamage(t *testing.T) {
	w, d, a := ownedPortWorld(t)
	a.Sector = d.Sector
	a.Cloak, d.Cloak = 0, 0
	d.Mines = 5
	intent, err := w.PrepareAttack(a.ID, d.ID, 1)
	if err != nil {
		t.Fatal(err)
	}
	w.NextNews = math.MaxUint64 - 1
	before, _ := json.Marshal(w)
	if _, err = w.CommitAttack(intent, func() float64 { t.Fatal("exhausted journal reached RNG"); return 0 }, clock); err == nil {
		t.Fatal("journal exhaustion accepted")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("failed preflight changed world")
	}
}
