package game

import (
	"errors"
	"math"
	"math/rand"
	"time"
)

// NewWithGeneration independently selects port and warp rules for a new world.
// The legacy graph and existing saved worlds are never retroactively regenerated.
func NewWithGeneration(now time.Time, seed int64, count int, ports, warps string) (*World, error) {
	if warps != "" && warps != "dos" {
		return nil, errors.New("unknown warp generation profile")
	}
	w, err := NewWithPortGeneration(now, seed, count, ports)
	if err != nil {
		return nil, err
	}
	if warps == "" {
		return w, nil
	}
	rng := rand.New(rand.NewSource(seed))
	table, err := generateDOSWarpTable(count, rng)
	if err != nil {
		return nil, err
	}
	if err = repairDOSWarps(table, rng); err != nil {
		return nil, err
	}
	if err = shortcutDOSWarps(table, rng); err != nil {
		return nil, err
	}
	if !dosGraphConnected(table, false) || !dosGraphConnected(table, true) {
		return nil, errors.New("generated DOS warp graph is not Earth-connected")
	}
	for id := 1; id <= count; id++ {
		links := make([]int, 0, 6)
		for _, to := range table[id] {
			// DOS retains Earth1->1. Dropping this redundant edge preserves the modern
			// no-self-warp invariant. Skip holes without changing relative slot order.
			if to != 0 && to != id && !contains(links, to) {
				links = append(links, to)
			}
		}
		w.Sectors[id].Warps = links
	}
	w.WarpGeneration = warps
	return w, w.Validate()
}

// Repair follows the original ascending-target BFS and persistent reached set.
// Select uniformly from eligible earlier free sixth slots rather than unbounded
// rejection. An exhausted repair slot pool fails the unpublished candidate.
func repairDOSWarps(table dosWarpTable, rng *rand.Rand) error {
	seen := make([]bool, len(table))
	for target := 2; target < len(table); target++ {
		if seen[target] {
			continue
		}
		reached := make([]bool, len(table))
		reached[1] = true
		queue := []int{1}
		for head := 0; head < len(queue) && !reached[target]; head++ {
			for _, to := range table[queue[head]] {
				if to == 0 || reached[to] {
					continue
				}
				reached[to] = true
				seen[to] = true
				queue = append(queue, to)
			}
		}
		if reached[target] {
			continue
		}
		choices := []int{}
		for source := 1; source < target; source++ {
			if table[source][5] == 0 {
				choices = append(choices, source)
			}
		}
		if len(choices) == 0 {
			return errors.New("DOS warp repair has no earlier free sixth slot")
		}
		source := choices[rng.Intn(len(choices))]
		table[source][5] = target
		table[target][5] = source
	}
	return nil
}

// DOS uses single-precision cumulative random steps, not per-sector chances.
// The bounded draw budget also terminates a pathological stream of zero steps.
func shortcutDOSWarps(table dosWarpTable, rng *rand.Rand) error {
	x := float32(8) + float32(400*float32(rng.Float64()))
	for draws := 0; x < float32(len(table)-1); draws++ {
		if draws >= 32*len(table) {
			return errors.New("DOS Earth shortcut draw budget exhausted")
		}
		// Five native controls establish nearest conversion, positive halves up.
		index := int(math.Floor(float64(x) + .5))
		if index > 1 && index < len(table) && table[index][5] == 0 {
			table[index][5] = 1
		}
		x = float32(x + float32(400*float32(rng.Float64())))
	}
	return nil
}

func dosGraphConnected(table dosWarpTable, reverse bool) bool {
	links := make([][]int, len(table))
	for from := 1; from < len(table); from++ {
		for _, to := range table[from] {
			if to < 0 || to >= len(table) {
				return false
			}
			if to == 0 {
				continue
			}
			if reverse {
				links[to] = append(links[to], from)
			} else {
				links[from] = append(links[from], to)
			}
		}
	}
	seen := make([]bool, len(table))
	seen[1] = true
	queue := []int{1}
	for head := 0; head < len(queue); head++ {
		for _, to := range links[queue[head]] {
			if !seen[to] {
				seen[to] = true
				queue = append(queue, to)
			}
		}
	}
	return len(queue) == len(table)-1
}
