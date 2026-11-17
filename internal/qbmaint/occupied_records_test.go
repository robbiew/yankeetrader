package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

type occupiedFilesCase struct {
	Name      string
	Initial   string            `json:"initial_before_sha256"`
	Startup   uint32            `json:"startup_state"`
	Day       int               `json:"final_day"`
	Expected  map[string]string `json:"expected_files"`
	Final     uint32            `json:"final_state"`
	Lottery   string
	Candidate int
	Tail      struct {
		Before  string `json:"before_sha256"`
		State   uint32 `json:"initial_state"`
		Draws   int
		Helpers []struct {
			Family int
			Caller uint16
			Timer  string
		}
	}
	Mercenary struct {
		Desertion   []int `json:"desertion_sectors"`
		Movement    int   `json:"movement_gate_draws"`
		Targets     int   `json:"target_draws"`
		Final       []int `json:"final_sectors"`
		Force       int
		Activations []struct {
			Origin, Force, Target int
			Gate                  float64
			Held                  bool
			Candidates, Route     []int
		}
	}
}

func occupiedFilesLoad(t *testing.T) []occupiedFilesCase {
	t.Helper()
	b, e := os.ReadFile("testdata/occupied_records.json")
	if e != nil {
		t.Fatal(e)
	}
	var d struct {
		Format      string
		Cases       []occupiedFilesCase
		Comparisons int `json:"native_six_file_comparisons"`
		Witnesses   int `json:"native_rng_witnesses"`
	}
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-occupied-records-v1" || len(d.Cases) != 30 || d.Comparisons != 180 || d.Witnesses != 1872 {
		t.Fatal("complete qualified inventory")
	}
	return d.Cases
}
func occupiedFilesInputs(t *testing.T, c occupiedFilesCase) (map[string][]byte, OccupiedInputs) {
	t.Helper()
	p, r, a := occupiedPlanetLoad(t), occupiedRouteLoad(t), reportLoad(t)
	var in OccupiedInputs
	var before map[string][]byte
	in.StartupState = c.Startup
	in.FinalDay = c.Day
	for _, v := range p.Cases {
		if v.Name == c.Name {
			in.Ports = PortSchedule{Days: v.Ports.Days, Capped: true}
			for _, s := range v.Ports.Timers {
				in.Ports.TimerMinutes = append(in.Ports.TimerMinutes, planetRaw(t, s))
			}
			in.Planets = occupiedPlanetInputs(t, v).Clocks
		}
	}
	for _, v := range r.Cases {
		if v.Name == c.Name {
			x := occupiedRouteInputs(t, v)
			in.Creation = x.Creation
			in.RoutingHelpers = x.Helpers
		}
	}
	for _, v := range a.Cases {
		if v.Name == c.Name {
			before, _, in.Reports, _ = reportInputs(t, a, v)
		}
	}
	for _, v := range c.Tail.Helpers {
		in.TailHelpers = append(in.TailHelpers, ContinuationClock{Family: v.Family, Caller: v.Caller, Timer: planetRaw(t, v.Timer)})
	}
	if before == nil || digest(before["YTDATA.DAT"]) != c.Initial || len(in.Ports.Days) != 1000 {
		t.Fatal("joined fixture inputs")
	}
	return before, in
}
func TestOccupiedFilesCompleteBeforeOnlyComposition(t *testing.T) {
	cases := occupiedFilesLoad(t)
	routes := occupiedRouteLoad(t)
	activations, events := 0, 0
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			before, in := occupiedFilesInputs(t, c)
			saved := cloneAuxFiles(before)
			recipe, _ := json.Marshal(in)
			files, s, e := ReplayOccupiedFiles(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if len(files) != 6 {
				t.Fatal("six files")
			}
			for n, sha := range c.Expected {
				if digest(files[n]) != sha {
					t.Fatal("complete six-file mismatch", n)
				}
			}
			if s.Planets.InitialState != in.StartupState || s.Routing.InitialState != s.Planets.FinalState || s.Tail.InitialState != s.Routing.FinalState || s.Tail.InitialState != c.Tail.State || s.Tail.FinalState != c.Final || s.Tail.Draws != c.Tail.Draws || s.Tail.Lottery != planetRaw(t, c.Lottery) || s.Tail.Candidate != c.Candidate {
				t.Fatal("calculated RNG continuation/lottery")
			}
			for _, r := range routes.Cases {
				if r.Name == c.Name && r.SHA != c.Tail.Before {
					t.Fatal("source phase boundary")
				}
			}
			m := c.Mercenary
			if !reflect.DeepEqual(s.Tail.DesertionSectors, m.Desertion) || s.Tail.MovementGateDraws != m.Movement || s.Tail.TargetDraws != m.Targets || len(s.Tail.FinalMercenarySectors) != len(m.Final) || s.Tail.MercenaryForce != m.Force || len(s.Tail.Activations) != len(m.Activations) {
				t.Fatal("physical tail receipts")
			}
			for i, a := range s.Tail.Activations {
				v := m.Activations[i]
				if a.Origin != v.Origin || a.Force != v.Force || a.Target != v.Target || a.Held != v.Held || a.Gate != portSingleBytes(float32(v.Gate)) || !reflect.DeepEqual(a.Candidates, v.Candidates) || !reflect.DeepEqual(a.Route, v.Route) {
					t.Fatal("mutable descending scan receipt")
				}
			}
			for i, v := range m.Final {
				if s.Tail.FinalMercenarySectors[i] != v {
					t.Fatal("final Mercenary sectors")
				}
			}
			activations += len(s.Tail.Activations)
			events += len(s.Routing.Events)
			if raw := [4]byte(files["YTDATA.DAT"][81:85]); raw != encode(306) {
				t.Fatal("final watermark")
			}
			for r := 2; r <= 51; r++ {
				at := (r-1)*137 + 109
				if [4]byte(files["YTDATA.DAT"][at:at+4]) != encode(-1) {
					t.Fatal("inactive ranks")
				}
			}
			after, _ := json.Marshal(in)
			if !bytes.Equal(recipe, after) || !reflect.DeepEqual(saved, before) {
				t.Fatal("input mutation")
			}
			for _, v := range files {
				if len(v) > 0 {
					v[0] ^= 1
				}
			}
			if !reflect.DeepEqual(saved, before) {
				t.Fatal("output alias")
			}
		})
	}
	if events != 120 || activations == 0 {
		t.Fatal("combat and tail coverage", events, activations)
	}
}
func TestOccupiedFilesAtomicLateRefusals(t *testing.T) {
	var chosen occupiedFilesCase
	for _, c := range occupiedFilesLoad(t) {
		if len(c.Tail.Helpers) > 0 {
			chosen = c
			break
		}
	}
	if chosen.Name == "" {
		t.Fatal("late helper case")
	}
	tests := map[string]func(map[string][]byte, *OccupiedInputs){
		"world pin":         func(b map[string][]byte, in *OccupiedInputs) { b["YTDATA.DAT"][0] ^= 1 },
		"names pin":         func(b map[string][]byte, in *OccupiedInputs) { b["YTNAME.DAT"][0] ^= 1 },
		"news pin":          func(b map[string][]byte, in *OccupiedInputs) { b["YTNEWS.DAT"][0] ^= 1 },
		"extra file":        func(b map[string][]byte, in *OccupiedInputs) { b["YTRMSG.DAT"] = nil },
		"state":             func(b map[string][]byte, in *OccupiedInputs) { in.StartupState = 1 << 24 },
		"port day":          func(b map[string][]byte, in *OccupiedInputs) { in.Ports.Days[999] = 307 },
		"strict ports":      func(b map[string][]byte, in *OccupiedInputs) { in.Ports.Capped = false },
		"final calendar":    func(b map[string][]byte, in *OccupiedInputs) { in.FinalDay = 307 },
		"news calendar":     func(b map[string][]byte, in *OccupiedInputs) { in.Reports.NewsDate = "2026-11-03" },
		"late report clock": func(b map[string][]byte, in *OccupiedInputs) { in.Reports.ScoreClock = "bad" },
		"tail exhaustion":   func(b map[string][]byte, in *OccupiedInputs) { in.TailHelpers = in.TailHelpers[:len(in.TailHelpers)-1] },
		"tail caller":       func(b map[string][]byte, in *OccupiedInputs) { in.TailHelpers[len(in.TailHelpers)-1].Caller ^= 1 },
		"tail TIMER": func(b map[string][]byte, in *OccupiedInputs) {
			in.TailHelpers[len(in.TailHelpers)-1].Timer = encode(-1)
		},
		"surplus tail clock": func(b map[string][]byte, in *OccupiedInputs) {
			in.TailHelpers = append(in.TailHelpers, in.TailHelpers[0])
		},
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			before, in := occupiedFilesInputs(t, chosen)
			change(before, &in)
			saved := cloneAuxFiles(before)
			recipe, _ := json.Marshal(in)
			files, s, e := ReplayOccupiedFiles(before, in)
			after, _ := json.Marshal(in)
			if e == nil || files != nil || !reflect.DeepEqual(s, OccupiedStats{}) || !bytes.Equal(recipe, after) || !reflect.DeepEqual(before, saved) {
				t.Fatal("non-atomic refusal", e)
			}
		})
	}
}
