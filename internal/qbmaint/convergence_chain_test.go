package qbmaint

import (
	"bytes"
	"encoding/json"
	"reflect"
	"strings"
	"testing"
)

// Only the original day-one before files are decompressed. Later before worlds,
// phase worlds, observed endpoints and auxiliary targets never enter the recipe.
func convergenceRecipe(t *testing.T, observation string) (map[string][]byte, []ConvergenceDayInputs, []evolvedAuxCase) {
	t.Helper()
	aux, ports, planets := evolvedAuxLoad(t), evolvedLoad(t), planetLoad(t)
	births, homes, tails := dayOneLoad(t), continuationLoad(t), evolvedTailLoad(t)
	var before map[string][]byte
	days := []ConvergenceDayInputs{}
	expected := []evolvedAuxCase{}
	for _, a := range aux.Cases {
		if !strings.HasPrefix(a.Name, observation+"/") {
			continue
		}
		if a.FinalDay == 306 {
			before = map[string][]byte{}
			for n, sha := range a.Before {
				before[n] = unpack(t, aux.Blobs[sha])
				if digest(before[n]) != sha {
					t.Fatal("initial identity")
				}
			}
		}
		in := ConvergenceDayInputs{Day: a.FinalDay, Reports: AuxInputs{NewsDate: a.NewsDate, NewsClock: a.NewsClock, ScoreDate: a.ScoreDate, ScoreClock: a.ScoreClock}}
		found := [4]bool{}
		for _, p := range ports.Cases {
			if p.Name == a.Name {
				found[0] = true
				in.Ports.Days = p.Days
				for _, timer := range p.Timers {
					in.Ports.TimerMinutes = append(in.Ports.TimerMinutes, planetRaw(t, timer))
				}
			}
		}
		for _, p := range planets.Cases {
			if p.Name == a.Name {
				found[1] = true
				v := planetInputs(t, p)
				in.InitialState = v.State
				in.Planets = v.Clocks
			}
		}
		if in.Day == 306 {
			for _, h := range births.Cases {
				if h.Name == a.Name {
					found[2] = true
					v := dayOneInputs(t, h)
					in.Creation = &ConvergenceCreationClocks{WandererDay: v.WandererDay, XannoronDay: v.XannoronDay, BaseDay: v.BaseDay, XannoronTimer: v.XannoronTimer}
					in.HomeHelpers = v.Helpers
				}
			}
		} else {
			for _, h := range homes.Cases {
				if h.Name == a.Name {
					found[2] = true
					in.HomeHelpers = continuationInputs(t, h).Helpers
				}
			}
		}
		for _, tail := range tails.Cases {
			if tail.Name == "convergence/"+a.Name {
				found[3] = true
				in.TailHelpers = evolvedTailInputs(t, tail).Helpers
			}
		}
		if found != [4]bool{true, true, true, true} {
			t.Fatal("complete clock-only recipe inventory")
		}
		days = append(days, in)
		expected = append(expected, a)
	}
	if len(days) != 3 || before == nil {
		t.Fatal("three source days")
	}
	return before, days, expected
}

