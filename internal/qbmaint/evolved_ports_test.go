package qbmaint

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"os"
	"reflect"
	"strings"
	"testing"
)

type evolvedFixture struct {
	Format      string
	Initial     string `json:"initial_gzip"`
	InitialSHA  string `json:"initial_sha256"`
	Comparisons int    `json:"native_block_comparisons"`
	Cases       []struct {
		Name       string
		Days       []int
		Timers     []string `json:"timer_minutes"`
		SHA        string   `json:"expected_sha256"`
		Classes    [3]int   `json:"class_counts"`
		Promotions int      `json:"rate_promotions"`
		Min        string   `json:"elapsed_min"`
		Max        string   `json:"elapsed_max"`
	}
}

func evolvedLoad(t *testing.T) evolvedFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/evolved_ports.json")
	if e != nil {
		t.Fatal(e)
	}
	var d evolvedFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-evolved-port-replay-v1" || len(d.Cases) != 9 || d.Comparisons != 54 {
		t.Fatal("coverage")
	}
	return d
}
func TestEvolvedNativePortChains(t *testing.T) {
	d := evolvedLoad(t)
	initial := unpack(t, d.Initial)
	if digest(initial) != d.InitialSHA {
		t.Fatal("initial fingerprint")
	}
	var world []byte
	for _, c := range d.Cases {
		if strings.HasSuffix(c.Name, "day-1") {
			world = bytes.Clone(initial)
		}
		s := EvolvedPortSchedule{Days: append([]int(nil), c.Days...)}
		for _, v := range c.Timers {
			b, e := hex.DecodeString(v)
			if e != nil || len(b) != 4 {
				t.Fatal("timer")
			}
			s.TimerMinutes = append(s.TimerMinutes, [4]byte(b))
		}
		saved := bytes.Clone(world)
		days := append([]int(nil), s.Days...)
		timers := append([][4]byte(nil), s.TimerMinutes...)
		block, stats, e := ReplayEvolvedPorts(world, s)
		if e != nil {
			t.Fatalf("%s: %v", c.Name, e)
		}
		if digest(block) != c.SHA {
			t.Fatalf("%s: complete native block mismatch", c.Name)
		}
		if stats.Ports != 1000 || stats.Bytes != 137000 || stats.Day != c.Days[0] || stats.ClassCounts != c.Classes || stats.RatePromotions != c.Promotions || stats.RNGDraws != 0 || hex.EncodeToString(stats.ElapsedMin[:]) != c.Min || hex.EncodeToString(stats.ElapsedMax[:]) != c.Max {
			t.Fatalf("%s: stats %+v", c.Name, stats)
		}
		if !bytes.Equal(world, saved) || !reflect.DeepEqual(days, s.Days) || !reflect.DeepEqual(timers, s.TimerMinutes) {
			t.Fatal("mutated source")
		}
		for i, b := range block {
			off := i % RecordSize
			if !(off >= 41 && off < 85 || off >= 101 && off < 105) && b != world[PortStart+i] {
				t.Fatal("unwritten byte changed")
			}
		}
		if s.Days[0] > 306 {
			if _, _, e := ReplayCleanPorts(world, PortSchedule{Days: s.Days, TimerMinutes: s.TimerMinutes, Capped: true}); e == nil {
				t.Fatal("strict initial API admitted evolved world")
			}
		}
		copy(world[PortStart:], block)
		block[0] ^= 255
		if world[PortStart] != saved[PortStart] {
			t.Fatal("block aliases world")
		}
	}
}
func evolvedSynthetic(t *testing.T, day int) ([]byte, EvolvedPortSchedule) {
	t.Helper()
	d := evolvedLoad(t)
	world := unpack(t, d.Initial)
	s := EvolvedPortSchedule{Days: make([]int, 1000), TimerMinutes: make([][4]byte, 1000)}
	for i := 0; i < 1000; i++ {
		s.Days[i] = day
		rec := world[PortStart+i*RecordSize:]
		put := func(o int, v [4]byte) { copy(rec[o:o+4], v[:]) }
		last := day - 1
		stock := 10000
		if day == 306 {
			last = 296
			stock = 0
		}
		put(45, encode(last))
		put(101, [4]byte{})
		put(89, [4]byte{})
		put(97, [4]byte{})
		for j := 0; j < 3; j++ {
			put(49+4*j, encode(stock))
			put(61+4*j, encode(1000))
			put(73+4*j, encode((j+1)*11))
		}
	}
	return world, s
}
func TestEvolvedWideMaximumRounding(t *testing.T) {
	// Synthetic source-model boundary, not an additional native observation.
	for _, day := range []int{306, 307} {
		world, s := evolvedSynthetic(t, day)
		wantClass := 3
		if day == 307 {
			wantClass = 1
			for i := range s.TimerMinutes {
				s.TimerMinutes[i] = portSingleBytes(.0002)
			}
		}
		block, stats, e := ReplayEvolvedPorts(world, s)
		if e != nil {
			t.Fatal(e)
		}
		if v, ok := integer([4]byte(block[41:45])); !ok || v != wantClass {
			t.Fatalf("day %d class %d", day, v)
		}
		if day == 307 {
			if stats.RatePromotions != 3000 {
				t.Fatal(stats)
			}
			if v, _ := integer([4]byte(block[49:53])); v != 11000 {
				t.Fatal("stored stock")
			}
			if v, _ := integer([4]byte(block[61:65])); v != 1100 {
				t.Fatal("promoted rate")
			}
		}
	}
}
func TestEvolvedRefusesUnsupportedInputsAtomically(t *testing.T) {
	cases := map[string]func([]byte, *EvolvedPortSchedule){
		"short schedule": func(w []byte, s *EvolvedPortSchedule) { s.Days = nil },
		"day": func(w []byte, s *EvolvedPortSchedule) {
			for i := range s.Days {
				s.Days[i] = 309
			}
		},
		"mixed days":          func(w []byte, s *EvolvedPortSchedule) { s.Days[999] = 308 },
		"timer one":           func(w []byte, s *EvolvedPortSchedule) { s.TimerMinutes[999] = encode(1) },
		"negative timer":      func(w []byte, s *EvolvedPortSchedule) { s.TimerMinutes[0] = portSingleBytes(-.1) },
		"clock reversal":      func(w []byte, s *EvolvedPortSchedule) { s.TimerMinutes[0] = portSingleBytes(.1) },
		"geometry":            func(w []byte, s *EvolvedPortSchedule) { v := encode(50); copy(w[53:57], v[:]) },
		"treasury":            func(w []byte, s *EvolvedPortSchedule) { v := encode(1); copy(w[PortStart+89:], v[:]) },
		"date gap":            func(w []byte, s *EvolvedPortSchedule) { v := encode(304); copy(w[PortStart+45:], v[:]) },
		"rate":                func(w []byte, s *EvolvedPortSchedule) { v := encode(999); copy(w[PortStart+61:], v[:]) },
		"coefficient":         func(w []byte, s *EvolvedPortSchedule) { copy(w[PortStart+73:], make([]byte, 4)) },
		"last record failure": func(w []byte, s *EvolvedPortSchedule) { v := encode(1); copy(w[PortStart+999*RecordSize+97:], v[:]) },
		"not full stock":      func(w []byte, s *EvolvedPortSchedule) { copy(w[PortStart+49:], make([]byte, 4)) },
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			w, s := evolvedSynthetic(t, 307)
			mutate(w, &s)
			saved := bytes.Clone(w)
			b, stats, e := ReplayEvolvedPorts(w, s)
			if e == nil || b != nil || stats != (EvolvedPortStats{}) {
				t.Fatal("non-atomic refusal")
			}
			if !bytes.Equal(w, saved) {
				t.Fatal("source mutated")
			}
		})
	}
}

func TestEvolvedRequiresCompleteWorld(t *testing.T) {
	w, s := evolvedSynthetic(t, 307)
	for _, bad := range [][]byte{nil, w[:len(w)-1], append(bytes.Clone(w), 0)} {
		b, stats, e := ReplayEvolvedPorts(bad, s)
		if e == nil || b != nil || stats != (EvolvedPortStats{}) {
			t.Fatal("world extent admitted")
		}
	}
}
