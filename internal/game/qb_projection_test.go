package game

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"math"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/qbinit"
)

func TestQBProjectionNativeAdmissionAndBootstrap(t *testing.T) {
	now := time.Date(2032, 6, 13, 14, 15, 0, 0, time.FixedZone("operator", -7*3600))
	for _, state := range []uint32{0xc805, 0x61b205, 0x275905} {
		t.Run(fmt.Sprintf("%06x", state), func(t *testing.T) {
			input := qbinit.Options{State: state, Date: "2027-01-01"}
			source, err := qbinit.Generate(input)
			if err != nil {
				t.Fatal(err)
			}
			original := append([]byte(nil), source.Bytes...)
			c, err := prepareQBWorld(now, 36, input)
			if err != nil {
				t.Fatal(err)
			}
			w := c.world
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
			if c.sourceSHA256 != sha256.Sum256(source.Bytes) || c.stats != source.Stats || c.inputs != input {
				t.Fatal("source provenance/stream lost")
			}
			if !bytes.Equal(original, source.Bytes) {
				t.Fatal("source bytes mutated")
			}
			if w.Created != now.UTC() || w.LastMaintenance != "2032-06-13" || len(w.Players) != 0 || len(w.Planets) != 3 {
				t.Fatal("old DOS dates/inactive records became live state")
			}
			if !reflect.DeepEqual(w.Sectors[1].Warps, []int{2, 3, 4, 5, 6}) {
				t.Fatal("Earth warp order/self-link projection")
			}
			if w.Xannor.HQ != source.Stats.HQ || w.Xannor.Reserve != 0 || w.xannorHome().Sector != w.Xannor.HQ || w.Sectors[w.Xannor.HQ].Defense.Fighters != 10000 {
				t.Fatal("bootstrap displaced or doubled HQ force")
			}
			if w.wanderer() == nil {
				t.Fatal("required Wanderer missing")
			}
			for _, p := range w.Ports {
				if p.Owner != 0 || p.Treasury != 0 || p.Updated != now.UTC() {
					t.Fatal("initial port ownership/watermark")
				}
				for good := 0; good < 3; good++ {
					if p.Supply[good] != 10*p.Production[good] {
						t.Fatal("initial production not materialized once")
					}
				}
			}
			if state == 0xc805 {
				earth := w.Ports[1]
				if earth.Production != [3]float64{18616, 30871, 10578} || earth.Coefficient != [3]float64{61, -75, -63} {
					t.Fatal("native Earth economy changed")
				}
			}
		})
	}
}

func TestQBProjectionRejectsNativeCollisionProtectedHQAndBudget(t *testing.T) {
	for _, test := range []struct {
		options qbinit.Options
		message string
	}{
		{qbinit.Options{State: 0xa90a05, Date: "2026-11-02"}, "duplicate port"},
		{qbinit.Options{State: 619, Date: "2026-11-02"}, "HQ"},
		{qbinit.Options{State: 0xc805, Date: "2026-11-02", DrawLimit: 10}, "draw limit"},
		{qbinit.Options{State: 0x1000000, Date: "2026-11-02"}, "24 bits"},
	} {
		candidate, err := prepareQBWorld(clock, 36, test.options)
		if candidate != nil || err == nil || !strings.Contains(err.Error(), test.message) {
			t.Fatalf("partial/incorrect admission: %v %v", candidate, err)
		}
	}
}

func setQBNumber(raw []byte, rec, offset int, value float32) {
	at := (rec-1)*qbinit.RecordSize + offset
	if value == 0 {
		copy(raw[at:at+4], []byte{0, 0, 0, 0})
		return
	}
	b := math.Float32bits(value)
	copy(raw[at:at+4], []byte{byte(b), byte(b >> 8), byte((b>>16)&0x7f) | byte((b>>24)&0x80), byte((b>>23)&255) + 2})
}

