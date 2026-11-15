package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

type continuationCase struct {
	Name               string
	BeforeSHA          string `json:"before_sha256"`
	State              uint32 `json:"initial_state"`
	Final              uint32 `json:"final_state"`
	SHA                string `json:"expected_sha256"`
	Draws, Allocations int
	Increment          int   `json:"xannoron_increment"`
	Wanderer           int   `json:"wanderer_sector"`
	Base               int   `json:"base_sector"`
	Attempts           []int `json:"wanderer_attempts"`
	Helpers            []struct {
		Family int
		Caller uint16
		Timer  string
	}
	Seeds []struct {
		Family int
		Caller uint16
		Timer  string
		Old    uint32 `json:"old_state"`
		Seed   uint32 `json:"seeded_state"`
	}
	Groups, Cache [20]MobileGroup
	Routes        []struct {
		Group, Origin, Target, Fallback, Candidate, Preferred, Strength int
		CandidateDraws                                                  int `json:"candidate_draws"`
		InterceptionDraws                                               int `json:"interception_draws"`
		Route                                                           []int
	}
}
type continuationFixture struct {
	Format      string
	Worlds      map[string]string
	Cases       []continuationCase
	Comparisons int `json:"native_six_file_comparisons"`
	Witnesses   int `json:"native_rng_witnesses"`
	Fields      int `json:"native_cache_fields"`
}

func continuationLoad(t *testing.T) continuationFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/evolved_continuation.json")
	if e != nil {
		t.Fatal(e)
	}
	var d continuationFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-evolved-continuation-v1" || len(d.Cases) != 6 || d.Comparisons != 54 || d.Witnesses != 501 || d.Fields != 1440 {
		t.Fatal("qualified corpus inventory")
	}
	return d
}
func continuationInputs(t *testing.T, c continuationCase) ContinuationInputs {
	t.Helper()
	in := ContinuationInputs{State: c.State}
	for _, h := range c.Helpers {
		in.Helpers = append(in.Helpers, ContinuationClock{Family: h.Family, Caller: h.Caller, Timer: planetRaw(t, h.Timer)})
	}
	return in
}
func TestExistingHomeQualifiedContinuation(t *testing.T) {
	d := continuationLoad(t)
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			if digest(before) != c.BeforeSHA {
				t.Fatal("modeled before identity")
			}
			saved := bytes.Clone(before)
			in := continuationInputs(t, c)
			helpers := append([]ContinuationClock(nil), in.Helpers...)
			got, s, e := ReplayExistingHomeContinuation(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(got) != c.SHA {
				t.Fatal("complete Python-qualified continuation world mismatch")
			}
			if s.InitialState != c.State || s.FinalState != c.Final || s.Draws != c.Draws || s.Allocations != c.Allocations || s.Groups != c.Groups || s.Cache != c.Cache || s.WandererSector != c.Wanderer || s.BaseSector != c.Base || s.XannoronIncrement != c.Increment || !reflect.DeepEqual(s.WandererAttempts, c.Attempts) {
				t.Fatalf("phase statistics mismatch: %+v", s)
			}
			if len(s.Seeds) != len(c.Seeds) || len(s.Routes) != len(c.Routes) {
				t.Fatal("chronology inventory")
			}
			for i, v := range s.Seeds {
				w := c.Seeds[i]
				if v.Clock.Family != w.Family || v.Clock.Caller != w.Caller || v.Clock.Timer != planetRaw(t, w.Timer) || v.OldState != w.Old || v.SeededState != w.Seed {
					t.Fatal("derived helper reseeding")
				}
			}
			for i, v := range s.Routes {
				w := c.Routes[i]
				want := ContinuationRoute{Group: w.Group, Origin: w.Origin, Target: w.Target, Fallback: w.Fallback, Candidate: w.Candidate, Preferred: w.Preferred, Strength: w.Strength, CandidateDraws: w.CandidateDraws, InterceptionDraws: w.InterceptionDraws, Route: w.Route}
				if !reflect.DeepEqual(v, want) {
					t.Fatal("directed route / draw receipt")
				}
			}
			if s.TopFallback != c.Routes[len(c.Routes)-1].Target {
				t.Fatal("group20 fallback")
			}
			// Cache force belongs to a physical sector, never to every duplicate pointer.
			consumed := map[int]bool{}
			sum := 0
			for i, g := range s.Cache {
				sum += g.Strength
				if g.Strength > 0 {
					if consumed[g.Sector] {
						t.Fatal("duplicate normalized physical force")
					}
					consumed[g.Sector] = true
				}
				if c.Allocations == 17 && i > 0 && g.Strength == 0 && g.Sector != 0 {
					t.Fatal("empty duplicate not cleared")
				}
			}
			if sum != 10000 {
				t.Fatal("cache conservation")
			}
			// No planet economy, timestamps, restoration or creation writes are repeated.
			allowed := map[int]bool{}
			for sector := 1; sector <= 3000; sector++ {
				for _, o := range []int{81, 85, 93, 105, 129} {
					for j := 0; j < 4; j++ {
						allowed[(50+sector)*RecordSize+o+j] = true
					}
				}
			}
			for _, r := range []int{4052, 4151} {
				for _, o := range []int{73, 77, 117} {
					for j := 0; j < 4; j++ {
						allowed[(r-1)*RecordSize+o+j] = true
					}
				}
			}
			for i, b := range got {
				if !allowed[i] && b != saved[i] {
					t.Fatal("unrelated byte changed")
				}
			}
			a := (4150 - 1) * RecordSize
			if !bytes.Equal(got[a:a+RecordSize], saved[a:a+RecordSize]) {
				t.Fatal("existing Base was restored")
			}
			if !bytes.Equal(before, saved) || !reflect.DeepEqual(in.Helpers, helpers) || in.State != c.State {
				t.Fatal("mutated input")
			}
			got[0] ^= 255
			if !bytes.Equal(before, saved) {
				t.Fatal("returned world aliases input")
			}
		})
	}
}
func TestExistingHomeContinuationAtomicRefusals(t *testing.T) {
	d := continuationLoad(t)
	c := d.Cases[0]
	cases := map[string]func([]byte, *ContinuationInputs){
		"state":         func(w []byte, i *ContinuationInputs) { i.State = 1 << 24 },
		"birth day":     func(w []byte, i *ContinuationInputs) { planetPut(w, 1, 81, 305) },
		"missing clock": func(w []byte, i *ContinuationInputs) { i.Helpers = i.Helpers[:len(i.Helpers)-1] },
		"trailing tail clock": func(w []byte, i *ContinuationInputs) {
			i.Helpers = append(i.Helpers, ContinuationClock{Family: 1, Caller: 0x53b4})
		},
		"wrong callsite":     func(w []byte, i *ContinuationInputs) { i.Helpers[1].Caller = 0x2186 },
		"wrong family":       func(w []byte, i *ContinuationInputs) { i.Helpers[1].Family = 2 },
		"timer":              func(w []byte, i *ContinuationInputs) { i.Helpers[0].Timer = encode(86400) },
		"human":              func(w []byte, i *ContinuationInputs) { planetPut(w, 2, 85, 1) },
		"hiring":             func(w []byte, i *ContinuationInputs) { planetPut(w, 3052, 89, 1) },
		"revenge":            func(w []byte, i *ContinuationInputs) { planetPut(w, 72, 105, 1) },
		"unknown home":       func(w []byte, i *ContinuationInputs) { planetPut(w, 4054, 85, 1) },
		"pre-economy home":   func(w []byte, i *ContinuationInputs) { planetPut(w, 4052, 41, 306) },
		"fractional pointer": func(w []byte, i *ContinuationInputs) { planetPut(w, 53, 105, 10.5) },
		"untracked force":    func(w []byte, i *ContinuationInputs) { planetPut(w, 51+c.Base, 81, 1); planetPut(w, 51+c.Base, 85, -1) },
		"missing Base":       func(w []byte, i *ContinuationInputs) { planetPut(w, 51+c.Base, 93, 0) },
		"lost Wanderer": func(w []byte, i *ContinuationInputs) {
			for s := 1; s <= 3000; s++ {
				a := (50+s)*RecordSize + 93
				if portSingleValue([4]byte(w[a:a+4])) == 1 {
					planetPut(w, 51+s, 93, 0)
				}
			}
		},
		"invalid warp": func(w []byte, i *ContinuationInputs) { planetPut(w, 52, 41, 3001) },
		"entered mine": func(w []byte, i *ContinuationInputs) {
			for _, r := range c.Routes {
				if len(r.Route) > 1 {
					planetPut(w, 51+r.Route[1], 129, 1)
					return
				}
			}
			t.Fatal("no route edge")
		},
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			w := unpack(t, d.Worlds[c.BeforeSHA])
			in := continuationInputs(t, c)
			change(w, &in)
			saved := bytes.Clone(w)
			helpers := append([]ContinuationClock(nil), in.Helpers...)
			out, s, e := ReplayExistingHomeContinuation(w, in)
			if e == nil || out != nil || !reflect.DeepEqual(s, ContinuationStats{}) {
				t.Fatal("non-atomic refusal")
			}
			if !bytes.Equal(saved, w) || !reflect.DeepEqual(in.Helpers, helpers) {
				t.Fatal("source changed on refusal")
			}
		})
	}
	if out, _, e := ReplayExistingHomeContinuation(nil, continuationInputs(t, c)); e == nil || out != nil {
		t.Fatal("short world")
	}
}

