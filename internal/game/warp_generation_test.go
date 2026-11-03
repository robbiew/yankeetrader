package game

import (
	"math"
	"math/rand"
	"reflect"
	"testing"
)

func TestDOSLocalWarpMatchingColumnsBoundariesAndDuplicates(t *testing.T) {
	table := make(dosWarpTable, 33)
	if !tryDOSLocalWarp(table, 22, 3, 10) || table[22][3] != 32 || table[32][3] != 22 {
		t.Fatal("N-10 must still point forward", table[22], table[32])
	}
	if !tryDOSLocalWarp(table, 23, 2, 10) || table[23][2] != 13 || table[13][2] != 23 {
		t.Fatal("last ten sectors must reverse", table[23], table[13])
	}
	if tryDOSLocalWarp(table, 22, 1, 10) || table[22][1] != 0 {
		t.Fatal("cross-column duplicate allowed")
	}
	table[1][1] = 2
	if tryDOSLocalWarp(table, 1, 1, 5) {
		t.Fatal("occupied origin slot replaced")
	}
	table[9][0] = 8
	if tryDOSLocalWarp(table, 4, 0, 5) {
		t.Fatal("occupied target slot replaced")
	}
	if tryDOSLocalWarp(table, 4, 5, 1) {
		t.Fatal("local warp used reserved long column")
	}
	small := make(dosWarpTable, 9)
	if tryDOSLocalWarp(small, 1, 0, 10) {
		t.Fatal("small-world negative target allowed")
	}
}
func TestDOSLongWarpFinalColumnAndDuplicateCorrection(t *testing.T) {
	table := make(dosWarpTable, 33)
	if !tryDOSLongWarp(table, 3, 30) || table[3][5] != 30 || table[30][5] != 3 {
		t.Fatal("missing reciprocal long warp")
	}
	before := append(dosWarpTable(nil), table...)
	for _, pair := range [][2]int{{3, 3}, {3, 15}, {15, 30}, {0, 15}, {15, 33}} {
		if tryDOSLongWarp(table, pair[0], pair[1]) {
			t.Fatal("invalid or occupied long warp allowed", pair)
		}
	}
	if !reflect.DeepEqual(table, before) {
		t.Fatal("failed long warp changed table")
	}
	table[4][0] = 20
	table[20][0] = 4
	if tryDOSLongWarp(table, 4, 20) {
		t.Fatal("DOS duplicate-exit defect reproduced")
	}
}

type warpConstantSource int64

func (s warpConstantSource) Seed(int64)   {}
func (s warpConstantSource) Int63() int64 { return int64(s) }

func TestDOSWarpGenerationEarthSeedFiniteFallbackAndTableInvariants(t *testing.T) {
	for _, count := range []int{8, 32, 3000} {
		// Constant.5 never passes either random edge gate: empty rows must take the
		// bounded deterministic fallback rather than retrying forever.
		table, err := generateDOSWarpTable(count, rand.New(warpConstantSource(1<<62)))
		if err != nil {
			t.Fatal(count, err)
		}
		if table[0] != [6]int{} || table[1] != [6]int{1, 2, 3, 4, 5, 6} {
			t.Fatal("original Earth seed changed", table[1])
		}
		verifyDOSWarpTable(t, table)
	}
}
func verifyDOSWarpTable(t *testing.T, table dosWarpTable) {
	t.Helper()
	count := len(table) - 1
	for sector := 1; sector <= count; sector++ {
		if !table.populated(sector) {
			t.Fatal("empty sector", sector)
		}
		seen := map[int]bool{}
		for column, to := range table[sector] {
			if to == 0 {
				continue
			}
			if to < 1 || to > count || seen[to] || table[to][column] != sector {
				t.Fatal("invalid, duplicate or nonmatching reciprocal warp", sector, column, to)
			}
			if to == sector && sector != 1 {
				t.Fatal("non-Earth self-warp", sector)
			}
			if column < 5 && absInt(to-sector) > 10 {
				t.Fatal("local edge beyond ten sectors", sector, to)
			}
			seen[to] = true
		}
	}
}
func absInt(n int) int {
	if n < 0 {
		return -n
	}
	return n
}
func TestDOSWarpGenerationSeededAndAdmission(t *testing.T) {
	for _, seed := range []int64{0, 1, 36, 77, 999} {
		a, err := generateDOSWarpTable(3000, rand.New(rand.NewSource(seed)))
		if err != nil {
			t.Fatal(seed, err)
		}
		b, err := generateDOSWarpTable(3000, rand.New(rand.NewSource(seed)))
		if err != nil || !reflect.DeepEqual(a, b) {
			t.Fatal("same Go seed changed graph", seed, err)
		}
		verifyDOSWarpTable(t, a)
	}
	for _, count := range []int{0, 7, 3001} {
		if _, err := generateDOSWarpTable(count, rand.New(rand.NewSource(1))); err == nil {
			t.Fatal("invalid count accepted", count)
		}
	}
	if _, err := generateDOSWarpTable(32, nil); err == nil {
		t.Fatal("nil RNG accepted")
	}
}

type warpScriptedSource struct {
	values []int64
	index  int
}

func (s *warpScriptedSource) Seed(int64) { s.index = 0 }
func (s *warpScriptedSource) Int63() int64 {
	if s.index >= len(s.values) {
		panic("unexpected warp random draw")
	}
	v := s.values[s.index]
	s.index++
	return v
}
func TestDOSWarpChanceThresholdsAndDrawOrder(t *testing.T) {
	raw := func(r float64) int64 { return int64(r * 9223372036854775808.0) }
	half := raw(.5)
	for _, accept := range []bool{false, true} {
		local, long := float64(float32(.4)), float64(float32(.985))
		if !accept {
			local = math.Nextafter(local, 1)
			long = math.Nextafter(long, 0)
		}
		values := []int64{raw(local)}
		if accept {
			values = append(values, 0)
		} // Intn10 chooses local offset1.
		values = append(values, half, half, half, half, half, raw(long))
		if accept {
			values = append(values, 24<<32)
		} // Intn32 chooses sector25.
		source := &warpScriptedSource{values: values}
		table := make(dosWarpTable, 33)
		attemptDOSWarpRow(table, 10, rand.New(source))
		if accept && (table[10][0] != 11 || table[11][0] != 10 || table[10][5] != 25 || table[25][5] != 10) {
			t.Fatal("inclusive MBF thresholds rejected", table[10])
		}
		if !accept && table.populated(10) {
			t.Fatal("outside chance thresholds accepted", table[10])
		}
		if source.index != len(source.values) {
			t.Fatal("unexpected original slot draw order", source.index, len(source.values))
		}
	}
}
