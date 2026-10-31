package game

import (
	"encoding/json"
	"errors"
	"math"
	"math/rand"
	"reflect"
	"testing"
	"time"
)

func disruptionStream(t *testing.T, values ...float64) func() float64 {
	t.Helper()
	i := 0
	return func() float64 {
		if i == len(values) {
			t.Fatal("unexpected arrival draw")
			return 0
		}
		v := values[i]
		i++
		return v
	}
}
func bindHole(t *testing.T, w *World, p *Player, holes [2]int) {
	t.Helper()
	if e := w.BindDisruption(Disruption{Player: p.ID, Generation: p.ShipGeneration, Season: w.Season, Locations: holes}, nil, nil); e != nil {
		t.Fatal(e)
	}
}
func TestDisruptionIndependentInteriorLocationsAndReadOnlyViews(t *testing.T) {
	w, p := setup(t)
	before, _ := json.Marshal(w)
	d, e := w.NewDisruption(p.ID, disruptionStream(t, 0, .999999))
	if e != nil || d.Locations != [2]int{2, 7} {
		t.Fatal(d, e)
	}
	if e = w.BindDisruption(d, nil, nil); e != nil {
		t.Fatal(e)
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("runtime state persisted")
	}
	for i := 0; i < 3; i++ {
		if !w.Disrupted(p.ID, 2) || !w.Disrupted(p.ID, 7) || w.Disrupted(p.ID, 1) || w.Disrupted(p.ID, 8) {
			t.Fatal("session boundaries")
		}
	}
	d, e = w.NewDisruption(p.ID, disruptionStream(t, .2, .2))
	if e != nil || d.Locations[0] != d.Locations[1] {
		t.Fatal(d, e)
	}
	for _, v := range []float64{math.NaN(), math.Inf(1), -1, 1} {
		if _, e = w.NewDisruption(p.ID, func() float64 { return v }); e == nil {
			t.Fatal("invalid location RNG", v)
		}
	}
	if _, e = w.NewDisruption(p.ID, nil); e == nil {
		t.Fatal("nil RNG")
	}
	w.Season++
	if w.Disrupted(p.ID, 2) {
		t.Fatal("stale epoch visible")
	}
	if e = w.BindDisruption(d, nil, nil); !errors.Is(e, ErrSeasonChanged) {
		t.Fatal(e)
	}
}
func TestDisruptionZeroTurnsChainsBypassHazardsAndPreserveCloak(t *testing.T) {
	for _, turns := range []int64{0, 7, 500} {
		w, p := setup(t)
		p.Sector = 2
		p.Turns = turns
		p.Cloak = .5
		p.DockToken = "old"
		p.PlanetToken = "old"
		p.LandedPlanet = 1
		w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 3}}
		w.Sectors[2].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 100}
		bindHole(t, w, p, [2]int{2, 2})
		_, e := w.ResolveArrival(p.ID, disruptionStream(t, 0, 0, .125, 0, .9, 0, 0, .99, 0, .9), clock)
		out := w.ArrivalOutcome()
		if e != nil || p.Sector != 8 || p.Turns != max(0, turns-6) || p.WarpSequence != 2 || p.Cloak != .5 || len(out.Warps) != 2 || p.DockToken != "" || p.PlanetToken != "" || p.LandedPlanet != 0 {
			t.Fatal(p, out, e)
		}
		if w.Sectors[2].Minefield[0].Count != 3 || w.Sectors[2].Defense.Fighters != 100 {
			t.Fatal("initial hazards resolved before hole")
		}
	}
}
func TestDisruptionReachedMineDeathAndDefenses(t *testing.T) {
	for _, dead := range []bool{false, true} {
		w, p := setup(t)
		p.Sector = 2
		p.Turns = 100
		p.Mines = 0
		p.Cloak = 0
		p.Fighters = 0
		p.Cargo = [3]int64{}
		p.Missiles = 0
		p.Shields = 1000
		p.Holds = 10
		if dead {
			p.Shields = 0
			p.Holds = 1
		}
		w.Sectors[8].Minefield = []MineLayer{{Owner: 0, Count: 1}}
		w.Sectors[8].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 100}
		bindHole(t, w, p, [2]int{2, 2})
		i := 0
		rng := func() float64 {
			i++
			if i == 3 {
				return .99
			}
			if i > 5 {
				return .5
			}
			return 0
		}
		out, e := w.ResolveArrival(p.ID, rng, clock)
		if e != nil || out.Destroyed != dead || out.Spent != 1 || len(w.ArrivalOutcome().Mines) != 1 {
			t.Fatal(out, e)
		}
		if dead {
			if p.Death == nil || p.Death.Killer != 0 {
				t.Fatal("wrong fatal source", p.Death)
			}
		} else if p.Shields >= 1000 || !w.ArrivalOutcome().HostileDefense {
			t.Fatal("reached aftermath skipped")
		}
		if w.Sectors[8].Defense.Fighters != 100 {
			t.Fatal("automatic arrival attacked fighters")
		}
	}
}
func TestDisruptionFiniteChainAndSequenceCapacity(t *testing.T) {
	w, p := setup(t)
	p.Sector = 2
	bindHole(t, w, p, [2]int{2, 2})
	draws := 0
	_, e := w.ResolveArrival(p.ID, func() float64 {
		draws++
		if draws%5 == 3 {
			return .125
		}
		return 0
	}, clock)
	if !errors.Is(e, ErrDisruptionLimit) || draws != MaxDisruptionWarps*5 || len(w.ArrivalOutcome().Warps) != 32 {
		t.Fatal(draws, e)
	}
	w, p = setup(t)
	p.Sector = 2
	p.WarpSequence = math.MaxUint64
	bindHole(t, w, p, [2]int{2, 2})
	if _, e = w.ResolveArrival(p.ID, func() float64 { t.Fatal("capacity drew RNG"); return 0 }, clock); e == nil {
		t.Fatal("exhausted sequence")
	}
}
func TestDisruptionPlanetHelperBoundaryAndIndependentPositions(t *testing.T) {
	for _, kind := range []string{"intermediate", "finish", "mines", "fighters", "wanderer"} {
		t.Run(kind, func(t *testing.T) {
			w, p, planet := mobilityWorld(t)
			to := 10
			if kind == "finish" || kind == "wanderer" {
				to = 9
			}
			if kind == "wanderer" {
				// Retain the actual marked Wanderer identity and reserved slot.
				w.Sectors[planet.Sector].Planet = 0
				delete(w.Planets, planet.ID)
				planet.ID = 1
				planet.Wanderer = true
				w.Planets[1] = planet
				planet.Sector = 8
				planet.Owner = p.ID
				planet.Ground = 0
				w.Sectors[8].Planet = 1
			}
			if kind == "mines" {
				w.Sectors[9].Minefield = []MineLayer{{Owner: 0, Count: 3}}
			}
			if kind == "fighters" {
				w.Sectors[9].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 3}
			}
			bindHole(t, w, p, [2]int{9, 9})
			entry := mobilityEntry(t, w, p, "thrusters", to, 0)
			values := []float64{0, 0, 0, .99, 0, 0} // stress, zero budget, destination32, extra, jitter
			if kind == "intermediate" {
				values = []float64{0, 0}
			}
			if kind == "wanderer" {
				values = []float64{0, 0, 0, 0, .99, 0, 0}
			}
			out, e := w.CommitPlanetAction(entry, disruptionStream(t, values...), clock)
			if e != nil {
				t.Fatal(e)
			}
			if kind == "intermediate" {
				if p.Sector != 10 || planet.Sector != 10 || len(w.ArrivalOutcome().Warps) != 0 || out.TransportTurns != 20 {
					t.Fatal(out)
				}
				return
			}
			if p.Sector != 32 || planet.Sector == 32 || len(w.ArrivalOutcome().Warps) != 1 || out.TransportTurns != 10 || out.FinalSector != 32 {
				t.Fatal(out, planet.Sector, w.ArrivalOutcome())
			}
			if kind == "mines" && w.Sectors[9].Minefield[0].Count != 3 {
				t.Fatal("intermediate hole mines consumed")
			}
		})
	}
}
func TestWarpHeatBudgetIsCachedAcrossMixedDraws(t *testing.T) {
	for _, values := range [][]float64{{.03, .03, 0, 0, 0, 0}, {.01, .01, .9}} {
		heat, e := warpHeat(disruptionStream(t, values...))
		if e != nil {
			t.Fatal(e)
		}
		if heat != int(math.Round(values[len(values)-1])) {
			t.Fatal(heat)
		}
	}
}
func TestScannerWarnsAboutLoginLocalHoleWithoutAssets(t *testing.T) {
	w, p := setup(t)
	p.DangerScanner = true
	w.Sectors[1].Warps = []int{2}
	bindHole(t, w, p, [2]int{2, 2})
	entry, e := w.PrepareScannerEntry(p.ID, 2)
	if e != nil || !entry.Dangerous() || !entry.Disruption {
		t.Fatal(entry, e)
	}
	reports, e := w.Scan(p.ID)
	if e != nil || !reports[0].Disruption {
		t.Fatal(reports, e)
	}
	snapshot := *p
	p.WarpSequence++
	if _, e = w.CommitScannerEntry(entry, func() float64 { t.Fatal("stale scanner drew"); return 0 }, clock); e == nil {
		t.Fatal("same-sector sequence replay")
	}
	p.WarpSequence--
	if !reflect.DeepEqual(snapshot, *p) {
		t.Fatal("stale warning changed assets")
	}
}

