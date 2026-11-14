package qbmaint

import (
	"fmt"

	"github.com/robbiew/yankeetrader/internal/qbmbf"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// TailInputs supplies the post-base state and only the conditional lottery
// candidate helper clock. Nil is required when the gate does not select a player.
type TailInputs struct {
	State          uint32
	CandidateTimer *[4]byte
}
type TailStats struct {
	DesertionDraws, Draws, Candidate int
	Lottery                          float32
	FinalState                       uint32
}

// ReplayInitialNPCTail models only eager defense-desertion draws and the
// super-planet lottery's inactive-player branch. The admitted no-hiring profile
// has no world writes. Active players, human defenses and funded hiring are
// excluded. No targets, reports or native endpoint corrections enter this API.
func ReplayInitialNPCTail(before []byte, in TailInputs) (TailStats, error) {
	fail := func(s string) (TailStats, error) { return TailStats{}, fmt.Errorf("initial NPC tail: %s", s) }
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff {
		return fail("world/state extent")
	}
	read := func(r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(before[a : a+4]) }
	get := func(r, o int) int {
		v, ok := integer(read(r, o))
		if !ok {
			return -999999
		}
		return v
	}
	for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		if get(1, o) != n {
			return fail("geometry")
		}
	}
	for r := 2; r <= 51; r++ {
		if read(r, 85)[3] != 0 {
			return fail("active lottery player")
		}
	}
	// Even Earth is constrained to zero treasury in this initial capture profile.
	for r := 3052; r <= 4051; r++ {
		if read(r, 89)[3] != 0 {
			return fail("port treasury/no-hiring profile")
		}
	}
	if string(before[4149*RecordSize:4149*RecordSize+14]) != "Mercenary Base" || get(4150, 85) != 14 || get(4150, 73) != -2 {
		return fail("modeled base predecessor")
	}
	if read(72, 105)[3] != 0 {
		return fail("pending revenge")
	}
	total, count := 0, 0
	seen := map[int]bool{}
	for g := 1; g <= 20; g++ {
		s := get(51+g, 105)
		if s < 8 || s > 3000 || seen[s] {
			return fail("twenty distinct group endpoints required")
		}
		seen[s] = true
	}
	for s := 1; s <= 3000; s++ {
		force := get(51+s, 81)
		if force < 0 || force > 10000 {
			return fail("bounded defense")
		}
		if force == 0 {
			continue
		}
		if s < 8 || !seen[s] || get(51+s, 85) != -1 {
			return fail("ordinary Xannor defense only")
		}
		total += force
		count++
	}
	if total != 10000 || count != 20 {
		return fail("initial force inventory")
	}
	rng := qbrng.New(in.State)
	for j := 0; j < count; j++ {
		rng.Float32()
	}
	lottery := rng.Float32()
	stats := TailStats{DesertionDraws: count, Draws: count + 1, Lottery: lottery}
	if lottery >= .5 {
		if in.CandidateTimer == nil {
			return fail("candidate clock required")
		}
		timer := *in.CandidateTimer
		if qbmbf.SignZeroSingle(timer).Carry || !qbmbf.CompareSingle(timer, encode(86400)).Carry {
			return fail("candidate TIMER")
		}
		rng.RandomizeMBF(timer)
		stats.Candidate = int(float32(rng.Float32()*50)) + 2
		stats.Draws++
	} else if in.CandidateTimer != nil {
		return fail("unexpected candidate clock")
	}
	stats.FinalState = rng.State()
	return stats, nil
}
