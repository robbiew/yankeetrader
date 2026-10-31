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

func plasmaWorld(t *testing.T, count int) (*World, *Player) {
	t.Helper()
	w, err := New(clock, 36, count)
	if err != nil {
		t.Fatal(err)
	}
	w.Planets = map[int]*Planet{}
	for i, s := range w.Sectors {
		s.Defense = nil
		s.Minefield = nil
		s.Planet = 0
		s.Warps = nil
		if i < count {
			s.Warps = []int{i + 1}
		}
	}
	p, err := w.Join("plasma-source", "Launcher")
	if err != nil {
		t.Fatal(err)
	}
	p.Plasma = 64
	p.Fighters = 0
	p.Shields = 1_000_000
	p.Cloak = 0
	return w, p
}
func firePlasma(t *testing.T, w *World, p *Player, to int, count int64, rng func() float64) PlasmaResult {
	t.Helper()
	intent, err := w.PreparePlasma(p.ID, to, count)
	if err != nil {
		t.Fatal(err)
	}
	result, err := w.CommitPlasma(intent, rng, clock)
	if err != nil {
		t.Fatal(err)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	return result
}
func plasmaTarget(t *testing.T, w *World, sector int) *Player {
	t.Helper()
	p, err := w.Join("plasma-target", "Hidden Target")
	if err != nil {
		t.Fatal(err)
	}
	p.Sector = sector
	p.Cloak = 1
	p.Fighters = 0
	p.Shields = 1_000_000
	p.Missiles = 0
	return p
}
func plasmaTestPlanet(w *World, owner int) *Planet {
	p := &Planet{ID: 2, Generation: 101, Owner: owner, Sector: 2, Name: "Private Planet", Updated: clock, Production: [3]float64{10000, 10000, 10000}, Cargo: [3]float64{100000, 100000, 100000}, Ground: 5000, Bank: 777}
	w.Planets[2] = p
	w.Sectors[2].Planet = 2
	w.NextPlanetGeneration = 102
	return p
}
func TestPlasmaAdmissionAndUnreachableLaunchAccounting(t *testing.T) {
	for _, mode := range []string{"empty", "unreachable", "last-turn", "self", "no-turns", "no-stock", "zero", "negative", "over-stock", "over-limit", "bad-sector"} {
		t.Run(mode, func(t *testing.T) {
			w, a := plasmaWorld(t, 8)
			to, n := 2, int64(1)
			switch mode {
			case "unreachable":
				w.Sectors[1].Warps = nil
			case "last-turn":
				a.Turns = 1
			case "self":
				to = 1
			case "no-turns":
				a.Turns = 0
			case "no-stock":
				a.Plasma = 0
			case "zero":
				n = 0
			case "negative":
				n = -1
			case "over-stock":
				a.Plasma = 1
				n = 2
			case "over-limit":
				a.Plasma = 100
				n = 65
			case "bad-sector":
				to = 9
			}
			before, _ := json.Marshal(w)
			stock, turns := a.Plasma, a.Turns
			intent, err := w.PreparePlasma(a.ID, to, n)
			invalid := mode == "no-turns" || mode == "no-stock" || mode == "zero" || mode == "negative" || mode == "over-stock" || mode == "over-limit" || mode == "bad-sector"
			if invalid {
				after, _ := json.Marshal(w)
				if err == nil || string(before) != string(after) {
					t.Fatal("invalid admission mutated", err)
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			out, err := w.CommitPlasma(intent, func() float64 { return .5 }, clock)
			if err != nil || out.Launched != 1 || out.TurnsSpent != 1 || a.Plasma != stock-1 || a.Turns != turns-1 {
				t.Fatal(out, err, a)
			}
			if out.RouteUnavailable != (mode == "unreachable") {
				t.Fatal(out)
			}
			if mode == "self" && a.Shields >= 1_000_000 {
				t.Fatal("self immunity")
			}
		})
	}
}
func TestPlasmaDirectedCourseRangeAvoidAndSharedPool(t *testing.T) {
	w, a := plasmaWorld(t, 80)
	a.AvoidSectors = []int{2}
	out := firePlasma(t, w, a, 80, 1, func() float64 { return .5 })
	if out.Visits != 50 || out.Redirects != 0 || a.Plasma != 63 || a.Turns != 499 {
		t.Fatal(out)
	}
	// Both tie branches are equal; only the first stored exit receives damage.
	for _, first := range []int{2, 3} {
		w, a = plasmaWorld(t, 8)
		other := 5 - first
		w.Sectors[1].Warps = []int{first, other}
		w.Sectors[2].Warps = []int{4}
		w.Sectors[3].Warps = []int{4}
		for _, s := range []int{2, 3} {
			w.Sectors[s].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: MaxQuantity}
		}
		out = firePlasma(t, w, a, 4, 1, func() float64 { return .5 })
		if w.Sectors[first].Defense.Fighters == MaxQuantity || w.Sectors[other].Defense.Fighters != MaxQuantity || out.Visits != 1 {
			t.Fatal("wrong tie/shared energy", out)
		}
	}
}
func TestPlasmaIndiscriminateShipsAndFightersBeforeShields(t *testing.T) {
	for _, mode := range []string{"cloaked", "team", "self", "fighters"} {
		t.Run(mode, func(t *testing.T) {
			w, a := plasmaWorld(t, 8)
			d := plasmaTarget(t, w, 2)
			to := 2
			switch mode {
			case "team":
				if err := w.CreateTeam(a.ID, "Peers", "ABCD"); err != nil {
					t.Fatal(err)
				}
				d.Team = a.Team
			case "self":
				to = 1
				d = a
			case "fighters":
				d.Fighters = MaxQuantity
			}
			before := d.Shields
			out := firePlasma(t, w, a, to, 1, func() float64 { return .5 })
			if out.ShipsHit != 1 {
				t.Fatal(out)
			}
			if mode == "fighters" {
				if d.Shields != before || d.Fighters >= MaxQuantity {
					t.Fatal("wrong absorption order")
				}
			} else if d.Shields >= before {
				t.Fatal("physical immunity", mode)
			}
			if d.Cloak != map[bool]float64{true: 0, false: 1}[mode == "self"] {
				t.Fatal("hit permanently changed visibility")
			}
		})
	}
}
func TestPlasmaSharedShipOrderAndWreckMines(t *testing.T) {
	w, a := plasmaWorld(t, 8)
	d := plasmaTarget(t, w, 2)
	later, _ := w.Join("later", "Later")
	later.Sector = 2
	later.Shields = 1000
	later.Fighters = 0
	firePlasma(t, w, a, 2, 1, func() float64 { return .5 })
	if d.Shields >= 1_000_000 || later.Shields != 1000 {
		t.Fatal("pool reset across ships")
	}
	w, a = plasmaWorld(t, 8)
	d = plasmaTarget(t, w, 2)
	d.Shields = 1
	d.Mines = 1000
	d.Credits = 1000
	p := plasmaTestPlanet(w, d.ID)
	before := *p
	w.Sectors[2].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 1}
	w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 1}}
	out := firePlasma(t, w, a, 2, 1, func() float64 { return .5 })
	if out.ShipsDestroyed != 1 || out.Dropped != 1000 || out.Salvage.Mines != 0 || out.MinesDestroyed < 2 || out.PlanetsHit != 0 || *p != before {
		t.Fatal("wreck energy/planet gate", out, *p)
	}
	if d.Death == nil || d.Death.Cause != "plasma" || d.Death.Killer != a.ID || d.Shields != 0 || d.Credits != 0 {
		t.Fatal(d)
	}
	if len(w.Sectors[2].Minefield) != 1 || w.Sectors[2].Minefield[0].Owner != d.ID {
		t.Fatal("wreck attribution", w.Sectors[2])
	}
}
func TestPlasmaPlanetProjectionRetirementAndUnreachedPreservation(t *testing.T) {
	for _, mode := range []string{"productive", "ore-only", "surplus", "zero", "small", "intercepted", "future"} {
		t.Run(mode, func(t *testing.T) {
			w, a := plasmaWorld(t, 8)
			p := plasmaTestPlanet(w, a.ID)
			switch mode {
			case "ore-only":
				p.Production = [3]float64{10000, 0, 0}
				p.Cargo = [3]float64{}
			case "surplus":
				p.Production = [3]float64{}
				p.Cargo = [3]float64{1000, 2000, 3000}
				p.Updated = clock.Add(-time.Hour)
			case "zero":
				p.Production = [3]float64{}
				p.Cargo = [3]float64{}
			case "small":
				p.Production = [3]float64{.1, .1, .1}
				p.Cargo = [3]float64{1000, 2000, 3000}
			case "intercepted":
				p.Updated = clock.Add(-48 * time.Hour)
				w.Sectors[2].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: MaxQuantity}
			case "future":
				p.Updated = clock.Add(time.Hour)
			}
			before := *p
			intent, err := w.PreparePlasma(a.ID, 2, 1)
			if err != nil {
				t.Fatal(err)
			}
			out, err := w.CommitPlasma(intent, func() float64 { return .5 }, clock)
			if mode == "future" {
				if err == nil {
					t.Fatal("future projection accepted")
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if mode == "intercepted" {
				if *p != before || out.PlanetsHit != 0 {
					t.Fatal("unreached planet updated")
				}
				return
			}
			if out.PlanetsHit != 1 {
				t.Fatal(out)
			}
			if mode == "zero" || mode == "small" || mode == "surplus" {
				if out.PlanetsDestroyed != 1 || w.Planets[2] != nil || w.Sectors[2].Planet != 0 || a.Death != nil {
					t.Fatal(out, p)
				}
			} else {
				if math.Abs(p.Production[0]-8995) > .0001 || p.Ground < 3994 || p.Ground > 3995 || p.Cargo[0] > 10*p.Production[0] {
					t.Fatal(p)
				}
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}
func TestPlasmaHolePrecedenceRebuildAndFiniteRedirects(t *testing.T) {
	w, a := plasmaWorld(t, 8)
	d := Disruption{Player: a.ID, Generation: a.ShipGeneration, Season: w.Season, Locations: [2]int{2, 3}}
	if err := w.BindDisruption(d, nil, nil); err != nil {
		t.Fatal(err)
	}
	w.Sectors[2].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
	w.Sectors[2].Warps = []int{1}
	w.Sectors[1].Warps = []int{2, 8}
	calls := 0
	out := firePlasma(t, w, a, 2, 1, func() float64 {
		calls++
		if calls == 1 {
			return .99
		}
		return .5
	})
	if out.Redirects != 1 || out.Visits != 2 || w.Sectors[2].Defense.Fighters != 100 || a.Sector != 1 || out.OwnShieldsLost <= 0 {
		t.Fatal(out)
	}
	w, a = plasmaWorld(t, 8)
	_ = w.BindDisruption(d, nil, nil)
	intent, _ := w.PreparePlasma(a.ID, 2, 1)
	calls = 0
	_, err := w.CommitPlasma(intent, func() float64 { calls++; return .125 }, clock)
	if !errors.Is(err, ErrPlasmaLimit) || calls != MaxPlasmaRedirects {
		t.Fatal(err, calls)
	}
}
func TestPlasmaDeathSelfFriendlyPosthumousAndProtectedMines(t *testing.T) {
	for _, mode := range []string{"self-earth", "self-interior", "friendly", "posthumous"} {
		t.Run(mode, func(t *testing.T) {
			w, a := plasmaWorld(t, 8)
			a.Fighters = 0
			a.Shields = 1
			a.Mines = 3
			d := plasmaTarget(t, w, 2)
			d.Shields = 1
			d.Mines = 3
			to := 1
			if mode == "self-interior" {
				a.Sector = 8
				to = 8
			}
			if mode == "friendly" {
				a.Shields = 1_000_000
				to = 2
				if err := w.CreateTeam(a.ID, "Peers", "ABCD"); err != nil {
					t.Fatal(err)
				}
				d.Team = a.Team
				w.Teams[a.Team].Captain = d.ID
				w.Ports[2].Owner = d.ID
			}
			if mode == "posthumous" {
				d.Sector = 1
				w.Ports[2].Owner = d.ID
			}
			out := firePlasma(t, w, a, to, 1, func() float64 { return .5 })
			if mode == "friendly" {
				if a.Death != nil || d.Death == nil || w.Ports[2].Owner != a.ID || out.Salvage.Holds == 0 {
					t.Fatal(out, a, d)
				}
				return
			}
			if !out.Destroyed || a.Death.Killer != a.ID || a.Death.Cause != "plasma" || a.Shields != 0 || a.Plasma != 0 {
				t.Fatal(a, out)
			}
			if err := w.LoginShip(a.ID, clock); err == nil {
				t.Fatal("self death bypassed cooldown")
			}
			if mode == "self-earth" && out.Disarmed != 3 {
				t.Fatal(out)
			}
			if mode == "self-interior" && out.Dropped != 3 {
				t.Fatal(out)
			}
			if mode == "posthumous" {
				if d.Death == nil || d.Death.Killer != a.ID || out.Salvage != (Salvage{}) || w.Ports[2].Owner != 0 {
					t.Fatal(out, d)
				}
			}
			if err := w.LoginShip(a.ID, clock.Add(24*time.Hour)); err != nil || a.Turns != 499 {
				t.Fatal("replacement changed turns", err, a)
			}
		})
	}
}
func TestPlasmaSealsAllReachableStateAndLoginContext(t *testing.T) {
	for _, mode := range []string{"bolts", "turns", "route", "target", "hidden", "planet", "sequence", "season", "holes", "nonce"} {
		t.Run(mode, func(t *testing.T) {
			w, a := plasmaWorld(t, 8)
			d := plasmaTarget(t, w, 2)
			p := plasmaTestPlanet(w, d.ID)
			_ = w.BindDisruption(Disruption{Player: 1, Season: 1, Locations: [2]int{6, 7}}, nil, nil)
			intent, _ := w.PreparePlasma(a.ID, 2, 1)
			switch mode {
			case "bolts":
				a.Plasma--
			case "turns":
				a.Turns--
			case "route":
				w.Sectors[1].Warps = []int{3}
			case "target":
				d.ShipGeneration++
			case "hidden":
				d.Cloak = .5
			case "planet":
				p.Generation++
			case "sequence":
				a.WarpSequence++
			case "season":
				w.Season++
			case "holes":
				w.arrival.state.Locations = [2]int{5, 6}
			case "nonce":
				intent.Count = 2
			}
			_, err := w.CommitPlasma(intent, func() float64 { t.Fatal("stale intent sampled"); return 0 }, clock)
			if err == nil {
				t.Fatal("stale accepted", mode)
			}
		})
	}
}
func TestPlasmaFiniteDamageAndInvalidRandomness(t *testing.T) {
	for _, r := range []float64{0, math.NaN(), math.Inf(1), -1, 1} {
		w, a := plasmaWorld(t, 8)
		d := plasmaTarget(t, w, 2)
		d.Fighters = MaxQuantity
		d.Shields = MaxQuantity
		w.Sectors[2].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: MaxQuantity}
		intent, _ := w.PreparePlasma(a.ID, 2, 64)
		calls := 0
		_, err := w.CommitPlasma(intent, func() float64 { calls++; return r }, clock)
		if err == nil || calls > MaxPlasmaRounds {
			t.Fatal("unbounded/invalid RNG", err, calls)
		}
	}
}
func TestPlasmaSeededConservationAndMigration(t *testing.T) {
	for seed := int64(0); seed < 32; seed++ {
		w, a := plasmaWorld(t, 8)
		d := plasmaTarget(t, w, 2)
		d.Fighters = 1000
		d.Shields = 1_000_000
		beforeStock := a.Plasma
		out := firePlasma(t, w, a, 2, 1, rand.New(rand.NewSource(seed)).Float64)
		if a.Plasma != beforeStock-1 || a.Turns != 499 || d.Fighters < 0 || d.Shields < 0 || d.Shields > 1_000_000 || out.Salvage != (Salvage{}) {
			t.Fatal(out)
		}
	}
	w, _ := plasmaWorld(t, 8)
	w.Version = 25
	before, _ := json.Marshal(w.Players)
	if err := w.Upgrade(); err != nil || w.Version != 26 {
		t.Fatal(err, w.Version)
	}
	after, _ := json.Marshal(w.Players)
	if !reflect.DeepEqual(before, after) {
		t.Fatal("migration minted stock")
	}
	w.Players[1].Death = &Death{Cause: "plasma"}
	w.Version = 25
	if w.Upgrade() == nil {
		t.Fatal("legacy plasma record accepted")
	}
}

func TestPlasmaHQRewardsUseActualOwnerAndCreditHeadroom(t *testing.T) {
	for _, owner := range []int{MercenaryOwner, XannorOwner, 1} {
		for _, headroom := range []int64{0, 1, 1_000_000} {
			w, a := plasmaWorld(t, 8)
			a.Credits = MaxMoney - headroom
			w.Xannor = &XannorState{HQ: 8}
			w.Sectors[8].Defense = &SectorDefense{Owner: owner, Fighters: 1}
			out := firePlasma(t, w, a, 8, 1, func() float64 { return .5 })
			if w.Sectors[8].Defense != nil {
				t.Fatal("force survived")
			}
			if owner == XannorOwner {
				if len(out.HQRewards) != 1 || out.HQRewards[0].Credits != headroom || a.Credits != MaxMoney || w.Xannor.Revenge == nil {
					t.Fatal(out, a)
				}
			} else if len(out.HQRewards) != 0 || a.Credits != MaxMoney-headroom || w.Xannor.Revenge != nil {
				t.Fatal("DOS owner exploit", out)
			}
		}
	}
}
func TestPlasmaDestroyedPlanetRevokesAllLandingGrants(t *testing.T) {
	w, a := plasmaWorld(t, 8)
	a.Sector = 2
	p := plasmaTestPlanet(w, a.ID)
	p.Production = [3]float64{1, 1, 1}
	p.Cargo = [3]float64{}
	p.Ground = 0
	d := plasmaTarget(t, w, 2)
	a.Fighters = MaxQuantity
	a.Shields = MaxQuantity
	// A large current ship would absorb the shot, so test destruction through an
	// adjacent launcher while two other ships retain grants to the target planet.
	a.Sector = 1
	d.Sector = 2
	d.Fighters = 0
	d.Shields = 1
	p.Owner = d.ID
	if err := w.Land(d.ID, clock); err != nil {
		t.Fatal(err)
	}
	oldGeneration := p.Generation
	out := firePlasma(t, w, a, 2, 1, func() float64 { return .5 })
	if out.PlanetsDestroyed != 1 || d.PlanetToken != "" || d.LandedPlanet != 0 || w.Planets[p.ID] != nil {
		t.Fatal(out)
	}
	// The allocator is not rolled back or reset by destruction.
	if w.NextPlanetGeneration <= oldGeneration {
		t.Fatal("planet generation reused")
	}
}

func TestPlasmaLocalWreckHazardsResolveInSameAction(t *testing.T) {
	for _, fatal := range []bool{false, true} {
		w, victim := plasmaWorld(t, 8)
		source := plasmaTarget(t, w, 8)
		victim.Sector = 8
		victim.Shields = 1
		victim.Mines = 1000
		source.Plasma = 1
		source.Turns = 37
		source.Cloak = 0
		if fatal {
			source.Shields = 0
			source.Holds = 1
		}
		out := firePlasma(t, w, source, 8, 1, func() float64 { return .5 })
		left := int64(0)
		for _, layer := range w.Sectors[8].Minefield {
			left += layer.Count
		}
		if victim.Death == nil || victim.Death.Killer != source.ID || out.Aftermath.Spent == 0 || out.MinesDestroyed+out.Aftermath.Spent+left != 1000 || source.Turns != 36 {
			t.Fatal(out)
		}
		if fatal {
			if !out.Destroyed || source.Death == nil || source.Death.Cause != "mines" || source.Death.Killer != victim.ID {
				t.Fatal("lost mine-source attribution", out)
			}
		} else if source.Death != nil || w.HasMineEncounter(source.ID) || out.OwnShieldsLost == 0 {
			t.Fatal("deferred or unreported hazard", out)
		}
	}
}
func TestPlasmaDoesNotInventMissileRetaliation(t *testing.T) {
	w, a := plasmaWorld(t, 8)
	d := plasmaTarget(t, w, 2)
	d.Missiles = MaxQuantity
	before := a.Shields
	firePlasma(t, w, a, 2, 1, func() float64 { return .99 })
	if d.Missiles != MaxQuantity || a.Shields != before {
		t.Fatal("invented retaliation")
	}
}