func TestDisruptionPrecedesAdjacentDefenseBattleAndBribe(t *testing.T) {
	for _, bribe := range []bool{false, true} {
		w, p := setup(t)
		p.Fighters = 1000
		p.Credits = 1000
		w.Sectors[1].Warps = []int{2}
		w.Sectors[2].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
		bindHole(t, w, p, [2]int{2, 2})
		rng := disruptionStream(t, 0, 0, .99, 0, 0)
		if bribe {
			entry, e := w.PrepareBribeAt(p.ID, 2, 100, false)
			if e != nil {
				t.Fatal(e)
			}
			out, e := w.CommitBribe(entry, false, rng, clock)
			if e != nil || out.Paid != 0 || out.Joined != 0 || out.Combat {
				t.Fatal(out, e)
			}
		} else {
			entry, e := w.PrepareDefenseFight(p.ID, 2, 100, false)
			if e != nil {
				t.Fatal(e)
			}
			out, e := w.CommitDefense(entry, rng, clock)
			if e != nil || out.Battle.AttackerLosses != 0 || out.HQReward != nil {
				t.Fatal(out, e)
			}
		}
		if p.Fighters != 1000 || p.Credits != 1000 || p.Sector != 8 || p.Turns != 499 || w.Sectors[2].Defense.Fighters != 100 {
			t.Fatal("hole applied after fighter settlement")
		}
	}
}

