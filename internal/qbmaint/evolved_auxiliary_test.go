package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"strings"
	"testing"
)

type evolvedAuxCase struct {
	Name       string
	Before     map[string]string
	Modeled    string `json:"modeled_sha256"`
	FinalDay   int    `json:"final_day"`
	NewsDate   string `json:"news_date"`
	NewsClock  string `json:"news_clock"`
	ScoreDate  string `json:"score_date"`
	ScoreClock string `json:"score_clock"`
	Created    [3]bool
	Expected   map[string]string `json:"expected_files"`
}
type evolvedAuxFixture struct {
	Format      string
	Blobs       map[string]string
	Cases       []evolvedAuxCase
	Comparisons int `json:"native_six_file_comparisons"`
	Witnesses   int `json:"native_rng_witnesses"`
	Fields      int `json:"native_cache_fields"`
}

func evolvedAuxLoad(t *testing.T) evolvedAuxFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/evolved_auxiliary.json")
	if e != nil {
		t.Fatal(e)
	}
	var d evolvedAuxFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-evolved-aux-v1" || len(d.Cases) != 9 || d.Comparisons != 54 || d.Witnesses != 501 || d.Fields != 1440 {
		t.Fatal("qualified inventory")
	}
	return d
}
func evolvedAuxInputs(t *testing.T, d evolvedAuxFixture, c evolvedAuxCase) (map[string][]byte, []byte, EvolvedAuxInputs) {
	t.Helper()
	before := map[string][]byte{}
	for n, sha := range c.Before {
		before[n] = unpack(t, d.Blobs[sha])
		if digest(before[n]) != sha {
			t.Fatal("before identity")
		}
	}
	world := unpack(t, d.Blobs[c.Modeled])
	if digest(world) != c.Modeled {
		t.Fatal("modeled pre-final identity")
	}
	return before, world, EvolvedAuxInputs{AuxInputs: AuxInputs{NewsDate: c.NewsDate, NewsClock: c.NewsClock, ScoreDate: c.ScoreDate, ScoreClock: c.ScoreClock}, FinalDay: c.FinalDay, Created: c.Created}
}
func cloneAuxFiles(files map[string][]byte) map[string][]byte {
	out := map[string][]byte{}
	for n, b := range files {
		out[n] = bytes.Clone(b)
	}
	return out
}
func TestEvolvedAuxNativeQualifiedSixFiles(t *testing.T) {
	d := evolvedAuxLoad(t)
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, world, in := evolvedAuxInputs(t, d, c)
			saved := cloneAuxFiles(before)
			savedWorld := bytes.Clone(world)
			out, e := ReplayEvolvedAux(before, world, in)
			if e != nil {
				t.Fatal(e)
			}
			if len(out) != 6 || len(c.Expected) != 6 {
				t.Fatal("six-file publication")
			}
			for n, sha := range c.Expected {
				if b, ok := out[n]; !ok || digest(b) != sha {
					t.Fatalf("complete native-qualified file mismatch: %s", n)
				}
			}
			if !reflect.DeepEqual(saved, before) || !bytes.Equal(savedWorld, world) {
				t.Fatal("source mutation")
			}
			if !bytes.Equal(out["YTNAME.DAT"], before["YTNAME.DAT"]) || !bytes.Equal(out["YTYNEWS.DAT"], before["YTNEWS.DAT"]) || len(out["YTRMSG.DAT"]) != 0 {
				t.Fatal("name/journal/private semantics")
			}
			for _, n := range []string{"YTNEWS.DAT", "YTSCORE.ASC"} {
				b := out[n]
				if !bytes.HasSuffix(b, []byte{'\r', '\n', 26}) || bytes.Count(b, []byte{26}) != 1 || bytes.Contains(bytes.ReplaceAll(b, []byte("\r\n"), nil), []byte{'\n'}) {
					t.Fatal("exact DOS CRLF/EOF")
				}
			}
			if bytes.Contains(out["YTNEWS.DAT"], []byte("regenerated")) != c.Created[0] || bytes.Contains(out["YTNEWS.DAT"], []byte("have made a Planet")) != c.Created[1] || bytes.Contains(out["YTNEWS.DAT"], []byte("captured Genesis Device")) != c.Created[2] {
				t.Fatal("creation-news mask")
			}
			if !bytes.HasPrefix(out["YTNEWS.DAT"], []byte(c.NewsClock+" ")) || !bytes.Contains(out["YTSCORE.ASC"], []byte(" "+c.ScoreClock+"\r\n")) {
				t.Fatal("independent text clocks")
			}
			allowed := map[int]bool{}
			for j := 0; j < 4; j++ {
				allowed[81+j] = true
			}
			for r := 2; r <= 51; r++ {
				a := (r-1)*RecordSize + 109
				for j := 0; j < 4; j++ {
					allowed[a+j] = true
				}
				if [4]byte(out["YTDATA.DAT"][a:a+4]) != encode(-1) {
					t.Fatal("inactive rank cache")
				}
			}
			for i, b := range out["YTDATA.DAT"] {
				if !allowed[i] && b != world[i] {
					t.Fatal("unowned metadata byte changed")
				}
			}
			if [4]byte(out["YTDATA.DAT"][81:85]) != encode(c.FinalDay) {
				t.Fatal("final source day")
			}
			for _, b := range out {
				if len(b) > 0 {
					b[0] ^= 255
				}
			}
			if !reflect.DeepEqual(saved, before) || !bytes.Equal(savedWorld, world) {
				t.Fatal("returned storage aliases input")
			}
		})
	}
}
func TestEvolvedAuxConsumesActualGoTailWorld(t *testing.T) {
	d := evolvedAuxLoad(t)
	tails := evolvedTailLoad(t)
	continuations := continuationLoad(t)
	days := dayOneLoad(t)
	count := 0
	for _, c := range d.Cases {
		for _, tail := range tails.Cases {
			if tail.Name != "convergence/"+c.Name {
				continue
			}
			// Each case starts from its original/model-derived day input; cross-day Go
			// six-file chaining remains a separate orchestrator qualification task.
			before, _, in := evolvedAuxInputs(t, d, c)
			world := bytes.Clone(before["YTDATA.DAT"])
			ports := evolvedLoad(t)
			for _, p := range ports.Cases {
				if p.Name != c.Name {
					continue
				}
				s := EvolvedPortSchedule{Days: p.Days}
				for _, timer := range p.Timers {
					s.TimerMinutes = append(s.TimerMinutes, planetRaw(t, timer))
				}
				block, _, e := ReplayEvolvedPorts(world, s)
				if e != nil {
					t.Fatal(e)
				}
				copy(world[PortStart:], block)
			}
			planets := planetLoad(t)
			state := uint32(0)
			found := false
			for _, p := range planets.Cases {
				if p.Name != c.Name {
					continue
				}
				var stats EvolvedPlanetStats
				var e error
				world, stats, e = ReplayEvolvedPlanets(world, planetInputs(t, p))
				if e != nil {
					t.Fatal(e)
				}
				state = stats.FinalState
				found = true
			}
			if !found {
				t.Fatal("planet inputs")
			}
			var home ContinuationStats
			var e error
			if c.FinalDay == 306 {
				for _, h := range days.Cases {
					if h.Name != c.Name {
						continue
					}
					hi := dayOneInputs(t, h)
					hi.State = state
					world, home, e = ReplayConvergenceDayOneHomes(world, hi)
				}
			} else {
				for _, h := range continuations.Cases {
					if h.Name != c.Name {
						continue
					}
					hi := continuationInputs(t, h)
					hi.State = state
					world, home, e = ReplayExistingHomeContinuation(world, hi)
				}
			}
			if e != nil {
				t.Fatal(e)
			}
			in.Created = [3]bool{}
			if home.Births != nil {
				for i, key := range []string{"wanderer", "xannoron", "base"} {
					in.Created[i] = home.Births.Created[i] == key
				}
			}
			ti := evolvedTailInputs(t, tail)
			ti.State = home.FinalState
			world, _, e = ReplayEvolvedNPCTail(world, ti)
			if e != nil {
				t.Fatal(e)
			}
			if digest(world) != c.Modeled {
				t.Fatal("actual Go pre-final handoff")
			}
			out, e := ReplayEvolvedAux(before, world, in)
			if e != nil {
				t.Fatal(e)
			}
			for n, sha := range c.Expected {
				if digest(out[n]) != sha {
					t.Fatal("composed six-file mismatch", n)
				}
			}
			count++
		}
	}
	if count != 9 {
		t.Fatal("per-day Go composition inventory")
	}
}
func TestEvolvedAuxAtomicRefusals(t *testing.T) {
	d := evolvedAuxLoad(t)
	c := d.Cases[1]
	cases := map[string]func(map[string][]byte, []byte, *EvolvedAuxInputs){
		"unknown file":         func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { b["unknown"] = nil },
		"missing file":         func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { delete(b, "YTSCORE.ASC") },
		"private compression":  func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { b["YTRMSG.DAT"] = []byte{26} },
		"partial creation":     func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { i.Created = [3]bool{true, false, false} },
		"invented creation":    func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { i.Created = [3]bool{true, true, true} },
		"day":                  func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { i.FinalDay = 309 },
		"source date":          func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { i.ScoreDate = "2026-11-05" },
		"clock":                func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { i.NewsClock = "0:00:00" },
		"score path":           func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { w[0] = 'X' },
		"already final":        func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { planetPut(w, 1, 81, float64(i.FinalDay)) },
		"human before assets":  func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { planetPut(b["YTDATA.DAT"], 2, 117, 1) },
		"human modeled assets": func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { planetPut(w, 2, 117, 1) },
		"tax":                  func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { planetPut(w, 3052, 89, 1) },
		"physical owner": func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) {
			for s := 1; s <= 3000; s++ {
				a := (50+s)*RecordSize + 81
				if portSingleValue([4]byte(w[a:a+4])) > 0 {
					planetPut(w, 51+s, 85, -2)
					return
				}
			}
		},
		"unknown planet": func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { planetPut(w, 4054, 85, 1) },
		"wrong home":     func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { planetPut(w, 4150, 73, 0) },
		"Haven":          func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { planetPut(w, 4053, 73, 0) },
		"stale link":     func(b map[string][]byte, w []byte, i *EvolvedAuxInputs) { planetPut(w, 52, 93, 99) },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			before, world, in := evolvedAuxInputs(t, d, c)
			change(before, world, &in)
			saved := cloneAuxFiles(before)
			savedWorld := bytes.Clone(world)
			out, e := ReplayEvolvedAux(before, world, in)
			if e == nil || out != nil {
				t.Fatal("non-atomic refusal")
			}
			if !reflect.DeepEqual(saved, before) || !bytes.Equal(savedWorld, world) {
				t.Fatal("input mutation on refusal")
			}
		})
	}
	before, world, in := evolvedAuxInputs(t, d, d.Cases[0])
	if _, e := ReplayInitialAux(before, world, in.AuxInputs); e == nil {
		t.Fatal("strict bootstrap auxiliary API broadened")
	}
	if out, e := ReplayEvolvedAux(nil, nil, EvolvedAuxInputs{}); e == nil || out != nil {
		t.Fatal("world/inventory extent")
	}
}
func TestEvolvedAuxRawJournalRotationAndSeparateClocks(t *testing.T) {
	d := evolvedAuxLoad(t)
	before, world, in := evolvedAuxInputs(t, d, d.Cases[1])
	raw := []byte{'A', '\r', '\n', 26, 0, 'B'}
	before["YTNEWS.DAT"] = raw
	in.NewsClock = "01:02:03"
	in.ScoreClock = "24:00:00"
	out, e := ReplayEvolvedAux(before, world, in)
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(out["YTYNEWS.DAT"], raw) || !bytes.HasPrefix(out["YTNEWS.DAT"], []byte("01:02:03 ")) || !strings.Contains(string(out["YTSCORE.ASC"]), "24:00:00\r\n") {
		t.Fatal("rotation/clock boundary")
	}
	out["YTYNEWS.DAT"][0] = 'X'
	if raw[0] != 'A' {
		t.Fatal("rotation alias")
	}
}
