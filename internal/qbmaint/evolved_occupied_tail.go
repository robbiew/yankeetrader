package qbmaint

import (
	"bytes"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// EvolvedMercenaryBattle records the selected unit-offense phase at its sector.
type EvolvedMercenaryBattle struct {
	Sector int
	GatewayVictoryBattle
}

// EvolvedOccupiedTailStats keeps initial inventory, capped losses and saved force
// distinct. Activation Force follows this profile's source post-encounter stamp.
type EvolvedOccupiedTailStats struct {
	EvolvedTailStats
	FinalForce, Losses int
	Battles            []EvolvedMercenaryBattle
}

// ReplayEvolvedOccupiedTail derives the retained child Mercenary scan, selected
// unit victory and inactive lottery from modeled state and suffix helper clocks.
// It does not publish metadata or reports; unsupported paths fail atomically.
func ReplayEvolvedOccupiedTail(before []byte, in EvolvedTailInputs) ([]byte, EvolvedOccupiedTailStats, error) {
	fail := func(s string) ([]byte, EvolvedOccupiedTailStats, error) {
		return nil, EvolvedOccupiedTailStats{}, fmt.Errorf("evolved occupied tail: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff || len(in.Helpers) > 256 {
		return fail("world/state/clock extent")
	}
	work := bytes.Clone(before)
	day, ok := integer([4]byte(before[81:85]))
	if !ok || (day != 306 && day != 307) {
		return fail("child days 307/308")
	}

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
	stats := EvolvedOccupiedTailStats{EvolvedTailStats: EvolvedTailStats{InitialState: in.State}}
	mercenaryCount := 0
	xannor, neutral := 0, 0
	for s := 1; s <= 3000; s++ {
		force, owner := get(51+s, 81), get(51+s, 85)
		if force < 0 || force > 1000000 {
			return fail("bounded whole physical force")
		}
		if force > 0 {
			if owner != -2 && owner != -1 && owner != 0 {
				return fail("human or unknown defense owner")
			}
			if owner == -1 {
				xannor += force
			}
			if owner == 0 {
				neutral += force
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
	if xannor > 10000 || neutral > 37 {
		return fail("bounded faction totals")
	}
	if mercenaryCount > 1 || stats.MercenaryForce != 0 && stats.MercenaryForce != 97525 {
		return fail("only absent/97525 Mercenary force admitted")
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
		if origin < 8 {
			return fail("non-Union Mercenary origin")
		}
		if force != stats.MercenaryForce-stats.Losses || len(stats.Activations) >= 16 {
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
				if s != 109 || get(160, 81) != 182 || get(160, 85) != -1 || get(160, 93) != 0 || force != 97525 || len(stats.Battles) != 0 {
					return fail("only retained unit Mercenary victory")
				}
				b := EvolvedMercenaryBattle{Sector: s, GatewayVictoryBattle: GatewayVictoryBattle{InitialState: rng.State(), InitialForce: force, InitialDefenders: 182, Gate: portSingleBytes(draw())}}
				remaining := 182
				for force > 0 && remaining > 0 {
					if b.Rounds >= 200000 {
						return fail("battle guard")
					}
					if draw() < .5 {
						remaining--
					} else {
						force--
					}
					b.Rounds++
				}
				b.Force = force
				b.Defenders = remaining
				b.Losses = b.InitialForce - force
				b.DefenderLosses = 182 - remaining
				b.Draws = b.Rounds + 1
				b.FinalState = rng.State()
				if force <= 0 || remaining != 0 {
					return fail("qualified surviving victory required")
				}
				stats.Losses += b.Losses
				stats.Battles = append(stats.Battles, b)
				put(160, 81, 0)
				put(160, 85, 0)
			}
			if get(51+s, 93) > 0 {
				return fail("planet stock pickup")
			}
		}
		put(51+target, 81, force)
		put(51+target, 85, -2)
		activation.Force = force // Python/source row reports post-encounter moving force.
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
	if total+stats.Losses != stats.MercenaryForce {
		return fail("Mercenary conservation")
	}
	stats.FinalForce = total
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
