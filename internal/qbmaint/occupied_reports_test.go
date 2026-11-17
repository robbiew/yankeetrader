package qbmaint

import (
	"bytes"
	"encoding/json"
	"math"
	"os"
	"reflect"
	"strings"
	"testing"
)

type occupiedReportCase struct {
	Name       string
	Before     map[string]string
	World      string `json:"world_sha256"`
	NewsDate   string `json:"news_date"`
	NewsClock  string `json:"news_clock"`
	ScoreDate  string `json:"score_date"`
	ScoreClock string `json:"score_clock"`
	Events     []json.RawMessage
	Expected   map[string]string `json:"expected_files"`
	Statistics struct {
		Scores       map[string]int
		Losses       map[string]int `json:"modeled_losses"`
		Physical     []map[string]int
		Percentages  []float64
		PublicEvents int `json:"public_events"`
	}
}
type occupiedReportFixture struct {
	Format      string
	Blobs       map[string]string
	Cases       []occupiedReportCase
	Comparisons int `json:"native_six_file_comparisons"`
	Witnesses   int `json:"native_rng_witnesses"`
}

func reportLoad(t *testing.T) occupiedReportFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/occupied_reports.json")
	if e != nil {
		t.Fatal(e)
	}
	var d occupiedReportFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-occupied-reports-v1" || len(d.Cases) != 30 || d.Comparisons != 180 || d.Witnesses != 1872 {
		t.Fatal("qualified inventory")
	}
	return d
}
func reportInputs(t *testing.T, d occupiedReportFixture, c occupiedReportCase) (map[string][]byte, []byte, AuxInputs, []OccupiedCombatEvent) {
	t.Helper()
	before := map[string][]byte{}
	for n, sha := range c.Before {
		before[n] = unpack(t, d.Blobs[sha])
		if digest(before[n]) != sha {
			t.Fatal("original before identity")
		}
	}
	world := unpack(t, d.Blobs[c.World])
	if digest(world) != c.World {
		t.Fatal("modeled finalized-world identity")
	}
	events := []OccupiedCombatEvent{}
	for _, raw := range c.Events {
		var v struct {
			Kind                            string
			Group, Sector, Force, Defenders int
			InitialForce                    int `json:"initial_force"`
			InitialDefenders                int `json:"initial_defenders"`
			XDamage                         int `json:"x_damage"`
			DefenderDamage                  int `json:"defender_damage"`
		}
		if e := json.Unmarshal(raw, &v); e != nil {
			t.Fatal(e)
		}
		event := OccupiedCombatEvent{Kind: v.Kind, Group: v.Group, Sector: v.Sector}
		if v.Kind == "defense" {
			event.Defense = &ForeignDefenseStats{InitialForce: v.InitialForce, Force: v.Force, InitialDefenders: v.InitialDefenders, Defenders: v.Defenders, XDamage: v.XDamage, DefenderDamage: v.DefenderDamage}
		} else {
			event.Ground = &NeutralGroundStats{InitialForce: v.InitialForce, Force: v.Force}
		}
		events = append(events, event)
	}
	return before, world, AuxInputs{NewsDate: c.NewsDate, NewsClock: c.NewsClock, ScoreDate: c.ScoreDate, ScoreClock: c.ScoreClock}, events
}
func TestOccupiedReportsQualifiedFiveFilesAndGoEvents(t *testing.T) {
	d := reportLoad(t)
	routing, economy := occupiedRouteLoad(t), occupiedPlanetLoad(t)
	count := 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, world, in, events := reportInputs(t, d, c)
			saved := cloneAuxFiles(before)
			savedWorld := bytes.Clone(world)
			receipt, _ := json.Marshal(events)
			files, stats, e := ReplayOccupiedAux(before, world, in, events)
			if e != nil {
				t.Fatal(e)
			}
			if len(files) != 5 || stats.PublicEvents != len(events) {
				t.Fatal("five-file/event inventory")
			}
			for n, sha := range c.Expected {
				if digest(files[n]) != sha {
					t.Fatal("complete qualified output mismatch", n)
				}
			}
			for i, key := range []string{"-1", "-2"} {
				if stats.Scores[i] != c.Statistics.Scores[key] || stats.Losses[i] != c.Statistics.Losses[key] || stats.PercentHundredths[i] != int(math.Round(c.Statistics.Percentages[i]*100)) {
					t.Fatal("scores/losses/display rounding")
				}
			}
			for i, p := range stats.Physical {
				for j, key := range []string{"-1", "-2", "0"} {
					if p[j] != c.Statistics.Physical[i][key] {
						t.Fatal("unique physical faction totals")
					}
				}
			}
			for _, n := range []string{"YTNEWS.DAT", "YTSCORE.ASC"} {
				b := files[n]
				if !bytes.HasSuffix(b, []byte{'\r', '\n', 26}) || bytes.Count(b, []byte{26}) != 1 || bytes.Contains(bytes.ReplaceAll(b, []byte("\r\n"), nil), []byte{'\n'}) {
					t.Fatal("DOS report framing")
				}
			}
			after, _ := json.Marshal(events)
			if !bytes.Equal(receipt, after) || !reflect.DeepEqual(before, saved) || !bytes.Equal(world, savedWorld) {
				t.Fatal("source mutation")
			}
			found := false
			for _, r := range routing.Cases {
				if r.Name != c.Name {
					continue
				}
				for _, p := range economy.Cases {
					if p.Name != c.Name {
						continue
					}
					found = true
					work := unpack(t, economy.Worlds[p.Initial])
					schedule := PortSchedule{Days: p.Ports.Days, Capped: true}
					for _, s := range p.Ports.Timers {
						schedule.TimerMinutes = append(schedule.TimerMinutes, planetRaw(t, s))
					}
					block, _, e := ReplayCleanPorts(work, schedule)
					if e != nil {
						t.Fatal(e)
					}
					copy(work[PortStart:PortStart+PortCount*RecordSize], block)
					work, planet, e := ReplayOccupiedPlanets(work, occupiedPlanetInputs(t, p))
					if e != nil {
						t.Fatal(e)
					}
					routeInput := occupiedRouteInputs(t, r)
					routeInput.State = planet.FinalState
					_, goEvents, e := ReplayOccupiedHomeMobile(work, routeInput)
					if e != nil {
						t.Fatal(e)
					}
					// Tail/final metadata still come from the independently modeled fixture.
					// This qualifies actual Go event handoff, not complete Go six-file replay.
					out, actual, e := ReplayOccupiedAux(before, world, in, goEvents.Events)
					if e != nil || !reflect.DeepEqual(stats, actual) {
						t.Fatal("actual Go event handoff", e)
					}
					for n, sha := range c.Expected {
						if digest(out[n]) != sha {
							t.Fatal("composed Go-event report", n)
						}
					}
				}
			}
			if !found {
				t.Fatal("Go routing/economy input inventory")
			}
			for _, b := range files {
				if len(b) > 0 {
					b[0] ^= 255
				}
			}
			if !reflect.DeepEqual(before, saved) || !bytes.Equal(world, savedWorld) {
				t.Fatal("output aliases input")
			}
			count += len(events)
		})
	}
	if count != 120 {
		t.Fatal("complete event corpus", count)
	}
}
func TestOccupiedReportsAtomicRefusals(t *testing.T) {
	d := reportLoad(t)
	var c occupiedReportCase
	for _, v := range d.Cases {
		if strings.HasPrefix(v.Name, "route-mercenary-37/") {
			c = v
			break
		}
	}
	cases := map[string]func(map[string][]byte, []byte, *AuxInputs, *[]OccupiedCombatEvent){
		"extra file": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) { b["YTRMSG.DAT"] = nil },
		"score path": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) { b["YTDATA.DAT"][0] = 'X' },
		"geometry": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) {
			planetPut(w, 1, 61, 4052)
		},
		"unpublished ranks": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) { planetPut(w, 2, 109, 0) },
		"human assets":      func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) { planetPut(w, 2, 41, 1) },
		"before bank": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) {
			planetPut(b["YTDATA.DAT"], 2, 117, 1)
		},
		"tax": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) {
			planetPut(b["YTDATA.DAT"], 3053, 89, 1)
		},
		"changed home":    func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) { w[4051*RecordSize] = 'X' },
		"unknown owner":   func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) { planetPut(w, 52, 85, 1) },
		"unknown event":   func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) { (*e)[0].Kind = "ship" },
		"missing payload": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) { (*e)[0].Defense = nil },
		"dead group repeated": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) {
			(*e)[1].Group = (*e)[0].Group
		},
		"wrong sector": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) { (*e)[0].Sector = 853 },
		"forged casualties": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) {
			(*e)[0].Defense.InitialForce++
		},
		"negative counter": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) {
			(*e)[0].Defense.XDamage = -1
		},
		"oversized counter": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) {
			(*e)[0].Defense.DefenderDamage = 200000
		},
		"both survive": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) {
			(*e)[0].Defense.Force = 1
		},
		"date": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) { in.NewsDate = "bad" },
		"clock": func(b map[string][]byte, w []byte, in *AuxInputs, e *[]OccupiedCombatEvent) {
			in.ScoreClock = "0:00:00"
		},
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			before, world, in, events := reportInputs(t, d, c)
			change(before, world, &in, &events)
			saved := cloneAuxFiles(before)
			savedWorld := bytes.Clone(world)
			recipe, _ := json.Marshal(events)
			out, stats, e := ReplayOccupiedAux(before, world, in, events)
			if e == nil || out != nil || !reflect.DeepEqual(stats, OccupiedReportStats{}) {
				t.Fatal("unsupported/partial publication")
			}
			after, _ := json.Marshal(events)
			if !reflect.DeepEqual(before, saved) || !bytes.Equal(world, savedWorld) || !bytes.Equal(recipe, after) {
				t.Fatal("failed replay mutated input")
			}
		})
	}
}
func TestOccupiedReportsSourceLabelsAndIndependentClocks(t *testing.T) {
	d := reportLoad(t)
	for _, c := range d.Cases {
		if !strings.HasSuffix(c.Name, "observed-a") {
			continue
		}
		before, world, in, events := reportInputs(t, d, c)
		before["YTNEWS.DAT"] = []byte{'A', 13, 10, 26, 0, 'B'}
		in.NewsClock = "01:02:03"
		in.ScoreClock = "24:00:00"
		in.ScoreDate = "2026-11-03"
		out, stats, e := ReplayOccupiedAux(before, world, in, events)
		if e != nil {
			t.Fatal(e)
		}
		if !bytes.Equal(out["YTYNEWS.DAT"], before["YTNEWS.DAT"]) || !bytes.HasPrefix(out["YTNEWS.DAT"], []byte("01:02:03 11-02-2026")) || !bytes.Contains(out["YTSCORE.ASC"], []byte("11-03-2026 24:00:00")) {
			t.Fatal("raw rotation/separate calendar clocks")
		}
		if strings.HasPrefix(c.Name, "route-mercenary-37/") {
			if !bytes.Contains(out["YTNEWS.DAT"], []byte("(Plyr ftrs dstrd)")) || !bytes.Contains(out["YTNEWS.DAT"], []byte("(Xannor ftrs dstrd)")) {
				t.Fatal("misleading source suffixes corrected")
			}
		}
		if strings.HasPrefix(c.Name, "route-mercenary-100000/") {
			if stats.Scores != [2]int{514800, 9752500} || !bytes.Contains(out["YTSCORE.ASC"], []byte("5.28%")) {
				t.Fatal("positive Mercenary leader/rounding")
			}
		}
		if strings.HasPrefix(c.Name, "route-neutral-37/") {
			if stats.Scores != [2]int{1000000, 0} || stats.Physical[1][2] != 37 {
				t.Fatal("neutral fighters scored or lost")
			}
		}
	}
}

