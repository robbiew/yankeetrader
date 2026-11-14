package qbmaint

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

type lateEvent struct {
	Group, Sector, Force int
	State                uint32
	Final                uint32 `json:"final_state"`
	RawForce             int    `json:"raw_force"`
	Draws, Rounds        int
	Damage               int `json:"damage_rounds"`
	Rates                []string
}
type lateCase struct {
	Name         string
	Days         map[string]int
	InitialState uint32   `json:"initial_state"`
	One          []string `json:"helper_one"`
	Two          []string `json:"helper_two"`
	Timer        string   `json:"xannoron_timer"`
	Aux          AuxInputs
	Events       []lateEvent
	Groups       []MobileGroup
	MobileFinal  uint32 `json:"mobile_final_state"`
	Final        uint32 `json:"final_state"`
	Draws        int
	Desertion    int `json:"desertion_draws"`
	Lottery      float32
	Candidate    int
	Native       map[string]string `json:"native_files"`
}
type lateFixture struct {
	Format string
	Before map[string]string `json:"before_aux"`
	Cases  []lateCase
}

func lateData(t *testing.T) lateFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/late_clock.json")
	if e != nil {
		t.Fatal(e)
	}
	var d lateFixture
	if e = json.Unmarshal(b, &d); e != nil || d.Format != "qb-late-clock-integration-v1" || len(d.Cases) != 3 {
		t.Fatal("late fixture", e)
	}
	return d
}
func lateInput(t *testing.T, d lateFixture, c lateCase) (map[string][]byte, InitialRecipe) {
	t.Helper()
	p := load(t)
	var pc *fixtureCase
	for i := range p.Cases {
		if p.Cases[i].Name == c.Name {
			pc = &p.Cases[i]
			break
		}
	}
	if pc == nil {
		t.Fatal("qualified before/schedule")
	}
	before := map[string][]byte{"YTDATA.DAT": unpack(t, p.Worlds[pc.BeforeSHA])}
	for n, v := range d.Before {
		b, e := base64.StdEncoding.DecodeString(v)
		if e != nil {
			t.Fatal(e)
		}
		before[n] = b
	}
	r := InitialRecipe{Ports: schedule(t, *pc), WandererDay: c.Days["wanderer"], XannoronDay: c.Days["xannoron"], BaseDay: c.Days["base"], FinalDay: c.Days["final"], InitialState: c.InitialState, XannoronTimer: raw4(t, c.Timer), Aux: c.Aux}
	for _, v := range c.One {
		r.HelperOne = append(r.HelperOne, raw4(t, v))
	}
	for _, v := range c.Two {
		r.HelperTwo = append(r.HelperTwo, raw4(t, v))
	}
	return before, r
}
func lateMobilePrefix(t *testing.T, before map[string][]byte, r InitialRecipe) ([]byte, MobileInputs) {
	t.Helper()
	b := before["YTDATA.DAT"]
	ports, _, e := ReplayCleanPorts(b, r.Ports)
	if e != nil {
		t.Fatal(e)
	}
	world := append([]byte(nil), b...)
	copy(world[PortStart:PortStart+len(ports)], ports)
	world, w, e := ReplayWandererBirth(world, WandererInputs{Day: r.WandererDay, State: r.InitialState, HelperTimer: r.HelperOne[0]})
	if e != nil {
		t.Fatal(e)
	}
	world, x, e := ReplayXannoronBirth(world, XannoronInputs{Day: r.XannoronDay, State: w.FinalState, TimerSeconds: r.XannoronTimer})
	if e != nil {
		t.Fatal(e)
	}
	in := MobileInputs{State: x.FinalState}
	copy(in.HelperOne[:], r.HelperOne[1:40])
	copy(in.HelperTwo[:], r.HelperTwo)
	return world, in
}
func TestLateClockAllSixNativeFilesAndReceipts(t *testing.T) {
	d := lateData(t)
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, r := lateInput(t, d, c)
			saved := copyFiles(before)
			recipe := cloneRecipe(r)
			out, s, e := ReplayInitialMaintenanceWithWanderer(before, r)
			if e != nil {
				t.Fatal(e)
			}
			if len(out) != 6 || len(c.Native) != 6 {
				t.Fatal("six-file inventory")
			}
			for n, h := range c.Native {
				value, ok := out[n]
				if !ok || digest(value) != h {
					t.Fatal("whole native file", n)
				}
			}
			if s.Draws != c.Draws || s.FinalState != c.Final || s.Mobile.FinalState != c.MobileFinal || s.Tail.DesertionDraws != c.Desertion || s.Tail.Lottery != c.Lottery || s.Tail.Candidate != c.Candidate {
				t.Fatal("composed model RNG/scans", s.Draws, c.Draws, s.FinalState, c.Final)
			}
			if len(s.Encounters) != 18 || len(c.Events) != 18 {
				t.Fatal("complete retained encounter inventory")
			}
			lost := 0
			for i, want := range c.Events {
				got := s.Encounters[i]
				var rates [3][4]byte
				for j, v := range want.Rates {
					rates[j] = raw4(t, v)
				}
				if got.Inputs != (AssaultInputs{Group: want.Group, Sector: want.Sector, Force: want.Force, State: want.State}) || got.Result != (AssaultStats{InitialForce: want.Force, RawForce: want.RawForce, Rounds: want.Rounds, DamageRounds: want.Damage, Draws: want.Draws, FinalRates: rates, FinalState: want.Final}) {
					t.Fatal("routing/state receipt", i)
				}
				lost += got.Inputs.Force
			}
			surviving := 0
			for i, g := range s.Mobile.Groups {
				if g != c.Groups[i] {
					t.Fatal("final group", i, g, c.Groups[i])
				}
				surviving += g.Strength
			}
			if surviving+lost != 10000 || c.Desertion != 2 {
				t.Fatal("force accounting/eager tail draws")
			}
			if bytes.Count(out["YTNEWS.DAT"], []byte("Xannor attacked the planet")) != 18 || bytes.Count(out["YTNEWS.DAT"], []byte("Xannor fighters destroyed!")) != 18 {
				t.Fatal("complete encounter news")
			}
			if !reflect.DeepEqual(before, saved) || !reflect.DeepEqual(r, recipe) {
				t.Fatal("mutated inputs")
			}
			out["YTDATA.DAT"][0] ^= 255
			out["YTNAME.DAT"][0] ^= 255
			if !reflect.DeepEqual(before, saved) {
				t.Fatal("output aliases inputs")
			}
			// Historical entry point must keep rejecting this exact recipe atomically.
			strict, stats, e := ReplayInitialMaintenance(before, r)
			if e == nil || strict != nil || stats != (InitialStats{}) || !reflect.DeepEqual(before, saved) {
				t.Fatal("historical admission broadened")
			}
		})
	}
}
func TestWandererProfileOrdinaryRegression(t *testing.T) {
	d := auxFixture(t)
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, r, tc := initialInput(t, d, c)
			out, s, e := ReplayInitialMaintenanceWithWanderer(before, r)
			if e != nil || len(s.Encounters) != 0 || s.FinalState != tc.Final {
				t.Fatal("ordinary profile", e)
			}
			for n, h := range c.Native {
				value, ok := out[n]
				if !ok || digest(value) != h {
					t.Fatal("ordinary native file", n)
				}
			}
		})
	}
}
func TestLateClockAtomicAdmissionAndReceiptChecks(t *testing.T) {
	d := lateData(t)
	c := d.Cases[0]
	before, r := lateInput(t, d, c)
	prefix, in := lateMobilePrefix(t, before, r)
	saved := append([]byte(nil), prefix...)
	out, ms, e := ReplayInitialMobileGroupsWithWanderer(prefix, in)
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(prefix, saved) {
		t.Fatal("mutated prefix")
	}
	strict, st, e := ReplayInitialMobileGroups(prefix, in)
	if e == nil || strict != nil || st != (MobileStats{}) {
		t.Fatal("strict mobile broadened")
	}
	events := append([]WandererEncounter(nil), ms.Encounters...)
	events[0].Inputs.Force++
	if _, e := retainedWandererLosses(out, events); e == nil {
		t.Fatal("altered loss receipt accepted")
	}
	if _, e := retainedWandererLosses(out, ms.Encounters[:17]); e == nil {
		t.Fatal("partial chain accepted")
	}
	bad := cloneRecipe(r)
	bad.Aux.NewsClock = "24:00:01"
	files, stats, e := ReplayInitialMaintenanceWithWanderer(before, bad)
	if e == nil || files != nil || !reflect.DeepEqual(stats, WandererInitialStats{}) {
		t.Fatal("late error leaked partial output")
	}
	// An unsupported defended Wanderer must fail after the new routing path starts.
	defended := append([]byte(nil), prefix...)
	v := encode(1)
	copy(defended[4051*137+77:], v[:])
	snapshot := append([]byte(nil), defended...)
	filesWorld, statsMobile, e := ReplayInitialMobileGroupsWithWanderer(defended, in)
	if e == nil || filesWorld != nil || !reflect.DeepEqual(statsMobile, WandererMobileStats{}) || !bytes.Equal(defended, snapshot) {
		t.Fatal("unsupported encounter admitted/partially written")
	}
}

