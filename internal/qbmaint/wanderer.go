package qbmaint

import (
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbmbf"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

type WandererInputs struct {
	Day         int
	State       uint32
	HelperTimer [4]byte // Actual raw helper TIMER seconds, including zero residues.
}
type WandererStats struct {
	Sector                  int
	SeededState, FinalState uint32
	Draws                   int
}

// ReplayWandererBirth models only initial Wanderer creation/placement. It takes
// a before-world and explicit source clock/RNG inputs, never a native target.
// All sector planet links and planet/player activity must be zero. Candidate
// rejection/retry, later movement/combat and other NPCs are not admitted.
// Invalid inputs return no output; the caller authenticates clock/state origins.
func ReplayWandererBirth(before []byte, in WandererInputs) ([]byte, WandererStats, error) {
	fail := func(message string) ([]byte, WandererStats, error) {
		return nil, WandererStats{}, fmt.Errorf("Wanderer birth: %s", message)
	}
	if len(before) != WorldRecords*RecordSize || in.Day < 1 || in.Day > 732 || in.State > 0xffffff {
		return fail("default world and explicit bounded day/state required")
	}
	for off, want := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		v, ok := integer([4]byte(before[off : off+4]))
		if !ok || v != want {
			return fail("default geometry required")
		}
	}
	if qbmbf.SignZeroSingle(in.HelperTimer).Carry || !qbmbf.CompareSingle(in.HelperTimer, encode(86400)).Carry {
		return fail("raw TIMER outside [0,86400)")
	}
	for i := 1; i <= 50; i++ {
		if before[i*RecordSize+88] != 0 {
			return fail("active player outside profile")
		}
	}
	for i := 4051; i < 4151; i++ {
		if before[i*RecordSize+88] != 0 {
			return fail("existing planet outside birth profile")
		}
	}
	for sector := 1; sector <= 3000; sector++ {
		if before[(50+sector)*RecordSize+96] != 0 {
			return fail("occupied planet link/retry outside profile")
		}
	}
	rng := qbrng.New(in.State)
	rng.RandomizeMBF(in.HelperTimer)
	seeded := rng.State()
	sector := int(float32(rng.Float32()*3000)) + 1
	if sector < 1 || sector > 3000 {
		return fail("selected sector outside profile")
	}
	out := append([]byte(nil), before...)
	rec := out[4051*RecordSize : 4052*RecordSize]
	for i := 0; i < 41; i++ {
		rec[i] = ' '
	}
	copy(rec[:41], "The Wanderer")
	put := func(off int, value [4]byte) { copy(rec[off:off+4], value[:]) }
	put(41, encode(in.Day-10))
	put(85, encode(12))
	for _, off := range []int{45, 49, 53} {
		put(off, [4]byte{0, 0x40, 0x1c, 0x8d})
	}
	for _, off := range []int{57, 61, 65, 69, 77, 125} {
		put(off, [4]byte{0, 0, 0x1c, 0})
	}
	put(117, [4]byte{0, 0x24, 0x74, 0x92})
	put(73, [4]byte{})
	link := (50+sector)*RecordSize + 93
	one := encode(1)
	copy(out[link:link+4], one[:])
	return out, WandererStats{Sector: sector, SeededState: seeded, FinalState: rng.State(), Draws: 1}, nil
}