func TestConvergenceChainOwnSixFileHandoffs(t *testing.T) {
	for _, observation := range []string{"observed-a", "observed-b", "observed-c"} {
		t.Run(observation, func(t *testing.T) {
			before, days, expected := convergenceRecipe(t, observation)
			saved := cloneAuxFiles(before)
			recipe, _ := json.Marshal(days)
			rows, err := ReplayConvergenceChain(before, days)
			if err != nil {
				t.Fatal(err)
			}
			if len(rows) != 3 {
				t.Fatal("three complete results")
			}
			planets, homes, births, tails := planetLoad(t), continuationLoad(t), dayOneLoad(t), evolvedTailLoad(t)
			for index, row := range rows {
				c := expected[index]
				if len(row.Files) != 6 {
					t.Fatal("six files")
				}
				for n, sha := range c.Expected {
					if digest(row.Files[n]) != sha {
						t.Fatalf("%s %s: complete output mismatch", c.Name, n)
					}
				}
				previous := before
				if index > 0 {
					previous = rows[index-1].Files
				}
				if !bytes.Equal(row.Files["YTYNEWS.DAT"], previous["YTNEWS.DAT"]) || !bytes.Equal(row.Files["YTNAME.DAT"], before["YTNAME.DAT"]) {
					t.Fatal("actual prior Go journal/name handoff")
				}
				if row.Planets.InitialState != days[index].InitialState || row.Homes.InitialState != row.Planets.FinalState || row.Tail.InitialState != row.Homes.FinalState {
					t.Fatal("within-day computed RNG continuation")
				}
				// End states and helper-derived outcomes remain model receipts, separate
				// from the complete native-qualified six-file hashes above.
				for _, p := range planets.Cases {
					if p.Name == c.Name && row.Planets.FinalState != p.Final {
						t.Fatal("planet state")
					}
				}
				for _, h := range homes.Cases {
					if h.Name == c.Name && row.Homes.FinalState != h.Final {
						t.Fatal("existing-home state")
					}
				}
				for _, h := range births.Cases {
					if h.Name == c.Name && row.Homes.FinalState != h.Final {
						t.Fatal("birth state")
					}
				}
				for _, tail := range tails.Cases {
					if tail.Name == "convergence/"+c.Name && row.Tail.FinalState != tail.Final {
						t.Fatal("tail state")
					}
				}
				if row.Ports.Day != 306+index || (row.Homes.Births != nil) != (index == 0) {
					t.Fatal("phase day/creation boundary")
				}
			}
			after, _ := json.Marshal(days)
			if !bytes.Equal(recipe, after) || !reflect.DeepEqual(saved, before) {
				t.Fatal("input mutation")
			}
			// Later computation must not overwrite earlier owned results; mutation after
			// return must not reach another day or the original before files.
			snapshots := make([]map[string][]byte, 3)
			for i, r := range rows {
				snapshots[i] = cloneAuxFiles(r.Files)
			}
			for i, row := range rows {
				for _, b := range row.Files {
					if len(b) > 0 {
						b[0] ^= 255
					}
				}
				for j := i + 1; j < 3; j++ {
					if !reflect.DeepEqual(rows[j].Files, snapshots[j]) {
						t.Fatal("cross-day alias")
					}
				}
			}
			if !reflect.DeepEqual(before, saved) {
				t.Fatal("output aliases original input")
			}
		})
	}
}

func TestConvergenceChainAtomicRefusals(t *testing.T) {
	cases := map[string]func(map[string][]byte, []ConvergenceDayInputs) []ConvergenceDayInputs{
		"missing day": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs { return d[:2] },
		"extra day":   func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs { return append(d, d[2]) },
		"reordered days": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			d[1], d[2] = d[2], d[1]
			return d
		},
		"unknown initial file": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs { b["other"] = nil; return d },
		"changed initial world": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			b["YTDATA.DAT"][0] ^= 1
			return d
		},
		"changed names": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			b["YTNAME.DAT"][0] ^= 1
			return d
		},
		"changed journal": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			b["YTNEWS.DAT"] = []byte("changed")
			return d
		},
		"startup state": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			d[2].InitialState = 0x1000000
			return d
		},
		"mixed port day": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			d[1].Ports.Days[500]--
			return d
		},
		"mixed planet day": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			d[2].Planets[0].Day--
			return d
		},
		"missing creation": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			d[0].Creation = nil
			return d
		},
		"repeated creation": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			d[2].Creation = d[0].Creation
			return d
		},
		"day two exhausted helpers": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			d[1].HomeHelpers = nil
			return d
		},
		"day three wrong tail caller": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			d[2].TailHelpers[0].Caller ^= 1
			return d
		},
		"day three bad report": func(b map[string][]byte, d []ConvergenceDayInputs) []ConvergenceDayInputs {
			d[2].Reports.ScoreClock = "bad"
			return d
		},
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			before, days, _ := convergenceRecipe(t, "observed-a")
			days = change(before, days)
			saved := cloneAuxFiles(before)
			recipe, _ := json.Marshal(days)
			rows, err := ReplayConvergenceChain(before, days)
			if err == nil || rows != nil {
				t.Fatal("unsupported chain published partial results")
			}
			after, _ := json.Marshal(days)
			if !bytes.Equal(recipe, after) || !reflect.DeepEqual(before, saved) {
				t.Fatal("failed chain mutated inputs")
			}
		})
	}
}
