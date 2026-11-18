package qbmaint

import (
	"bytes"
	"encoding/json"
	"github.com/robbiew/yankeetrader/internal/qbrng"
	"os"
	"reflect"
	"strings"
	"testing"
)

type defenderExtra struct {
	Name       string
	Statistics struct {
		Events []struct {
			InitialForce                     int `json:"initial_force"`
			InitialDefenders                 int `json:"initial_defenders"`
			Force, Defenders, Losses, Rounds int
			DefenderLosses                   int    `json:"defender_losses"`
			Draws                            int    `json:"rng_draws"`
			Initial                          uint32 `json:"initial_rng_state"`
			Final                            uint32 `json:"final_rng_state"`
			Gate                             float32
		}
	}
}

func defenderLoad(t *testing.T) (friendlyFixture, map[string]defenderExtra) {
	t.Helper()
	b, e := os.ReadFile("testdata/defender_stock.json")
	if e != nil {
		t.Fatal(e)
	}
	var d friendlyFixture
	var extras struct{ Cases []defenderExtra }
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(b, &extras); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-defender-stock-v1" || len(d.Cases) != 24 || d.Audit.Comparisons != 144 || d.Audit.Files != 864 || d.Audit.Witnesses != 1074 || d.Audit.Normalized != 0 {
		t.Fatal("complete fatal/extinct inventory")
	}
	index := map[string]defenderExtra{}
	for _, v := range extras.Cases {
		index[v.Name] = v
	}
	return d, index
}
func TestDefenderStockQualifiedFatalAndExtinctPhases(t *testing.T) {
	d, extras := defenderLoad(t)
	battles, extinct := 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayDefenderStockMercenary(before, in)
			if e != nil {
				t.Fatal(e)
			}
			v := c.Statistics
			if digest(world) != c.SHA || s.InitialState != c.State || s.FinalState != c.Final || s.Draws != c.Draws || s.TargetDraws != v.Targets || !reflect.DeepEqual(s.DesertionSectors, v.Physical) || len(s.Seeds) != len(c.Seeds) || v.Force != 0 || len(v.Final) != 0 || v.Pickup != 0 {
				t.Fatal("complete phase/continuation/extinction")
			}
			for i, h := range s.Seeds {
				want := c.Seeds[i]
				if h.Clock.Family != 1 || want.Family != "h1" || h.Clock.Caller != want.Caller || h.Clock.Timer != planetRaw(t, want.Timer) || h.OldState != want.Old || h.SeededState != want.Seed {
					t.Fatal("calculated target reseed", i)
				}
			}
			allowed := map[int]bool{}
			allow := func(r, o int) {
				for i := 0; i < 4; i++ {
					allowed[(r-1)*137+o+i] = true
				}
			}
			if len(v.Events) > 0 {
				battles++
				if len(v.Events) != 1 || len(v.Activations) != 1 || s.Battle == nil || s.Activation == nil {
					t.Fatal("single fatal gateway battle")
				}
				x := extras[c.Name].Statistics.Events[0]
				want := &MercenaryDefenseStats{InitialState: x.Initial, FinalState: x.Final, InitialForce: x.InitialForce, InitialDefenders: x.InitialDefenders, Force: x.Force, Defenders: x.Defenders, Losses: x.Losses, DefenderLosses: x.DefenderLosses, Rounds: x.Rounds, Draws: x.Draws, Gate: portSingleBytes(x.Gate)}
				if !reflect.DeepEqual(s.Battle, want) || s.Battle.Force != 0 || s.Battle.Defenders <= 0 || s.Battle.Draws != s.Battle.Rounds+1 || s.Battle.Rounds != s.Battle.Losses+s.Battle.DefenderLosses || v.Losses != x.InitialForce {
					t.Fatal("eager gate/unit casualty ledger")
				}
				a, wa := s.Activation, v.Activations[0]
				if a.Origin != wa.Origin || a.Force != wa.Force || a.Target != wa.Target || a.Gate != planetRaw(t, c.Gates[0]) || !reflect.DeepEqual(a.Candidates, wa.Candidates) || !reflect.DeepEqual(a.Route, wa.Route) || !reflect.DeepEqual(a.Entered, []int{3000}) || !reflect.DeepEqual(a.Entered, wa.Entered) || a.FinalSector != wa.Final || a.FinalForce != 0 || a.StoppedForPickup {
					t.Fatal("actual fatal first hop suppresses remainder/pickup")
				}
				allow(2419, 81)
				allow(2419, 85)
				allow(3051, 81)
			} else {
				extinct++
				if s.Activation != nil || s.Battle != nil || len(s.Seeds) != 0 || s.Draws != len(s.DesertionSectors) || !bytes.Equal(world, before) {
					t.Fatal("extinct phase changed bytes or resurrected actions")
				}
			}
			for i, b := range world {
				if b != before[i] && !allowed[i] {
					t.Fatal("unowned write", i)
				}
			}
			for _, o := range []int{81, 85} {
				at := 2418*137 + o
				if [4]byte(world[at:at+4]) != [4]byte{0, 0, 0x28, 0} {
					t.Fatal("exact inherited departure residue")
				}
			}
			if !bytes.Equal(world[4053*137:4054*137], before[4053*137:4054*137]) {
				t.Fatal("uncollected stock/governor and planet must survive")
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
	if battles != 12 || extinct != 12 {
		t.Fatal("two-child phase coverage", battles, extinct)
	}
}
func TestDefenderStockAtomicAdmissionAndLateRefusals(t *testing.T) {
	d, _ := defenderLoad(t)
	var fatal, extinct friendlyCase
	for _, c := range d.Cases {
		if strings.Contains(c.Name, "/child-1/") {
			fatal = c
		}
		if strings.Contains(c.Name, "/child-2/") {
			extinct = c
		}
	}
	tests := map[string]func([]byte, *EvolvedTailInputs){
		"geometry":           func(w []byte, in *EvolvedTailInputs) { planetPut(w, 1, 53, 52) },
		"human":              func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2, 85, 1) },
		"tax":                func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3052, 89, 1) },
		"attacker":           func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2419, 81, 38) },
		"defense owner":      func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 85, 0) },
		"gateway mine":       func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 129, 1) },
		"stock alias":        func(w []byte, in *EvolvedTailInputs) { copy(w[4053*137+129:], []byte{1, 2, 3, 0}) },
		"governor alias":     func(w []byte, in *EvolvedTailInputs) { copy(w[4053*137+73:], []byte{0, 0, 128, 0}) },
		"bank":               func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 117, 1) },
		"name":               func(w []byte, in *EvolvedTailInputs) { w[4053*137] ^= 1 },
		"extra Mercenary":    func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 81, 1); planetPut(w, 52, 85, -2) },
		"fractional defense": func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 81, 37.5) },
		"state":              func(w []byte, in *EvolvedTailInputs) { in.State = 1 << 24 },
		"helper exhaustion":  func(w []byte, in *EvolvedTailInputs) { in.Helpers = nil },
		"surplus helper":     func(w []byte, in *EvolvedTailInputs) { in.Helpers = append(in.Helpers, in.Helpers[0]) },
		"family":             func(w []byte, in *EvolvedTailInputs) { in.Helpers[0].Family = 2 },
		"caller":             func(w []byte, in *EvolvedTailInputs) { in.Helpers[0].Caller ^= 1 },
		"TIMER":              func(w []byte, in *EvolvedTailInputs) { in.Helpers[0].Timer = encode(60) },
		"unreachable": func(w []byte, in *EvolvedTailInputs) {
			for o := 41; o < 65; o += 4 {
				planetPut(w, 2419, o, 2368)
			}
		},
		"nonfatal first hop": func(w []byte, in *EvolvedTailInputs) {
			for o := 41; o < 65; o += 4 {
				planetPut(w, 2419, o, 1)
			}
		},
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, fatal)
			change(before, &in)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayDefenderStockMercenary(before, in)
			after, _ := json.Marshal(in)
			if e == nil || world != nil || !reflect.DeepEqual(s, DefenderStockStats{}) || !bytes.Equal(before, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("non-atomic refusal", e)
			}
		})
	}
	for _, offset := range []int{81, 85} {
		before, in := friendlyInputs(t, d, extinct)
		planetPut(before, 2419, offset, 0)
		if world, s, e := ReplayDefenderStockMercenary(before, in); e == nil || world != nil || !reflect.DeepEqual(s, DefenderStockStats{}) {
			t.Fatal("numeric-zero alias replaced inherited departure residue")
		}
	}
	before, in := friendlyInputs(t, d, extinct)
	in.Helpers = []ContinuationClock{{Family: 1, Caller: 0x48cf, Timer: encode(2)}}
	if world, s, e := ReplayDefenderStockMercenary(before, in); e == nil || world != nil || !reflect.DeepEqual(s, DefenderStockStats{}) {
		t.Fatal("extinct phase consumed helper or emitted partial output")
	}
	before, in = friendlyInputs(t, d, fatal)
	if _, _, e := ReplayEvolvedNPCTail(before, in); e == nil {
		t.Fatal("historical tail widened")
	}
}