func TestMineEscapeUsesOriginalCachedHeatBudget(t *testing.T) {
	for _, values := range [][]float64{{.03, .03, 0, 0, 0, 0, .99, 0, .99}, {.01, .01, .9, .99, 0, .99}} {
		w, p := setup(t)
		p.Sector = 2
		p.Turns = 500
		p.Cloak = .5
		count := 0
		e := w.escapeMines(p, func() float64 {
			if count == len(values) {
				t.Fatal("escape heat budget grew")
				return 0
			}
			v := values[count]
			count++
			return v
		})
		expected := int64(3)
		if len(values) == 6 {
			expected = 7
		}
		if e != nil || count != len(values) || p.Sector != 8 || p.Turns != 500-expected {
			t.Fatal(count, p.Sector, p.Turns, e)
		}
	}
}

func TestDisruptionSeededConservation(t *testing.T) {
	for seed := int64(0); seed < 32; seed++ {
		w, p := setup(t)
		p.Sector = 2
		p.Cloak = .5
		p.Cargo = [3]int64{1, 2, 3}
		before := *p
		bindHole(t, w, p, [2]int{2, 3})
		rng := rand.New(rand.NewSource(seed))
		_, e := w.ResolveArrival(p.ID, rng.Float64, clock)
		if e != nil {
			t.Fatal(seed, e)
		}
		out := w.ArrivalOutcome()
		var charged int64
		for _, step := range out.Warps {
			charged += step.RechargeTurns
			if step.Heat > 31 || step.RechargeTurns < 0 {
				t.Fatal(seed, step)
			}
		}
		if len(out.Warps) == 0 || len(out.Warps) > 32 || charged != before.Turns-p.Turns || w.Disrupted(p.ID, p.Sector) || p.Cloak != before.Cloak || p.Credits != before.Credits || p.Cargo != before.Cargo || p.Fighters != before.Fighters || p.Shields != before.Shields || p.Holds != before.Holds {
			t.Fatal(seed, out)
		}
		if e = w.Validate(); e != nil {
			t.Fatal(seed, e)
		}
	}
}

