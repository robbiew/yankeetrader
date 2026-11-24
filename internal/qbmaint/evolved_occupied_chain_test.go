package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

type occupiedChainClock struct {
	Family int
	Caller uint16
	Timer  string
}
type occupiedChainDay struct {
	Day   int
	State uint32 `json:"startup_state"`
	Ports struct {
		Days   []int
		Timers []string
	}
	Planets []struct {
		Record, Day int
		Timer       string
	}
	Creation *struct {
		Wanderer int    `json:"wanderer_day"`
		Xannoron int    `json:"xannoron_day"`
		Base     int    `json:"base_day"`
		Timer    string `json:"xannoron_timer"`
	}
	Home    []occupiedChainClock `json:"home_helpers"`
	Tail    []occupiedChainClock `json:"tail_helpers"`
	Reports struct {
		NewsDate   string `json:"news_date"`
		NewsClock  string `json:"news_clock"`
		ScoreDate  string `json:"score_date"`
		ScoreClock string `json:"score_clock"`
	}
	Expected map[string]string `json:"expected_files"`
	Routing  uint32            `json:"routing_final_state"`
	Final    uint32            `json:"final_state"`
}
type occupiedChainCase struct {
	Name    string
	Initial map[string]string `json:"initial_files"`
	Days    []occupiedChainDay
}
type occupiedChainFixture struct {
	Format      string
	Worlds      map[string]string
	Cases       []occupiedChainCase
	Comparisons int `json:"native_six_file_comparisons"`
	Witnesses   int `json:"native_rng_witnesses"`
}

