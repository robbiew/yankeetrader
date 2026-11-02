package game

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"math/rand"
	"reflect"
	"strings"
	"testing"
	"time"
)

func TestDOSPortSyllablePoolIdentity(t *testing.T) {
	sum := sha256.Sum256([]byte(dosPortSyllableData))
	if len(dosPortSyllables) != 908 || hex.EncodeToString(sum[:]) != "8a59a909d232084d89a82db77339f680475c3187aef96ef0ce6444bd0b4002b7" {
		t.Fatal("original syllable pool changed")
	}
	seen := map[string]bool{}
	duplicates := 0
	for _, part := range dosPortSyllables {
		if part == "" || strings.ContainsAny(part, " \n\r\t") {
			t.Fatal("invalid raw syllable", part)
		}
		if seen[part] {
			duplicates++
		}
		seen[part] = true
	}
	if duplicates != 29 {
		t.Fatal("duplicate syllable weighting lost", duplicates)
	}
}

type portNameSource struct {
	values []int64
	index  int
}

func (s *portNameSource) Seed(int64) { s.index = 0 }
func (s *portNameSource) Int63() int64 {
	if s.index >= len(s.values) {
		panic("unexpected name random draw")
	}
	v := s.values[s.index]
	s.index++
	return v
}
func TestDOSPortNameChunkCountAndWordSpacing(t *testing.T) {
	find := func(want string) int64 {
		for i, part := range dosPortSyllables {
			if part == want {
				return int64(i) << 32
			}
		}
		t.Fatal("missing syllable", want)
		return 0
	}
	for _, tc := range []struct {
		values []int64
		want   string
	}{
		{[]int64{0, 0, find("tractor"), find("ing")}, "Tractoring"},
		{[]int64{0, 0, find("ing"), find("tractor")}, "Ing Tractor"},
		// .9*.9*3 floors to2, so four chunks rather than a uniform2..4 draw.
		{[]int64{8301034833169298432, 8301034833169298432, find("ing"), find("bat"), find("tractor"), find("lightning")}, "Ingbat Tractor Lightning"},
	} {
		source := &portNameSource{values: tc.values}
		got := dosPortName(rand.New(source))
		if got != tc.want || source.index != len(source.values) {
			t.Fatal(got, tc.want, source.index)
		}
	}
}

func TestDOSPortsEconomyPlacementAndReproducibility(t *testing.T) {
	for _, count := range []int{8, 32, 3000} {
		w, err := New(clock, 36, count)
		if err != nil {
			t.Fatal(err)
		}
		if err = generateDOSPorts(w, rand.New(rand.NewSource(1234))); err != nil {
			t.Fatal(err)
		}
		if len(w.Ports) != min(1000, count) {
			t.Fatal("port count", count, len(w.Ports))
		}
		locations := map[int]bool{}
		sells := [3]int{}
		for id, port := range w.Ports {
			if port.ID != id || port.Owner != 0 || port.Treasury != 0 || port.Updated != w.Created || w.Sectors[port.Sector].Port != id || locations[port.Sector] {
				t.Fatal("invalid or orphaned port", port)
			}
			locations[port.Sector] = true
			if id <= 4 && port.Sector != 2*id-1 {
				t.Fatal("protected-sector placement", port)
			}
			if !clean(port.Name) || len(port.Name) > 39 || strings.TrimSpace(port.Name) != port.Name {
				t.Fatal("invalid generated name", port.Name)
			}
			positive := 0
			for good := 0; good < 3; good++ {
				production, coefficient := port.Production[good], port.Coefficient[good]
				if production < 1000 || production > 32766 || production != float64(int64(production)) || port.Supply[good] != 10*production {
					t.Fatal("wrong production/initial stock", port)
				}
				if coefficient == 0 || coefficient < -100 || coefficient > 100 || coefficient != float64(int64(coefficient)) {
					t.Fatal("wrong coefficient", port)
				}
				if coefficient > 0 {
					positive++
					sells[good]++
				}
			}
			if positive != 1 {
				t.Fatal("must sell exactly one commodity", port)
			}
		}
		if w.Ports[1].Name != "Earth" {
			t.Fatal("Earth missing")
		}
		for _, sector := range w.Sectors {
			if sector.Port != 0 && w.Ports[sector.Port].Sector != sector.ID {
				t.Fatal("stale sector link")
			}
		}
		if err = w.Validate(); err != nil {
			t.Fatal(err)
		}
		again, _ := New(clock, 36, count)
		if err = generateDOSPorts(again, rand.New(rand.NewSource(1234))); err != nil {
			t.Fatal(err)
		}
		if !reflect.DeepEqual(w.Ports, again.Ports) {
			t.Fatal("same Go seed changed port generation")
		}
		other, _ := New(clock, 36, count)
		_ = generateDOSPorts(other, rand.New(rand.NewSource(5678)))
		if reflect.DeepEqual(w.Ports, other.Ports) {
			t.Fatal("different Go seed ignored")
		}
		if count == 3000 {
			for _, n := range sells {
				if n == 0 {
					t.Fatal("selling class omitted")
				}
			}
		}
	}
}
func TestDOSPortGenerationAdmissionDoesNotAlterExistingWorld(t *testing.T) {
	for _, mode := range []string{"nil RNG", "players", "bad sector", "clock"} {
		w, _ := New(clock, 36, 8)
		rng := rand.New(rand.NewSource(1))
		switch mode {
		case "nil RNG":
			rng = nil
		case "players":
			_, _ = w.Join("existing", "Existing")
		case "bad sector":
			w.Sectors[8].ID = 99
		case "clock":
			w.Created = time.Time{}
		}
		before, _ := json.Marshal(w)
		if err := generateDOSPorts(w, rng); err == nil {
			t.Fatal("invalid generation admitted", mode)
		}
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("failed generation mutated world", mode)
		}
	}
	if generateDOSPorts(nil, rand.New(rand.NewSource(1))) == nil {
		t.Fatal("nil world accepted")
	}
}

