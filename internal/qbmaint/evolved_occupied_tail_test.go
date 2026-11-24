package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"slices"
	"testing"
)

type occupiedTailCase struct {
	occupiedRouteCase
	Lottery   string
	Candidate int
	Mercenary struct {
		Initial       int `json:"initial_force"`
		Force, Losses int
		Physical      []int `json:"desertion_sectors"`
		Final         []int `json:"final_sectors"`
		Movement      int   `json:"movement_gate_draws"`
		Targets       int   `json:"target_draws"`
		Activations   []struct {
			Origin, Force, Target int
			Held                  bool
			Candidates, Route     []int
			Final                 int `json:"final_force"`
		}
		Events []struct {
			Sector, Force, Defenders, Losses, Rounds int
			InitialForce                             int `json:"initial_force"`
			InitialDefenders                         int `json:"initial_defenders"`
			DefenderLosses                           int `json:"defender_losses"`
			Gate                                     float32
			Old                                      uint32 `json:"initial_rng_state"`
			Final                                    uint32 `json:"final_rng_state"`
			Draws                                    int    `json:"rng_draws"`
		}
	}
	Gates        []string
	ReportBefore map[string]string `json:"report_before"`
	ReportWorld  string            `json:"report_world"`
	Clock        struct {
		NewsDate   string `json:"news_date"`
		NewsClock  string `json:"news_clock"`
		ScoreDate  string `json:"score_date"`
		ScoreClock string `json:"score_clock"`
	} `json:"report_clock"`
	ReportSHA   map[string]string `json:"report_sha256"`
	ReportStats struct {
		Scores map[string]int
		Losses map[string]int `json:"modeled_losses"`
		Public int            `json:"public_events"`
	} `json:"report_stats"`
}
type occupiedTailFixture struct {
	Format      string
	Worlds      map[string]string
	Cases       []occupiedTailCase
	Comparisons int `json:"native_six_file_comparisons"`
	Witnesses   int `json:"native_rng_witnesses"`
}

