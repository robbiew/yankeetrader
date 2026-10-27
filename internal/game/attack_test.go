package game

import (
	"encoding/json"
	"testing"
	"time"
)

func TestAttackConfirmationRevalidatesBeforeRandomness(t *testing.T) {
	for _, name := range []string{"target moves", "attacker moves", "target replaced", "attacker replaced", "team changes", "force spent", "target dies"} {
		t.Run(name, func(t *testing.T) {
			w, d, a := ownedPortWorld(t)
			a.Sector = d.Sector
			a.Cloak, d.Cloak = 0, 0
			a.Fighters = 100
			intent, err := w.PrepareAttack(a.ID, d.ID, 50)
			if err != nil {
				t.Fatal(err)
			}
			switch name {
			case "target moves":
				d.Sector = 3
			case "attacker moves":
				a.Sector = 3
			case "target replaced":
				d.ShipGeneration++
			case "attacker replaced":
				a.ShipGeneration++
			case "team changes":
				a.Team = 1
				d.Team = 1
			case "force spent":
				a.Fighters = 49
			case "target dies":
				d.Death = &Death{}
			}
			before, _ := json.Marshal(w)
			_, err = w.CommitAttack(intent, func() float64 { t.Fatal("stale attack consumed randomness"); return 0 }, time.Now())
			after, _ := json.Marshal(w)
			if err == nil || string(before) != string(after) {
				t.Fatal("stale attack accepted or mutated state", err)
			}
		})
	}
}

func TestAttackSelectionAndSurvivingDuel(t *testing.T) {
	w, d, a := ownedPortWorld(t)
	a.Sector = d.Sector
	a.Cloak, d.Cloak = 0, 0
	a.Fighters = 100
	d.Fighters = 1000
	d.Shields = 50
	candidates, err := w.AttackCandidates(a.ID)
	if err != nil || len(candidates) != 1 || candidates[0].ID != d.ID {
		t.Fatal(candidates, err)
	}
	if _, err = w.PrepareAttack(a.ID, a.ID, 1); err == nil {
		t.Fatal("self attack")
	}
	for _, n := range []int64{0, -1, 101} {
		if _, err = w.PrepareAttack(a.ID, d.ID, n); err == nil {
			t.Fatal("invalid force", n)
		}
	}
	intent, _ := w.PrepareAttack(a.ID, d.ID, 10)
	turns := a.Turns
	result, err := w.CommitAttack(intent, func() float64 { return 0 }, time.Now())
	if err != nil || result.Destroyed || a.Fighters != 90 || d.Fighters != 1000 || d.Shields != 50 || a.Turns != turns {
		t.Fatal(result, err, a, d)
	}
}
