package qbmaint

import (
	"bytes"
	"fmt"
	"math"

	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// PlanetClock binds an explicit source DATE and raw TIMER/60 to a physical record.
type PlanetClock struct {
	Record, Day  int
	TimerMinutes [4]byte
}

// EvolvedPlanetInputs carries caller-authenticated source clocks and modeled RNG.
type EvolvedPlanetInputs struct {
	State  uint32
	Clocks []PlanetClock
}

// PlanetEconomyRow records calculated outcomes, not native endpoint observations.
type PlanetEconomyRow struct {
	Record, Day int
	Elapsed     [4]byte
	EventDraws  [3][4]byte
	Ground      int
	CargoRates  [3][4]byte
}

// EvolvedPlanetStats describes the modeled phase and its three eager draws per planet.
type EvolvedPlanetStats struct {
	InitialState, FinalState uint32
	Draws                    int
	Rows                     []PlanetEconomyRow
}

// ReplayEvolvedPlanets returns a new complete world after only the bounded planet
// economy phase. It admits the retained named convergence planets on days 306..308,
// without selected event damage. Unknown contexts fail without partial output or
// state publication. It accepts no target, observed RNG endpoint or correction.
func ReplayEvolvedPlanets(before []byte, in EvolvedPlanetInputs) ([]byte, EvolvedPlanetStats, error) {
	fail := func(s string) ([]byte, EvolvedPlanetStats, error) {
		return nil, EvolvedPlanetStats{}, fmt.Errorf("evolved planets: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff {
		return fail("world/state extent")
	}
	raw := func(r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(before[a : a+4]) }
	get := func(r, o int) float64 { return portSingleValue(raw(r, o)) }
	for o, v := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		if get(1, o) != float64(v) {
			return fail("default geometry")
		}
	}
	// The profile excludes active human players; clocks cannot broaden admission.
	for r := 2; r <= 51; r++ {
		if get(r, 85) != 0 {
			return fail("active human player")
		}
	}
	day := get(1, 81) + 1
	if day != 306 && day != 307 && day != 308 {
		return fail("advancing convergence day")
	}
	active := []int{4053}
	if day > 306 {
		active = []int{4052, 4053, 4150, 4151}
	}
	actual := []int{}
	for r := 4052; r <= 4151; r++ {
		if get(r, 85) != 0 {
			actual = append(actual, r)
		}
	}
	if len(actual) != len(active) || len(in.Clocks) != len(active) {
		return fail("complete active planet inventory")
	}
	names := map[int]string{4052: "The Wanderer", 4053: "Convergence Haven", 4150: "Mercenary Base", 4151: "Xannoron"}
	owners := map[int]int{4052: 0, 4053: -1, 4150: -2, 4151: -1}
	for i, r := range active {
		c := in.Clocks[i]
		minute := portSingleValue(c.TimerMinutes)
		if actual[i] != r || c.Record != r || c.Day != int(day) || minute < 0 || minute >= 1 {
			return fail("ordered record-qualified midnight clocks")
		}
		name := names[r]
		at := (r - 1) * RecordSize
		if get(r, 85) != float64(len(name)) || !bytes.Equal(before[at:at+41], append([]byte(name), bytes.Repeat([]byte{' '}, 41-len(name))...)) || get(r, 73) != float64(owners[r]) {
			return fail("named planet/owner context")
		}
		// Keep this IEEE-backed source quantization away from MBF underflow and
		// IEEE subnormal precision. The retained smallest positive stock is > .09.
		for _, o := range []int{57, 61, 65, 69, 77, 113, 117, 125, 129} {
			if v := get(r, o); v != 0 && v < math.Ldexp(1, -24) {
				return fail("positive assets below bounded numeric scale")
			}
		}
		last := get(r, 41)
		if last != 296 && last != 305 && last != 306 && last != 307 {
			return fail("bounded old date")
		}
		if get(r, 77) < 0 || get(r, 77) > 600000 || get(r, 117) < 0 || get(r, 117) > 30000000 {
			return fail("bounded ground/bank")
		}
		for _, o := range []int{45, 49, 53} {
			if v := get(r, o); v < 1 || v > 200000 {
				return fail("bounded cargo rate")
			}
		}
		for _, o := range []int{57, 61, 65, 69, 113, 125, 129} {
			if v := get(r, o); v < 0 || v > 10000000 {
				return fail("bounded resource stock")
			}
		}
		inherited := map[int]int{81: 0, 93: 0, 97: 0, 101: 0, 105: 0, 109: 0, 121: 0, 133: 0}
		if r != 4053 {
			inherited = map[int]int{81: 305, 93: 4151, 97: 0, 101: 5, 105: 300, 109: 0, 121: 1000, 133: 0}
		}
		for o, v := range inherited {
			if get(r, o) != float64(v) {
				return fail("inherited reserved fields")
			}
		}
		links := 0
		for s := 1; s <= 3000; s++ {
			if get(51+s, 93) == float64(r-4051) {
				links++
			}
		}
		if links != 1 {
			return fail("one physical sector link per active planet")
		}
	}
	return replayQualifiedPlanetEconomy(before, in, "evolved planets")
}

// replayQualifiedPlanetEconomy shares source arithmetic only after each public
// profile has checked its own complete admission. It does not select a profile.
func replayQualifiedPlanetEconomy(before []byte, in EvolvedPlanetInputs, context string) ([]byte, EvolvedPlanetStats, error) {
	fail := func(s string) ([]byte, EvolvedPlanetStats, error) {
		return nil, EvolvedPlanetStats{}, fmt.Errorf("%s: %s", context, s)
	}
	work := bytes.Clone(before)
	read := func(r, o int) float64 { a := (r-1)*RecordSize + o; return portSingleValue([4]byte(work[a : a+4])) }
	put := func(r, o int, v float64) {
		b := portSingleBytes(float32(v))
		a := (r-1)*RecordSize + o
		copy(work[a:a+4], b[:])
	}
	f := func(v float64) float64 { return float64(float32(v)) }
	rng := qbrng.New(in.State)
	stats := EvolvedPlanetStats{InitialState: in.State}
	for _, c := range in.Clocks {
		r := c.Record
		elapsed := f(f(float64(c.Day)-read(r, 41)) + f(f(portSingleValue(c.TimerMinutes)-read(r, 89))/1440))
		if elapsed < 0 || elapsed > 10 {
			elapsed = 10
		}
		if elapsed < .999 || elapsed > 10 {
			return fail("bounded elapsed interval")
		}
		rates := [3]float64{read(r, 45), read(r, 49), read(r, 53)}
		total := f(f(rates[0]+rates[1]) + rates[2])
		resource := [6]float64{rates[0], rates[1], rates[2], math.Floor(total), math.Floor(total / 2500), math.Floor(total / 25000)}
		bank, ground := read(r, 117), read(r, 77)
		// Explicit float64 conversion separates the wider expression operations;
		// source SINGLE conversion precedes INT floor, including interest boundaries.
		interest := float64(float64(bank*elapsed) * f(.01))
		put(r, 117, math.Floor(f(float64(bank+interest))))
		groundInterest := float64(float64(ground*elapsed) * f(.01))
		groundBonus := float64(f(bank/10000) * elapsed)
		put(r, 77, math.Floor(f(float64(float64(ground+groundInterest)+groundBonus))))
		bonuses := [6]float64{f(bank / 10000), f(bank / 20000), f(bank / 30000), f(bank / 500), f(bank * f(.00001)), f(bank * f(.000004))}
		for j, o := range []int{57, 61, 65, 129, 69, 125} {
			put(r, o, f(read(r, o)+f(f(resource[j]+bonuses[j])*elapsed)))
		}
		put(r, 113, f(read(r, 113)+f(f(math.Floor(total/100000)+f(bank/25000000))*elapsed)))
		for j, o := range []int{45, 49, 53} {
			rate := rates[j]
			if read(r, 57+4*j) > f(10*rate) {
				rate = f(read(r, 57+4*j) / 10)
			}
			put(r, o, f(rate+f(f(rate*elapsed)*f(.01))))
		}
		production := f(f(read(r, 45)+read(r, 49)) + read(r, 53))
		row := PlanetEconomyRow{Record: r, Day: c.Day, Elapsed: portSingleBytes(float32(elapsed)), Ground: int(read(r, 77))}
		var draws [3]float64
		for j := range draws {
			v := rng.Float32()
			draws[j] = float64(v)
			row.EventDraws[j] = portSingleBytes(v)
		}
		if f(draws[0]*production) > f(f(draws[1]*1000000)+100000) || f(draws[2]*read(r, 77)) > 1000000 {
			return fail("selected event damage outside profile")
		}
		put(r, 41, float64(c.Day))
		a := (r-1)*RecordSize + 89
		copy(work[a:a+4], c.TimerMinutes[:])
		for j, o := range []int{45, 49, 53} {
			a := (r-1)*RecordSize + o
			row.CargoRates[j] = [4]byte(work[a : a+4])
		}
		stats.Rows = append(stats.Rows, row)
		stats.Draws += 3
	}
	stats.FinalState = rng.State()
	return work, stats, nil
}