func occupiedTailLoad(t *testing.T) occupiedTailFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/evolved_occupied_tail.json")
	if e != nil {
		t.Fatal(e)
	}
	var d occupiedTailFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-evolved-occupied-tail-v1" || len(d.Cases) != 24 || d.Comparisons != 144 || d.Witnesses != 1242 {
		t.Fatal("qualification inventory")
	}
	return d
}
func tailBefore(t *testing.T, d occupiedTailFixture, c occupiedTailCase) map[string][]byte {
	v := map[string][]byte{}
	for n, h := range c.ReportBefore {
		v[n] = unpack(t, d.Worlds[h])
	}
	return v
}
func tailClock(c occupiedTailCase) AuxInputs {
	return AuxInputs{NewsDate: c.Clock.NewsDate, NewsClock: c.Clock.NewsClock, ScoreDate: c.Clock.ScoreDate, ScoreClock: c.Clock.ScoreClock}
}
func TestEvolvedOccupiedTailReportsAndMobileHandoff(t *testing.T) {
	d := occupiedTailLoad(t)
	mobile := evolvedMobileLoad(t)
	acts, battles, lotteries := 0, 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			in := EvolvedTailInputs{State: c.State, Helpers: continuationInputs(t, c.continuationCase).Helpers}
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			world, s, e := ReplayEvolvedOccupiedTail(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(world) != c.SHA || s.InitialState != c.State || s.FinalState != c.Final || s.Draws != c.Draws || s.Lottery != planetRaw(t, c.Lottery) || s.Candidate != c.Candidate || s.MercenaryForce != c.Mercenary.Initial || s.FinalForce != c.Mercenary.Force || s.Losses != c.Mercenary.Losses || s.MovementGateDraws != c.Mercenary.Movement || s.TargetDraws != c.Mercenary.Targets || !slices.Equal(s.DesertionSectors, c.Mercenary.Physical) || !slices.Equal(s.FinalMercenarySectors, c.Mercenary.Final) {
				t.Fatal("complete tail world/state/force mismatch")
			}
			if len(s.Activations) != len(c.Mercenary.Activations) || len(s.Seeds) != len(c.Seeds) || len(s.Battles) != len(c.Mercenary.Events) {
				t.Fatal("receipt inventory")
			}
			acts += len(s.Activations)
			battles += len(s.Battles)
			if s.Candidate != 0 {
				lotteries++
			}
			for i, a := range s.Activations {
				v := c.Mercenary.Activations[i]
				if a.Origin != v.Origin || a.Force != v.Force || a.Target != v.Target || a.Held != v.Held || a.Gate != planetRaw(t, c.Gates[i]) || !reflect.DeepEqual(a.Candidates, v.Candidates) || !reflect.DeepEqual(a.Route, v.Route) {
					t.Fatal("activation receipt")
				}
			}
			for i, h := range s.Seeds {
				v := c.Seeds[i]
				family := 1
				if h.Clock.Family != family || v.Family != family || h.Clock.Caller != v.Caller || h.Clock.Timer != planetRaw(t, v.Timer) || h.OldState != v.Old || h.SeededState != v.Seed {
					t.Fatal("reseed receipt")
				}
			}
			for i, b := range s.Battles {
				v := c.Mercenary.Events[i]
				if b.Sector != v.Sector || b.InitialState != v.Old || b.FinalState != v.Final || b.InitialForce != v.InitialForce || b.Force != v.Force || b.InitialDefenders != v.InitialDefenders || b.Defenders != v.Defenders || b.Losses != v.Losses || b.DefenderLosses != v.DefenderLosses || b.Rounds != v.Rounds || b.Draws != v.Draws || b.Gate != portSingleBytes(v.Gate) {
					t.Fatal("unit battle receipt")
				}
			}
			var source *occupiedRouteCase
			for i := range mobile.Cases {
				if mobile.Cases[i].Name == c.Name {
					source = &mobile.Cases[i]
					break
				}
			}
			if source == nil {
				t.Fatal("mobile join")
			}
			prefix, ms, e := ReplayEvolvedOccupiedHomeMobile(unpack(t, mobile.Worlds[source.BeforeSHA]), continuationInputs(t, source.continuationCase))
			if e != nil || digest(prefix) != c.BeforeSHA || ms.FinalState != c.State {
				t.Fatal("Go mobile handoff", e)
			}
			linked := in
			linked.State = ms.FinalState
			joined, js, e := ReplayEvolvedOccupiedTail(prefix, linked)
			if e != nil || digest(joined) != c.SHA || js.FinalState != c.Final {
				t.Fatal("calculated tail handoff", e)
			}
			day := 307
			if c.Clock.NewsDate == "2026-11-04" {
				day = 308
			}
			final, e := ReplayInactiveRanks(joined, day)
			if e != nil || digest(final) != c.ReportWorld {
				t.Fatal("actual Go metadata handoff", e)
			}
			files, rs, e := ReplayEvolvedOccupiedAux(tailBefore(t, d, c), final, tailClock(c), ms.Events, js)
			if e != nil {
				t.Fatal(e)
			}
			if len(files) != 5 {
				t.Fatal("five report files")
			}
			for n, h := range c.ReportSHA {
				if digest(files[n]) != h {
					t.Fatal("native-qualified modeled report mismatch", n)
				}
			}
			if rs.Scores != [2]int{c.ReportStats.Scores["-1"], c.ReportStats.Scores["-2"]} || rs.Losses != [2]int{c.ReportStats.Losses["-1"], c.ReportStats.Losses["-2"]} || rs.PublicEvents != c.ReportStats.Public {
				t.Fatal("faction/public ledger")
			}
			after, _ := json.Marshal(in)
			if !bytes.Equal(saved, before) || !bytes.Equal(recipe, after) {
				t.Fatal("input mutation")
			}
			world[0] ^= 1
			if !bytes.Equal(saved, before) {
				t.Fatal("output alias")
			}
		})
	}
	if acts != 12 || battles != 3 || lotteries != 18 {
		t.Fatal("tail coverage", acts, battles, lotteries)
	}
}

