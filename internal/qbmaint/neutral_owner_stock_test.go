package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"strings"
	"testing"
)

type ownerExtra struct {
	Name       string
	Statistics struct {
		Neutral int `json:"neutral_transferred"`
		Events  []struct {
			Kind                 string
			Neutral              int `json:"neutral_transferred"`
			Force, Losses, Mines int
			InitialForce         int    `json:"initial_force"`
			InitialMines         int    `json:"initial_mines"`
			MinesSpent           int    `json:"mines_spent"`
			RNGDraws             int    `json:"rng_draws"`
			InitialState         uint32 `json:"initial_rng_state"`
			FinalState           uint32 `json:"final_rng_state"`
			Rolls                []int
		}
	}
}

func ownerLoad(t *testing.T) (friendlyFixture, map[string]ownerExtra) {
	t.Helper()
	b, e := os.ReadFile("testdata/neutral_owner_stock.json")
	if e != nil {
		t.Fatal(e)
	}
	var d friendlyFixture
	var extras struct{ Cases []ownerExtra }
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(b, &extras); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-neutral-owner-stock-v1" || len(d.Cases) != 18 || d.Audit.Comparisons != 108 || d.Audit.Files != 648 || d.Audit.Witnesses != 855 || d.Audit.Normalized != 0 {
		t.Fatal("complete owner/mine inventory")
	}
	index := map[string]ownerExtra{}
	for _, v := range extras.Cases {
		index[v.Name] = v
	}
	return d, index
}
func TestNeutralOwnerStockQualifiedMineOrderAndTransfer(t *testing.T) {
	d, extra := ownerLoad(t)
	acts, mines, transfers, captures := 0, 0, 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayNeutralOwnerStockMercenary(before, in)
			if e != nil {
				t.Fatal(e)
			}
			v := c.Statistics
			x := extra[c.Name].Statistics
			if digest(world) != c.SHA || s.InitialState != c.State || s.FinalState != c.Final || s.Draws != c.Draws || s.TargetDraws != v.Targets || !reflect.DeepEqual(s.DesertionSectors, v.Physical) || len(s.Activations) != len(v.Activations) || len(s.Seeds) != len(c.Seeds) {
				t.Fatal("whole phase/continuation")
			}
			acts += len(s.Activations)
			transfers += s.NeutralTransferred
			if s.Captured {
				captures++
			}
			allowed := map[int]bool{}
			allow := func(r, o int) {
				for i := 0; i < 4; i++ {
					allowed[(r-1)*137+o+i] = true
				}
			}
			allow(4054, 129)
			for i, a := range s.Activations {
				want := v.Activations[i]
				if a.Origin != want.Origin || a.Force != want.Force || a.Target != want.Target || a.Held != want.Held || a.Gate != planetRaw(t, c.Gates[i]) || !reflect.DeepEqual(a.Candidates, want.Candidates) || !reflect.DeepEqual(a.Route, want.Route) || !reflect.DeepEqual(a.Entered, want.Entered) || a.FinalSector != want.Final || a.FinalForce != want.Remaining || a.StoppedForPickup != want.Stopped {
					t.Fatal("source scan receipt", i)
				}
				if !a.Held {
					for _, r := range []int{51 + a.Origin, 51 + a.FinalSector} {
						allow(r, 81)
						allow(r, 85)
					}
				}
			}
			for i, h := range s.Seeds {
				want := c.Seeds[i]
				family := 1
				if want.Family == "h2" {
					family = 2
				}
				if h.Clock.Family != family || h.Clock.Caller != want.Caller || h.Clock.Timer != planetRaw(t, want.Timer) || h.OldState != want.Old || h.SeededState != want.Seed {
					t.Fatal("chronological source reseed", i)
				}
			}
			var pickup int
			for i, event := range v.Events {
				if event.Kind == "mercenary-pickup" {
					pickup = i
				}
			}
			event := v.Events[pickup]
			want := FriendlyStockPickup{Incoming: event.Incoming, Friendly: event.Friendly, Actor: event.Actor, Amount: event.Pickup, Force: event.Force, Governor: event.Governor, RawStock: planetRaw(t, c.Stock), FractionalDiscard: event.Fraction, Taking: event.Pickup > 0}
			if s.Pickup != want || s.Captured != event.Captured || s.PhysicalForce != v.Force || s.Losses != v.Losses || s.InitialMercenary != v.Initial || s.Merged != v.Merged || s.NeutralTransferred != x.Neutral || !reflect.DeepEqual(s.FinalSectors, v.Final) || s.NeutralPhysical[0]-s.NeutralPhysical[1] != x.Neutral || s.PhysicalForce+s.Losses != s.InitialMercenary+s.Pickup.Amount+s.NeutralTransferred {
				t.Fatal("neutral debit versus friendly merge/casualty/actor accounting")
			}
			if v.Events[0].Kind == "mercenary-mine" {
				mines++
				allow(3051, 129)
				m := x.Events[0]
				want := &GatewayMineStats{InitialState: m.InitialState, FinalState: m.FinalState, InitialForce: m.InitialForce, Force: m.Force, Losses: m.Losses, InitialMines: m.InitialMines, Mines: m.Mines, Spent: m.MinesSpent, Draws: m.RNGDraws, Rolls: m.Rolls}
				if !reflect.DeepEqual(s.Mine, want) || s.Mine.Draws != 2 || s.Mine.InitialForce != 97337 || s.Pickup.Incoming != s.Mine.Force || s.Pickup.Actor != s.Mine.Force+s.Pickup.Friendly || !reflect.DeepEqual(s.EventOrder, []string{"mine", "pickup"}) {
					t.Fatal("incoming-only count-two mine before local/stock addition")
				}
				if [4]byte(world[3050*137+129:3050*137+133]) != [4]byte{} {
					t.Fatal("spent mine canonical subtraction zero")
				}
			} else if s.Mine != nil || !reflect.DeepEqual(s.EventOrder, []string{"pickup"}) {
				t.Fatal("unexpected mine")
			}
			if [4]byte(world[4053*137+129:4053*137+133]) != [4]byte{0, 0, 0x80, 0} {
				t.Fatal("distinct pickup cleanup zero")
			}
			for i, b := range world {
				if b != before[i] && !allowed[i] {
					t.Fatal("unowned write", i)
				}
			}
			after, _ := json.Marshal(in)
			if !bytes.Equal(before, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("input mutation")
			}
			world[0] ^= 1
			if !bytes.Equal(before, saved) {
				t.Fatal("output alias")
			}
		})
	}
	if acts != 27 || mines != 9 || transfers != 336 || captures != 3 {
		t.Fatal("all owner/mine/hold/departure controls", acts, mines, transfers, captures)
	}
}
func TestNeutralOwnerStockAtomicRefusalsAndOlderGuards(t *testing.T) {
	d, _ := ownerLoad(t)
	var c friendlyCase
	for _, v := range d.Cases {
		if strings.HasPrefix(v.Name, "friendly-mine-second-four/") {
			c = v
			break
		}
	}
	if c.Name == "" {
		t.Fatal("late local scan case")
	}
	tests := map[string]func([]byte, *EvolvedTailInputs){
		"geometry":        func(w []byte, in *EvolvedTailInputs) { planetPut(w, 1, 53, 52) },
		"human":           func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2, 85, 1) },
		"tax":             func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3052, 89, 1) },
		"incoming":        func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2419, 81, 97336) },
		"local":           func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 81, 38) },
		"governor":        func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 73, -2) },
		"stock":           func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 129, 1.5) },
		"mines":           func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 129, 2) },
		"bank":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 117, 1) },
		"stock residue":   func(w []byte, in *EvolvedTailInputs) { copy(w[4053*137+129:], []byte{1, 2, 3, 0}) },
		"extra Mercenary": func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 81, 37); planetPut(w, 52, 85, -2) },
		"state":           func(w []byte, in *EvolvedTailInputs) { in.State = 1 << 24 },
		"mine helper family": func(w []byte, in *EvolvedTailInputs) {
			for i := range in.Helpers {
				if in.Helpers[i].Family == 2 {
					in.Helpers[i].Family = 1
					return
				}
			}
			t.Fatal("mine helper missing")
		},
		"mine helper caller": func(w []byte, in *EvolvedTailInputs) {
			for i := range in.Helpers {
				if in.Helpers[i].Family == 2 {
					in.Helpers[i].Caller ^= 1
					return
				}
			}
		},
		"missing mine helper": func(w []byte, in *EvolvedTailInputs) {
			for i := range in.Helpers {
				if in.Helpers[i].Family == 2 {
					in.Helpers = append(in.Helpers[:i], in.Helpers[i+1:]...)
					return
				}
			}
		},
		"late exhaustion": func(w []byte, in *EvolvedTailInputs) { in.Helpers = in.Helpers[:len(in.Helpers)-1] },
		"surplus helper":  func(w []byte, in *EvolvedTailInputs) { in.Helpers = append(in.Helpers, in.Helpers[len(in.Helpers)-1]) },
		"late route": func(w []byte, in *EvolvedTailInputs) {
			for o := 41; o < 65; o += 4 {
				planetPut(w, 51+13, o, 13)
			}
		},
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			change(before, &in)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayNeutralOwnerStockMercenary(before, in)
			after, _ := json.Marshal(in)
			if e == nil || world != nil || !reflect.DeepEqual(s, NeutralOwnerStockStats{}) || !bytes.Equal(before, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("non-atomic refusal", e)
			}
		})
	}
	for _, v := range d.Cases {
		before, in := friendlyInputs(t, d, v)
		if _, _, e := ReplayFriendlyStockMercenary(before, in); e == nil {
			t.Fatal("held-only guard widened")
		}
		if _, _, e := ReplayDepartedStockMercenary(before, in); e == nil {
			t.Fatal("departure guard widened")
		}
	}
}
