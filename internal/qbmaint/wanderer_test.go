package qbmaint

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestWandererBirthNative(t *testing.T) {
	parent := load(t)
	raw, e := os.ReadFile("testdata/wanderer_birth.json")
	if e != nil {
		t.Fatal(e)
	}
	var d struct {
		Format   string
		Excluded []string `json:"excluded_later_encounters"`
		Cases    []struct {
			Name      string
			BeforeSHA string `json:"before_sha256"`
			Day       int
			Timer     string `json:"timer_hex"`
			State     uint32 `json:"initial_state"`
			Sector    int
			Seeded    uint32 `json:"seeded_state"`
			Final     uint32 `json:"final_state"`
			Record    string `json:"record_hex"`
			Link      string `json:"link_hex"`
		}
	}
	if e = json.Unmarshal(raw, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-wanderer-birth-v1" || len(d.Cases) != 29 || len(d.Excluded) != 3 {
		t.Fatal("birth coverage")
	}
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, parent.Worlds[c.BeforeSHA])
			saved := append([]byte(nil), before...)
			timer, e := hex.DecodeString(c.Timer)
			if e != nil || len(timer) != 4 {
				t.Fatal("raw timer")
			}
			out, stats, e := ReplayWandererBirth(before, WandererInputs{Day: c.Day, State: c.State, HelperTimer: [4]byte(timer)})
			if e != nil {
				t.Fatal(e)
			}
			record, e := hex.DecodeString(c.Record)
			if e != nil || len(record) != 137 {
				t.Fatal("record")
			}
			link, e := hex.DecodeString(c.Link)
			if e != nil || len(link) != 4 {
				t.Fatal("link")
			}
			at := (50+c.Sector)*RecordSize + 93
			if !bytes.Equal(out[4051*RecordSize:4052*RecordSize], record) || !bytes.Equal(out[at:at+4], link) {
				t.Fatal("native whole record/link")
			}
			if stats != (WandererStats{c.Sector, c.Seeded, c.Final, 1}) {
				t.Fatal("independent Python RNG model")
			}
			for i, b := range out {
				if !(i >= 4051*RecordSize && i < 4052*RecordSize) && !(i >= at && i < at+4) && b != before[i] {
					t.Fatalf("unrelated byte %d changed", i)
				}
			}
			if !bytes.Equal(before, saved) {
				t.Fatal("input mutated")
			}
			out[0] ^= 255
			if !bytes.Equal(before, saved) {
				t.Fatal("output alias")
			}
		})
	}
}
func TestWandererBirthAdmissionAndInheritance(t *testing.T) {
	parent := load(t)
	c := parent.Cases[0]
	source := unpack(t, parent.Worlds[c.BeforeSHA])
	valid := WandererInputs{Day: 306, State: 0xc805, HelperTimer: [4]byte{}}
	for name, input := range map[string]WandererInputs{"day": {Day: 0}, "state": {Day: 306, State: 0x1000000}, "negative-timer": {Day: 306, HelperTimer: encode(-1)}, "day-end": {Day: 306, HelperTimer: encode(86400)}} {
		t.Run(name, func(t *testing.T) {
			if got, stats, e := ReplayWandererBirth(source, input); e == nil || got != nil || stats != (WandererStats{}) {
				t.Fatal("unsupported input accepted")
			}
		})
	}
	if got, _, e := ReplayWandererBirth(source[:len(source)-1], valid); e == nil || got != nil {
		t.Fatal("extent")
	}
	for _, at := range []int{53, 50*RecordSize + 85, 4150*RecordSize + 85, (50+3000)*RecordSize + 93} {
		b := append([]byte(nil), source...)
		one := encode(1)
		copy(b[at:at+4], one[:])
		saved := append([]byte(nil), b...)
		if got, stats, e := ReplayWandererBirth(b, valid); e == nil || got != nil || stats != (WandererStats{}) || !bytes.Equal(b, saved) {
			t.Fatal("invalid world must fail atomically")
		}
	}
	b := append([]byte(nil), source...)
	at := 4051 * RecordSize
	b[at+133] = 0xa5
	copy(b[at+85:at+89], []byte{255, 255, 255, 0})
	out, _, e := ReplayWandererBirth(b, valid)
	if e != nil {
		t.Fatal(e)
	}
	if out[at+133] != 0xa5 || !bytes.Equal(out[at+57:at+61], []byte{0, 0, 0x1c, 0}) {
		t.Fatal("inherited field or native zero residue lost")
	}
	input := valid
	input.HelperTimer = [4]byte{1, 2, 128, 0}
	_, a, e := ReplayWandererBirth(source, input)
	if e != nil {
		t.Fatal(e)
	}
	_, z, e := ReplayWandererBirth(source, valid)
	if e != nil || a.SeededState == z.SeededState {
		t.Fatal("raw zero timer residue must affect seeding")
	}
}
