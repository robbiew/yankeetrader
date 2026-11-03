package game

import (
	"errors"
	"fmt"
	"math/rand"
)

// dosWarpTable preserves the initializer's six int16-like columns while the
// graph is being constructed. Index zero is unused; zero slot values are empty.
// The DOS layout uses DS185a + 2*(column*3001 + sector).
type dosWarpTable [][6]int

const dosWarpRowAttempts = 128

func (table dosWarpTable) hasWarp(from, to int) bool {
	for _, value := range table[from] {
		if value == to {
			return true
		}
	}
	return false
}
func (table dosWarpTable) populated(sector int) bool {
	for _, to := range table[sector] {
		if to != 0 {
			return true
		}
	}
	return false
}

// tryDOSLocalWarp implements the matching-column and both-direction duplicate
// tests from initializer 0f2a..1067. The caller selects a positive offset1..10;
// the final ten sectors reverse direction. Out-of-range candidates in modern
// small test universes are skipped instead of indexing outside the table.
func tryDOSLocalWarp(table dosWarpTable, sector, column, offset int) bool {
	count := len(table) - 1
	if sector < 1 || sector > count || column < 0 || column >= 5 || offset < 1 || offset > 10 {
		return false
	}
	to := sector + offset
	if sector > count-10 {
		to = sector - offset
	}
	if to < 1 || to > count || table[sector][column] != 0 || table[to][column] != 0 || table.hasWarp(sector, to) || table.hasWarp(to, sector) {
		return false
	}
	table[sector][column] = to
	table[to][column] = sector
	return true
}

// tryDOSLongWarp uses only the final column. Unlike DOS's 10b4..113a branch,
// reject an existing pair in another column as well, preventing duplicate exits.
func tryDOSLongWarp(table dosWarpTable, sector, to int) bool {
	count := len(table) - 1
	if sector < 1 || sector > count || to < 1 || to > count || to == sector || table[sector][5] != 0 || table[to][5] != 0 || table.hasWarp(sector, to) || table.hasWarp(to, sector) {
		return false
	}
	table[sector][5] = to
	table[to][5] = sector
	return true
}

func generateDOSWarpTable(count int, rng *rand.Rand) (dosWarpTable, error) {
	if count < 8 || count > 3000 || rng == nil {
		return nil, errors.New("DOS-style warps require 8..3000 sectors and a seeded RNG")
	}
	table := make(dosWarpTable, count+1)
	// 0e0b..0e6f: preserve the original self-warp in this intermediate table.
	// The final graph adapter decides how to handle the modern no-self-warp policy.
	for column := 0; column < 6; column++ {
		to := column + 1
		table[1][column] = to
		table[to][column] = 1
	}
	for sector := 1; sector <= count; sector++ {
		for attempt := 0; attempt < dosWarpRowAttempts; attempt++ {
			attemptDOSWarpRow(table, sector, rng)
			if table.populated(sector) {
				break
			}
		}
		if !table.populated(sector) && !forceDOSLocalWarp(table, sector) {
			return nil, fmt.Errorf("no free nearby matching warp column for sector %d", sector)
		}
	}
	return table, nil
}

// attemptDOSWarpRow preserves slot order and the otherwise-unused first draw
// in the long column. Rejected self-targets retry the long chance gate as in
// DOS, with a finite bound so a pathological RNG cannot trap generation.
func attemptDOSWarpRow(table dosWarpTable, sector int, rng *rand.Rand) {
	for column := 0; column < 6; column++ {
		if rng.Float64() <= float64(float32(.4)) && column < 5 {
			tryDOSLocalWarp(table, sector, column, rng.Intn(10)+1)
		}
		if column == 5 && table[sector][5] == 0 {
			for attempt := 0; attempt < dosWarpRowAttempts; attempt++ {
				if rng.Float64() < float64(float32(.985)) {
					break
				}
				to := rng.Intn(len(table)-1) + 1
				if to == sector {
					continue
				}
				tryDOSLongWarp(table, sector, to)
				break
			}
		}
	}
}

// DOS's 11c7..1209 retries an empty row indefinitely. Bound that retry and use a
// deterministic nearby reciprocal pair when random attempts never connect it.
// This fallback is an explicit modern safety correction, not a recovered draw.
func forceDOSLocalWarp(table dosWarpTable, sector int) bool {
	count := len(table) - 1
	for distance := 1; distance <= 10; distance++ {
		for _, to := range []int{sector - distance, sector + distance} {
			if to < 1 || to > count || table.hasWarp(sector, to) || table.hasWarp(to, sector) {
				continue
			}
			for column := 0; column < 5; column++ {
				if table[sector][column] == 0 && table[to][column] == 0 {
					table[sector][column] = to
					table[to][column] = sector
					return true
				}
			}
		}
	}
	return false
}
