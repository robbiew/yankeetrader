package game

import (
	"compress/gzip"
	"encoding/json"
	"math/rand"
	"os"
	"reflect"
	"strings"
	"testing"
	"time"
)

func TestDOSWarpProfileNewSaveAndResets(t *testing.T) {
	for _, count := range []int{8, 32, 3000} {
		for _, seed := range []int64{0, 1, 36, 77, 999} {
			w, err := NewWithGeneration(clock, seed, count, "dos", "dos")
			if err != nil {
				t.Fatal(count, seed, err)
			}
			legacy, err := NewWithPortGeneration(clock, seed, count, "dos")
			if err != nil {
				t.Fatal(err)
			}
			if !reflect.DeepEqual(w.Ports, legacy.Ports) {
				t.Fatal("warp profile rerolled port economy")
			}
			if w.WarpGeneration != "dos" || w.PortGeneration != "dos" {
				t.Fatal("lost independent profiles")
			}
			if !reflect.DeepEqual(w.Sectors[1].Warps, []int{2, 3, 4, 5, 6}) {
				t.Fatal("Earth exit order", w.Sectors[1].Warps)
			}
			table := make(dosWarpTable, count+1)
			for id, s := range w.Sectors {
				if len(s.Warps) < 1 || len(s.Warps) > 6 {
					t.Fatal("invalid exit count", id, s.Warps)
				}
				seen := map[int]bool{}
				for i, to := range s.Warps {
					if to == id || to < 1 || to > count || seen[to] {
						t.Fatal("invalid exit", id, to)
					}
					seen[to] = true
					table[id][i] = to
				}
			}
			if !dosGraphConnected(table, false) || !dosGraphConnected(table, true) {
				t.Fatal("unreachable sector")
			}
			raw, _ := json.Marshal(w)
			var loaded World
			if err = json.Unmarshal(raw, &loaded); err != nil {
				t.Fatal(err)
			}
			if err = loaded.Upgrade(); err != nil {
				t.Fatal(err)
			}
			if err = loaded.Validate(); err != nil || !reflect.DeepEqual(w, &loaded) {
				t.Fatal("roundtrip changed universe", err)
			}
			again, err := NewWithGeneration(clock, seed, count, "dos", "dos")
			if err != nil || !reflect.DeepEqual(w, again) {
				t.Fatal("nonreproducible generation", err)
			}
		}
	}
	w, err := NewWithGeneration(clock, 36, 32, "dos", "dos")
	if err != nil {
		t.Fatal(err)
	}
	admin, err := w.AdministrativeCandidate(1, clock.Add(time.Hour), 77)
	if err != nil || admin.WarpGeneration != "dos" || admin.PortGeneration != "dos" {
		t.Fatal(admin, err)
	}
	p, err := w.Join("winner", "Winner")
	if err != nil {
		t.Fatal(err)
	}
	n := 20
	w.GenesisPorts = &n
	for i := 2; i <= 21; i++ {
		w.Ports[i].Owner = p.ID
	}
	intent, err := w.PrepareGenesis(p.ID, clock)
	if err != nil {
		t.Fatal(err)
	}
	next, _, err := w.GenesisCandidate(intent, clock.Add(time.Second), 77)
	if err != nil || next.WarpGeneration != "dos" || next.PortGeneration != "dos" {
		t.Fatal(next, err)
	}
	w.WarpGeneration = ""
	if _, _, err = w.GenesisCandidate(intent, clock.Add(time.Second), 77); err == nil {
		t.Fatal("stale warp setting quote accepted")
	}
}

func TestDOSWarpMigrationPreservesMapAndAdmission(t *testing.T) {
	for _, ports := range []string{"", "dos"} {
		w, err := NewWithPortGeneration(clock, 36, 32, ports)
		if err != nil {
			t.Fatal(err)
		}
		w.Version = 33
		sectors, _ := json.Marshal(w.Sectors)
		portData, _ := json.Marshal(w.Ports)
		if err = w.Upgrade(); err != nil {
			t.Fatal(err)
		}
		after, _ := json.Marshal(w.Sectors)
		afterPorts, _ := json.Marshal(w.Ports)
		if w.Version != WorldVersion || w.WarpGeneration != "" || string(sectors) != string(after) || string(portData) != string(afterPorts) {
			t.Fatal("upgrade rerolled map/economy")
		}
		w.Version = 33
		w.WarpGeneration = "dos"
		if w.Upgrade() == nil {
			t.Fatal("legacy profile accepted")
		}
	}
	if _, err := NewWithGeneration(clock, 36, 32, "", "unknown"); err == nil {
		t.Fatal("unknown profile accepted")
	}
	w, _ := New(clock, 36, 32)
	w.WarpGeneration = "unknown"
	if w.Validate() == nil {
		t.Fatal("unknown saved profile accepted")
	}
}

func TestDOSWarpIsolationRepairAndExhaustedSlots(t *testing.T) {
	table := make(dosWarpTable, 9)
	for col := 0; col < 6; col++ {
		table[1][col] = col + 1
		table[col+1][col] = 1
	}
	table[7][0] = 8
	table[8][0] = 7
	if dosGraphConnected(table, false) {
		t.Fatal("fixture unexpectedly connected")
	}
	if err := repairDOSWarps(table, rand.New(rand.NewSource(36))); err != nil {
		t.Fatal(err)
	}
	if !dosGraphConnected(table, false) || !dosGraphConnected(table, true) {
		t.Fatal("repair did not connect component")
	}
	blocked := make(dosWarpTable, 9)
	for id := 1; id <= 6; id++ {
		blocked[id][5] = id%6 + 1
	}
	before := append(dosWarpTable(nil), blocked...)
	err := repairDOSWarps(blocked, rand.New(rand.NewSource(36)))
	if err == nil || !strings.Contains(err.Error(), "no earlier free sixth slot") || !reflect.DeepEqual(before, blocked) {
		t.Fatal("unbounded or destructive unavailable repair", err)
	}
}