func TestEvolvedOccupiedTailAtomicRefusals(t *testing.T) {
	d := occupiedTailLoad(t)
	c := d.Cases[0]
	for _, v := range d.Cases {
		if len(v.Mercenary.Events) > 0 {
			c = v
			break
		}
	}
	tests := map[string]func([]byte, *EvolvedTailInputs){
		"state":              func(w []byte, i *EvolvedTailInputs) { i.State = 1 << 24 },
		"day":                func(w []byte, i *EvolvedTailInputs) { planetPut(w, 1, 81, 305) },
		"geometry":           func(w []byte, i *EvolvedTailInputs) { planetPut(w, 1, 53, 52) },
		"human":              func(w []byte, i *EvolvedTailInputs) { planetPut(w, 2, 85, 1) },
		"hiring":             func(w []byte, i *EvolvedTailInputs) { planetPut(w, 3052, 89, 1) },
		"revenge":            func(w []byte, i *EvolvedTailInputs) { planetPut(w, 72, 105, 1) },
		"bankless base":      func(w []byte, i *EvolvedTailInputs) { planetPut(w, 4150, 73, 0) },
		"foreign defense":    func(w []byte, i *EvolvedTailInputs) { planetPut(w, 160, 85, -2) },
		"batch defense":      func(w []byte, i *EvolvedTailInputs) { planetPut(w, 160, 81, 201) },
		"fractional defense": func(w []byte, i *EvolvedTailInputs) { planetPut(w, 160, 81, .5) },
		"late mine":          func(w []byte, i *EvolvedTailInputs) { planetPut(w, 160, 129, 1) },
		"late planet":        func(w []byte, i *EvolvedTailInputs) { planetPut(w, 160, 93, 2) },
		"exhaustion":         func(w []byte, i *EvolvedTailInputs) { i.Helpers = nil },
		"late exhaustion":    func(w []byte, i *EvolvedTailInputs) { i.Helpers = i.Helpers[:len(i.Helpers)-1] },
		"surplus":            func(w []byte, i *EvolvedTailInputs) { i.Helpers = append(i.Helpers, i.Helpers[0]) },
		"caller":             func(w []byte, i *EvolvedTailInputs) { i.Helpers[0].Caller ^= 1 },
		"family":             func(w []byte, i *EvolvedTailInputs) { i.Helpers[0].Family = 2 },
		"timer":              func(w []byte, i *EvolvedTailInputs) { i.Helpers[0].Timer = encode(86400) },
		"graph":              func(w []byte, i *EvolvedTailInputs) { planetPut(w, 52, 41, 3001) },
	}
	for name, f := range tests {
		t.Run(name, func(t *testing.T) {
			w := unpack(t, d.Worlds[c.BeforeSHA])
			i := EvolvedTailInputs{State: c.State, Helpers: continuationInputs(t, c.continuationCase).Helpers}
			f(w, &i)
			saved := bytes.Clone(w)
			recipe, _ := json.Marshal(i)
			out, s, e := ReplayEvolvedOccupiedTail(w, i)
			after, _ := json.Marshal(i)
			if e == nil || out != nil || !reflect.DeepEqual(s, EvolvedOccupiedTailStats{}) || !bytes.Equal(w, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("non-atomic tail refusal", e)
			}
		})
	}
	w := unpack(t, d.Worlds[c.BeforeSHA])
	i := EvolvedTailInputs{State: c.State, Helpers: continuationInputs(t, c.continuationCase).Helpers}
	if _, _, e := ReplayEvolvedNPCTail(w, i); e == nil {
		t.Fatal("old empty-route tail widened")
	}
	if _, _, e := ReplayEvolvedOccupiedTail(w[:10], i); e == nil {
		t.Fatal("short world")
	}
}