func TestExistingHomeZeroBanksUseCommonDefaults(t *testing.T) {
	d := continuationLoad(t)
	c := d.Cases[0]
	w := unpack(t, d.Worlds[c.BeforeSHA])
	planetPut(w, 4052, 117, 0)
	planetPut(w, 4151, 117, 0)
	out, s, e := ReplayExistingHomeContinuation(w, continuationInputs(t, c))
	if e != nil {
		t.Fatal(e)
	}
	for r, want := range map[int]float64{4052: 250000, 4151: 1000000} {
		a := (r-1)*RecordSize + 117
		if got := portSingleValue([4]byte(out[a : a+4])); got != want {
			t.Fatalf("record %d bank %v", r, got)
		}
	}
	if s.FinalState != c.Final || s.Draws != c.Draws {
		t.Fatal("existing bank fallback consumed creation draws")
	}
}

func TestGoPlanetEconomyFeedsExistingHomeContinuation(t *testing.T) {
	d := continuationLoad(t)
	p := planetLoad(t)
	count := 0
	for _, c := range d.Cases {
		for _, phase := range p.Cases {
			if phase.Name != c.Name {
				continue
			}
			economy, stats, e := ReplayEvolvedPlanets(unpack(t, p.Worlds[phase.BeforeSHA]), planetInputs(t, phase))
			if e != nil {
				t.Fatal(e)
			}
			if digest(economy) != c.BeforeSHA || stats.FinalState != c.State {
				t.Fatal("Go economy handoff identity")
			}
			in := continuationInputs(t, c)
			in.State = stats.FinalState
			out, _, e := ReplayExistingHomeContinuation(economy, in)
			if e != nil || digest(out) != c.SHA {
				t.Fatal("Go-only phase composition", e)
			}
			count++
		}
	}
	if count != 6 {
		t.Fatal("composition coverage")
	}
}
