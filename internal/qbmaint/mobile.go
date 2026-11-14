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
	fail := func(s string) ([]byte, MobileStats, error) {
		return nil, MobileStats{}, fmt.Errorf("initial mobile groups: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.State > 0xffffff {
		return fail("world/state extent")
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
		for j := 0; j < 50; j++ {
			draw(1)
		}
		target := fallback
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
		for s := target; s != hq; s = prev[s] {
			if get(51+s, 93) != 0 || get(51+s, 89) != 0 || get(51+s, 129) != 0 {
				return fail("entered encounter")
			}
			for j := 0; j < 50; j++ {
				draw(1)
			}
		}
		stats.Groups[g] = MobileGroup{target, strength}
	}
	stats.Groups[0] = MobileGroup{hq, remaining}
	seen := map[int]bool{}
	for _, g := range stats.Groups {
		if g.Strength <= 0 || seen[g.Sector] {
			return fail("zero or merged group")
		}
		seen[g.Sector] = true
	}
	out := append([]byte(nil), before...)
	put := func(r, o, n int) { a := (r-1)*RecordSize + o; v := encode(n); copy(out[a:a+4], v[:]) }
	put(51+hq, 81, 0)
	put(51+hq, 85, 0)
	for g, item := range stats.Groups {
		put(52+g, 105, item.Sector)
		put(51+item.Sector, 81, item.Strength)
		put(51+item.Sector, 85, -1)
	}
	put(51+stats.Groups[19].Sector, 129, 1)
	stats.FinalState = rng.State()
	return out, stats, nil
}
