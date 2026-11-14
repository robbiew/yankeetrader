package qbmaint

import (
	"fmt"

	"github.com/robbiew/yankeetrader/internal/qbmbf"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

type BaseInputs struct {
	Day         int
	State       uint32
	HelperTimer [4]byte
}
type BaseStats struct {
	Sector, Draws           int
	SeededState, FinalState uint32
}

// ReplayMercenaryBaseBirth restores reserved slot 99 in an independently modeled
// post-mobile-group world. It admits only the ordinary default initial prefix.
// Existing bases, placement retries and later hiring/desertion are excluded.
// Clock/state provenance is the caller's responsibility. Targets are not inputs.
func ReplayMercenaryBaseBirth(before []byte, in BaseInputs) ([]byte, BaseStats, error) {
	fail := func(s string) ([]byte, BaseStats, error) {
		return nil, BaseStats{}, fmt.Errorf("Mercenary Base birth: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.Day < 1 || in.Day > 732 || in.State > 0xffffff {
		return fail("world/day/state extent")
	}
	read := func(r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(before[a : a+4]) }
	get := func(r, o int) int {
		n, ok := integer(read(r, o))
		if !ok {
			return -999999
		}
		return n
	}
	for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		if get(1, o) != n {
			return fail("geometry")
		}
	}
	if qbmbf.SignZeroSingle(in.HelperTimer).Carry || !qbmbf.CompareSingle(in.HelperTimer, encode(86400)).Carry {
		return fail("raw TIMER")
	}
	for r := 2; r <= 51; r++ {
		if read(r, 85)[3] != 0 {
			return fail("active player")
		}
	}
	for r := 4052; r <= 4151; r++ {
		want := 0
		if r == 4052 {
			want = 12
		}
		if r == 4151 {
			want = 8
		}
		if get(r, 85) != want {
			return fail("planet activity")
		}
	}
	if string(before[4051*RecordSize:4051*RecordSize+12]) != "The Wanderer" || string(before[4150*RecordSize:4150*RecordSize+8]) != "Xannoron" || get(4151, 73) != -1 || read(72, 105)[3] != 0 {
		return fail("ordinary birth prefix")
	}
	hq := get(1, 117)
	if hq < 8 || hq > 3000 || get(52, 105) != hq {
		return fail("tracked HQ")
	}
	groups := map[int]bool{}
	total := 0
	endpoint := 0
	for g := 1; g <= 20; g++ {
		s := get(51+g, 105)
		if s < 8 || s > 3000 || groups[s] {
			return fail("20 distinct mobile endpoints required")
		}
		groups[s] = true
		n := get(51+s, 81)
		if n <= 0 || n > 10000 || get(51+s, 85) != -1 {
			return fail("Xannor group force/owner")
		}
		total += n
		if g == 20 {
			endpoint = s
		}
	}
	if total != 10000 {
		return fail("initial force total")
	}
	wandererLinks := 0
	for s := 1; s <= 3000; s++ {
		r := 51 + s
		if !groups[s] && get(r, 81) != 0 {
			return fail("foreign force")
		}
		if read(r, 89)[3] != 0 {
			return fail("sector hazard")
		}
		mines := 0
		if s == endpoint {
			mines = 1
		}
		if get(r, 129) != mines {
			return fail("group-20 mine prefix")
		}
		link := get(r, 93)
		if s == hq {
			if link != 100 {
				return fail("HQ planet link")
			}
		} else if link == 1 {
			wandererLinks++
		} else if link != 0 {
			return fail("unexpected planet link")
		}
	}
	if wandererLinks != 1 {
		return fail("Wanderer planet link")
	}
	rng := qbrng.New(in.State)
	rng.RandomizeMBF(in.HelperTimer)
	seeded := rng.State()
	sector := int(float32(rng.Float32()*3000)) + 1
	if get(51+sector, 93) != 0 {
		return fail("occupied placement/retry outside profile")
	}
	out := append([]byte(nil), before...)
	rec := out[4149*RecordSize : 4150*RecordSize]
	for i := 0; i < 41; i++ {
		rec[i] = ' '
	}
	copy(rec[:41], "Mercenary Base")
	put := func(o int, v [4]byte) { copy(rec[o:o+4], v[:]) }
	put(85, encode(14))
	put(41, encode(in.Day-10))
	for _, o := range []int{45, 49, 53} {
		put(o, [4]byte{0, 0x50, 0x43, 0x91})
	}
	for _, o := range []int{57, 61, 65, 69} {
		put(o, [4]byte{0, 0, 0xa0, 0})
	}
	put(73, [4]byte{0, 0, 0x80, 0x82})
	put(77, [4]byte{0, 0x7c, 0x12, 0x92})
	put(117, [4]byte{0x20, 0xbc, 0x3e, 0x99})
	put(125, [4]byte{0, 0, 0x3e, 0})
	at := (50+sector)*RecordSize + 93
	v := encode(99)
	copy(out[at:at+4], v[:])
	return out, BaseStats{Sector: sector, Draws: 1, SeededState: seeded, FinalState: rng.State()}, nil
}