func occupiedChainLoad(t *testing.T) occupiedChainFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/evolved_occupied_chain.json")
	if e != nil {
		t.Fatal(e)
	}
	var d occupiedChainFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-evolved-occupied-chain-v1" || len(d.Cases) != 12 || d.Comparisons != 144 || d.Witnesses != 1242 {
		t.Fatal("qualified chain inventory")
	}
	return d
}
func occupiedChainInputs(t *testing.T, d occupiedChainFixture, c occupiedChainCase) (map[string][]byte, []EvolvedOccupiedDayInputs) {
	t.Helper()
	before := map[string][]byte{}
	for n, h := range c.Initial {
		before[n] = unpack(t, d.Worlds[h])
		if digest(before[n]) != h {
			t.Fatal("original fingerprint")
		}
	}
	days := []EvolvedOccupiedDayInputs{}
	for _, v := range c.Days {
		in := EvolvedOccupiedDayInputs{Day: v.Day, InitialState: v.State, Ports: EvolvedPortSchedule{Days: append([]int(nil), v.Ports.Days...)}, Reports: AuxInputs{NewsDate: v.Reports.NewsDate, NewsClock: v.Reports.NewsClock, ScoreDate: v.Reports.ScoreDate, ScoreClock: v.Reports.ScoreClock}}
		for _, s := range v.Ports.Timers {
			in.Ports.TimerMinutes = append(in.Ports.TimerMinutes, planetRaw(t, s))
		}
		for _, r := range v.Planets {
			in.Planets = append(in.Planets, PlanetClock{Record: r.Record, Day: r.Day, TimerMinutes: planetRaw(t, r.Timer)})
		}
		if v.Creation != nil {
			r := v.Creation
			in.Creation = &ConvergenceCreationClocks{WandererDay: r.Wanderer, XannoronDay: r.Xannoron, BaseDay: r.Base, XannoronTimer: planetRaw(t, r.Timer)}
		}
		for _, r := range v.Home {
			in.HomeHelpers = append(in.HomeHelpers, ContinuationClock{Family: r.Family, Caller: r.Caller, Timer: planetRaw(t, r.Timer)})
		}
		for _, r := range v.Tail {
			in.TailHelpers = append(in.TailHelpers, ContinuationClock{Family: r.Family, Caller: r.Caller, Timer: planetRaw(t, r.Timer)})
		}
		days = append(days, in)
	}
	return before, days
}
func TestEvolvedOccupiedChainOwnDailyResults(t *testing.T) {
	d := occupiedChainLoad(t)
	results := 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, days := occupiedChainInputs(t, d, c)
			saved := cloneAuxFiles(before)
			recipe, _ := json.Marshal(days)
			out, e := ReplayEvolvedOccupiedChain(before, days)
			if e != nil {
				t.Fatal(e)
			}
			if len(out) != 3 {
				t.Fatal("complete three days")
			}
			for i, row := range out {
				want := c.Days[i]
				results++
				if row.Day != 306+i || len(row.Files) != 6 {
					t.Fatal("day/file inventory")
				}
				for n, h := range want.Expected {
					if digest(row.Files[n]) != h {
						t.Fatal("complete modeled six-file mismatch", i, n)
					}
				}
				if i == 0 {
					if row.Initial == nil || row.Initial.Planets.InitialState != days[i].InitialState || row.Initial.Routing.InitialState != row.Initial.Planets.FinalState || row.Initial.Tail.InitialState != row.Initial.Routing.FinalState || row.Initial.Routing.FinalState != want.Routing || row.Initial.Tail.FinalState != want.Final {
						t.Fatal("first-day calculated state handoff")
					}
				}
				if i > 0 {
					if row.Initial != nil || row.Ports.RNGDraws != 0 || row.Planets.InitialState != days[i].InitialState || row.Mobile.InitialState != row.Planets.FinalState || row.Tail.InitialState != row.Mobile.FinalState || row.Mobile.FinalState != want.Routing || row.Tail.FinalState != want.Final {
						t.Fatal("child state handoff")
					}
					if !bytes.Equal(row.Files["YTYNEWS.DAT"], out[i-1].Files["YTNEWS.DAT"]) {
						t.Fatal("own previous-news rotation")
					}
				}
			}
			after, _ := json.Marshal(days)
			if !reflect.DeepEqual(saved, before) || !bytes.Equal(recipe, after) {
				t.Fatal("caller input mutation")
			}
			// World/name/news buffers must remain owned across days as well as input.
			snapshots := []map[string][]byte{}
			for _, row := range out {
				snapshots = append(snapshots, cloneAuxFiles(row.Files))
			}
			for day := range out {
				for n, b := range out[day].Files {
					if len(b) == 0 {
						continue
					}
					b[0] ^= 1
					for j, row := range out {
						if j != day && !reflect.DeepEqual(row.Files, snapshots[j]) {
							t.Fatal("cross-day alias", day, j, n)
						}
					}
					b[0] ^= 1
				}
			}
			if !reflect.DeepEqual(before, saved) {
				t.Fatal("output/input alias")
			}
		})
	}
	if results != 36 {
		t.Fatal("result coverage", results)
	}
}
func TestEvolvedOccupiedChainAtomicRefusals(t *testing.T) {
	d := occupiedChainLoad(t)
	c := d.Cases[0]
	tests := map[string]func(map[string][]byte, *[]EvolvedOccupiedDayInputs){
		"world pin":            func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { b["YTDATA.DAT"][0] ^= 1 },
		"side pin":             func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { b["YTNAME.DAT"][0] ^= 1 },
		"extra file":           func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { b["YTRMSG.DAT"] = nil },
		"missing day":          func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { *p = (*p)[:2] },
		"day order":            func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[1], (*p)[2] = (*p)[2], (*p)[1] },
		"day repeat":           func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[2].Day = 307 },
		"startup":              func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[2].InitialState = 1 << 24 },
		"missing creation":     func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[0].Creation = nil },
		"child creation":       func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[1].Creation = (*p)[0].Creation },
		"port calendar":        func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[1].Ports.Days[999]++ },
		"port timer extent":    func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[1].Ports.TimerMinutes = nil },
		"planet calendar":      func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[2].Planets[0].Day++ },
		"report calendar":      func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[2].Reports.ScoreDate = "2026-11-03" },
		"late port clock":      func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[2].Ports.TimerMinutes[999] = encode(1) },
		"late planet clock":    func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[2].Planets[0].TimerMinutes = encode(1) },
		"late home exhaustion": func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[2].HomeHelpers = nil },
		"late home caller": func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) {
			(*p)[2].HomeHelpers[len((*p)[2].HomeHelpers)-1].Caller ^= 1
		},
		"late tail exhaustion": func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[2].TailHelpers = nil },
		"late tail surplus": func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) {
			i := &(*p)[2]
			i.TailHelpers = append(i.TailHelpers, ContinuationClock{Family: 1, Caller: 0x53b4})
		},
		"late report clock": func(b map[string][]byte, p *[]EvolvedOccupiedDayInputs) { (*p)[2].Reports.NewsClock = "25:00:00" },
	}
	for name, f := range tests {
		t.Run(name, func(t *testing.T) {
			b, p := occupiedChainInputs(t, d, c)
			f(b, &p)
			saved := cloneAuxFiles(b)
			recipe, _ := json.Marshal(p)
			out, e := ReplayEvolvedOccupiedChain(b, p)
			after, _ := json.Marshal(p)
			if e == nil || out != nil || !reflect.DeepEqual(b, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("non-atomic chain failure", e)
			}
		})
	}
	// The separate convergence pin and all six other occupied originals stay out.
	rejected := map[string]bool{}
	for _, v := range occupiedFilesLoad(t) {
		if v.Name == c.Name {
			continue
		}
		b, _ := occupiedFilesInputs(t, v)
		_, p := occupiedChainInputs(t, d, c)
		h := digest(b["YTDATA.DAT"])
		admitted := false
		for _, row := range d.Cases {
			if row.Initial["YTDATA.DAT"] == h {
				admitted = true
			}
		}
		if !admitted {
			if out, e := ReplayEvolvedOccupiedChain(b, p); e == nil || out != nil {
				t.Fatal("unqualified occupied original")
			}
			rejected[h] = true
		}
	}
	if len(rejected) != 6 {
		t.Fatal("six other occupied originals", len(rejected))
	}
	other, _, _ := convergenceRecipe(t, "observed-a")
	_, recipe := occupiedChainInputs(t, d, c)
	if out, e := ReplayEvolvedOccupiedChain(other, recipe); e == nil || out != nil {
		t.Fatal("convergence original incorrectly admitted")
	}
}
