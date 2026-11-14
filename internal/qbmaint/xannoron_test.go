package qbmaint

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

type xannoronCase struct {
	Name          string
	BeforeSHA     string `json:"before_sha256"`
	WandererDay   int    `json:"wanderer_day"`
	WandererTimer string `json:"wanderer_timer"`
	InitialState  uint32 `json:"initial_state"`
	Day           int
	Timer         string `json:"timer_hex"`
	State         uint32
	HQ, Ground    int
	Bank          string `json:"bank_hex"`
	Timestamp     string `json:"timestamp_hex"`
	Final         uint32 `json:"final_state"`
	Record        string `json:"record_hex"`
	Link          string `json:"link_hex"`
}

func xannoronFixture(t *testing.T) (fixture, []xannoronCase) {
	t.Helper()
	parent := load(t)
	raw, e := os.ReadFile("testdata/xannoron_birth.json")
	if e != nil {
		t.Fatal(e)
	}
	var d struct {
		Format string
		Cases  []xannoronCase
	}
	if e = json.Unmarshal(raw, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-xannoron-birth-v1" || len(d.Cases) != 32 {
		t.Fatal("Xannoron native coverage")
	}
	return parent, d.Cases
}
func raw4(t *testing.T, s string) [4]byte {
	t.Helper()
	b, e := hex.DecodeString(s)
	if e != nil || len(b) != 4 {
		t.Fatal("raw four-byte field")
	}
	return [4]byte(b)
}
func xannoronPrefix(t *testing.T, parent fixture, c xannoronCase) []byte {
	t.Helper()
	before := unpack(t, parent.Worlds[c.BeforeSHA])
	if digest(before) != c.BeforeSHA {
		t.Fatal("before digest")
	}
	out, stats, e := ReplayWandererBirth(before, WandererInputs{Day: c.WandererDay, State: c.InitialState, HelperTimer: raw4(t, c.WandererTimer)})
	if e != nil {
		t.Fatal(e)
	}
	if stats.FinalState != c.State {
		t.Fatal("independent modeled prefix RNG state")
	}
	return out
}
func TestXannoronNativeWithModeledPrefix(t *testing.T) {
	parent, cases := xannoronFixture(t)
	residues, whole := 0, 0
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			before := xannoronPrefix(t, parent, c)
			saved := append([]byte(nil), before...)
			out, stats, e := ReplayXannoronBirth(before, XannoronInputs{Day: c.Day, State: c.State, TimerSeconds: raw4(t, c.Timer)})
			if e != nil {
				t.Fatal(e)
			}
			record, e := hex.DecodeString(c.Record)
			if e != nil || len(record) != RecordSize {
				t.Fatal("native record")
			}
			link := raw4(t, c.Link)
			at := (50+c.HQ)*RecordSize + 93
			if !bytes.Equal(out[4150*RecordSize:4151*RecordSize], record) || !bytes.Equal(out[at:at+4], link[:]) {
				t.Fatal("whole native record/HQ link mismatch")
			}
			if stats != (XannoronStats{HQ: c.HQ, Ground: c.Ground, Draws: 3, Timestamp: raw4(t, c.Timestamp), Bank: raw4(t, c.Bank), FinalState: c.Final}) {
				t.Fatal("native fields / independent RNG model statistics")
			}
			for i, b := range out {
				if !(i >= 4150*RecordSize && i < 4151*RecordSize) && !(i >= at && i < at+4) && b != before[i] {
					t.Fatalf("unrelated byte changed: %d", i)
				}
			}
			if !bytes.Equal(before, saved) {
				t.Fatal("input mutated")
			}
			out[0] ^= 255
			if !bytes.Equal(before, saved) {
				t.Fatal("output aliases input")
			}
			if stats.Timestamp[3] == 0 {
				residues++
				if stats.Timestamp == ([4]byte{}) {
					t.Fatal("native sub-minute INT residue lost")
				}
			} else {
				whole++
			}
		})
	}
	if residues == 0 || whole == 0 {
		t.Fatal("sub-minute and whole-minute timestamp coverage")
	}
}
func TestXannoronAdmissionAndInheritedBytes(t *testing.T) {
	parent, cases := xannoronFixture(t)
	c := cases[0]
	source := xannoronPrefix(t, parent, c)
	valid := XannoronInputs{Day: c.Day, State: c.State, TimerSeconds: raw4(t, c.Timer)}
	for name, in := range map[string]XannoronInputs{"zero-ground": {Day: c.Day, State: 4382, TimerSeconds: valid.TimerSeconds}, "zero-day": {Day: 0}, "high-day": {Day: 733}, "high-state": {Day: 306, State: 0x1000000}, "zero-timer": {Day: 306}, "zero-alias": {Day: 306, TimerSeconds: [4]byte{1, 2, 128, 0}}, "sub-centisecond": {Day: 306, TimerSeconds: [4]byte{0, 0, 0, 1}}, "negative-timer": {Day: 306, TimerSeconds: encode(-1)}, "end-of-day": {Day: 306, TimerSeconds: encode(86400)}} {
		t.Run(name, func(t *testing.T) {
			if out, stats, e := ReplayXannoronBirth(source, in); e == nil || out != nil || stats != (XannoronStats{}) {
				t.Fatal("unsupported input admitted")
			}
		})
	}
	if out, _, e := ReplayXannoronBirth(source[:len(source)-1], valid); e == nil || out != nil {
		t.Fatal("extent")
	}
	fields := []int{53, 117, 51*RecordSize + 105, 50*RecordSize + 85, 4150*RecordSize + 85, (50+c.HQ)*RecordSize + 81, (50+c.HQ)*RecordSize + 85, (50+c.HQ)*RecordSize + 93}
	for _, at := range fields {
		b := append([]byte(nil), source...)
		value := encode(1)
		copy(b[at:at+4], value[:])
		saved := append([]byte(nil), b...)
		if out, stats, e := ReplayXannoronBirth(b, valid); e == nil || out != nil || stats != (XannoronStats{}) || !bytes.Equal(b, saved) {
			t.Fatalf("bad world at %d not rejected atomically", at)
		}
	}
	b := append([]byte(nil), source...)
	b[4051*RecordSize] = '?'
	if out, _, e := ReplayXannoronBirth(b, valid); e == nil || out != nil {
		t.Fatal("wrong predecessor")
	}
	b = append([]byte(nil), source...)
	b[4150*RecordSize+133] = 0xa5
	out, _, e := ReplayXannoronBirth(b, valid)
	if e != nil {
		t.Fatal(e)
	}
	if out[4150*RecordSize+133] != 0xa5 || !bytes.Equal(out[4150*RecordSize+57:4150*RecordSize+61], []byte{0, 0, 0x70, 0}) {
		t.Fatal("inheritance or stock-zero residue lost")
	}
}
