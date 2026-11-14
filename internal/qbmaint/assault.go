package qbmaint

import (
	"fmt"
	"math/bits"

	"github.com/robbiew/yankeetrader/internal/qbmbf"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

type AssaultInputs struct {
	Group, Sector, Force int
	State                uint32
}
type AssaultStats struct {
	InitialForce, RawForce, Rounds, DamageRounds, Draws int
	FinalRates                                          [3][4]byte
	FinalState                                          uint32
}

// ReplayWandererAssault is an explicit research extension for one unscreened,
// neutral, zero-ground Wanderer encounter. It preserves the original location-
// subscript 450-batch defect; modern gameplay is unchanged. Moving group loss,
// routing/shared pursuit, other combat branches and full maintenance integration
// are not implemented here. Input is an independently modeled encounter prefix,
// never a native target. Errors return no partial world/statistics.
func ReplayWandererAssault(before []byte, in AssaultInputs) ([]byte, AssaultStats, error) {
	fail := func(s string) ([]byte, AssaultStats, error) {
		return nil, AssaultStats{}, fmt.Errorf("Wanderer assault: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.Group < 2 || in.Group > 19 || in.Sector < 8 || in.Sector > 3000 || in.Force < 1 || in.Force > 10000 || in.State > 0xffffff {
		return fail("bounded world/group/sector/force/state")
	}
	read := func(r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(before[a : a+4]) }
	for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		v, ok := integer(read(1, o))
		if !ok || v != n {
			return fail("geometry")
		}
	}
	if string(before[4051*137:4051*137+12]) != "The Wanderer" || read(4052, 85) != encode(12) || read(51+in.Sector, 93) != encode(1) {
		return fail("active Wanderer placement")
	}
	for _, o := range []int{73, 77, 57, 61, 65} {
		if read(4052, o)[3] != 0 {
			return fail("neutral zero-ground empty Wanderer")
		}
	}
	for _, o := range []int{81, 89, 129} {
		if read(51+in.Sector, o)[3] != 0 {
			return fail("unscreened hazard-free sector")
		}
	}
	var rates [3][4]byte
	for i, o := range []int{45, 49, 53} {
		rates[i] = read(4052, o)
		if !qbmbf.CompareSingle(encode(500), rates[i]).Carry || qbmbf.CompareSingle(encode(5000), rates[i]).Carry {
			return fail("large-batch rates in (500,5000]")
		}
	}
	rng := qbrng.New(in.State)
	stats := AssaultStats{InitialForce: in.Force}
	force := in.Force
	rnd := func() [4]byte {
		rng.Float32()
		stats.Draws++
		n := rng.State()
		if n == 0 {
			return [4]byte{}
		}
		l := bits.Len32(n)
		m := (n << uint(24-l)) & 0x7fffff
		return [4]byte{byte(m), byte(m >> 8), byte(m >> 16), byte(104 + l)}
	}
	for force > 0 {
		if stats.Rounds >= 4096 {
			return fail("round bound")
		}
		for _, r := range rates {
			if !qbmbf.CompareSingle(encode(500), r).Carry {
				return fail("small-rate branch")
			}
		}
		gate := rnd()
		stats.Rounds++
		// The exact [0,1) RND fraction admits the source's strict .5 damage gate.
		if qbmbf.CompareSingle(gate, [4]byte{0, 0, 0, 0x80}).Carry {
			stats.DamageRounds++
			for i, r := range rates {
				product, ok := qbmbf.MultiplySingle(rnd(), encode(450))
				if !ok {
					return fail("damage product")
				}
				damage, e := qbmbf.DivideSingle(product, encode(3))
				if e != nil {
					return fail("damage division")
				}
				value, ok := qbmbf.SubtractSingle(r, damage)
				if !ok {
					return fail("rate subtraction")
				}
				rates[i] = value
			}
		} else {
			force -= 450
		}
	}
	for _, r := range rates {
		if !qbmbf.CompareSingle(encode(500), r).Carry {
			return fail("small-rate aftermath")
		}
	}
	out := append([]byte(nil), before...)
	rec := out[4051*RecordSize : 4052*RecordSize]
	for i, o := range []int{45, 49, 53} {
		v := rates[i]
		copy(rec[o:o+4], v[:])
	}
	copy(rec[73:77], []byte{0, 0, 0x20, 0})
	stats.RawForce = force
	stats.FinalRates = rates
	stats.FinalState = rng.State()
	return out, stats, nil
}