func TestDOSWarpEarthShortcutsAndDrawBudget(t *testing.T) {
	raw := func(v float64) int64 { return int64(v * 9223372036854775808.0) }
	source := &warpScriptedSource{values: []int64{raw(.00125), raw(.01), raw(.5)}}
	table := make(dosWarpTable, 21)
	table[13][5] = 14
	table[14][5] = 13
	if err := shortcutDOSWarps(table, rand.New(source)); err != nil {
		t.Fatal(err)
	}
	if table[9][5] != 1 || table[13][5] != 14 || table[1][5] != 0 || source.index != 3 {
		t.Fatal("direction/occupied slot/rounding/stepping", table, source.index)
	}
	// A zero increment must fail finitely instead of hanging as the DOS loop can.
	zero := rand.New(warpConstantSource(0))
	if err := shortcutDOSWarps(make(dosWarpTable, 21), zero); err == nil {
		t.Fatal("zero-step stream did not terminate")
	}
}

func TestDOSWarpRepairAndShortcutsMatchNativePhaseFixtures(t *testing.T) {
	f, err := os.Open("testdata/dos_warps.json.gz")
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	zipped, err := gzip.NewReader(f)
	if err != nil {
		t.Fatal(err)
	}
	defer zipped.Close()
	var fixture struct {
		Format      int
		Cases       map[string]struct{ Slots dosWarpTable }
		RepairPairs [][2]int `json:"repair_pairs"`
	}
	if err = json.NewDecoder(zipped).Decode(&fixture); err != nil {
		t.Fatal(err)
	}
	if fixture.Format != 1 || len(fixture.RepairPairs) != 19 {
		t.Fatal("unexpected native phase fixture")
	}
	original := fixture.Cases["no-repair"].Slots
	if dosGraphConnected(original, false) {
		t.Fatal("native raw phase unexpectedly connected")
	}
	planning := append(dosWarpTable(nil), original...)
	values := []int64{}
	for _, pair := range fixture.RepairPairs {
		target, source := pair[0], pair[1]
		rank := -1
		eligible := 0
		for i := 1; i < target; i++ {
			if planning[i][5] == 0 {
				if i == source {
					rank = eligible
				}
				eligible++
			}
		}
		if rank < 0 {
			t.Fatal("native repair source unavailable", pair)
		}
		values = append(values, int64(rank)<<32)
		planning[source][5] = target
		planning[target][5] = source
	}
	scripted := &warpScriptedSource{values: values}
	repaired := append(dosWarpTable(nil), original...)
	if err = repairDOSWarps(repaired, rand.New(scripted)); err != nil {
		t.Fatal(err)
	}
	if scripted.index != len(values) || !reflect.DeepEqual(repaired, fixture.Cases["repair-only"].Slots) {
		t.Fatal("BFS repair differs from native phase capture")
	}
	// Select the native observed shortcut sectors with Go draws. This validates
	// the cumulative-step/write semantics without claiming identical QB seed draws.
	nativeFinal := fixture.Cases["original"].Slots
	values = nil
	previous := 8
	for sector := 1; sector < len(repaired); sector++ {
		if repaired[sector] != nativeFinal[sector] {
			if repaired[sector][5] != 0 || nativeFinal[sector][5] != 1 {
				t.Fatal("unexpected native shortcut diff", sector)
			}
			step := sector - previous
			if step < 0 || step >= 400 {
				t.Fatal("shortcut fixture cannot use cumulative steps", sector)
			}
			values = append(values, int64(float64(step)/400*9223372036854775808.0))
			previous = sector
		}
	}
	lastDraw := .99
	values = append(values, int64(lastDraw*9223372036854775808.0))
	scripted = &warpScriptedSource{values: values}
	if err = shortcutDOSWarps(repaired, rand.New(scripted)); err != nil {
		t.Fatal(err)
	}
	if scripted.index != len(values) || !reflect.DeepEqual(repaired, nativeFinal) {
		t.Fatal("Earth shortcuts differ from native phase capture")
	}
}

func TestDOSWarpShortcutPositiveHalfUpNativeControls(t *testing.T) {
	for _, tc := range []struct {
		x    float64
		want int
	}{{100, 100}, {100.25, 100}, {100.5, 101}, {100.75, 101}, {101.5, 102}} {
		first := (tc.x - 8) / 400
		last := .9
		source := &warpScriptedSource{values: []int64{int64(first * 9223372036854775808.0), int64(last * 9223372036854775808.0)}}
		table := make(dosWarpTable, 201)
		if err := shortcutDOSWarps(table, rand.New(source)); err != nil {
			t.Fatal(err)
		}
		changed := []int{}
		for sector := 1; sector < len(table); sector++ {
			if table[sector][5] != 0 {
				changed = append(changed, sector)
			}
		}
		if !reflect.DeepEqual(changed, []int{tc.want}) {
			t.Fatal(tc, changed)
		}
	}
}
