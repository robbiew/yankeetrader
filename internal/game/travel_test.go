package game

import (
	"encoding/json"
	"math"
	"math/rand"
	"reflect"
	"testing"
	"time"
)

func travelWorld(t *testing.T) (*World, *Player) {
	t.Helper()
	w, p := setup(t)
	p.Sector = 8
	p.Shields = 100000
	p.Cloak = 0
	w.Sectors[8].Warps = []int{2}
	return w, p
}
func warpStream(t *testing.T, dest float64, hot bool, jitter float64) func() float64 {
	t.Helper()
	v := []float64{0, 0}
	if hot {
		v = []float64{.99, .99}
		for i := 0; i < 31; i++ {
			v = append(v, .99)
		}
	}
	v = append(v, dest, .99, jitter)
	i := 0
	return func() float64 {
		if i >= len(v) {
			t.Fatal("unexpected extra warp draw")
			return 0
		}
		r := v[i]
		i++
		return r
	}
}
func TestDangerScannerPurchaseExactSinkAndRejections(t *testing.T) {
	for _, cash := range []int64{249999, 250000, 250001, MaxMoney} {
		w, p := setup(t)
		p.Credits = cash
		if err := w.Dock(p.ID, clock); err != nil {
			t.Fatal(err)
		}
		token := p.DockToken
		turns := p.Turns
		err := w.Equip(p.ID, token, "scanner", 1, clock)
		if cash < DangerScannerPrice {
			if err == nil || p.Credits != cash || p.DangerScanner {
				t.Fatal("unaffordable purchase", err)
			}
			continue
		}
		if err != nil || !p.DangerScanner || p.Credits != cash-DangerScannerPrice || p.Turns != turns || w.Ports[1].Treasury != 0 {
			t.Fatal("scanner purchase", p, err)
		}
		before, _ := json.Marshal(w)
		if err = w.Equip(p.ID, token, "scanner", 1, clock); err == nil {
			t.Fatal("duplicate scanner")
		}
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("duplicate charge")
		}
	}
	for _, q := range []int64{0, 2, MaxQuantity} {
		w, p := setup(t)
		p.Credits = MaxMoney
		_ = w.Dock(p.ID, clock)
		if err := w.Equip(p.ID, p.DockToken, "scanner", q, clock); err == nil || p.DangerScanner || p.Credits != MaxMoney {
			t.Fatal("scanner quantity", q, err)
		}
	}
	w, p := setup(t)
	p.Credits = 500000
	_ = w.Dock(p.ID, clock)
	token := p.DockToken
	if err := w.Equip(p.ID, token, "scanner", 1, clock.Add(11*time.Minute)); err == nil {
		t.Fatal("expired docking purchase")
	}
	p.Sector = 2
	p.DockToken = ""
	if err := w.Equip(p.ID, token, "scanner", 1, clock); err == nil {
		t.Fatal("remote purchase")
	}
}
func TestScannerWarningsCaptureHazardsAndStaleState(t *testing.T) {
	for _, mode := range []string{"accept", "mine-change", "defense-change", "team-change", "shield-change", "scanner-loss", "generation", "maintenance"} {
		w, p := travelWorld(t)
		p.DangerScanner = true
		w.Sectors[2].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 7}
		w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 1}}
		e, err := w.PrepareScannerEntry(p.ID, 2)
		if err != nil || !e.Dangerous() {
			t.Fatal(err)
		}
		switch mode {
		case "mine-change":
			w.Sectors[2].Minefield[0].Count++
		case "defense-change":
			w.Sectors[2].Defense.Fighters++
		case "team-change":
			p.Team = 1
		case "shield-change":
			p.Shields--
		case "scanner-loss":
			p.DangerScanner = false
		case "generation":
			p.ShipGeneration++
		case "maintenance":
			w.LastMaintenance = "2026-10-25"
		}
		before, _ := json.Marshal(w)
		out, err := w.CommitScannerEntry(e, func() float64 { return 0 }, clock)
		if mode == "accept" {
			if err != nil || p.Sector != 2 || p.Turns != 499 || out.Spent != 1 || w.Sectors[2].Defense.Fighters != 7 || !w.HostileDefense(p.ID, 2) {
				t.Fatal("scanner entry", out, err)
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		} else {
			after, _ := json.Marshal(w)
			if err == nil || string(before) != string(after) {
				t.Fatal("stale warning accepted", mode, err)
			}
		}
	}
	w, p := travelWorld(t)
	p.DangerScanner = true
	w.Sectors[2].Defense = &SectorDefense{Owner: p.ID, Fighters: 3}
	e, err := w.PrepareScannerEntry(p.ID, 2)
	if err != nil || e.Dangerous() {
		t.Fatal("own fighters warned", err)
	}
	if _, err = w.PrepareScannerEntry(p.ID, 3); err == nil {
		t.Fatal("nonadjacent scanned")
	}
}
func TestManualWarpCostsDestinationsReplayAndBoundedWork(t *testing.T) {
	for _, tc := range []struct {
		turns  int64
		hot    bool
		jitter float64
		cost   int64
	}{{500, false, 0, 0}, {500, false, .99, 3}, {1, false, .99, 1}, {500, true, .99, 500}} {
		w, p := travelWorld(t)
		p.Turns = tc.turns
		p.AvoidSectors = []int{8}
		p.DockToken = "old"
		p.PlanetToken = "old"
		p.LandedPlanet = 1
		e, err := w.PrepareWarp(p.ID)
		if err != nil {
			t.Fatal(err)
		}
		out, err := w.CommitWarp(e, warpStream(t, .99, tc.hot, tc.jitter), clock)
		if err != nil || out.Destination != 8 || p.Sector != 8 || out.RechargeTurns != tc.cost || out.TurnsSpent != tc.cost || p.Turns != tc.turns-tc.cost || out.Meltdown != tc.hot || p.WarpSequence != 1 || p.DockToken != "" || p.PlanetToken != "" || p.LandedPlanet != 0 {
			t.Fatal("warp accounting", out, p, err)
		}
		before, _ := json.Marshal(w)
		if _, err = w.CommitWarp(e, func() float64 { t.Fatal("replay drew"); return 0 }, clock); err == nil {
			t.Fatal("zero-cost/same-sector replay")
		}
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("replay changed world")
		}
		if err = w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
	for seed := int64(0); seed < 64; seed++ {
		w, p := travelWorld(t)
		old := p.Credits
		e, _ := w.PrepareWarp(p.ID)
		r := rand.New(rand.NewSource(seed))
		draws := 0
		out, err := w.CommitWarp(e, func() float64 { draws++; return r.Float64() }, clock)
		if err != nil || draws > 144 || p.Turns < 0 || p.Turns > 500 || p.Credits != old || out.TurnsSpent != 500-p.Turns || w.Sectors[p.Sector] == nil {
			t.Fatal(seed, out, draws, err)
		}
		if err = w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
	w, p := travelWorld(t)
	p.Turns = 0
	if _, err := w.PrepareWarp(p.ID); err == nil {
		t.Fatal("zero-turn warp")
	}
	p.Turns = 1
	p.WarpSequence = math.MaxUint64
	if _, err := w.PrepareWarp(p.ID); err == nil {
		t.Fatal("sequence overflow")
	}
}
func TestManualWarpArrivalMinesDefenseAndFatalEstate(t *testing.T) {
	for _, fatal := range []bool{false, true} {
		w, p := travelWorld(t)
		p.DangerScanner = true
		p.Holds = 1
		p.Shields = 100000
		p.Cargo = [3]int64{}
		p.Fighters = 0
		p.Missiles = 0
		p.Mines = 0
		p.Cloak = 0
		w.Sectors[8].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 100}
		w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 1}}
		w.Sectors[2].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 100}
		if fatal {
			p.Shields = 0
			w.Ports[2].Owner = p.ID
			w.Ports[2].Treasury = 123
		}
		e, _ := w.PrepareWarp(p.ID)
		draws := []float64{0, 0, .2, .99, .99}
		i := 0
		out, err := w.CommitWarp(e, func() float64 {
			if i < len(draws) {
				r := draws[i]
				i++
				return r
			}
			return 0
		}, clock)
		if err != nil || out.Destination != 2 || out.RechargeTurns != 3 || out.TurnsSpent != 3 || out.Mines.Spent != 1 || w.Sectors[2].Defense.Fighters != 100 {
			t.Fatal("arrival", out, err)
		}
		if fatal {
			if p.Death == nil || p.Death.Cause != "mines" || p.Death.Killer != 0 || p.DangerScanner || w.Ports[2].Owner != 0 {
				t.Fatal("fatal warp aftermath", p)
			}
		} else if !out.HostileDefense || p.Death != nil || p.Sector != 2 {
			t.Fatal("hostile arrival bypassed", out)
		}
		if err = w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}