func TestDOSPortProfileMigrationAndSeasonReset(t *testing.T) {
	w, err := NewWithPortGeneration(clock, 36, 32, "dos")
	if err != nil {
		t.Fatal(err)
	}
	if w.PortGeneration != "dos" {
		t.Fatal("missing profile")
	}
	raw, _ := json.Marshal(w)
	var loaded World
	if err = json.Unmarshal(raw, &loaded); err != nil {
		t.Fatal(err)
	}
	if err = loaded.Upgrade(); err != nil {
		t.Fatal(err)
	}
	if err = loaded.Validate(); err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(w, &loaded) {
		t.Fatal("profile save rerolled world")
	}
	admin, err := w.AdministrativeCandidate(1, clock.Add(time.Hour), 77)
	if err != nil || admin.PortGeneration != "dos" || admin.Ports[2].Sector != 3 {
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
	next, _, err := w.GenesisCandidate(intent, clock.Add(time.Second), 78)
	if err != nil || next.PortGeneration != "dos" || next.Ports[2].Sector != 3 {
		t.Fatal(next, err)
	}
	w.PortGeneration = ""
	if _, _, err = w.GenesisCandidate(intent, clock.Add(time.Second), 78); err == nil {
		t.Fatal("changed profile accepted stale Genesis quote")
	}
	legacy, _ := New(clock, 36, 32)
	legacy.Version = 32
	original, _ := json.Marshal(legacy.Ports)
	if err = legacy.Upgrade(); err != nil {
		t.Fatal(err)
	}
	after, _ := json.Marshal(legacy.Ports)
	if legacy.Version != 33 || legacy.PortGeneration != "" || string(original) != string(after) {
		t.Fatal("legacy economy changed")
	}
	legacy.Version = 32
	legacy.PortGeneration = "dos"
	if legacy.Upgrade() == nil {
		t.Fatal("legacy profile smuggled through migration")
	}
	if _, err = NewWithPortGeneration(clock, 36, 32, "unknown"); err == nil {
		t.Fatal("unknown generation profile")
	}
}

func TestDOSPortPricesMatchRetainedControlsAndReports(t *testing.T) {
	if dosReferencePrices != [3]float64{20.051570892333984, 29.302257537841797, 41.20359420776367} {
		t.Fatal(dosReferencePrices)
	}
	w, err := NewWithPortGeneration(clock, 36, 32, "dos")
	if err != nil {
		t.Fatal(err)
	}
	p, err := w.Join("trader", "Trader")
	if err != nil {
		t.Fatal(err)
	}
	port := w.Ports[2]
	p.Sector = port.Sector
	for _, tc := range []struct {
		coefficient float64
		want        [3]int64
	}{{0, [3]int64{20, 29, 41}}, {-50, [3]int64{30, 44, 62}}, {-10000, [3]int64{2025, 2960, 4162}}, {100, [3]int64{1, 1, 1}}} {
		port.Supply = [3]float64{1000, 1000, 1000}
		port.Production = [3]float64{100, 100, 100}
		port.Coefficient = [3]float64{tc.coefficient, tc.coefficient, tc.coefficient}
		report, err := w.RemotePortReport(p.ID, port.Sector, clock)
		if err != nil {
			t.Fatal(err)
		}
		if err = w.Dock(p.ID, clock); err != nil {
			t.Fatal(err)
		}
		if p.DockPrices != tc.want || report.Prices != tc.want {
			t.Fatal(tc, p.DockPrices, report.Prices)
		}
	}
	w.PortGeneration = ""
	port.Coefficient = [3]float64{-50, -50, -50}
	if err = w.Dock(p.ID, clock); err != nil {
		t.Fatal(err)
	}
	if p.DockPrices != [3]int64{30, 45, 60} {
		t.Fatal("legacy reference prices changed", p.DockPrices)
	}
}
