package qbmaint

import (
	"bytes"
	"fmt"

	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// ContinuationClock binds a helper family (1 or 2), original caller and raw TIMER.
// It contains no captured RNG state or expected result.
type ContinuationClock struct {
	Family int
	Caller uint16
	Timer  [4]byte
}

// ContinuationInputs begins after planet economy and ends before Mercenary tail.
// Only the exact helper prefix for this phase is supplied; creation clocks and
// tail clocks have no representation in this existing-home API.
type ContinuationInputs struct {
	State   uint32
	Helpers []ContinuationClock
}

// ContinuationSeed records modeled reseeding, never a native endpoint correction.
type ContinuationSeed struct {
	Clock                 ContinuationClock
	OldState, SeededState uint32
}

// ContinuationRoute records source-derived activity and directed BFS traversal.
type ContinuationRoute struct {
	Group, Origin, Target, Fallback, Candidate, Preferred, Strength int
	CandidateDraws, InterceptionDraws                               int
	Route                                                           []int
}

// ContinuationStats describes only the existing-home/mobile phase.
type ContinuationStats struct {
	InitialState, FinalState                                                       uint32
	Draws, Allocations, TopFallback, WandererSector, BaseSector, XannoronIncrement int
	Cache                                                                          [20]MobileGroup
	Groups                                                                         [20]MobileGroup
	ClearedSectors, WandererAttempts                                               []int
	Seeds                                                                          []ContinuationSeed
	Routes                                                                         []ContinuationRoute
}

// ReplayExistingHomeContinuation preserves existing homes and normalizes mobile
// caches before peaceful routing on convergence days 307/308. It returns a new
// complete world at the pre-Mercenary boundary. Unknown homes, combat, exhausted
// clocks/guards or unconsumed clocks fail without output, statistics or mutation.
func ReplayExistingHomeContinuation(before []byte, in ContinuationInputs) ([]byte, ContinuationStats, error) {
	fail := func(s string) ([]byte, ContinuationStats, error) {
		return nil, ContinuationStats{}, fmt.Errorf("existing-home continuation: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff || len(in.Helpers) < 1 || len(in.Helpers) > 256 {
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
	number := func(r, o int) float64 { return portSingleValue(raw(r, o)) }
	putraw := func(r, o int, b [4]byte) { a := (r-1)*RecordSize + o; copy(work[a:a+4], b[:]) }
	put := func(r, o, n int) { putraw(r, o, encode(n)) }
	for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		if get(1, o) != n {
			return fail("default geometry")
		}
	}
	day := get(1, 81) + 1
	if day != 307 && day != 308 {
		return fail("post-economy existing-home day")
	}
	for r := 2; r <= 51; r++ {
		if number(r, 85) != 0 {
			return fail("active human player")
		}
	}
	for r := 3052; r <= 4051; r++ {
		if number(r, 89) != 0 {
			return fail("tax-funded hiring")
		}
	}
	if number(72, 105) != 0 {
		return fail("pending revenge")
	}
	names := map[int]string{4052: "The Wanderer", 4053: "Convergence Haven", 4150: "Mercenary Base", 4151: "Xannoron"}
	owners := map[int]int{4052: 0, 4053: -1, 4150: -2, 4151: -1}
	for r := 4052; r <= 4151; r++ {
		name, active := names[r]
		if !active {
			if number(r, 85) != 0 {
				return fail("unknown active planet")
			}
			continue
		}
		at := (r - 1) * RecordSize
		if get(r, 85) != len(name) || !bytes.Equal(work[at:at+41], append([]byte(name), bytes.Repeat([]byte{' '}, 41-len(name))...)) || get(r, 73) != owners[r] || get(r, 41) != day {
			return fail("existing named post-economy homes required")
		}
		if number(r, 117) < 0 || number(r, 117) > 33000000 {
			return fail("bounded existing bank")
		}
	}
	ground := get(4151, 77)
	if ground < 0 || ground > 1000000 {
		return fail("bounded whole Xannoron ground")
	}
	hq := get(1, 117)
	if hq < 8 || hq > 3000 || get(52, 105) != hq {
		return fail("tracked HQ")
	}
	var warps [3001][6]int
	links := map[int][]int{}
	total := 0
	for s := 1; s <= 3000; s++ {
		r := 51 + s
		force, owner, link, mine := get(r, 81), get(r, 85), get(r, 93), get(r, 129)
		if force < 0 || force > 10000 || force > 0 && owner != -1 {
			return fail("peaceful whole Xannor force")
		}
		total += force
		if link < -1 || link > 100 || link > 0 && link != 1 && link != 2 && link != 99 && link != 100 {
			return fail("known planet links")
		}
		if link > 0 {
			links[link] = append(links[link], s)
		}
		if mine < 0 || mine > 1000000 {
			return fail("bounded whole mine counts")
		}
		for j := 0; j < 6; j++ {
			n := get(r, 41+4*j)
			if n < 0 || n > 3000 {
				return fail("bounded integer warps")
			}
			warps[s][j] = n
		}
	}
	if total != 10000 || get(51+hq, 85) != -1 || get(51+hq, 81) < 1 {
		return fail("conserved physical HQ force")
	}
	for _, slot := range []int{1, 2, 99, 100} {
		if len(links[slot]) != 1 {
			return fail("one existing home link")
		}
	}
	if links[100][0] != hq {
		return fail("existing Xannoron at HQ")
	}
	for _, c := range in.Helpers {
		v := portSingleValue(c.Timer)
		if (c.Family != 1 && c.Family != 2) || v < 0 || v >= 86400 {
			return fail("typed bounded helper TIMER")
		}
	}
	stats := ContinuationStats{InitialState: in.State, BaseSector: links[99][0]}
	// Cache ownership is consumed once per physical sector, before pair cleanup.
	consumed := map[int]bool{}
	for g := 0; g < 20; g++ {
		s := get(52+g, 105)
		if s < 0 || s > 3000 {
			return fail("bounded group pointer")
		}
		stats.Cache[g].Sector = s
		if s > 0 && !consumed[s] && get(51+s, 85) == -1 {
			stats.Cache[g].Strength = get(51+s, 81)
			consumed[s] = true
			stats.ClearedSectors = append(stats.ClearedSectors, s)
		}
	}
	for i := 0; i < 19; i++ {
		for j := i + 1; j < 20; j++ {
			if stats.Cache[i].Sector == stats.Cache[j].Sector {
				stats.Cache[j].Sector = 0
				stats.Cache[i].Strength += stats.Cache[j].Strength
				stats.Cache[j].Strength = 0
			}
		}
	}
	cacheTotal := 0
	for i, c := range stats.Cache {
		if c.Sector < 1 || c.Strength < 1 {
			stats.Cache[i] = MobileGroup{}
		}
		cacheTotal += stats.Cache[i].Strength
	}
	if cacheTotal != 10000 || stats.Cache[0].Sector != hq || stats.Cache[0].Strength < 1 {
		return fail("complete conserved normalized cache")
	}
	rng := qbrng.New(in.State)
	index := 0
	draw := func(bound int) int { stats.Draws++; return int(float32(rng.Float32()*float32(bound))) + 1 }
	helper := func(family int, caller uint16, bound int) (int, error) {
		if index >= len(in.Helpers) || bound < 1 || bound > 10000 {
			return 0, fmt.Errorf("helper exhaustion or bound")
		}
		c := in.Helpers[index]
		if c.Family != family || c.Caller != caller {
			return 0, fmt.Errorf("helper chronology")
		}
		index++
		old := rng.State()
		rng.RandomizeMBF(c.Timer)
		stats.Seeds = append(stats.Seeds, ContinuationSeed{Clock: c, OldState: old, SeededState: rng.State()})
		n := draw(bound)
		if family == 2 {
			for j := 0; j < 3; j++ {
				n = draw(n)
			}
		}
		return n, nil
	}
	put(51+links[1][0], 93, 0)
	accepted := false
	for attempt := 0; attempt < 64; attempt++ {
		s, e := helper(1, 0x1f88, 3000)
		if e != nil {
			return fail(e.Error())
		}
		stats.WandererAttempts = append(stats.WandererAttempts, s)
		if get(51+s, 93) <= 0 {
			stats.WandererSector = s
			accepted = true
			break
		}
	}
	if !accepted {
		return fail("Wanderer placement guard")
	}
	put(51+stats.WandererSector, 93, 1)
	put(4052, 73, 0)
	if number(4052, 117) == 0 {
		put(4052, 117, 250000)
	}
	stats.Draws++
	stats.XannoronIncrement = int(float32(rng.Float32() * 25))
	put(4151, 77, ground+stats.XannoronIncrement)
	put(4151, 73, -1)
	if number(4151, 117) == 0 {
		put(4151, 117, 1000000)
	}
	top, e := helper(1, 0x26a8, 2993)
	if e != nil {
		return fail(e.Error())
	}
	stats.TopFallback = top + 7
	for g := 0; g < 20; g++ {
		put(52+g, 105, 0)
	}
	for _, s := range stats.ClearedSectors {
		putraw(51+s, 81, [4]byte{0, 0, 128, 0})
		putraw(51+s, 85, [4]byte{0, 0, 128, 0})
	}
	stats.Groups = stats.Cache
	remaining := stats.Cache[0].Strength
	preferred := 0
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
	for g := 1; g < 20; g++ {
		strength, origin := stats.Groups[g].Strength, stats.Groups[g].Sector
		if strength < 1 || origin < 1 {
			strength, e = helper(2, 0x31a3, remaining)
			if e != nil {
				return fail(e.Error())
			}
			remaining -= strength
			origin = hq
			stats.Allocations++
		}
		completed := false
		for activity := 0; activity < 64; activity++ {
			fallback := 0
			different := false
			for retry := 0; retry < 64; retry++ {
				fallback, e = helper(1, 0x320a, 3000)
				if e != nil {
					return fail(e.Error())
				}
				if fallback != origin {
					different = true
					break
				}
			}
			if !different {
				return fail("fallback rejection guard")
			}
			candidate, e := helper(1, 0x3284, 3000)
			if e != nil {
				return fail(e.Error())
			}
			if get(51+candidate, 81) > 1 && get(51+candidate, 85) != -1 || get(51+candidate, 93) > 1 {
				preferred = candidate
			}
			candidateDraws := 0
			if preferred == 0 {
				candidateDraws = 50
				for j := 0; j < 50; j++ {
					draw(1)
				}
			}
			target := fallback
			if preferred > 7 {
				target = preferred
			}
			if g == 19 {
				target = stats.TopFallback
			}
			route, ok := path(origin, target)
			if !ok {
				return fail("unreachable route")
			}
			scans := 0
			for _, s := range route[1:] {
				if get(51+s, 129) != 0 {
					return fail("entered mine encounter")
				}
				if get(51+s, 81) > 0 && get(51+s, 85) != 0 && get(51+s, 85) != -1 {
					return fail("foreign defense")
				}
				if slot := get(51+s, 93); slot > 0 && get(4051+slot, 85) != 0 && get(4051+slot, 73) != -1 {
					return fail("entered planet combat")
				}
				for j := 0; j < 50; j++ {
					draw(1)
				}
				scans += 50
			}
			stats.Routes = append(stats.Routes, ContinuationRoute{Group: g + 1, Origin: origin, Target: target, Fallback: fallback, Candidate: candidate, Preferred: preferred, Strength: strength, CandidateDraws: candidateDraws, InterceptionDraws: scans, Route: route})
			origin = target
			if strength == 0 {
				origin = 0
			}
			if !(origin > 0 && origin < 8 && strength > 0) {
				completed = true
				break
			}
		}
		if !completed {
			return fail("protected-sector activity guard")
		}
		stats.Groups[g] = MobileGroup{origin, strength}
	}
	stats.Groups[0].Strength = remaining
	if stats.Groups[19].Strength > 0 {
		s := stats.Groups[19].Sector
		put(51+s, 129, get(51+s, 129)+1)
	}
	groupTotal := 0
	for g, item := range stats.Groups {
		put(52+g, 105, item.Sector)
		if item.Strength > 0 {
			put(51+item.Sector, 81, get(51+item.Sector, 81)+item.Strength)
			put(51+item.Sector, 85, -1)
		}
		groupTotal += item.Strength
	}
	if groupTotal != 10000 {
		return fail("group conservation")
	}
	if index != len(in.Helpers) {
		return fail("unconsumed phase helper clocks")
	}
	stats.FinalState = rng.State()
	return work, stats, nil
}
