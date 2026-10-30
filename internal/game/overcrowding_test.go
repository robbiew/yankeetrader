package game

import (
	"encoding/json"
	"math"
	"math/rand"
	"reflect"
	"testing"
	"time"
)

func eventSequence(t *testing.T, values ...float64) (func() float64, *int) {
	t.Helper()
	n := 0
	return func() float64 {
		t.Helper()
		if n >= len(values) {
			t.Fatal("unexpected event draw", n)
			return 0
		}
		v := values[n]
		n++
		return v
	}, &n
}
func eventWorld(t *testing.T) (*World, *Planet) {
	t.Helper()
	w, p := setup(t)
	planet := &Planet{ID: 2, Sector: 2, Owner: p.ID, Name: "Crowded", Updated: clock,
		Production: [3]float64{100, 200, 300}, Cargo: [3]float64{1000, 2000, 3000},
		Ground: 100, Bank: 12345, Fighters: 11, Missiles: 13, Mines: 17, Plasma: 19}
	w.Planets[2] = planet
	w.Sectors[2].Planet = 2
	return w, planet
}
func TestPortPlagueThresholdDrawsAndGrowth(t *testing.T) {
	for _, total := range []float64{999999, 1000000, 1000001} {
		w, _ := setup(t)
		p := w.Ports[1]
		p.Production = [3]float64{total - 2, 1, 1}
		p.Supply = [3]float64{total - 2, 1, 1}
		values := []float64{}
		if total > 1000000 {
			values = []float64{0}
		}
		rng, n := eventSequence(t, values...)
		w.overcrowding(clock, rng)
		if *n != len(values) {
			t.Fatal("draw count", *n)
		}
		if total > 1000000 {
			if p.Production[0] != 500 || p.Supply[0] != 5000 || len(w.News) != 1 || w.News[0].PortCount != 1 {
				t.Fatal(p, w.News)
			}
		} else if p.Production[0] != total-2 || len(w.News) != 0 {
			t.Fatal(p, w.News)
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
	w, _ := setup(t)
	p := w.Ports[2]
	// Ordinary growth promotes rates before the outbreak threshold is tested.
	p.Production = [3]float64{400000, 300000, 300000}
	p.Supply = [3]float64{4000000, 3000000, 3000000}
	w.overcrowding(clock.Add(24*time.Hour), func() float64 { return 0 })
	if p.Production != [3]float64{500, 500, 500} || w.News[0].PortCount != 1 {
		t.Fatal(p, w.News)
	}
}
func TestPortPlagueCutoffSinglePassAndSelection(t *testing.T) {
	w, _ := setup(t)
	p := w.Ports[1]
	p.Production = [3]float64{2000000, 500, 501}
	p.Supply = [3]float64{10000000, 5000, 5010}
	rng, n := eventSequence(t, .9, .5)
	w.overcrowding(clock, rng)
	if *n != 2 || p.Production != [3]float64{1800500, 500, 750.5} {
		t.Fatal(p, *n)
	}
	if len(w.News) != 1 || w.News[0].PortCount != 1 || p.Production[0] < 1000000 {
		t.Fatal("rerolled until cured", w.News)
	}
	for i, c := range p.Coefficient {
		if (c > 0) != (i == 0) {
			t.Fatal(p)
		}
	}
	// No-event commodity switching uses first exact positive tie, or ore for zero.
	for _, supply := range [][3]float64{{0, 0, 0}, {100, 100, 100}, {0, 100, 200}, {0, 200, 100}} {
		p.Supply = supply
		p.Production = [3]float64{100, 100, 100}
		rng, n = eventSequence(t)
		w.overcrowding(clock, rng)
		winner := 0
		for i := 1; i < 3; i++ {
			if supply[i] > supply[winner] {
				winner = i
			}
		}
		for i, c := range p.Coefficient {
			if (c > 0) != (i == winner) {
				t.Fatal(supply, p)
			}
		}
		if *n != 0 {
			t.Fatal(*n)
		}
	}
	p.Production = [3]float64{1e12, 500, 500}
	p.Supply = [3]float64{1e12, 0, 0}
	w.overcrowding(clock, func() float64 { return math.Nextafter(1, 0) })
	if p.Production[0] != 1e12 {
		t.Fatal("port numerical limit", p)
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}
func TestPlanetOutbreakStrictEagerGates(t *testing.T) {
	for _, spec := range []struct {
		rates  [3]float64
		ground int64
		draws  []float64
	}{
		{[3]float64{100000, 0, 0}, 1000000, []float64{math.Nextafter(1, 0), 0, math.Nextafter(1, 0)}},
		{[3]float64{200000, 0, 0}, 2000000, []float64{.5, 0, .5}},
		{[3]float64{}, 0, []float64{.9, .1, .8}},
	} {
		w, p := eventWorld(t)
		p.Production = spec.rates
		p.Ground = spec.ground
		before := *p
		rng, n := eventSequence(t, spec.draws...)
		w.overcrowding(clock, rng)
		if *n != 3 || *p != before || len(w.News) != 0 {
			t.Fatal(p, before, *n, w.News)
		}
	}
}
func TestPlanetOutbreakDamageCivilOverrideAndAccurateDebit(t *testing.T) {
	for _, civil := range []bool{false, true} {
		w, p := eventWorld(t)
		p.Production = [3]float64{1000000, 200, 300}
		p.Cargo = [3]float64{10000000, 2000, 3000}
		if civil {
			p.Ground = 4000000
		}
		before := *p
		values := []float64{.9, 0, .5, .25, 0, .5, .5, .5}
		if civil {
			values = append(values, .5)
		}
		rng, n := eventSequence(t, values...)
		w.overcrowding(clock, rng)
		kind := NewsPlanetPlague
		bank := before.Bank
		if civil {
			kind = NewsCivilWar
			bank -= 6172
		}
		if *n != len(values) || p.Bank != bank || p.Ground != before.Ground*3/4 || p.Production != [3]float64{250000, 0, 150} || p.Cargo != [3]float64{2500000, 0, 1500} {
			t.Fatal(p, *n)
		}
		if p.Owner != before.Owner || p.Name != before.Name || p.Fighters != before.Fighters || p.Missiles != before.Missiles || p.Mines != before.Mines || p.Plasma != before.Plasma {
			t.Fatal("event changed identity/weapons")
		}
		if len(w.News) != 1 || w.News[0].Kind != kind || w.News[0].PlanetName != before.Name || w.News[0].Alias != "" || w.News[0].Outcome != "" {
			t.Fatal(w.News)
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
	// A civil event must not charge a subsequent plague, despite the DOS stale text.
	w, p := eventWorld(t)
	p.Ground = 4000000
	p.Bank = 100
	q := *p
	q.ID = 3
	q.Sector = 3
	q.Name = "Following"
	q.Ground = 0
	q.Bank = 12345
	q.Production = [3]float64{1000000, 0, 0}
	w.Planets[3] = &q
	w.Sectors[3].Planet = 3
	rng, n := eventSequence(t, 0, 0, .5, .5, .5, .5, .5, .5, .5, .9, 0, 0, .5, .5, .5)
	w.overcrowding(clock, rng)
	if *n != 15 || p.Bank != 50 || q.Bank != 12345 || len(w.News) != 2 || w.News[0].Kind != NewsCivilWar || w.News[1].Kind != NewsPlanetPlague {
		t.Fatal(p, q, w.News, *n)
	}
}
func TestPlanetGroundZeroHomeIdentityAndCreditBoundaries(t *testing.T) {
	for _, owner := range []int{0, 1, MercenaryOwner, XannorOwner} {
		w, p := eventWorld(t)
		p.Owner = owner
		p.Sector = 8
		w.Sectors[2].Planet = 0
		w.Sectors[8].Planet = 2
		if owner == MercenaryOwner {
			p.FactionHome = MercenaryHome
		}
		if owner == XannorOwner {
			p.FactionHome = XannorHome
			w.Xannor = &XannorState{HQ: 8}
		}
		p.Production = [3]float64{1000000, 0, 0}
		p.Ground = 0
		before := *p
		rng, n := eventSequence(t, .9, 0, .9, 0, 0, 0)
		w.overcrowding(clock, rng)
		if *n != 6 || p.Ground != 0 || p.Production != [3]float64{} || p.Cargo != [3]float64{} || p.Owner != owner || p.FactionHome != before.FactionHome || w.Sectors[8].Planet != 2 {
			t.Fatal(p, *n)
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
	for _, bank := range []int64{0, 1, 100, MaxMoney} {
		for _, r := range []float64{0, .5, math.Nextafter(1, 0)} {
			debit := eventDebit(bank, r)
			if debit < 0 || debit > bank || (bank > 0 && debit == bank) {
				t.Fatal(bank, r, debit)
			}
		}
	}
	if eventDebit(MaxMoney, math.Nextafter(1, 0)) != MaxMoney-1 {
		t.Fatal("rounded credit multiplication")
	}
	w, p := eventWorld(t)
	p.Ground = 1
	p.Production = [3]float64{1000000, 0, 0}
	rng, _ := eventSequence(t, .9, 0, 0, .5, .5, .5, .5, .5)
	w.overcrowding(clock, rng)
	if p.Ground != 0 || p.Owner != 1 {
		t.Fatal("fraction rounding or title changed", p)
	}
}
func TestOvercrowdingBoundedFullWorldStableOrderAndMetadata(t *testing.T) {
	w, err := New(clock, 36, 1000)
	if err != nil {
		t.Fatal(err)
	}
	for _, p := range w.Ports {
		p.Production = [3]float64{1000000, 1000, 1000}
	}
	for id := 2; id <= 100; id++ {
		w.Planets[id] = &Planet{ID: id, Sector: id, Name: "Crowded", Updated: clock, Production: [3]float64{2000000, 0, 0}}
		w.Sectors[id].Planet = id
	}
	calls := 0
	w.overcrowding(clock, func() float64 { calls++; return .5 })
	if calls != 1000*3+99*6 || len(w.News) != 100 || w.News[0].PortCount != 1000 {
		t.Fatal(calls, len(w.News))
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	// Fixed seeds and sorted IDs produce identical results across map iteration.
	for seed := int64(0); seed < 32; seed++ {
		a, p := eventWorld(t)
		p.Production = [3]float64{1000000000, 1000000000, 1000000000}
		p.Ground = MaxQuantity
		p.Bank = MaxMoney
		raw, _ := json.Marshal(a)
		var b World
		_ = json.Unmarshal(raw, &b)
		a.overcrowding(clock, rand.New(rand.NewSource(seed)).Float64)
		b.overcrowding(clock, rand.New(rand.NewSource(seed)).Float64)
		if !reflect.DeepEqual(a, &b) {
			t.Fatal("unstable map order", seed)
		}
		if err = a.Validate(); err != nil {
			t.Fatal(seed, err)
		}
	}
	for _, mode := range []string{"sequence", "clock"} {
		a, p := eventWorld(t)
		p.Ground = MaxQuantity
		p.Production = [3]float64{1000000, 0, 0}
		a.Ports[1].Production = [3]float64{1000000, 1, 1}
		if mode == "sequence" {
			a.NextNews = math.MaxUint64
		} else {
			_ = a.RecordLogin(1, clock.Add(time.Hour))
		}
		before := *p
		port := *a.Ports[1]
		draws := 0
		a.overcrowding(clock, func() float64 { draws++; return .5 })
		if *p != before || a.Ports[1].Production != port.Production || draws != 3 {
			t.Fatal("unreportable damage", mode, p, draws)
		}
	}
}
func TestOvercrowdingNewsValidation(t *testing.T) {
	for _, event := range []NewsEvent{{Kind: NewsPortPlague, PortCount: 1000}, {Kind: NewsPlanetPlague, PlanetName: "Old Name"}, {Kind: NewsCivilWar, PlanetName: "Old Name"}} {
		w, p := eventWorld(t)
		event.At = clock
		w.appendNews(event)
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
		p.Name = "Renamed"
		delete(w.Planets, 2)
		w.Sectors[2].Planet = 0
		if err := w.Validate(); err != nil {
			t.Fatal("snapshot required live planet", err)
		}
		raw, _ := json.Marshal(w)
		for _, edit := range []func(*NewsEvent){func(e *NewsEvent) { e.Alias = "private" }, func(e *NewsEvent) { e.Team = 1 }, func(e *NewsEvent) { e.TeamName = "private" }, func(e *NewsEvent) { e.Outcome = "balance 12345" }, func(e *NewsEvent) { e.PortCount = -1 }, func(e *NewsEvent) { e.PlanetName = "\x1b" }} {
			var b World
			_ = json.Unmarshal(raw, &b)
			edit(&b.News[0])
			if b.Validate() == nil {
				t.Fatal("invalid event accepted", b.News)
			}
		}
	}
	w, _ := eventWorld(t)
	w.appendNews(NewsEvent{At: clock, Kind: NewsPortPlague, PortCount: 3001})
	if w.Validate() == nil {
		t.Fatal("unbounded count accepted")
	}
}

func TestPlanetEventsUsePostGrowthEconomy(t *testing.T) {
	w, p := eventWorld(t)
	p.Production = [3]float64{2000000, 0, 0}
	p.Ground = 4000000
	p.Bank = 10000
	rng, n := eventSequence(t, .5, .5, .5, .5, .5, .5, .5, .5, .5)
	w.overcrowding(clock.Add(24*time.Hour), rng)
	if *n != 9 || p.Bank != 5050 || p.Ground != 3030000 || p.Production[0] != 1010000 || p.Fighters != 2000031 {
		t.Fatal("event preceded growth/interest or burned weapons", p, *n)
	}
	if len(w.News) != 1 || w.News[0].Kind != NewsCivilWar {
		t.Fatal(w.News)
	}
}
func TestOvercrowdingFullJournalAndLastAvailableID(t *testing.T) {
	for _, last := range []bool{false, true} {
		w, p := eventWorld(t)
		p.Ground = 4000000
		w.Ports[1].Production = [3]float64{2000000, 500, 500}
		if last {
			w.NextNews = math.MaxUint64 - 1
		} else {
			for i := 0; i < MaxNewsEvents; i++ {
				w.appendNews(NewsEvent{At: clock, Kind: NewsLogin, Alias: "Q"})
			}
		}
		w.overcrowding(clock, func() float64 { return .5 })
		if last {
			if w.NextNews != math.MaxUint64 || len(w.News) != 1 || w.News[0].Kind != NewsPortPlague || p.Bank != 12345 || p.Ground != 4000000 {
				t.Fatal("unreportable planet damaged after final ID", p, w.News)
			}
		} else if len(w.News) != MaxNewsEvents || w.News[len(w.News)-1].Kind != NewsCivilWar || p.Bank != 6173 {
			t.Fatal("full retained history blocked event", p, w.News)
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}
