package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"strings"
	"testing"
)

type victoryExtra struct {
	Name       string
	Statistics struct {
		Events []struct {
			Kind                                    string
			InitialForce                            int `json:"initial_force"`
			InitialDefenders                        int `json:"initial_defenders"`
			Force, Defenders, Losses, Rounds, Mines int
			DefenderLosses                          int    `json:"defender_losses"`
			InitialMines                            int    `json:"initial_mines"`
			Spent                                   int    `json:"mines_spent"`
			Draws                                   int    `json:"rng_draws"`
			Initial                                 uint32 `json:"initial_rng_state"`
			Final                                   uint32 `json:"final_rng_state"`
			Gate                                    float32
			Rolls                                   []int
		}
	}
}

func victoryLoad(t *testing.T) (friendlyFixture, map[string]victoryExtra) {
	t.Helper()
	b, e := os.ReadFile("testdata/gateway_victory.json")
	if e != nil {
		t.Fatal(e)
	}
	var d friendlyFixture
	var x struct {
		Cases    []victoryExtra
		Selected struct {
			Comparisons int `json:"exact_comparisons"`
			Files       int
			Witness     int `json:"rng_witness_checks"`
		} `json:"selected_native_audit"`
	}
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(b, &x); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-gateway-victory-v1" || len(d.Cases) != 12 || d.Audit.Comparisons != 216 || d.Audit.Files != 1296 || d.Audit.Witnesses != 1962 || d.Audit.Normalized != 0 || x.Selected.Comparisons != 72 || x.Selected.Files != 432 || x.Selected.Witness != 660 {
		t.Fatal("selected two-profile and wider native qualification")
	}
	index := map[string]victoryExtra{}
	for _, v := range x.Cases {
		index[v.Name] = v
	}
	return d, index
}
func TestGatewayVictoryQualifiedWorldsAndNoPickupFallthrough(t *testing.T) {
	d, extras := victoryLoad(t)
	acts, battles, mines, continuations := 0, 0, 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayGatewayVictoryMercenary(before, in)
			if e != nil {
				t.Fatal(e)
			}
			v := c.Statistics
			if digest(world) != c.SHA || s.InitialState != c.State || s.FinalState != c.Final || s.Draws != c.Draws || s.TargetDraws != v.Targets || !reflect.DeepEqual(s.DesertionSectors, v.Physical) || len(s.Activations) != len(v.Activations) || len(s.Seeds) != len(c.Seeds) || s.InitialForce != v.Initial || s.FinalForce != v.Force || s.Losses != v.Losses || !reflect.DeepEqual(s.FinalSectors, v.Final) || v.Pickup != 0 {
				t.Fatal("whole phase/continuation/casualty inventory")
			}
			acts += len(s.Activations)
			allowed := map[int]bool{}
			allow := func(r, o int) {
				for i := 0; i < 4; i++ {
					allowed[(r-1)*137+o+i] = true
				}
			}
			for i, a := range s.Activations {
				want := v.Activations[i]
				if a.Origin != want.Origin || a.Force != want.Force || a.Target != want.Target || a.Gate != planetRaw(t, c.Gates[i]) || a.Held || !reflect.DeepEqual(a.Candidates, want.Candidates) || !reflect.DeepEqual(a.Route, want.Route) || !reflect.DeepEqual(a.Entered, want.Entered) || !reflect.DeepEqual(a.Entered, a.Route[1:]) || a.FinalSector != want.Final || a.FinalForce != want.Remaining || a.StoppedForPickup {
					t.Fatal("complete post-victory route and mutable scan receipt", i)
				}
				for _, r := range []int{51 + a.Origin, 51 + a.FinalSector} {
					allow(r, 81)
					allow(r, 85)
				}
			}
			for i, h := range s.Seeds {
				want := c.Seeds[i]
				family := 1
				if want.Family == "h2" {
					family = 2
				}
				if h.Clock.Family != family || h.Clock.Caller != want.Caller || h.Clock.Timer != planetRaw(t, want.Timer) || h.OldState != want.Old || h.SeededState != want.Seed {
					t.Fatal("source chronological reseed", i)
				}
			}
			bi, mi := 0, 0
			for i, event := range extras[c.Name].Statistics.Events {
				switch event.Kind {
				case "mercenary-attack":
					if bi >= len(s.Battles) {
						t.Fatal("missing battle")
					}
					want := GatewayVictoryBattle{InitialState: event.Initial, FinalState: event.Final, InitialForce: event.InitialForce, InitialDefenders: event.InitialDefenders, Force: event.Force, Defenders: event.Defenders, Losses: event.Losses, DefenderLosses: event.DefenderLosses, Rounds: event.Rounds, Draws: event.Draws, Gate: portSingleBytes(event.Gate)}
					if s.Battles[bi] != want || event.Defenders != 0 || event.Force <= 0 || event.Draws != event.Rounds+1 || event.Rounds != event.Losses+event.DefenderLosses || s.EventOrder[i] != "attack" {
						t.Fatal("calculated victorious unit battle")
					}
					bi++
					battles++
					allow(3051, 81)
					allow(3051, 85)
				case "mercenary-mine":
					if mi >= len(s.Mines) {
						t.Fatal("missing mine")
					}
					want := GatewayMineStats{InitialState: event.Initial, FinalState: event.Final, InitialForce: event.InitialForce, Force: event.Force, Losses: event.Losses, InitialMines: event.InitialMines, Mines: event.Mines, Spent: event.Spent, Draws: event.Draws, Rolls: event.Rolls}
					if !reflect.DeepEqual(s.Mines[mi], want) || event.Draws != 2 || s.EventOrder[i] != "mine" {
						t.Fatal("count-two incoming mine receipt")
					}
					mi++
					mines++
					allow(3051, 129)
				default:
					t.Fatal("unqualified event")
				}
			}
			if bi != len(s.Battles) || mi != len(s.Mines) || len(s.EventOrder) != len(v.Events) {
				t.Fatal("complete event inventory")
			}
			if len(v.Events) == 0 {
				continuations++
				if len(s.Battles) != 0 || len(s.Mines) != 0 {
					t.Fatal("invented next-day encounter")
				}
			}
			if s.Physical[1][0]+s.Losses != s.Physical[0][0] || s.Physical[1][1]+s.DefenderLosses != s.Physical[0][1] || s.Physical[1][2] != s.Physical[0][2] {
				t.Fatal("independent faction conservation")
			}
			if !bytes.Equal(world[4053*137:4054*137], before[4053*137:4054*137]) {
				t.Fatal("victory must not take or normalize planet stock/governor/ground")
			}
			for i, b := range world {
				if b != before[i] && !allowed[i] {
					t.Fatal("unowned write", i)
				}
			}
			if len(s.Battles) > 0 && ([4]byte(world[3050*137+81:3050*137+85]) != [4]byte{} || [4]byte(world[3050*137+85:3050*137+89]) != [4]byte{}) {
				t.Fatal("defeated defender canonical zero pair")
			}
			for _, a := range s.Activations {
				final := false
				for _, sector := range s.FinalSectors {
					final = final || sector == a.Origin
				}
				if !final {
					for _, o := range []int{81, 85} {
						at := (50+a.Origin)*137 + o
						if [4]byte(world[at:at+4]) != [4]byte{0, 0, 0x28, 0} {
							t.Fatal("departure residue")
						}
					}
				}
			}
			after, _ := json.Marshal(in)
			if !bytes.Equal(before, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("source mutation")
			}
			world[0] ^= 1
			if !bytes.Equal(before, saved) {
				t.Fatal("output alias")
			}
		})
	}
	if acts != 21 || battles != 6 || mines != 3 || continuations != 6 {
		t.Fatal("selected complete phase coverage", acts, battles, mines, continuations)
	}
}
func TestGatewayVictoryAtomicLateRefusals(t *testing.T) {
	d, _ := victoryLoad(t)
	var c friendlyCase
	for _, v := range d.Cases {
		if strings.HasPrefix(v.Name, "mine-guarded/child-1/") {
			c = v
			break
		}
	}
	tests := map[string]func([]byte, *EvolvedTailInputs){
		"geometry":        func(w []byte, in *EvolvedTailInputs) { planetPut(w, 1, 53, 52) },
		"active human":    func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2, 85, 1) },
		"tax":             func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3052, 89, 1) },
		"owner/pickup":    func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 85, 0) },
		"defender/batch":  func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 81, 201) },
		"stock":           func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 129, 1.5) },
		"mine count":      func(w []byte, in *EvolvedTailInputs) { planetPut(w, 3051, 129, 3) },
		"governor":        func(w []byte, in *EvolvedTailInputs) { planetPut(w, 4054, 73, -2) },
		"attacker":        func(w []byte, in *EvolvedTailInputs) { planetPut(w, 2419, 81, 37) },
		"extra Mercenary": func(w []byte, in *EvolvedTailInputs) { planetPut(w, 52, 81, 1); planetPut(w, 52, 85, -2) },
		"state":           func(w []byte, in *EvolvedTailInputs) { in.State = 1 << 24 },
		"mine chronology": func(w []byte, in *EvolvedTailInputs) {
			for i := range in.Helpers {
				if in.Helpers[i].Family == 2 {
					in.Helpers[i].Family = 1
					in.Helpers[i].Caller = 0x48cf
					return
				}
			}
		},
		"last clock exhaustion": func(w []byte, in *EvolvedTailInputs) { in.Helpers = in.Helpers[:len(in.Helpers)-1] },
		"extra helper":          func(w []byte, in *EvolvedTailInputs) { in.Helpers = append(in.Helpers, in.Helpers[len(in.Helpers)-1]) },
		"late unreachable": func(w []byte, in *EvolvedTailInputs) {
			for o := 41; o < 65; o += 4 {
				planetPut(w, 51+508, o, 508)
			}
		},
		"late mine":   func(w []byte, in *EvolvedTailInputs) { planetPut(w, 51+2054, 129, 1) },
		"late pickup": func(w []byte, in *EvolvedTailInputs) { planetPut(w, 51+2054, 93, 3) },
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			before, in := friendlyInputs(t, d, c)
			change(before, &in)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayGatewayVictoryMercenary(before, in)
			after, _ := json.Marshal(in)
			if e == nil || world != nil || !reflect.DeepEqual(s, GatewayVictoryStats{}) || !bytes.Equal(before, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("non-atomic refusal", e)
			}
		})
	}
	before, in := friendlyInputs(t, d, c)
	if _, _, e := ReplayDefenderStockMercenary(before, in); e == nil {
		t.Fatal("fatal-only admission widened")
	}
}