func TestDangerScannerMineLossBranches(t *testing.T) {
	for _, tc := range []struct {
		shields int64
		draws   []float64
		keep    bool
	}{{10000, []float64{0, .95}, true}, {10000, []float64{0, math.Nextafter(.95, 1)}, false}, {1, []float64{.5}, true}, {0, []float64{0, 0, 0}, false}} {
		p := Player{DangerScanner: true, Shields: tc.shields, Holds: 100}
		i := 0
		err := mineBurst(&p, 1, func() float64 {
			if i >= len(tc.draws) {
				t.Fatal("scanner loss extra draw")
				return 0
			}
			r := tc.draws[i]
			i++
			return r
		})
		if err != nil || p.DangerScanner != tc.keep || i != len(tc.draws) {
			t.Fatal("scanner loss branch", p, err, i)
		}
	}
}
func TestTravelVersion20UpgradeNoGiftAndLegacyFutureState(t *testing.T) {
	w, p := travelWorld(t)
	w.Version = 20
	before := *p
	if err := w.Upgrade(); err != nil || w.Version != 21 || !reflect.DeepEqual(before, *p) {
		t.Fatal("migration changed player", err)
	}
	for _, scanner := range []bool{false, true} {
		w, p = travelWorld(t)
		w.Version = 20
		p.DangerScanner = scanner
		if !scanner {
			p.WarpSequence = 1
		}
		if err := w.Upgrade(); err == nil {
			t.Fatal("legacy accepted future travel state")
		}
	}
}