func TestMineEscapeRechecksLoginHoleAndKeepsIntermediateReceipt(t *testing.T) {
	w, p := setup(t)
	p.Sector = 8
	p.Turns = 100
	p.Holds = 5
	p.Shields = 1000
	p.Cloak = .5
	w.Sectors[8].Minefield = []MineLayer{{Owner: 0, Count: 1}}
	bindHole(t, w, p, [2]int{2, 2})
	out, e := w.ResolveArrival(p.ID, disruptionStream(t, 0, .9, 0, 0, .2, 0, 0, 0, 0, 0, 0, 0), clock)
	receipt := w.ArrivalOutcome()
	if e != nil || !out.Escaped || out.Destroyed || out.Sector != 1 || p.Sector != 1 || p.Turns != 100 || len(receipt.Warps) != 1 || len(receipt.Mines) != 1 || receipt.Mines[0].Sector != 2 || !receipt.Mines[0].Escaped {
		t.Fatal(out, receipt, e)
	}
}

func TestWarpSequenceInvalidatesSameSectorMinePlacement(t *testing.T) {
	w, p := setup(t)
	p.Sector = 8
	p.Mines = 1
	entry, e := w.PrepareMinePlacement(p.ID, 1)
	if e != nil {
		t.Fatal(e)
	}
	p.WarpSequence++
	if _, e = w.CommitMinePlacement(entry); e == nil || p.Mines != 1 || len(w.Sectors[8].Minefield) != 0 {
		t.Fatal("same-sector warp accepted old placement", e)
	}
}

func TestDisruptionRejectsInvalidRuntimeStateBeforeCharge(t *testing.T) {
	for _, mode := range []string{"clock", "turns", "sector"} {
		w, p := setup(t)
		p.Sector = 2
		bindHole(t, w, p, [2]int{2, 2})
		at := clock
		switch mode {
		case "clock":
			at = clock.Add(-time.Second)
		case "turns":
			p.Turns = -1
		case "sector":
			clear(w.Sectors)
		}
		if _, e := w.ResolveArrival(p.ID, func() float64 { t.Fatal("invalid state drew warp RNG"); return 0 }, at); e == nil || p.WarpSequence != 0 {
			t.Fatal(mode, e)
		}
	}
	w, p := setup(t)
	bindHole(t, w, p, [2]int{2, 2})
	if e := w.FinishArrival(); e == nil {
		t.Fatal("read-only context accepted mutation clock")
	}
}