func TestLateDownstreamHistoricalAPIsStayStrict(t *testing.T) {
	d := lateData(t)
	before, r := lateInput(t, d, d.Cases[0])
	prefix, in := lateMobilePrefix(t, before, r)
	mobile, stats, e := ReplayInitialMobileGroupsWithWanderer(prefix, in)
	if e != nil {
		t.Fatal(e)
	}
	baseIn := BaseInputs{Day: r.BaseDay, State: stats.FinalState, HelperTimer: r.HelperOne[40]}
	if out, s, e := ReplayMercenaryBaseBirth(mobile, baseIn); e == nil || out != nil || s != (BaseStats{}) {
		t.Fatal("historical base admitted reduced groups")
	}
	world, base, e := replayMercenaryBaseBirth(mobile, baseIn, stats.Encounters)
	if e != nil {
		t.Fatal(e)
	}
	ti := TailInputs{State: base.FinalState}
	if len(r.HelperOne) == 42 {
		timer := r.HelperOne[41]
		ti.CandidateTimer = &timer
	}
	if s, e := ReplayInitialNPCTail(world, ti); e == nil || s != (TailStats{}) {
		t.Fatal("historical tail admitted reduced groups")
	}
	world, e = ReplayInactiveRanks(world, r.FinalDay)
	if e != nil {
		t.Fatal(e)
	}
	if out, e := ReplayInitialAux(before, world, r.Aux); e == nil || out != nil {
		t.Fatal("historical auxiliary admitted encounter score/news")
	}
	altered := append([]WandererEncounter(nil), stats.Encounters...)
	altered[17].Result.FinalRates[0][0] ^= 1
	if _, e := retainedWandererLosses(world, altered); e == nil {
		t.Fatal("altered arithmetic result accepted")
	}
	altered = append([]WandererEncounter(nil), stats.Encounters...)
	altered[0], altered[1] = altered[1], altered[0]
	if _, e := retainedWandererLosses(world, altered); e == nil {
		t.Fatal("reordered pursuit accepted")
	}
}