// This real-LCG counter-control is synthetic, not another native capture.
func TestDefenderStockRefusesComputedAttackerVictory(t *testing.T) {
	d, _ := defenderLoad(t)
	var c friendlyCase
	for _, v := range d.Cases {
		if strings.HasPrefix(v.Name, "balanced-37-whole/child-1/") {
			c = v
			break
		}
	}
	before, in := friendlyInputs(t, d, c)
	saved := bytes.Clone(before)
	found := false
	for second := 0; second < 60; second++ {
		rng := qbrng.New(in.State)
		for range c.Statistics.Physical {
			rng.Float32()
		}
		rng.Float32()
		timer := encode(second)
		rng.RandomizeMBF(timer)
		target := int(float32(rng.Float32()*3000)) + 1
		if target == 2368 {
			continue
		}
		rng.Float32()
		force, defenders := 37, 37
		for force > 0 && defenders > 0 {
			if rng.Float32() < .5 {
				defenders--
			} else {
				force--
			}
		}
		if force == 0 {
			continue
		}
		found = true
		in.Helpers = []ContinuationClock{{Family: 1, Caller: 0x48cf, Timer: timer}}
		world, s, e := ReplayDefenderStockMercenary(before, in)
		if e == nil || !strings.Contains(e.Error(), "only measured fatal offense") || world != nil || !reflect.DeepEqual(s, DefenderStockStats{}) || !bytes.Equal(before, saved) {
			t.Fatal("unqualified victory published or forced into captured loser", e)
		}
		break
	}
	if !found {
		t.Fatal("independently walked victory seed not found")
	}
}
