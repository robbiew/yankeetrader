package qbmaint

import (
	"bytes"
	"fmt"
	"math"

	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// OccupiedPlanetInputs carries only modeled state and ordered source clocks.
type OccupiedPlanetInputs struct {
	State  uint32
	Clocks []PlanetClock
}

// ReplayOccupiedPlanets models the clean day-306 ordinary slots 2/3 phase from
// the retained occupied-world corpus. It accepts zero, one or two active planets
// with prior-day dates, 1000 rates, 500000 ground, neutral/Xannor ownership and
// otherwise empty numeric fields. It does not admit combat or later economy.
// Errors publish no world/statistics; inputs are readonly and outputs owned.
func ReplayOccupiedPlanets(before []byte, in OccupiedPlanetInputs) ([]byte, EvolvedPlanetStats, error) {
	fail := func(s string) ([]byte, EvolvedPlanetStats, error) {
		return nil, EvolvedPlanetStats{}, fmt.Errorf("occupied planets: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff {
		return fail("world/state extent")
	}
	raw := func(r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(before[a : a+4]) }
	get := func(r, o int) float64 { return portSingleValue(raw(r, o)) }
	for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151, 81: 305} {
		if get(1, o) != float64(n) {
			return fail("default geometry and pre-day306 watermark")
		}
	}
	for r := 2; r <= 51; r++ {
		if get(r, 85) != 0 {
			return fail("active human player")
		}
	}
	active := []int{}
	for r := 4052; r <= 4151; r++ {
		if get(r, 85) != 0 {
			if r != 4053 && r != 4054 {
				return fail("ordinary slots 2/3 only")
			}
			active = append(active, r)
		}
	}
	if len(in.Clocks) != len(active) {
		return fail("complete active planet clock inventory")
	}
	for i, r := range active {
		c := in.Clocks[i]
		minute := portSingleValue(c.TimerMinutes)
		if c.Record != r || c.Day != 306 || minute < 0 || minute >= 1 {
			return fail("ordered day306 midnight source clocks")
		}
		n := get(r, 85)
		if n != math.Floor(n) || n < 1 || n > 41 {
			return fail("ASCII planet name length")
		}
		a := (r - 1) * RecordSize
		name := before[a : a+int(n)]
		for _, v := range name {
			if v < 32 || v > 126 {
				return fail("ASCII planet name")
			}
		}
		if !bytes.Equal(before[a:a+41], append(bytes.Clone(name), bytes.Repeat([]byte{' '}, 41-len(name))...)) {
			return fail("padded planet name")
		}
		if get(r, 41) != 305 || get(r, 77) != 500000 || (get(r, 73) != 0 && get(r, 73) != -1) {
			return fail("prior-day clean ground/owner context")
		}
		for _, o := range []int{45, 49, 53} {
			if get(r, o) != 1000 {
				return fail("1000 cargo rates required")
			}
		}
		for o := 41; o < 137; o += 4 {
			if o == 41 || o == 45 || o == 49 || o == 53 || o == 73 || o == 77 || o == 85 {
				continue
			}
			if get(r, o) != 0 {
				return fail("empty bank/stocks/reserved fields required")
			}
		}
		links := 0
		for s := 1; s <= 3000; s++ {
			if get(51+s, 93) == float64(r-4051) {
				links++
			}
		}
		if links != 1 {
			return fail("unique physical sector link")
		}
	}
	work := bytes.Clone(before)
	read := func(r, o int) float64 { a := (r-1)*RecordSize + o; return portSingleValue([4]byte(work[a : a+4])) }
	put := func(r, o int, v float64) {
		a := (r-1)*RecordSize + o
		b := portSingleBytes(float32(v))
		copy(work[a:a+4], b[:])
	}
	f := func(v float64) float64 { return float64(float32(v)) }
	rng := qbrng.New(in.State)
	stats := EvolvedPlanetStats{InitialState: in.State}
	for _, c := range in.Clocks {
		r := c.Record
		elapsed := f(f(float64(c.Day)-read(r, 41)) + f(f(portSingleValue(c.TimerMinutes)-read(r, 89))/1440))
		if elapsed < 1 || elapsed >= 1.001 {
			return fail("one-day fractional elapsed interval")
		}
		rates := [3]float64{read(r, 45), read(r, 49), read(r, 53)}
		total := f(f(rates[0]+rates[1]) + rates[2])
		resource := [6]float64{rates[0], rates[1], rates[2], total, math.Floor(total / 2500), math.Floor(total / 25000)}
		// This ordinary profile floors the full wider expression; it does not adopt
		// evolved-bank bonuses or the evolved profile's extra SINGLE conversion.
		bank, ground := read(r, 117), read(r, 77)
		interest := float64(float64(bank*elapsed) * f(.01))
		put(r, 117, math.Floor(float64(bank+interest)))
		growth := float64(float64(ground*elapsed) * f(.01))
		put(r, 77, math.Floor(float64(ground+growth)))
		for j, o := range []int{57, 61, 65, 129, 69, 125} {
			put(r, o, f(read(r, o)+f(resource[j]*elapsed)))
		}
		put(r, 113, f(read(r, 113)+f(math.Floor(total/100000)*elapsed)))
		for j, o := range []int{45, 49, 53} {
			if read(r, 57+4*j) > f(10*rates[j]) {
				return fail("surplus rate replacement")
			}
			put(r, o, f(rates[j]+f(f(rates[j]*elapsed)*f(.01))))
		}
		row := PlanetEconomyRow{Record: r, Day: c.Day, Elapsed: portSingleBytes(float32(elapsed)), Ground: int(read(r, 77))}
		var draws [3]float64
		for j := range draws {
			v := rng.Float32()
			draws[j] = float64(v)
			row.EventDraws[j] = portSingleBytes(v)
		}
		production := f(f(read(r, 45)+read(r, 49)) + read(r, 53))
		if f(draws[0]*production) > f(f(draws[1]*1000000)+100000) || f(draws[2]*read(r, 77)) > 1000000 {
			return fail("selected event damage")
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
