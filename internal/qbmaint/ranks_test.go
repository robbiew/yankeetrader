package qbmaint

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func rankWrites(b []byte) []byte {
	out := append([]byte(nil), b[81:85]...)
	for i := 1; i <= 50; i++ {
		at := i*RecordSize + 109
		out = append(out, b[at:at+4]...)
	}
	return out
}
func TestInactiveRanksNative(t *testing.T) {
	parent := load(t)
	raw, e := os.ReadFile("testdata/inactive_ranks.json")
	if e != nil {
		t.Fatal(e)
	}
	var d struct {
		Format string
		Cases  []struct {
			Name      string
			BeforeSHA string `json:"before_sha256"`
			Day       int    `json:"final_day"`
			Writes    string `json:"writes_hex"`
		}
	}
	if e = json.Unmarshal(raw, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-inactive-ranks-v1" || len(d.Cases) != 32 {
		t.Fatal("rank fixture coverage")
	}
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, parent.Worlds[c.BeforeSHA])
			saved := append([]byte(nil), before...)
			got, e := ReplayInactiveRanks(before, c.Day)
			if e != nil {
				t.Fatal(e)
			}
			want, e := hex.DecodeString(c.Writes)
			if e != nil || len(want) != 204 {
				t.Fatal("native writer fields")
			}
			if !bytes.Equal(rankWrites(got), want) {
				t.Fatal("all native fields must match")
			}
			for i, b := range got {
				writable := i >= 81 && i < 85
				rec, off := i/RecordSize, i%RecordSize
				writable = writable || (rec >= 1 && rec <= 50 && off >= 109 && off < 113)
				if !writable && b != before[i] {
					t.Fatalf("unrelated world byte changed: %d", i)
				}
			}
			if !bytes.Equal(before, saved) {
				t.Fatal("before-world mutated")
			}
			got[0] ^= 255
			if !bytes.Equal(before, saved) {
				t.Fatal("output aliases input")
			}
		})
	}
}
func TestInactiveRanksAdmissionAndResidues(t *testing.T) {
	d := load(t)
	c := d.Cases[0]
	source := unpack(t, d.Worlds[c.BeforeSHA])
	for _, day := range []int{-1, 0, 733} {
		if got, e := ReplayInactiveRanks(source, day); e == nil || got != nil {
			t.Fatal("day range")
		}
	}
	if got, e := ReplayInactiveRanks(source[:len(source)-1], 1); e == nil || got != nil {
		t.Fatal("world extent")
	}
	for _, at := range []int{53, 50*RecordSize + 85} {
		b := append([]byte(nil), source...)
		v := encode(1)
		copy(b[at:at+4], v[:])
		saved := append([]byte(nil), b...)
		if got, e := ReplayInactiveRanks(b, 1); e == nil || got != nil || !bytes.Equal(b, saved) {
			t.Fatal("invalid profile must be atomic")
		}
	}
	b := append([]byte(nil), source...)
	copy(b[RecordSize+85:RecordSize+89], []byte{0xff, 0xff, 0xff, 0})
	copy(b[RecordSize+109:RecordSize+113], []byte{1, 2, 3, 4})
	out, e := ReplayInactiveRanks(b, 732)
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(out[RecordSize+85:RecordSize+89], b[RecordSize+85:RecordSize+89]) {
		t.Fatal("inactive zero residue normalized")
	}
	v, _ := integer([4]byte(out[RecordSize+109 : RecordSize+113]))
	if v != -1 {
		t.Fatal("rank cache not reset")
	}
}
