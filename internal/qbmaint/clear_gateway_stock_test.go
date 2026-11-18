package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

func clearStockLoad(t *testing.T) friendlyFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/clear_gateway_stock.json")
	if e != nil {
		t.Fatal(e)
	}
	var d friendlyFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-clear-gateway-stock-v1" || len(d.Cases) != 36 || d.Audit.Comparisons != 216 || d.Audit.Files != 1296 || d.Audit.Normalized != 0 || d.Audit.Witnesses != 1656 {
		t.Fatal("complete qualification inventory")
	}
	return d
}
func TestClearGatewayStockQualifiedPhasesAndOwnedWrites(t *testing.T) {
	d := clearStockLoad(t)
	taking, silent := 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayClearGatewayStockMercenary(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(world) != c.SHA || s.InitialState != c.State || s.FinalState != c.Final || s.Draws != c.Draws || s.TargetDraws != c.Statistics.Targets || !reflect.DeepEqual(s.DesertionSectors, c.Statistics.Physical) || len(s.Activations) != 1 || c.Statistics.Movement != 1 || len(s.Seeds) != len(c.Seeds) {
				t.Fatal("complete phase/RNG/scan mismatch")
			}
			for i, a := range s.Activations {
				v := c.Statistics.Activations[i]
				if a.Origin != v.Origin || a.Force != v.Force || a.Target != v.Target || a.Held != v.Held || a.Gate != planetRaw(t, c.Gates[i]) || !reflect.DeepEqual(a.Candidates, v.Candidates) || !reflect.DeepEqual(a.Route, v.Route) || !reflect.DeepEqual(a.Entered, v.Entered) || a.FinalSector != v.Final || a.FinalForce != v.Remaining || a.StoppedForPickup != v.Stopped {
					t.Fatal("derived activation receipt", i)
				}
			}
			for i, h := range s.Seeds {
				v := c.Seeds[i]
				if v.Family != "h1" || h.Clock.Family != 1 || h.Clock.Caller != v.Caller || h.Clock.Timer != planetRaw(t, v.Timer) || h.OldState != v.Old || h.SeededState != v.Seed {
					t.Fatal("source reseed", i)
				}
			}
			if len(c.Statistics.Events) != 1 {
				t.Fatal("single pickup")
			}
			v := c.Statistics.Events[0]
			want := FriendlyStockPickup{Incoming: v.Actor, Friendly: 0, Actor: v.Actor, Amount: v.Pickup, Force: v.Force, Governor: v.Governor, RawStock: planetRaw(t, c.Stock), FractionalDiscard: v.Fraction, Taking: v.Pickup > 0}
			if s.Pickup != want || !v.Captured || v.Kind != "mercenary-pickup" || v.Sector != 3000 || c.Statistics.Losses != 0 || c.Statistics.Merged != v.Friendly || c.Statistics.Initial != 97337+v.Friendly || c.Statistics.Force != s.Pickup.Force || !reflect.DeepEqual(c.Statistics.Final, []int{3000}) {
				t.Fatal("once-only physical pickup/actor/governor")
			}
			if s.Pickup.Taking {
				taking++
			} else {
				silent++
			}
			allowed := map[int]bool{}
			for _, field := range [][2]int{{2419, 81}, {2419, 85}, {3051, 81}, {3051, 85}, {4054, 129}} {
				for i := 0; i < 4; i++ {
					allowed[(field[0]-1)*137+field[1]+i] = true
				}
			}
			for i, b := range world {
				if b != before[i] && !allowed[i] {
					t.Fatal("unowned write", i)
				}
			}
			for _, o := range []int{81, 85} {
				at := (2419-1)*137 + o
				if [4]byte(world[at:at+4]) != [4]byte{0, 0, 0x28, 0} {
					t.Fatal("departure residue")
				}
			}
			if [4]byte(world[4053*137+129:4053*137+133]) != [4]byte{0, 0, 0x80, 0} {
				t.Fatal("stock cleanup residue")
			}
			after, _ := json.Marshal(in)
			if !bytes.Equal(saved, before) || !bytes.Equal(recipe, after) {
				t.Fatal("input mutation")
			}
			world[0] ^= 1
			if !bytes.Equal(before, saved) {
				t.Fatal("output alias")
			}
		})
	}
	if taking != 24 || silent != 12 {
		t.Fatal("positive and silent stock cases", taking, silent)
	}
}
func TestClearGatewayStockAtomicRefusalsAndHistoricalSeparation(t *testing.T) {
	d := clearStockLoad(t)
	c := d.Cases[0]
	tests := map[string]func([]byte, *EvolvedTailInputs){
		"day":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 1, 81, 309) },
		"zero stock":     func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 129, 0) },
		"negative stock": func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 129, -.5) },
		"excess stock":   func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 129, 200000) },
		"raw governor":   func(w []byte, in *EvolvedTailInputs) { copy(w[4053*137+73:], []byte{0, 0, 128, 0}) },

		"geometry":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 1, 53, 52) },
		"human":               func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2, 85, 1) },
		"tax":                 func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3052, 89, 1) },
		"incoming":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2419, 81, 97336) },
		"friendly":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 81, 2) },
		"governor":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 73, -1) },
		"owner":               func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 85, -2) },
		"slot":                func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 93, 2) },
		"name":                func(w []byte, in *EvolvedTailInputs) { w[4053*137] ^= 1 },
		"bank":                func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 117, 1) },
		"stock":               func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 129, 3.5) },
		"canonical stock":     func(w []byte, in *EvolvedTailInputs) { copy(w[4053*137+129:], []byte{1, 2, 3, 0}) },
		"mine":                func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 129, 1) },
		"origin planet":       func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2419, 93, 1) },
		"extra Mercenary":     func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 81, 1); planetPut(w, 52, 85, -2) },
		"excess Xannor":       func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 81, 10001); planetPut(w, 52, 85, -1) },
		"neutral count":       func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 81, 38); planetPut(w, 52, 85, 0) },
		"fractional physical": func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 81, .5) },
		"graph":               func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 41, 3001) },
		"late unreachable": func(w []byte, in *EvolvedTailInputs) {
			for o := 41; o < 65; o += 4 {
				planetPut(w, 2419, o, 2368)
			}
		},
		"state":          func(w []byte, in *EvolvedTailInputs) { in.State = 1 << 24 },
		"exhaustion":     func(w []byte, in *EvolvedTailInputs) { in.Helpers = nil },
		"surplus clock":  func(w []byte, in *EvolvedTailInputs) { in.Helpers = append(in.Helpers, in.Helpers[0]) },
		"caller":         func(w []byte, in *EvolvedTailInputs) { in.Helpers[0].Caller ^= 1 },
		"family":         func(w []byte, in *EvolvedTailInputs) { in.Helpers[0].Family = 2 },
		"negative TIMER": func(w []byte, in *EvolvedTailInputs) { in.Helpers[0].Timer = encode(-1) },
		"late TIMER":     func(w []byte, in *EvolvedTailInputs) { in.Helpers[0].Timer = encode(60) },
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			change(before, &in)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayClearGatewayStockMercenary(before, in)
			after, _ := json.Marshal(in)
			if e == nil || world != nil || !reflect.DeepEqual(s, ClearGatewayStockStats{}) || !bytes.Equal(before, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("non-atomic refusal", e)
			}
		})
	}
	before, in := friendlyInputs(t, d, c)
	if _, _, e := ReplayFriendlyStockMercenary(before, in); e == nil {
		t.Fatal("historical tail admission widened")
	}
}
