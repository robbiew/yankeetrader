package qbmaint

import (
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"io"
	"os"
	"reflect"
	"testing"
)

type fixtureCase struct {
	Name        string
	BeforeSHA   string `json:"before_sha256"`
	Days        []int
	Timers      []string `json:"timer_minutes"`
	Capped      bool
	Expected    string `json:"expected_gzip"`
	ExpectedSHA string `json:"expected_sha256"`
	Classes     [3]int `json:"class_counts"`
}
type fixture struct {
	Format string
	Worlds map[string]string
	Cases  []fixtureCase
}

func unpack(t *testing.T, s string) []byte {
	t.Helper()
	b, e := base64.StdEncoding.DecodeString(s)
	if e != nil {
		t.Fatal(e)
	}
	r, e := gzip.NewReader(bytes.NewReader(b))
	if e != nil {
		t.Fatal(e)
	}
	defer r.Close()
	b, e = io.ReadAll(r)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func load(t *testing.T) fixture {
	t.Helper()
	b, e := os.ReadFile("testdata/clean_ports.json")
	if e != nil {
		t.Fatal(e)
	}
	var d fixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-clean-port-replay-v1" || len(d.Cases) != 32 {
		t.Fatal("native fixture coverage")
	}
	return d
}
func schedule(t *testing.T, c fixtureCase) PortSchedule {
	t.Helper()
	s := PortSchedule{Days: append([]int(nil), c.Days...), Capped: c.Capped}
	for _, raw := range c.Timers {
		b, e := hex.DecodeString(raw)
		if e != nil || len(b) != 4 {
			t.Fatal("timer")
		}
		s.TimerMinutes = append(s.TimerMinutes, [4]byte(b))
	}
	return s
}
func digest(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func TestRetainedNativePorts(t *testing.T) {
	d := load(t)
	strict, capped := 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			if digest(before) != c.BeforeSHA {
				t.Fatal("before digest")
			}
			saved := append([]byte(nil), before...)
			s := schedule(t, c)
			savedDays := append([]int(nil), s.Days...)
			savedTimers := append([][4]byte(nil), s.TimerMinutes...)
			got, stats, e := ReplayCleanPorts(before, s)
			if e != nil {
				t.Fatal(e)
			}
			want := unpack(t, c.Expected)
			if len(want) != 137000 || digest(want) != c.ExpectedSHA || !bytes.Equal(got, want) {
				t.Fatal("complete native port block mismatch")
			}
			if stats.Ports != 1000 || stats.Bytes != 137000 || stats.ElapsedDays != 10 || stats.ClassCounts != c.Classes {
				t.Fatal("port statistics")
			}
			day := s.Days[0]
			if day != s.Days[999] {
				day = 0
			}
			if stats.Day != day {
				t.Fatal("calendar summary")
			}
			if !bytes.Equal(before, saved) || !reflect.DeepEqual(s.Days, savedDays) || !reflect.DeepEqual(s.TimerMinutes, savedTimers) {
				t.Fatal("inputs mutated")
			}
			got[0] ^= 255
			if !bytes.Equal(before, saved) {
				t.Fatal("result aliases before-world")
			}
			if c.Capped {
				capped++
			} else {
				strict++
			}
		})
	}
	if strict != 8 || capped != 24 {
		t.Fatal("profile coverage")
	}
}

