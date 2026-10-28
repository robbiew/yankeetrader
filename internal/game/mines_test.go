package game

import (
	"encoding/json"
	"errors"
	"math"
	"os"
	"reflect"
	"testing"
	"time"
)

func TestRecoveredMineBurstModel(t *testing.T) {
	var cases []struct {
		Name             string
		Player, Expected Player
		Burst            int64
		Draws            []float64
	}
	data, err := os.ReadFile("testdata/mine-model.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(data, &cases); err != nil {
		t.Fatal(err)
	}
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			i := 0
			err := mineBurst(&c.Player, c.Burst, func() float64 {
				if i >= len(c.Draws) {
					t.Fatal("extra random draw")
				}
				r := c.Draws[i]
				i++
				return r
			})
			if err != nil || !reflect.DeepEqual(c.Player, c.Expected) || i != len(c.Draws) {
				t.Fatal(c.Player, c.Expected, err, i)
			}
		})
	}
}

func TestMineBurstDepletionAndSafeZeroTurnEscape(t *testing.T) {
	w, p := setup(t)
	p.Sector = 2
	p.Shields = 100000
	p.Holds = 10
	w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 20}}
	out, err := w.ResolveMinefield(p.ID, func() float64 { return .5 }, clock)
	if err != nil || out.Bursts != 19 || out.Spent != 20 || p.Shields != 90000 || len(w.Sectors[2].Minefield) != 0 {
		t.Fatal(out, p, err)
	}
	p.Holds = 9
	p.Turns = 0
	p.Shields = 1000
	w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 2}}
	draws := []float64{0, .9, 0, 0, 0, 0, 0} // shield hit, escape gate, cool warp, safe destination, overwritten draw, recharge
	i := 0
	out, err = w.ResolveMinefield(p.ID, func() float64 { r := draws[i]; i++; return r }, clock)
	if err != nil || !out.Escaped || out.Sector != 1 || p.Turns != 0 || w.Sectors[2].Minefield[0].Count != 1 {
		t.Fatal(out, p, err)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestLethalMineSourceSurvivesChainedDeaths(t *testing.T) {
	w, victim, attacker := ownedPortWorld(t)
	attacker.Sector = victim.Sector
	attacker.Cloak, victim.Cloak = 0, 0
	victim.Fighters, victim.Shields = 0, 0
	victim.Mines = 100
	attacker.Fighters = 1
	attacker.Shields = 0
	attacker.Holds = 10
	attacker.Mines = 0
	w.Ports[2].Owner = victim.ID
	w.Ports[2].Treasury = 777
	intent, err := w.PrepareAttack(attacker.ID, victim.ID, 1)
	if err != nil {
		t.Fatal(err)
	}
	// Zero salvage draws preserve all wreck mines. Then large exposed-damage draws
	// eliminate empty holds before an escape may run.
	draws := 0
	result, err := w.CommitAttack(intent, func() float64 {
		draws++
		if draws <= 6 {
			return 0
		}
		return math.Nextafter(1, 0)
	}, clock)
	if err != nil {
		t.Fatal(err)
	}
	if !result.Destroyed || !result.MineAftermath.Destroyed || attacker.Death.Cause != "mines" || attacker.Death.Killer != victim.ID || victim.Death.Killer != attacker.ID {
		t.Fatal(result, attacker.Death, victim.Death)
	}
	if w.Ports[2].Owner != 0 || w.Ports[2].Treasury != 0 {
		t.Fatal("dead source received estate")
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	for _, p := range []*Player{victim, attacker} {
		turns := p.Turns
		if err = w.ReplaceShip(p.ID, clock); err != nil {
			t.Fatal("false suicide cooldown", err)
		}
		if p.Turns != turns || p.Sector != 1 {
			t.Fatal("replacement refilled turns")
		}
	}
}

func TestMineEntryConfirmationAndRawMovementGate(t *testing.T) {
	w, p := setup(t)
	w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 1}}
	if err := w.Move(p.ID, 2); err == nil {
		t.Fatal("unconfirmed entry")
	}
	entry, err := w.PrepareMineEntry(p.ID, 2)
	if err != nil {
		t.Fatal(err)
	}
	w.Sectors[2].Minefield[0].Count = 2
	_, err = w.CommitMineEntry(entry, func() float64 { t.Fatal("stale warning RNG"); return 0 }, clock)
	if err == nil || p.Sector != 1 {
		t.Fatal("stale warning committed")
	}
	p.Sector = 2
	if err = w.Move(p.ID, 3); !errors.Is(err, ErrMineEncounter) {
		t.Fatal("left unresolved mines", err)
	}
}