func TestEvolvedOccupiedReportsAtomicRefusalsAndOwnership(t *testing.T) {
	d := occupiedTailLoad(t)
	c := d.Cases[0]
	for _, v := range d.Cases {
		if len(v.Mercenary.Events) > 0 {
			c = v
			break
		}
	}
	input := unpack(t, d.Worlds[c.BeforeSHA])
	i := EvolvedTailInputs{State: c.State, Helpers: continuationInputs(t, c.continuationCase).Helpers}
	_, tail, e := ReplayEvolvedOccupiedTail(input, i)
	if e != nil {
		t.Fatal(e)
	}
	before := tailBefore(t, d, c)
	world := unpack(t, d.Worlds[c.ReportWorld])
	clock := tailClock(c)
	saved, _ := json.Marshal(before)
	copyWorld := bytes.Clone(world)
	files, _, e := ReplayEvolvedOccupiedAux(before, world, clock, nil, tail)
	if e != nil {
		t.Fatal(e)
	}
	for _, n := range []string{"YTNAME.DAT", "YTYNEWS.DAT"} {
		files[n][0] ^= 1
	}
	after, _ := json.Marshal(before)
	if !bytes.Equal(saved, after) || !bytes.Equal(copyWorld, world) {
		t.Fatal("report alias")
	}
	tests := map[string]func(map[string][]byte, []byte, *AuxInputs, *EvolvedOccupiedTailStats){
		"missing side": func(b map[string][]byte, w []byte, a *AuxInputs, s *EvolvedOccupiedTailStats) {
			delete(b, "YTYNEWS.DAT")
		},
		"private": func(b map[string][]byte, w []byte, a *AuxInputs, s *EvolvedOccupiedTailStats) {
			b["YTRMSG.DAT"] = []byte{1}
		},
		"date": func(b map[string][]byte, w []byte, a *AuxInputs, s *EvolvedOccupiedTailStats) {
			a.NewsDate = "2026-11-02"
		},
		"clock": func(b map[string][]byte, w []byte, a *AuxInputs, s *EvolvedOccupiedTailStats) {
			a.ScoreClock = "25:00:00"
		},
		"world force": func(b map[string][]byte, w []byte, a *AuxInputs, s *EvolvedOccupiedTailStats) {
			planetPut(w, 52, 81, 10001)
			planetPut(w, 52, 85, -1)
		},
		"victory stamp": func(b map[string][]byte, w []byte, a *AuxInputs, s *EvolvedOccupiedTailStats) {
			s.Battles[0].InitialForce--
		},
		"survivor count": func(b map[string][]byte, w []byte, a *AuxInputs, s *EvolvedOccupiedTailStats) { s.FinalForce++ },
		"casualty":       func(b map[string][]byte, w []byte, a *AuxInputs, s *EvolvedOccupiedTailStats) { s.Losses++ },
	}
	for name, f := range tests {
		t.Run(name, func(t *testing.T) {
			b := tailBefore(t, d, c)
			w := bytes.Clone(world)
			a := clock
			s := tail
			s.Battles = append([]EvolvedMercenaryBattle(nil), tail.Battles...)
			f(b, w, &a, &s)
			bs, _ := json.Marshal(b)
			ws := bytes.Clone(w)
			ss, _ := json.Marshal(s)
			out, rs, e := ReplayEvolvedOccupiedAux(b, w, a, nil, s)
			ba, _ := json.Marshal(b)
			sa, _ := json.Marshal(s)
			if e == nil || out != nil || !reflect.DeepEqual(rs, OccupiedReportStats{}) || !bytes.Equal(bs, ba) || !bytes.Equal(ws, w) || !bytes.Equal(ss, sa) {
				t.Fatal("non-atomic report refusal", e)
			}
		})
	}
	if _, _, e := ReplayOccupiedAux(before, world, clock, nil); e == nil {
		t.Fatal("old report admission widened")
	}
}

func TestEvolvedOccupiedGroundReportLedgerRefusals(t *testing.T) {
	d := occupiedTailLoad(t)
	m := evolvedMobileLoad(t)
	c := d.Cases[0]
	for _, v := range d.Cases {
		if len(v.Events) > 1 {
			c = v
			break
		}
	}
	var source occupiedRouteCase
	for _, v := range m.Cases {
		if v.Name == c.Name {
			source = v
			break
		}
	}
	_, ms, e := ReplayEvolvedOccupiedHomeMobile(unpack(t, m.Worlds[source.BeforeSHA]), continuationInputs(t, source.continuationCase))
	if e != nil {
		t.Fatal(e)
	}
	_, tail, e := ReplayEvolvedOccupiedTail(unpack(t, d.Worlds[c.BeforeSHA]), EvolvedTailInputs{State: c.State, Helpers: continuationInputs(t, c.continuationCase).Helpers})
	if e != nil {
		t.Fatal(e)
	}
	for _, kind := range []string{"order", "ground", "payload", "group"} {
		t.Run(kind, func(t *testing.T) {
			events := append([]OccupiedCombatEvent(nil), ms.Events...)
			v := *events[len(events)-1].Ground
			events[len(events)-1].Ground = &v
			switch kind {
			case "order":
				events[0], events[1] = events[1], events[0]
			case "ground":
				v.Ground--
			case "payload":
				events[0].Defense = &ForeignDefenseStats{}
			case "group":
				events[1].Group = events[0].Group
			}
			world := unpack(t, d.Worlds[c.ReportWorld])
			before := tailBefore(t, d, c)
			snapshot, _ := json.Marshal(events)
			out, s, e := ReplayEvolvedOccupiedAux(before, world, tailClock(c), events, tail)
			after, _ := json.Marshal(events)
			if e == nil || out != nil || !reflect.DeepEqual(s, OccupiedReportStats{}) || !bytes.Equal(snapshot, after) {
				t.Fatal("ground ledger refusal", e)
			}
		})
	}
}
