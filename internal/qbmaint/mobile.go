package qbmaint

import (
	"fmt"

	"github.com/robbiew/yankeetrader/internal/qbmbf"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// MobileInputs supplies the post-Xannoron RNG state and the next 39 helper-one
// and 19 helper-two TIMER samples. It contains no observed output or patches.
type MobileInputs struct {
	State     uint32
	HelperOne [39][4]byte
	HelperTwo [19][4]byte
}
type MobileGroup struct{ Sector, Strength int }
type MobileStats struct {
	Groups             [20]MobileGroup
	TopFallback, Draws int
	FinalState         uint32
}

// ReplayInitialMobileGroups admits only the default initial 10000-force HQ,
// inactive players, two initial planets and plain, reachable
// routes. Retries, encounters, existing groups and regeneration are excluded.
// It preserves unrelated bytes and returns no partial output on rejection.
func ReplayInitialMobileGroups(before []byte, in MobileInputs) ([]byte, MobileStats, error) {
	out, stats, _, err := replayInitialMobileGroups(before, in, false)
	return out, stats, err
}

// WandererEncounter is a model-derived receipt, never an input correction.
type WandererEncounter struct {
	Inputs AssaultInputs
	Result AssaultStats
}
type WandererMobileStats struct {
	MobileStats
	Encounters []WandererEncounter
}

// ReplayInitialMobileGroupsWithWanderer explicitly admits the retained late-clock
// neutral Wanderer chain as well as ordinary plain routes. The strict API above
// continues rejecting encounters. Partial or other combat chains are excluded.
func ReplayInitialMobileGroupsWithWanderer(before []byte, in MobileInputs) ([]byte, WandererMobileStats, error) {
	out, stats, events, err := replayInitialMobileGroups(before, in, true)
	if err != nil {
		return nil, WandererMobileStats{}, err
	}
	return out, WandererMobileStats{MobileStats: stats, Encounters: events}, nil
}
func replayInitialMobileGroups(before []byte, in MobileInputs, allowWanderer bool) ([]byte, MobileStats, []WandererEncounter, error) {
	fail := func(s string) ([]byte, MobileStats, []WandererEncounter, error) {
		return nil, MobileStats{}, nil, fmt.Errorf("initial mobile groups: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff {
		return fail("world/state extent")
	}
	source := before
	read := func(r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(source[a : a+4]) }
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
	hq := get(1, 117)
	if hq < 8 || hq > 3000 || get(52, 105) != hq {
		return fail("HQ")
	}
	for r := 2; r <= 51; r++ {
		if read(r, 85)[3] != 0 {
			return fail("inactive players required")
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
			return fail("initial planet activity")
		}
	}
	if string(before[4051*RecordSize:4051*RecordSize+12]) != "The Wanderer" || string(before[4150*RecordSize:4150*RecordSize+8]) != "Xannoron" || get(4151, 73) != -1 {
		return fail("birth prefix")
	}
	// Sector 21 carries a pending player ID, independently of player activity.
	if read(72, 105)[3] != 0 {
		return fail("pending revenge outside ordinary initial profile")
	}
	var warps [3001][6]int
	links := 0
	for s := 1; s <= 3000; s++ {
		r := 51 + s
		force := 0
		if s == hq {
			force = 10000
		}
		if get(r, 81) != force {
			return fail("initial forces")
		}
		if s == hq && get(r, 85) != -1 {
			return fail("HQ owner")
		}
		link := get(r, 93)
		if s == hq {
			if link != 100 {
				return fail("HQ link")
			}
		} else if link == 1 {
			links++
		} else if link != 0 {
			return fail("planet links")
		}
		if read(r, 89)[3] != 0 || read(r, 129)[3] != 0 {
			return fail("hazards")
		}
		if s >= 2 && s <= 20 && read(r, 105)[3] != 0 {
			return fail("existing mobile group")
		}
		for i := 0; i < 6; i++ {
			n := get(r, 41+i*4)
			if n < 0 || n > 3000 {
				return fail("warp")
			}
			warps[s][i] = n
		}
	}
	if links != 1 {
		return fail("Wanderer link")
	}
	for _, ts := range in.HelperOne {
		if qbmbf.SignZeroSingle(ts).Carry || !qbmbf.CompareSingle(ts, encode(86400)).Carry {
			return fail("helper TIMER")
		}
	}
	for _, ts := range in.HelperTwo {
		if qbmbf.SignZeroSingle(ts).Carry || !qbmbf.CompareSingle(ts, encode(86400)).Carry {
			return fail("helper TIMER")
		}
	}
	work := append([]byte(nil), before...)
	source = work
	put := func(r, o, n int) { a := (r-1)*RecordSize + o; v := encode(n); copy(work[a:a+4], v[:]) }
	put(51+hq, 81, 0)
	put(51+hq, 85, 0)
	var encounters []WandererEncounter
	preferred := 0
	rng := qbrng.New(in.State)
	stats := MobileStats{}
	draw := func(n int) int { stats.Draws++; return int(float32(rng.Float32()*float32(n))) + 1 }
	oneIndex := 0
	one := func(n int) int { rng.RandomizeMBF(in.HelperOne[oneIndex]); oneIndex++; return draw(n) }
	stats.TopFallback = one(2993) + 7
	remaining := 10000
	for g := 1; g < 20; g++ {
		if remaining <= 0 {
			return fail("zero-bound allocation")
		}
		rng.RandomizeMBF(in.HelperTwo[g-1])
		strength := remaining
		for j := 0; j < 4; j++ {
			strength = draw(strength)
		}
		remaining -= strength
		fallback := one(3000)
		if fallback == hq {
			return fail("fallback retry")
		}
		candidate := one(3000)
		if get(51+candidate, 81) > 1 && get(51+candidate, 85) != -1 || get(51+candidate, 93) > 1 {
			return fail("candidate rejection")
		}
		if preferred == 0 {
			for j := 0; j < 50; j++ {
				draw(1)
			}
		}
		target := fallback
		if preferred != 0 {
			target = preferred
		}
		if g == 19 {
			target = stats.TopFallback
		}
		if target < 8 {
			return fail("protected target outside profile")
		}
		// Original column-order directed BFS. At most 3000 nodes are visited.
		var prev [3001]int
		prev[hq] = -1
		queue := []int{hq}
		for i := 0; i < len(queue) && prev[target] == 0; i++ {
			for _, n := range warps[queue[i]] {
				if n != 0 && prev[n] == 0 {
					prev[n] = queue[i]
					queue = append(queue, n)
				}
			}
		}
		if prev[target] == 0 {
			return fail("unreachable target")
		}
		route := []int{}
		for s := target; s != hq; s = prev[s] {
			route = append(route, s)
		}
		for j := len(route) - 1; j >= 0; j-- {
			sector := route[j]
			if get(51+sector, 93) != 0 || get(51+sector, 89) != 0 || get(51+sector, 129) != 0 {
				if !allowWanderer {
					return fail("entered encounter")
				}
				input := AssaultInputs{Group: g + 1, Sector: sector, Force: strength, State: rng.State()}
				updated, result, err := ReplayWandererAssault(work, input)
				if err != nil {
					return fail("unsupported entered encounter: " + err.Error())
				}
				work = updated
				source = work
				rng = qbrng.New(result.FinalState)
				stats.Draws += result.Draws
				encounters = append(encounters, WandererEncounter{Inputs: input, Result: result})
				preferred = sector
				strength = 0
				break // skip this sector's scans and all later edges
			}
			for k := 0; k < 50; k++ {
				draw(1)
			}
		}
		if strength == 0 {
			stats.Groups[g] = MobileGroup{}
		} else {
			stats.Groups[g] = MobileGroup{target, strength}
		}
	}
	stats.Groups[0] = MobileGroup{hq, remaining}
	seen := map[int]bool{}
	for _, g := range stats.Groups {
		if g.Strength == 0 && g.Sector == 0 && allowWanderer {
			continue
		}
		if g.Strength <= 0 || seen[g.Sector] {
			return fail("zero or merged group")
		}
		seen[g.Sector] = true
	}
	if len(encounters) != 0 {
		if len(encounters) != 18 {
			return fail("partial Wanderer chain outside retained profile")
		}
		for i, event := range encounters {
			if event.Inputs.Group != i+2 || event.Inputs.Sector != encounters[0].Inputs.Sector {
				return fail("ordinary groups 2..19 must share the retained pursuit")
			}
		}
	}
	out := work
	for g, item := range stats.Groups {
		put(52+g, 105, item.Sector)
		if item.Strength == 0 {
			continue
		}
		put(51+item.Sector, 81, item.Strength)
		put(51+item.Sector, 85, -1)
	}
	put(51+stats.Groups[19].Sector, 129, 1)
	if len(encounters) > 0 {
		lost, err := retainedWandererLosses(out, encounters)
		if err != nil {
			return fail(err.Error())
		}
		total := lost
		for _, group := range stats.Groups {
			total += group.Strength
		}
		if total != 10000 {
			return fail("encounter force conservation")
		}
	}
	stats.FinalState = rng.State()
	return out, stats, encounters, nil
}
