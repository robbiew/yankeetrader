package qbmaint

import (
	"bytes"
	"encoding/json"
	"github.com/robbiew/yankeetrader/internal/qbrng"
	"os"
	"reflect"
	"testing"
)

type friendlyCase struct {
	Name    string
	Before  string `json:"before_sha256"`
	State   uint32 `json:"initial_state"`
	SHA     string `json:"expected_sha256"`
	Final   uint32 `json:"final_state"`
	Draws   int
	Helpers []struct {
		Family int
		Caller uint16
		Timer  string
	}
	Seeds []struct {
		Family string
		Caller uint16
		Timer  string
		Old    uint32 `json:"old_state"`
		Seed   uint32 `json:"seeded_state"`
	}
	Gates      []string
	Stock      string `json:"raw_stock"`
	Statistics struct {
		Physical                      []int `json:"desertion_sectors"`
		Targets                       int   `json:"target_draws"`
		Movement                      int   `json:"movement_gate_draws"`
		Force, Pickup, Merged, Losses int
		Initial                       int   `json:"initial_force"`
		Final                         []int `json:"final_sectors"`
		Activations                   []struct {
			Origin, Force, Target      int
			Held                       bool
			Candidates, Route, Entered []int
			Stopped                    bool `json:"stopped_for_pickup"`
			Final                      int  `json:"final_sector"`
			Remaining                  int  `json:"final_force"`
		}
		Events []struct {
			Kind                                    string
			Sector, Force, Governor, Pickup, Merged int
			Incoming                                int     `json:"incoming_force"`
			Friendly                                int     `json:"entering_friendly_force"`
			Actor                                   int     `json:"initial_force"`
			Fraction                                float64 `json:"fractional_discard"`
			Captured                                bool
		}
	}
}
type friendlyFixture struct {
	Format string
	Worlds map[string]string
	Cases  []friendlyCase
	Audit  struct {
		Comparisons int `json:"exact_comparisons"`
		Files       int
		Normalized  int `json:"normalized_bytes"`
		Witnesses   int `json:"rng_witness_checks"`
	} `json:"native_audit"`
}

func friendlyLoad(t *testing.T) friendlyFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/friendly_stock.json")
	if e != nil {
		t.Fatal(e)
	}
	var d friendlyFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-friendly-stock-v1" || len(d.Cases) != 24 || d.Audit.Comparisons != 144 || d.Audit.Files != 864 || d.Audit.Normalized != 0 || d.Audit.Witnesses <= 0 {
		t.Fatal("complete qualification inventory")
	}
	return d
}
func friendlyInputs(t *testing.T, d friendlyFixture, c friendlyCase) ([]byte, EvolvedTailInputs) {
	t.Helper()
	b := unpack(t, d.Worlds[c.Before])
	if digest(b) != c.Before {
		t.Fatal("modeled phase identity")
	}
	in := EvolvedTailInputs{State: c.State}
	for _, h := range c.Helpers {
		in.Helpers = append(in.Helpers, ContinuationClock{Family: h.Family, Caller: h.Caller, Timer: planetRaw(t, h.Timer)})
	}
	return b, in
}
func TestFriendlyStockQualifiedPhasesAndOwnedWrites(t *testing.T) {
	d := friendlyLoad(t)
	taking, silent := 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayFriendlyStockMercenary(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(world) != c.SHA || s.InitialState != c.State || s.FinalState != c.Final || s.Draws != c.Draws || s.TargetDraws != c.Statistics.Targets || !reflect.DeepEqual(s.DesertionSectors, c.Statistics.Physical) || len(s.Activations) != 2 || c.Statistics.Movement != 2 || len(s.Seeds) != len(c.Seeds) {
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
			want := FriendlyStockPickup{Incoming: v.Incoming, Friendly: v.Friendly, Actor: v.Actor, Amount: v.Pickup, Force: v.Force, Governor: v.Governor, RawStock: planetRaw(t, c.Stock), FractionalDiscard: v.Fraction, Taking: v.Pickup > 0}
			if s.Pickup != want || v.Captured || v.Kind != "mercenary-pickup" || v.Sector != 3000 || c.Statistics.Losses != 0 || c.Statistics.Merged != v.Friendly || c.Statistics.Initial != 97337+v.Friendly || c.Statistics.Force != s.Pickup.Force || !reflect.DeepEqual(c.Statistics.Final, []int{3000}) {
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
	if taking != 15 || silent != 9 {
		t.Fatal("positive and silent stock cases", taking, silent)
	}
}
func TestFriendlyStockAtomicRefusalsAndHistoricalSeparation(t *testing.T) {
	d := friendlyLoad(t)
	c := d.Cases[0]
	tests := map[string]func([]byte, *EvolvedTailInputs){
		"geometry":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 1, 53, 52) },
		"human":               func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2, 85, 1) },
		"tax":                 func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3052, 89, 1) },
		"incoming":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2419, 81, 97336) },
		"friendly":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 81, 2) },
		"governor":            func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 73, -1) },
		"owner":               func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 85, 0) },
		"slot":                func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 93, 2) },
		"name":                func(w []byte, in *EvolvedTailInputs) { w[4053*137] ^= 1 },
		"bank":                func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 117, 1) },
		"stock":               func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 129, 2.5) },
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
		"departing garrison": func(w []byte, in *EvolvedTailInputs) {
			for seed := uint32(0); seed < 10000; seed++ {
				rng := qbrng.New(seed)
				for range c.Statistics.Physical {
					rng.Float32()
				}
				if rng.Float32() >= float32(.66) {
					in.State = seed
					return
				}
			}
			t.Fatal("synthetic real-LCG departure seed")
		},
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			change(before, &in)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayFriendlyStockMercenary(before, in)
			after, _ := json.Marshal(in)
			if e == nil || world != nil || !reflect.DeepEqual(s, FriendlyStockStats{}) || !bytes.Equal(before, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("non-atomic refusal", e)
			}
		})
	}
	before, in := friendlyInputs(t, d, c)
	if _, _, e := ReplayEvolvedNPCTail(before, in); e == nil {
		t.Fatal("historical tail admission widened")
	}
}
