package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"strings"
	"testing"
)

func departedLoad(t *testing.T) friendlyFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/departed_stock.json")
	if e != nil {
		t.Fatal(e)
	}
	var d friendlyFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-departed-stock-v1" || len(d.Cases) != 24 || d.Audit.Comparisons != 144 || d.Audit.Files != 864 || d.Audit.Normalized != 0 || d.Audit.Witnesses != 1152 {
		t.Fatal("complete departure qualification")
	}
	return d
}
func TestDepartedStockMutableScanAndQualifiedWorlds(t *testing.T) {
	d := departedLoad(t)
	acts, captures, held, extra := 0, 0, 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayDepartedStockMercenary(before, in)
			if e != nil {
				t.Fatal(e)
			}
			v := c.Statistics
			if digest(world) != c.SHA || s.InitialState != c.State || s.FinalState != c.Final || s.Draws != c.Draws || s.TargetDraws != v.Targets || !reflect.DeepEqual(s.DesertionSectors, v.Physical) || len(s.Activations) != len(v.Activations) || len(s.Activations) != v.Movement || len(s.Seeds) != len(c.Seeds) {
				t.Fatal("complete phase/continuation/scan mismatch")
			}
			acts += len(s.Activations)
			extra += len(s.Activations) - 2
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
					t.Fatal("derived mutable activation receipt", i)
				}
				if i > 0 && a.Origin >= s.Activations[i-1].Origin {
					t.Fatal("descending scan cursor")
				}
				if !a.Held {
					for _, r := range []int{51 + a.Origin, 51 + a.FinalSector} {
						allow(r, 81)
						allow(r, 85)
					}
				}
				if i >= 2 && a.Force != 37 {
					t.Fatal("only departed local group reactivates")
				}
			}
			for i, h := range s.Seeds {
				want := c.Seeds[i]
				if want.Family != "h1" || h.Clock.Family != 1 || h.Clock.Caller != want.Caller || h.Clock.Timer != planetRaw(t, want.Timer) || h.OldState != want.Old || h.SeededState != want.Seed {
					t.Fatal("source helper reseed", i)
				}
			}
			if len(v.Events) != 1 {
				t.Fatal("single pickup event")
			}
			event := v.Events[0]
			want := FriendlyStockPickup{Incoming: event.Incoming, Friendly: event.Friendly, Actor: event.Actor, Amount: event.Pickup, Force: event.Force, Governor: event.Governor, RawStock: planetRaw(t, c.Stock), FractionalDiscard: event.Fraction, Taking: event.Pickup > 0}
			if s.Pickup != want || s.Captured != event.Captured || s.PhysicalForce != v.Force || !reflect.DeepEqual(s.FinalSectors, v.Final) || v.Losses != 0 || v.Merged != event.Friendly || s.PhysicalForce != v.Initial+event.Pickup || v.Initial != 97374 {
				t.Fatal("separate local force, cached actor and total conservation")
			}
			if s.Captured {
				captures++
				if s.Pickup.Actor != 97337 || s.Pickup.Friendly != 0 || len(s.FinalSectors) != 2 {
					t.Fatal("departed force incorrectly counted in pickup actor")
				}
			} else {
				held++
				if s.Pickup.Actor != 97374 || s.Pickup.Friendly != 37 || !s.Activations[0].Held {
					t.Fatal("held counter-control")
				}
			}
			for i, b := range world {
				if b != before[i] && !allowed[i] {
					t.Fatal("unowned write", i)
				}
			}
			for _, a := range s.Activations {
				if !a.Held {
					final := false
					for _, sector := range s.FinalSectors {
						final = final || sector == a.Origin
					}
					if !final {
						for _, o := range []int{81, 85} {
							at := (50+a.Origin)*137 + o
							if [4]byte(world[at:at+4]) != [4]byte{0, 0, 0x28, 0} {
								t.Fatal("source departure residue")
							}
						}
					}
				}
			}
			if [4]byte(world[4053*137+129:4053*137+133]) != [4]byte{0, 0, 0x80, 0} {
				t.Fatal("source stock residue")
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
	if acts != 66 || extra != 18 || captures != 15 || held != 9 {
		t.Fatal("all held/departure/reactivation branches", acts, extra, captures, held)
	}
}
func TestDepartedStockAtomicLateRefusalsAndHistoricalGuards(t *testing.T) {
	d := departedLoad(t)
	var c friendlyCase
	for _, v := range d.Cases {
		if strings.HasPrefix(v.Name, "second-eight-whole/") {
			c = v
			break
		}
	}
	if c.Name == "" {
		t.Fatal("late scan fixture")
	}
	tests := map[string]func([]byte, *EvolvedTailInputs){
		"geometry":         func(w []byte, in *EvolvedTailInputs) { planetPut(w, 1, 53, 52) },
		"human":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2, 85, 1) },
		"tax":              func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3052, 89, 1) },
		"incoming":         func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2419, 81, 97336) },
		"local force":      func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 81, 1) },
		"stock context":    func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 129, 1.5) },
		"governor":         func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 73, -1) },
		"canonical stock":  func(w []byte, in *EvolvedTailInputs) { copy(w[4053*137+129:], []byte{1, 2, 3, 0}) },
		"gateway mine":     func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 129, 1) },
		"bank":             func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 117, 1) },
		"name":             func(w []byte, in *EvolvedTailInputs) { w[4053*137] ^= 1 },
		"extra Mercenary":  func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 81, 37); planetPut(w, 52, 85, -2) },
		"excess Xannor":    func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 81, 10001); planetPut(w, 52, 85, -1) },
		"fractional force": func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 81, .5) },
		"state":            func(w []byte, in *EvolvedTailInputs) { in.State = 1 << 24 },
		"family":           func(w []byte, in *EvolvedTailInputs) { in.Helpers[0].Family = 2 },
		"clock order":      func(w []byte, in *EvolvedTailInputs) { in.Helpers[0].Timer = encode(59) },
		"late caller":      func(w []byte, in *EvolvedTailInputs) { in.Helpers[len(in.Helpers)-1].Caller ^= 1 },
		"late exhaustion":  func(w []byte, in *EvolvedTailInputs) { in.Helpers = in.Helpers[:len(in.Helpers)-1] },
		"surplus helper":   func(w []byte, in *EvolvedTailInputs) { in.Helpers = append(in.Helpers, in.Helpers[len(in.Helpers)-1]) },
		"late graph": func(w []byte, in *EvolvedTailInputs) {
			for o := 41; o < 65; o += 4 {
				planetPut(w, 51+1622, o, 1622)
			}
		},
		"late mine":    func(w []byte, in *EvolvedTailInputs) { planetPut(w, 51+2862, 129, 1) },
		"late defense": func(w []byte, in *EvolvedTailInputs) { planetPut(w, 51+2862, 81, 1); planetPut(w, 51+2862, 85, -1) },
		"late planet":  func(w []byte, in *EvolvedTailInputs) { planetPut(w, 51+2862, 93, 2) },
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			change(before, &in)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayDepartedStockMercenary(before, in)
			after, _ := json.Marshal(in)
			if e == nil || world != nil || !reflect.DeepEqual(s, DepartedStockStats{}) || !bytes.Equal(before, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("non-atomic refusal", e)
			}
		})
	}
	before, in := friendlyInputs(t, d, c)
	if _, _, e := ReplayFriendlyStockMercenary(before, in); e == nil {
		t.Fatal("held-only guard widened")
	}
	if _, _, e := ReplayEvolvedNPCTail(before, in); e == nil {
		t.Fatal("historical tail widened")
	}
}
