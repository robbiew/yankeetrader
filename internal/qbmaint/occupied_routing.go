package qbmaint

import (
	"bytes"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// OccupiedRoutingInputs begins after ordinary economy and supplies only modeled
// state, source-labelled helper clocks and missing-home creation clocks.
type OccupiedRoutingInputs struct {
	State    uint32
	Helpers  []ContinuationClock
	Creation ConvergenceCreationClocks
}

// OccupiedCombatEvent preserves source event order and the derived primitive receipt.
type OccupiedCombatEvent struct {
	Kind          string
	Group, Sector int
	Defense       *ForeignDefenseStats
	Ground        *NeutralGroundStats
}

// OccupiedRoutingStats contains calculated traversal, combat and home receipts.
// Entered is the actually traversed prefix for each planned Route.
type OccupiedRoutingStats struct {
	ContinuationStats
	Entered [][]int
	Events  []OccupiedCombatEvent
}

// ReplayOccupiedHomeMobile runs the retained initial occupied-world phase from
// modeled post-economy bytes through home restoration/mobile combat/Base birth.
// It has no tail/news/score writes. Historical convergence APIs remain strict.
// Unknown contexts or late exhausted clocks return no partial world/statistics.
func ReplayOccupiedHomeMobile(before []byte, in OccupiedRoutingInputs) ([]byte, OccupiedRoutingStats, error) {
	fail := func(s string) ([]byte, OccupiedRoutingStats, error) {
		return nil, OccupiedRoutingStats{}, fmt.Errorf("occupied routing: %s", s)
	}
	c := in.Creation
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff || len(in.Helpers) < 1 || len(in.Helpers) > 256 || c.WandererDay != 306 || c.XannoronDay != 306 || c.BaseDay != 306 {
		return fail("bounded world/state/source clocks")
	}
	seconds := portSingleValue(c.XannoronTimer)
	if seconds < 0 || seconds >= 86400 || seconds > 0 && seconds < portSingleValue([4]byte{0x0a, 0xd7, 0x23, 0x7a}) {
		return fail("bounded creation TIMER")
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
	for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151, 81: 305} {
		if get(1, o) != n {
			return fail("default geometry/day")
		}
	}
	for r := 2; r <= 51; r++ {
		if number(r, 85) != 0 {
			return fail("active humans")
		}
	}
	for r := 3052; r <= 4051; r++ {
		if number(r, 89) != 0 {
			return fail("tax-funded hiring")
		}
	}
	if get(72, 105) != 0 {
		return fail("pending revenge")
	}
	hq := get(1, 117)
	if hq < 8 || hq > 3000 || get(52, 105) != hq || get(51+hq, 81) != 10000 || get(51+hq, 85) != -1 {
		return fail("tracked initial HQ")
	}
	for g := 1; g < 20; g++ {
		if get(52+g, 105) != 0 {
			return fail("initial mobile pointers")
		}
	}
	var warps [3001][6]int
	links := map[int][]int{}
	for s := 1; s <= 3000; s++ {
		r := 51 + s
		force, owner, link := get(r, 81), get(r, 85), get(r, 93)
		if s != hq && force != 0 && (s != 854 || (force != 37 && force != 100000) || (owner != 0 && owner != -2)) {
			return fail("bounded foreign/neutral physical defense")
		}
		if s != hq && force > 0 && owner == 0 && force != 37 {
			return fail("only retained 37 neutral fighters")
		}
		if get(r, 129) != 0 {
			return fail("mines outside occupied profile")
		}
		if link < 0 || link > 3 || link == 1 {
			return fail("ordinary slot2/3 references")
		}
		if link > 0 {
			links[link] = append(links[link], s)
		}
		for j := 0; j < 6; j++ {
			n := get(r, 41+4*j)
			if n < 0 || n > 3000 {
				return fail("bounded integer warps")
			}
			warps[s][j] = n
		}
	}
	if get(51+hq, 93) != 0 {
		return fail("missing HQ home")
	}
	for r := 4052; r <= 4151; r++ {
		if number(r, 85) == 0 {
			if r == 4053 || r == 4054 {
				if len(links[r-4051]) != 0 {
					return fail("stale ordinary link")
				}
			}
			continue
		}
		if r != 4053 && r != 4054 {
			return fail("only ordinary slots2/3 active")
		}
		at := (r - 1) * RecordSize
		n := get(r, 85)
		if n < 1 || n > 41 {
			return fail("planet name length")
		}
		title := string(work[at : at+n])
		if title != "Occupied Haven" && title != "Second Haven" && title != "Route Haven" {
			return fail("named ordinary planet")
		}
		if !bytes.Equal(work[at:at+41], []byte(fmt.Sprintf("%-41s", title))) || get(r, 41) != 306 || get(r, 77) != 505000 || (get(r, 73) != -1 && !(title == "Route Haven" && get(r, 73) == 0)) || len(links[r-4051]) != 1 {
			return fail("post-economy ordinary context")
		}
		for _, o := range []int{45, 49, 53} {
			if number(r, o) != 1010 {
				return fail("post-economy rates")
			}
		}
		for _, o := range []int{57, 61, 65} {
			if v := number(r, o); v < 1000 || v >= 1001 {
				return fail("post-economy cargo")
			}
		}
		if v := number(r, 129); v < 3000 || v >= 3001 {
			return fail("post-economy fighter stock")
		}
		if v := number(r, 69); v < 1 || v >= 1.001 {
			return fail("post-economy missiles")
		}
		if v := number(r, 89); v < 0 || v >= 1 {
			return fail("post-economy TIMER")
		}
		for _, o := range []int{81, 93, 97, 101, 105, 109, 113, 117, 121, 125, 133} {
			if number(r, o) != 0 {
				return fail("ordinary reserved/empty fields")
			}
		}
	}
	for _, clock := range in.Helpers {
		v := portSingleValue(clock.Timer)
		if (clock.Family != 1 && clock.Family != 2) || v < 0 || v >= 86400 {
			return fail("typed helper TIMER")
		}
	}
	birth := ConvergenceDayOneInputs{State: in.State, WandererDay: c.WandererDay, XannoronDay: c.XannoronDay, BaseDay: c.BaseDay, XannoronTimer: c.XannoronTimer, Helpers: in.Helpers}
	stats := OccupiedRoutingStats{ContinuationStats: ContinuationStats{InitialState: in.State, Births: &ConvergenceBirthStats{Created: [3]string{"wanderer", "xannoron", "base"}}}}
	stats.Cache[0] = MobileGroup{Sector: hq, Strength: 10000}
	stats.ClearedSectors = []int{hq}
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
	restoreConvergenceWanderer(work, birth.WandererDay)
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
	g, bank, stamp, err := restoreConvergenceXannoron(work, birth, hq, rng)
	if err != nil {
		return fail(err.Error())
	}
	stats.Draws += 2
	stats.Births.InitialGround = g
	stats.Births.Bank = bank
	stats.Births.Timestamp = stamp

	stats.Draws++
	stats.XannoronIncrement = int(float32(rng.Float32() * 25))
	put(4151, 77, stats.Births.InitialGround+stats.XannoronIncrement)
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
			entered := []int{}
			for _, sector := range route[1:] {
				entered = append(entered, sector)
				if get(51+sector, 129) != 0 {
					return fail("entered mine encounter")
				}
				if get(51+sector, 81) > 0 && get(51+sector, 85) != 0 && get(51+sector, 85) != -1 {
					next, event, err := ReplayForeignDefense(work, ForeignDefenseInputs{Group: g + 1, Sector: sector, Force: strength, State: rng.State()})
					if err != nil {
						return fail(err.Error())
					}
					work = next
					rng = qbrng.New(event.FinalState)
					stats.Draws += event.Draws
					stats.Events = append(stats.Events, OccupiedCombatEvent{Kind: "defense", Group: g + 1, Sector: sector, Defense: &event})
					strength = event.Force
					if event.PreferredCleared {
						preferred = 0
					}
					if strength == 0 {
						preferred = sector
						break
					}
				}
				if slot := get(51+sector, 93); slot > 0 && get(4051+slot, 85) != 0 && get(4051+slot, 73) != -1 {
					next, event, err := ReplayNeutralGroundAssault(work, NeutralGroundInputs{Group: g + 1, Sector: sector, Force: strength, State: rng.State()})
					if err != nil {
						return fail(err.Error())
					}
					work = next
					rng = qbrng.New(event.FinalState)
					stats.Draws += event.Draws
					stats.Events = append(stats.Events, OccupiedCombatEvent{Kind: "planet", Group: g + 1, Sector: sector, Ground: &event})
					strength = event.Force
					preferred = sector
					if strength == 0 {
						break
					}
				}
				for j := 0; j < 50; j++ {
					draw(1)
				}
				scans += 50
			}
			stats.Entered = append(stats.Entered, entered)
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
	losses := 0
	for _, event := range stats.Events {
		if event.Defense != nil {
			losses += event.Defense.InitialForce - event.Defense.Force
		} else {
			losses += event.Ground.InitialForce - event.Ground.Force
		}
	}
	if groupTotal != 10000-losses {
		return fail("group conservation")
	}
	restoreConvergenceBase(work, birth.BaseDay)
	accepted = false
	for attempt := 0; attempt < 64; attempt++ {
		sector, err := helper(1, 0x437a, 3000)
		if err != nil {
			return fail(err.Error())
		}
		stats.Births.BaseAttempts = append(stats.Births.BaseAttempts, sector)
		if get(51+sector, 93) <= 0 {
			stats.BaseSector = sector
			put(51+sector, 93, 99)
			accepted = true
			break
		}
	}
	if !accepted {
		return fail("Base placement guard")
	}

	if index != len(in.Helpers) {
		return fail("unconsumed phase helper clocks")
	}
	stats.FinalState = rng.State()
	return work, stats, nil
}