func TestOccupiedReportsRejectHalfwayPercentAndZeroDenominator(t *testing.T) {
	d := reportLoad(t)
	for _, kind := range []string{"halfway", "denominator"} {
		t.Run(kind, func(t *testing.T) {
			var c occupiedReportCase
			prefix := "route-mercenary-100000/"
			if kind == "denominator" {
				prefix = "route-planet-neutral/"
			}
			for _, v := range d.Cases {
				if strings.HasPrefix(v.Name, prefix) {
					c = v
					break
				}
			}
			before, world, in, _ := reportInputs(t, d, c)
			for s := 1; s <= 3000; s++ {
				planetPut(world, 51+s, 81, 0)
				planetPut(world, 51+s, 85, 0)
			}
			var events []OccupiedCombatEvent
			if kind == "halfway" {
				planetPut(world, 900, 81, 1)
				planetPut(world, 900, 85, -1)
				planetPut(world, 905, 81, 32)
				planetPut(world, 905, 85, -2)
				events = []OccupiedCombatEvent{{Kind: "defense", Group: 2, Sector: 854, Defense: &ForeignDefenseStats{InitialForce: 9999, Force: 0, InitialDefenders: 100000, Defenders: 32, XDamage: 9999, DefenderDamage: 99968}}}
			} else {
				events = []OccupiedCombatEvent{{Kind: "planet", Group: 2, Sector: 854, Ground: &NeutralGroundStats{InitialForce: 10000, Force: 0}}}
			}
			saved := bytes.Clone(world)
			out, stats, e := ReplayOccupiedAux(before, world, in, events)
			if e == nil || !strings.Contains(e.Error(), kind) || out != nil || !reflect.DeepEqual(stats, OccupiedReportStats{}) || !bytes.Equal(world, saved) {
				t.Fatal("unsupported numeric formatting did not fail atomically", e)
			}
		})
	}
}