func TestScannerTeamPassageAndScoredAsset(t *testing.T) {
	w, p := travelWorld(t)
	p.DangerScanner = true
	q, e := w.Join("friend", "Friend")
	if e != nil {
		t.Fatal(e)
	}
	if e = w.CreateTeam(p.ID, "Travel Team", "TEST"); e != nil {
		t.Fatal(e)
	}
	if e = w.JoinTeam(q.ID, p.Team, "TEST"); e != nil {
		t.Fatal(e)
	}
	w.Sectors[2].Defense = &SectorDefense{Owner: q.ID, Fighters: 10}
	entry, e := w.PrepareScannerEntry(p.ID, 2)
	if e != nil || entry.Dangerous() {
		t.Fatal("friendly team warning", e)
	}
	w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 1}}
	entry, e = w.PrepareScannerEntry(p.ID, 2)
	if e != nil {
		t.Fatal(e)
	}
	if e = w.LeaveTeam(q.ID, q.Team); e != nil {
		t.Fatal(e)
	}
	if _, e = w.CommitScannerEntry(entry, func() float64 { t.Fatal("stale team warning drew"); return 0 }, clock); e == nil {
		t.Fatal("team change did not invalidate warning")
	}
	if e = w.Validate(); e != nil {
		t.Fatal(e)
	}
	w, p = setup(t)
	p.Credits = DangerScannerPrice
	_ = w.Dock(p.ID, clock)
	before, _ := w.PlayerRankings(p.ID, false)
	cache := p.StoredScore
	if e = w.Equip(p.ID, p.DockToken, "scanner", 1, clock); e != nil {
		t.Fatal(e)
	}
	after, _ := w.PlayerRankings(p.ID, false)
	if before.Players[0].Score != after.Players[0].Score || p.StoredScore != cache {
		t.Fatal("scanner value omitted or score cache published during purchase")
	}
}

func TestManualWarpMeltdownUsesExistingDailyTurnReset(t *testing.T) {
	w, p := travelWorld(t)
	p.Sector = 1
	e, err := w.PrepareWarp(p.ID)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitWarp(e, warpStream(t, 0, true, 0), clock)
	if err != nil || !out.Meltdown || p.Turns != 0 || p.Sector != 1 {
		t.Fatal(out, err)
	}
	if w.MaintainWithRandom(clock, func() float64 { return 0 }) || p.Turns != 0 {
		t.Fatal("same-day maintenance repaired turns")
	}
	if !w.MaintainWithRandom(clock.AddDate(0, 0, 1), func() float64 { return 0 }) || p.Turns != 500 {
		t.Fatal("new-day turn reset missing")
	}
	if _, err = w.PrepareWarp(p.ID); err != nil {
		t.Fatal("hidden engine cooldown", err)
	}
}
