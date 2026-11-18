package qbmaint

import (
	"bytes"
	"fmt"
	"math"
)

// ReplayEvolvedOccupiedPlanets derives the retained occupied-combat child economy
// on days 307/308, with three homes and optional neutral Route Haven. It accepts
// modeled bytes/state and explicit planet clocks, and ends before mobile routing.
// Existing convergence/initial admission stays strict. Unsupported and late event
// paths return nil world/zero statistics without modifying input storage.
func ReplayEvolvedOccupiedPlanets(before []byte, in EvolvedPlanetInputs) ([]byte, EvolvedPlanetStats, error) {
	fail := func(s string) ([]byte, EvolvedPlanetStats, error) {
		return nil, EvolvedPlanetStats{}, fmt.Errorf("evolved occupied planets: %s", s)
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
	for r := 2; r <= 51; r++ {
		if get(r, 85) != 0 {
			return fail("active human player")
		}
	}
	prior := get(1, 81)
	if prior != 306 && prior != 307 {
		return fail("only occupied child days 307/308")
	}
	day := int(prior) + 1
	active := []int{4052, 4150, 4151}
	if get(4053, 85) != 0 {
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
	names := map[int]string{4052: "The Wanderer", 4053: "Route Haven", 4150: "Mercenary Base", 4151: "Xannoron"}
	owners := map[int]int{4052: 0, 4053: 0, 4150: -2, 4151: -1}
	for i, r := range active {
		c := in.Clocks[i]
		minute := portSingleValue(c.TimerMinutes)
		if actual[i] != r || c.Record != r || c.Day != day || minute < 0 || minute >= 1 {
			return fail("ordered record/day midnight clocks")
		}
		at := (r - 1) * RecordSize
		name := names[r]
		if get(r, 85) != float64(len(name)) || !bytes.Equal(before[at:at+41], []byte(fmt.Sprintf("%-41s", name))) || get(r, 73) != float64(owners[r]) {
			return fail("named planet and owner context")
		}
		last := prior
		if prior == 306 && (r == 4052 || r == 4150) {
			last = 296
		}
		if get(r, 41) != last || get(r, 89) < 0 || get(r, 89) >= 1 {
			return fail("source prior date/minute")
		}
		for _, o := range []int{57, 61, 65, 69, 77, 113, 117, 125, 129} {
			v := get(r, o)
			if v != 0 && v < math.Ldexp(1, -24) {
				return fail("positive assets below bounded numeric scale")
			}
		}
		if get(r, 77) < 0 || get(r, 77) > 600000 || get(r, 117) < 0 || get(r, 117) > 30000000 {
			return fail("bounded ground/bank")
		}
		for _, o := range []int{45, 49, 53} {
			if get(r, o) < 1 || get(r, o) > 200000 {
				return fail("bounded cargo rates")
			}
		}
		for _, o := range []int{57, 61, 65, 69, 113, 125, 129} {
			if get(r, o) < 0 || get(r, o) > 10000000 {
				return fail("bounded nonnegative stocks")
			}
		}
		inherited := map[int]int{81: 305, 93: 4151, 97: 0, 101: 5, 105: 300, 109: 0, 121: 1000, 133: 0}
		if r == 4053 {
			for o := range inherited {
				inherited[o] = 0
			}
		}
		for o, v := range inherited {
			if get(r, o) != float64(v) {
				return fail("inherited reserved fields")
			}
		}
		links := 0
		for sector := 1; sector <= 3000; sector++ {
			if get(51+sector, 93) == float64(r-4051) {
				links++
			}
		}
		if links != 1 {
			return fail("unique physical planet link")
		}
	}
	return replayQualifiedPlanetEconomy(before, in, "evolved occupied planets")
}
