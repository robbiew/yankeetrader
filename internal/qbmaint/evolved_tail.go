package qbmaint

import (
	"bytes"
	"fmt"

	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// EvolvedTailInputs begins after Base lookup/placement and supplies only the
// computed Mercenary-target and conditional lottery helper TIMER suffix.
type EvolvedTailInputs struct {
	State   uint32
	Helpers []ContinuationClock
}

// MercenaryActivation records a calculated descending-scan activation.
type MercenaryActivation struct {
	Origin, Force, Target int
	Gate                  [4]byte
	Held                  bool
	Candidates, Route     []int
}

// EvolvedTailStats contains modeled outcomes, never native endpoint corrections.
type EvolvedTailStats struct {
	InitialState, FinalState                                         uint32
	Draws, MovementGateDraws, TargetDraws, MercenaryForce, Candidate int
	DesertionSectors, FinalMercenarySectors                          []int
	Activations                                                      []MercenaryActivation
	Seeds                                                            []ContinuationSeed
	Lottery                                                          [4]byte
}

// ReplayEvolvedNPCTail admits inactive humans, zero taxes and absent or one
// retained 37/97525-fighter Mercenary deployment. It counts physical defenses,
// moves only through empty, mine-free, planet-free routes and then computes the
// inactive-player lottery. Errors return no world/statistics; inputs are readonly.
// This is separate from the strict initial and late-clock tail APIs.
func ReplayEvolvedNPCTail(before []byte, in EvolvedTailInputs) ([]byte, EvolvedTailStats, error) {
	fail := func(s string) ([]byte, EvolvedTailStats, error) {
		return nil, EvolvedTailStats{}, fmt.Errorf("evolved NPC tail: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff || len(in.Helpers) > 256 {
		return fail("world/state/clock extent")
	}
	work := bytes.Clone(before)
	raw := func(r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(work[a : a+4]) }
	get := func(r, o int) int {
		n, ok := integer(raw(r, o))
		if !ok {
			return -999999
		}
		return n
	}
	putraw := func(r, o int, b [4]byte) { a := (r-1)*RecordSize + o; copy(work[a:a+4], b[:]) }
	put := func(r, o, n int) { putraw(r, o, encode(n)) }
	for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		if get(1, o) != n {
			return fail("default geometry")
		}
	}
	for r := 2; r <= 51; r++ {
		if get(r, 85) != 0 {
			return fail("active human player")
		}
	}
	for r := 3052; r <= 4051; r++ {
		if get(r, 89) != 0 {
			return fail("tax-funded hiring")
		}
	}
	if get(72, 105) != 0 {
		return fail("pending revenge")
	}
	a := (4150 - 1) * RecordSize
	if !bytes.Equal(work[a:a+41], append([]byte("Mercenary Base"), bytes.Repeat([]byte{' '}, 27)...)) || get(4150, 85) != 14 || get(4150, 73) != -2 {
		return fail("existing Mercenary Base")
	}
	for _, c := range in.Helpers {
		v := portSingleValue(c.Timer)
		if c.Family != 1 || v < 0 || v >= 86400 {
			return fail("bounded helper-one TIMER")
		}
	}
	var warps [3001][6]int
	stats := EvolvedTailStats{InitialState: in.State}
	mercenaryCount := 0
	for s := 1; s <= 3000; s++ {
		force, owner := get(51+s, 81), get(51+s, 85)
		if force < 0 || force > 1000000 {
			return fail("bounded whole physical force")
		}
		if force > 0 {
			if owner != -2 && owner != -1 && owner != 0 {
				return fail("human or unknown defense owner")
			}
			stats.DesertionSectors = append(stats.DesertionSectors, s)
			if owner == -2 {
				stats.MercenaryForce += force
				mercenaryCount++
			}
		}
		if n := get(51+s, 129); n < 0 || n > 1000000 {
			return fail("bounded whole mine count")
		}
		if n := get(51+s, 93); n < -1 || n > 100 {
			return fail("bounded whole planet link")
		}
		for j := 0; j < 6; j++ {
			n := get(51+s, 41+4*j)
			if n < 0 || n > 3000 {
				return fail("bounded integer graph")
			}
			warps[s][j] = n
		}
	}
	if mercenaryCount > 1 || stats.MercenaryForce != 0 && stats.MercenaryForce != 37 && stats.MercenaryForce != 97525 {
		return fail("only absent/37/97525 Mercenary force admitted")
	}
	rng := qbrng.New(in.State)
	index := 0
	draw := func() float32 { stats.Draws++; return rng.Float32() }
	helper := func(caller uint16, bound int) (int, error) {
		if index >= len(in.Helpers) {
			return 0, fmt.Errorf("helper clock exhaustion")
		}
		c := in.Helpers[index]
		if c.Caller != caller {
			return 0, fmt.Errorf("helper chronology")
		}
		index++
		old := rng.State()
		rng.RandomizeMBF(c.Timer)
		stats.Seeds = append(stats.Seeds, ContinuationSeed{Clock: c, OldState: old, SeededState: rng.State()})
		return int(float32(draw()*float32(bound))) + 1, nil
	}
	for range stats.DesertionSectors {
		draw()
	}
	path := func(origin, target int) ([]int, bool) {
		var prev [3001]int
		prev[origin] = -1
		q := []int{origin}
		for i := 0; i < len(q) && prev[target] == 0; i++ {
			for _, n := range warps[q[i]] {
				if n != 0 && prev[n] == 0 {
					prev[n] = q[i]
					q = append(q, n)
				}
			}
		}
		if prev[target] == 0 {
			return nil, false
		}
		route := []int{target}
		for route[len(route)-1] != origin {
			route = append(route, prev[route[len(route)-1]])
		}
		for i, j := 0, len(route)-1; i < j; i, j = i+1, j-1 {
			route[i], route[j] = route[j], route[i]
		}
		return route, true
	}
	for origin := 3000; origin > 0; origin-- {
		force := get(51+origin, 81)
		if force <= 0 || get(51+origin, 85) != -2 {
			continue
		}
		if force != stats.MercenaryForce || len(stats.Activations) >= 16 {
			return fail("changed force or activation guard")
		}
		gate := draw()
		stats.MovementGateDraws++
		activation := MercenaryActivation{Origin: origin, Force: force, Gate: portSingleBytes(gate)}
		if get(51+origin, 93) > 0 {
			if gate < float32(.66) {
				activation.Held = true
				stats.Activations = append(stats.Activations, activation)
				continue
			}
			return fail("occupied-origin departure excluded")
		}
		// Original departure FAC residue differs from both cache and ordinary zeros.
		putraw(51+origin, 81, [4]byte{0, 0, 0x28, 0})
		putraw(51+origin, 85, [4]byte{0, 0, 0x28, 0})
		accepted := false
		target := 0
		for retry := 0; retry < 64; retry++ {
			n, e := helper(0x48cf, 3000)
			if e != nil {
				return fail(e.Error())
			}
			stats.TargetDraws++
			activation.Candidates = append(activation.Candidates, n)
			if n != origin {
				target = n
				accepted = true
				break
			}
		}
		if !accepted {
			return fail("same-origin rejection guard")
		}
		route, ok := path(origin, target)
		if !ok || len(route) < 2 {
			return fail("nonempty directed route required")
		}
		for _, s := range route[1:] {
			if get(51+s, 129) != 0 {
				return fail("mine encounter")
			}
			if get(51+s, 81) != 0 {
				return fail("merge/defense combat")
			}
			if get(51+s, 93) > 0 {
				return fail("planet stock pickup")
			}
		}
		put(51+target, 81, force)
		put(51+target, 85, -2)
		activation.Target = target
		activation.Route = route
		stats.Activations = append(stats.Activations, activation)
	}
	total := 0
	for s := 1; s <= 3000; s++ {
		if get(51+s, 81) > 0 && get(51+s, 85) == -2 {
			stats.FinalMercenarySectors = append(stats.FinalMercenarySectors, s)
			total += get(51+s, 81)
		}
	}
	if total != stats.MercenaryForce {
		return fail("Mercenary conservation")
	}
	lottery := draw()
	stats.Lottery = portSingleBytes(lottery)
	if lottery >= .5 {
		candidate, e := helper(0x53b4, 50)
		if e != nil {
			return fail(e.Error())
		}
		stats.Candidate = candidate + 1
		if get(stats.Candidate, 85) != 0 {
			return fail("named lottery candidate")
		}
	}
	if index != len(in.Helpers) {
		return fail("unconsumed tail helper clocks")
	}
	stats.FinalState = rng.State()
	return work, stats, nil
}