func TestMinefieldValidationAndInvalidRNG(t *testing.T) {
	for _, layers := range [][]MineLayer{{{Owner: 999, Count: 1}}, {{Owner: -1, Count: 1}}, {{Owner: 0, Count: 0}}, {{Owner: 0, Count: 1}, {Owner: 0, Count: 2}}, {{Owner: 0, Count: MaxQuantity + 1}}} {
		w, _ := setup(t)
		w.Sectors[2].Minefield = layers
		if w.Validate() == nil {
			t.Fatal("invalid field", layers)
		}
	}
	w, p := setup(t)
	w.Sectors[1].Minefield = []MineLayer{{Owner: 0, Count: 1}}
	if w.Validate() == nil {
		t.Fatal("Earth field")
	}
	w.Sectors[1].Minefield = nil
	p.Sector = 2
	w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 1}}
	if _, err := w.ResolveMinefield(p.ID, func() float64 { return math.NaN() }, time.Now()); err == nil {
		t.Fatal("bad RNG accepted")
	}
}

func TestMineSourceAttributionAndFIFOWithoutRemoteRewards(t *testing.T) {
	for _, source := range []int{0, 1, 2} {
		t.Run(string(rune('0'+source)), func(t *testing.T) {
			w, p := setup(t)
			owner, _ := w.Join("owner", "Owner")
			owner.Credits = 1234
			p.Sector = 2
			p.Holds = 1
			p.Fighters, p.Shields = 0, 0
			p.Cloak = 0
			p.Mines = 0
			p.Turns = 37
			w.Ports[2].Owner = p.ID
			w.Ports[2].Treasury = 777
			other := 0
			if source == 0 {
				other = owner.ID
			}
			w.Sectors[2].Minefield = []MineLayer{{Owner: source, Count: 1}, {Owner: other, Count: 2}}
			out, err := w.ResolveMinefield(p.ID, func() float64 { return .99 }, clock)
			if err != nil || !out.Destroyed || out.Killer != source || p.Death.Killer != source || p.Death.Cause != "mines" {
				t.Fatal(out, p.Death, err)
			}
			if owner.Credits != 1234 || w.Ports[2].Owner != 0 || w.Ports[2].Treasury != 0 {
				t.Fatal("remote mine reward invented")
			}
			field := w.Sectors[2].Minefield
			if len(field) != 1 || field[0].Owner != other || field[0].Count != 2 {
				t.Fatal("FIFO attribution lost", field)
			}
			if err = w.ReplaceShip(p.ID, clock); err != nil {
				t.Fatal("mine death treated as voluntary suicide", err)
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestMineEscapeMeltdownUsesRemainingTurnsAndSafeDestination(t *testing.T) {
	w, p := setup(t)
	p.Sector = 2
	p.Shields = 1000000
	p.Holds = 9
	p.Turns = 37
	w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 2}}
	draws := []float64{0, .9, .99, .99}
	for i := 0; i < 31; i++ {
		draws = append(draws, .9)
	}
	draws = append(draws, 0, 0, 0)
	i := 0
	out, err := w.ResolveMinefield(p.ID, func() float64 { r := draws[i]; i++; return r }, clock)
	if err != nil || !out.Escaped || p.Turns != 0 || p.Sector != 1 || i != len(draws) {
		t.Fatal(out, p.Turns, err, i)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}