func TestQBProjectionRejectsMalformedSourceWithoutMutation(t *testing.T) {
	base, err := qbinit.Generate(qbinit.Options{State: 0xc805, Date: "2026-11-02"})
	if err != nil {
		t.Fatal(err)
	}
	cases := map[string]func(*qbinit.Result){
		"truncated":       func(s *qbinit.Result) { s.Bytes = s.Bytes[:100] },
		"layout":          func(s *qbinit.Result) { setQBNumber(s.Bytes, 1, 53, 50) },
		"HQ metadata":     func(s *qbinit.Result) { s.Stats.HQ++ },
		"HQ pointer":      func(s *qbinit.Result) { setQBNumber(s.Bytes, 52, 105, 8) },
		"fractional warp": func(s *qbinit.Result) { setQBNumber(s.Bytes, 54, 41, 3.5) },
		"warp bounds":     func(s *qbinit.Result) { setQBNumber(s.Bytes, 54, 41, 3001) },
		"self warp":       func(s *qbinit.Result) { setQBNumber(s.Bytes, 54, 41, 3) },
		"duplicate warp":  func(s *qbinit.Result) { setQBNumber(s.Bytes, 54, 41, 2); setQBNumber(s.Bytes, 54, 45, 2) },
		"defense":         func(s *qbinit.Result) { setQBNumber(s.Bytes, 51+s.Stats.HQ, 81, 9999) },
		"orphan link":     func(s *qbinit.Result) { setQBNumber(s.Bytes, 52, 65, 2) },
		"production":      func(s *qbinit.Result) { setQBNumber(s.Bytes, 3052, 61, 0) },
		"coefficients":    func(s *qbinit.Result) { setQBNumber(s.Bytes, 3052, 73, -61) },
		"name":            func(s *qbinit.Result) { s.Bytes[3051*137] = 0 },
		"source stock":    func(s *qbinit.Result) { setQBNumber(s.Bytes, 3052, 49, 1) },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			source := qbinit.Result{Bytes: append([]byte(nil), base.Bytes...), Stats: base.Stats}
			change(&source)
			before := append([]byte(nil), source.Bytes...)
			candidate, err := projectQBSource(clock, 36, source)
			if candidate != nil || err == nil {
				t.Fatal("unsafe source admitted")
			}
			if !bytes.Equal(source.Bytes, before) {
				t.Fatal("rejected source mutated")
			}
		})
	}
	if c, err := projectQBSource(time.Time{}, 36, base); c != nil || err == nil {
		t.Fatal("zero clock admitted")
	}
}

func TestQBProjectionRejectsOneWayConnectivity(t *testing.T) {
	source, err := qbinit.Generate(qbinit.Options{State: 0xc805, Date: "2026-11-02"})
	if err != nil {
		t.Fatal(err)
	}
	// A directed path reaches every sector from Earth, but nothing can return.
	// This isolates the reverse-connectivity admission gate.
	for sector := 1; sector <= 3000; sector++ {
		for col := 0; col < 6; col++ {
			setQBNumber(source.Bytes, 51+sector, 41+4*col, 0)
		}
		if sector < 3000 {
			setQBNumber(source.Bytes, 51+sector, 41, float32(sector+1))
		}
	}
	candidate, err := projectQBSource(clock, 36, source)
	if candidate != nil || err == nil || !strings.Contains(err.Error(), "forward/reverse") {
		t.Fatalf("one-way graph admitted: %v", err)
	}
}

func TestQBProjectionReproducibilityAndIndependentBootstrap(t *testing.T) {
	input := qbinit.Options{State: 0xc805, Date: "2026-11-02"}
	a, err := prepareQBWorld(clock, 36, input)
	if err != nil {
		t.Fatal(err)
	}
	b, err := prepareQBWorld(clock, 36, input)
	if err != nil {
		t.Fatal(err)
	}
	c, err := prepareQBWorld(clock, 77, input)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(a, b) {
		t.Fatal("same inputs changed candidate")
	}
	if a.sourceSHA256 != c.sourceSHA256 || a.stats != c.stats || !reflect.DeepEqual(a.world.Ports, c.world.Ports) {
		t.Fatal("bootstrap changed source stream/economy")
	}
	for id, s := range a.world.Sectors {
		if !reflect.DeepEqual(s.Warps, c.world.Sectors[id].Warps) || s.Port != c.world.Sectors[id].Port {
			t.Fatal("bootstrap changed source map")
		}
	}
	if reflect.DeepEqual(a.world.Planets, c.world.Planets) {
		t.Fatal("modern bootstrap no longer independently seeded")
	}
	a.world.Sectors[1].Warps[0] = 999
	if b.world.Sectors[1].Warps[0] == 999 {
		t.Fatal("candidate maps share mutable storage")
	}
}
