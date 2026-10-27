package game

import (
	"encoding/json"
	"math"
	"os"
	"reflect"
	"testing"
)

func TestRecoveredShipDuelModel(t *testing.T) {
	var cases []struct {
		Name                          string
		Committed, Defenders, Shields int64
		Cloak                         float64
		Draws                         []float64
		Expected                      ShipDuelResult
	}
	b, err := os.ReadFile("testdata/ship-duel-model.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(b, &cases); err != nil {
		t.Fatal(err)
	}
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			n := 0
			rng := func() float64 { r := c.Draws[n%len(c.Draws)]; n++; return r }
			got, err := ResolveShipDuel(c.Committed, c.Defenders, c.Shields, c.Cloak, rng)
			if err != nil || !reflect.DeepEqual(got, c.Expected) {
				t.Fatal("recovered model mismatch", got, c.Expected, err)
			}
			if got.Survivors+got.AttackerLosses != c.Committed || got.DefenderFighters+got.DefenderLosses != c.Defenders {
				t.Fatal("fighter accounting lost resources")
			}
		})
	}
}

func TestShipDuelRejectsInvalidRNGAndBounds(t *testing.T) {
	for _, value := range []float64{math.NaN(), math.Inf(1), -.1, 1, 2} {
		result, err := ResolveShipDuel(10, 10, 10, 0, func() float64 { return value })
		if err == nil || result != (ShipDuelResult{}) {
			t.Fatal("bad RNG produced a partial outcome", result, err)
		}
	}
	for _, args := range [][3]int64{{0, 0, 0}, {-1, 10, 10}, {MaxQuantity + 1, 10, 10}, {1, -1, 0}, {1, 0, -1}, {1, MaxQuantity + 1, 0}, {1, 0, MaxQuantity + 1}} {
		if _, err := ResolveShipDuel(args[0], args[1], args[2], 0, func() float64 { return 0 }); err == nil {
			t.Fatal("invalid duel accepted", args)
		}
	}
	for _, cloak := range []float64{-.1, 1.1, math.NaN(), math.Inf(1)} {
		if _, err := ResolveShipDuel(10, 10, 10, cloak, func() float64 { return 0 }); err == nil {
			t.Fatal("invalid cloak accepted")
		}
	}
	if _, err := ResolveShipDuel(10, 10, 10, 0, nil); err == nil {
		t.Fatal("nil RNG accepted")
	}
	n := 0
	result, err := ResolveShipDuel(1, 0, MaxQuantity, 0, func() float64 { n++; return 0 })
	if err == nil || n != maxDuelRounds || result != (ShipDuelResult{}) {
		t.Fatal("unbounded or partial calculation", n, result, err)
	}
}

func TestCreditSalvageConsumesOnceAndTransfersEstate(t *testing.T) {
	w, victim, killer := ownedPortWorld(t)
	victim.Fighters, victim.Shields = 0, 0
	killer.Sector = victim.Sector
	victim.Credits, killer.Credits = 12345, 1005
	w.Ports[2].Owner, w.Ports[2].Treasury = victim.ID, 777
	ctx := DeathContext{Victim: victim.ID, Sector: victim.Sector, Killer: killer.ID, Cause: "combat"}
	before := victim.Credits + killer.Credits
	if err := w.SettleCreditSalvage(ctx, 6689, clock); err != nil {
		t.Fatal(err)
	}
	if victim.Credits != 5656 || killer.Credits != 7694 || victim.Credits+killer.Credits != before || victim.Death == nil || w.Ports[2].Owner != killer.ID || w.Ports[2].Treasury != 777 {
		t.Fatal("salvage duplicated or retitled assets", victim, killer)
	}
	if w.SettleCreditSalvage(ctx, 6689, clock) == nil {
		t.Fatal("death paid twice")
	}
	if err := w.ReplaceShip(victim.ID, clock); err != nil {
		t.Fatal(err)
	}
	victim.Sector = 2
	victim.Fighters, victim.Shields = 0, 0
	if w.SettleCreditSalvage(ctx, 100, clock) == nil {
		t.Fatal("old death claim paid on a replacement")
	}
	if killer.Credits != 7694 {
		t.Fatal("replay changed credits")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestCreditSalvagePreflightDoesNotPartiallyKill(t *testing.T) {
	for _, mode := range []string{"negative", "too-much", "capacity", "moved", "generation", "team", "still-defended", "cause"} {
		t.Run(mode, func(t *testing.T) {
			w, victim, killer := ownedPortWorld(t)
			killer.Sector = victim.Sector
			victim.Fighters, victim.Shields = 0, 0
			ctx := DeathContext{Victim: victim.ID, Sector: victim.Sector, Killer: killer.ID, Cause: "combat"}
			amount := int64(100)
			switch mode {
			case "negative":
				amount = -1
			case "too-much":
				amount = victim.Credits + 1
			case "capacity":
				killer.Credits = MaxMoney - 99
			case "moved":
				victim.Sector = 3
			case "generation":
				victim.ShipGeneration = 1
			case "team":
				_ = w.CreateTeam(victim.ID, "Orion", "ABCD")
				_ = w.JoinTeam(killer.ID, 1, "ABCD")
			case "still-defended":
				victim.Shields = 1
			case "cause":
				ctx.Cause = "self"
			}
			before, _ := json.Marshal(w)
			if w.SettleCreditSalvage(ctx, amount, clock) == nil {
				t.Fatal("invalid salvage accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("failed settlement partly changed world")
			}
		})
	}
}