func TestAdmissionAndAtomicFailure(t *testing.T) {
	d := load(t)
	c := d.Cases[0]
	source := unpack(t, d.Worlds[c.BeforeSHA])
	initial := schedule(t, c)
	type mutation func([]byte, *PortSchedule)
	tests := map[string]mutation{
		"multiple-midnight-wraps": func(_ []byte, s *PortSchedule) {
			s.Capped = true
			for i := range s.TimerMinutes {
				s.TimerMinutes[i] = [4]byte{}
			}
			s.TimerMinutes[990] = [4]byte{0, 0xf0, 0x33, 139}
			s.TimerMinutes[998] = s.TimerMinutes[990]
		},

		"calendar-count":   func(_ []byte, s *PortSchedule) { s.Days = s.Days[:999] },
		"timer-count":      func(_ []byte, s *PortSchedule) { s.TimerMinutes = s.TimerMinutes[:999] },
		"calendar-range":   func(_ []byte, s *PortSchedule) { s.Days[0] = 0 },
		"strict-days":      func(_ []byte, s *PortSchedule) { s.Days[999]++ },
		"calendar-retreat": func(_ []byte, s *PortSchedule) { s.Capped = true; s.Days[999]-- },
		"calendar-span":    func(_ []byte, s *PortSchedule) { s.Capped = true; s.Days[999] += 2 },
		"negative-timer":   func(_ []byte, s *PortSchedule) { s.TimerMinutes[999] = encode(-1) },
		"timer-upper":      func(_ []byte, s *PortSchedule) { s.TimerMinutes[999] = encode(1440) },
		"timer-rollback": func(_ []byte, s *PortSchedule) {
			s.Capped = true
			s.TimerMinutes[998] = encode(100)
			s.TimerMinutes[999] = encode(1)
		},
		"geometry": func(b []byte, _ *PortSchedule) { copy(b[53:57], []byte{0, 0, 0, 129}) },
		"late-nonempty": func(b []byte, _ *PortSchedule) {
			r := PortStart + 999*RecordSize
			v := encode(1)
			copy(b[r+49:r+53], v[:])
		},
		"stale-day":         func(b []byte, s *PortSchedule) { v := encode(s.Days[0] - 9); copy(b[PortStart+45:PortStart+49], v[:]) },
		"fractional-rate":   func(b []byte, _ *PortSchedule) { copy(b[PortStart+61:PortStart+65], []byte{0, 16, 122, 138}) },
		"low-rate":          func(b []byte, _ *PortSchedule) { v := encode(999); copy(b[PortStart+61:PortStart+65], v[:]) },
		"high-rate":         func(b []byte, _ *PortSchedule) { v := encode(32767); copy(b[PortStart+61:PortStart+65], v[:]) },
		"zero-coefficient":  func(b []byte, _ *PortSchedule) { clear(b[PortStart+73 : PortStart+77]) },
		"large-coefficient": func(b []byte, _ *PortSchedule) { v := encode(-101); copy(b[PortStart+73:PortStart+77], v[:]) },
	}
	for name, mutate := range tests {
		t.Run(name, func(t *testing.T) {
			b := append([]byte(nil), source...)
			s := PortSchedule{append([]int(nil), initial.Days...), append([][4]byte(nil), initial.TimerMinutes...), initial.Capped}
			mutate(b, &s)
			saved := append([]byte(nil), b...)
			got, stats, e := ReplayCleanPorts(b, s)
			if e == nil || got != nil || stats != (PortStats{}) || !bytes.Equal(b, saved) {
				t.Fatal("rejected profile must return no result and preserve input")
			}
		})
	}
	for _, n := range []int{0, len(source) - 1, len(source) + 1} {
		b := make([]byte, n)
		if got, _, e := ReplayCleanPorts(b, initial); e == nil || got != nil {
			t.Fatal("world extent")
		}
	}
}

func TestTiesResiduesAndNarrowWrites(t *testing.T) {
	d := load(t)
	c := d.Cases[0]
	b := unpack(t, d.Worlds[c.BeforeSHA])
	s := schedule(t, c)
	for i := range s.TimerMinutes {
		s.TimerMinutes[i] = [4]byte{0x12, 0x34, 0x80, 0}
	}
	rec := b[PortStart : PortStart+RecordSize]
	for _, off := range []int{61, 65, 69} {
		v := encode(1000)
		copy(rec[off:off+4], v[:])
	}
	copy(rec[89:93], []byte{0xff, 0xff, 0xff, 0})
	rec[120] = 0xa5
	got, _, e := ReplayCleanPorts(b, s)
	if e != nil {
		t.Fatal(e)
	}
	if v, _ := integer([4]byte(got[41:45])); v != 3 {
		t.Fatal("first equal maximum must win")
	}
	for j := 0; j < 3; j++ {
		v, _ := integer([4]byte(got[73+4*j : 77+4*j]))
		if (j == 0) != (v > 0) {
			t.Fatal("coefficient class sign")
		}
	}
	if !bytes.Equal(got[89:93], rec[89:93]) || got[120] != 0xa5 || !bytes.Equal(got[101:105], s.TimerMinutes[0][:]) {
		t.Fatal("untouched bytes and raw timer residues")
	}
}
