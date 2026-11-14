package qbmaint

import (
	"fmt"
	"math/bits"

	"github.com/robbiew/yankeetrader/internal/qbmbf"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

type XannoronInputs struct {
	Day          int
	State        uint32 // Modeled state after the preceding Wanderer placement draw.
	TimerSeconds [4]byte
}
type XannoronStats struct {
	HQ, Ground, Draws int
	Timestamp, Bank   [4]byte
	FinalState        uint32
}

// ReplayXannoronBirth creates only reserved planet 4151 and the initial HQ link.
// The input is an independently modeled post-Wanderer, pre-mobile-group world.
// Clock/state origins are authenticated by the caller. No targets are inputs.
// This slice admits nonzero DOS TIMER values, nonzero resulting ground defense,
// and an unoccupied HQ planet link. Zero-TIMER policy, later phases and gameplay
// integration remain separate. Errors return no partial world or statistics.
func ReplayXannoronBirth(before []byte, in XannoronInputs) ([]byte, XannoronStats, error) {
	fail := func(s string) ([]byte, XannoronStats, error) {
		return nil, XannoronStats{}, fmt.Errorf("Xannoron birth: %s", s)
	}
	if len(before) != WorldRecords*RecordSize || in.Day < 1 || in.Day > 732 || in.State > 0xffffff {
		return fail("default world and bounded source day/state required")
	}
	read := func(record, off int) [4]byte { at := (record-1)*RecordSize + off; return [4]byte(before[at : at+4]) }
	for off, want := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		v, ok := integer(read(1, off))
		if !ok || v != want {
			return fail("default geometry required")
		}
	}
	minTimer := [4]byte{0x0a, 0xd7, 0x23, 0x7a} // Nearest raw SINGLE to one centisecond.
	if qbmbf.SignZeroSingle(in.TimerSeconds).Carry || qbmbf.CompareSingle(in.TimerSeconds, minTimer).Carry || !qbmbf.CompareSingle(in.TimerSeconds, encode(86400)).Carry {
		return fail("nonzero DOS TIMER range required")
	}
	hq, ok := integer(read(1, 117))
	if !ok || hq < 8 || hq > 3000 {
		return fail("configured HQ range")
	}
	tracked, ok := integer(read(52, 105))
	if !ok || tracked != hq {
		return fail("tracked HQ differs")
	}
	for r := 2; r <= 51; r++ {
		if read(r, 85)[3] != 0 {
			return fail("active player outside profile")
		}
	}
	wanderer := before[4051*RecordSize : 4052*RecordSize]
	if string(wanderer[:12]) != "The Wanderer" || read(4052, 85) != encode(12) || read(4052, 73)[3] != 0 {
		return fail("modeled Wanderer predecessor required")
	}
	for r := 4053; r <= 4151; r++ {
		if read(r, 85)[3] != 0 {
			return fail("additional active planet outside profile")
		}
	}
	links := 0
	for sector := 1; sector <= 3000; sector++ {
		force, good := integer(read(51+sector, 81))
		want := 0
		if sector == hq {
			want = 10000
		}
		if !good || force != want {
			return fail("initial sector force profile required")
		}
		owner := read(51+sector, 85)
		if sector == hq && owner != encode(-1) {
			return fail("initial HQ owner required")
		}
		link, good := integer(read(51+sector, 93))
		if !good || link < 0 || link > 1 {
			return fail("only initial Wanderer link admitted")
		}
		if link == 1 {
			links++
		}
		if sector == hq && link != 0 {
			return fail("occupied HQ outside profile")
		}
	}
	if links != 1 {
		return fail("one modeled Wanderer sector link required")
	}
	minutes, err := qbmbf.DivideSingle(in.TimerSeconds, encode(60))
	if err != nil {
		return fail("TIMER division outside profile")
	}
	timestamp := qbmbf.IntSingle(minutes)
	rng := qbrng.New(in.State)
	rnd := func() [4]byte {
		rng.Float32()
		n := rng.State()
		if n == 0 {
			return [4]byte{}
		}
		length := bits.Len32(n)
		m := (n << uint(24-length)) & 0x7fffff
		return [4]byte{byte(m), byte(m >> 8), byte(m >> 16), byte(104 + length)}
	}
	product, good := qbmbf.MultiplySingle(rnd(), encode(250))
	if !good {
		return fail("ground product")
	}
	ground, good := integer(qbmbf.IntSingle(product))
	if !good {
		return fail("ground INT")
	}
	product, good = qbmbf.MultiplySingle(rnd(), encode(10000000))
	if !good {
		return fail("bank product")
	}
	bank, good := qbmbf.AddSingle(product, encode(100000))
	if !good {
		return fail("bank sum")
	}
	product, good = qbmbf.MultiplySingle(rnd(), encode(25))
	if !good {
		return fail("ground supplement")
	}
	extra, good := integer(qbmbf.IntSingle(product))
	if !good {
		return fail("supplement INT")
	}
	ground += extra
	if ground < 1 || ground > 273 {
		return fail("zero/out-of-range ground outside admitted birth profile")
	}
	out := append([]byte(nil), before...)
	rec := out[4150*RecordSize : 4151*RecordSize]
	for i := 0; i < 41; i++ {
		rec[i] = ' '
	}
	copy(rec[:41], "Xannoron")
	put := func(off int, v [4]byte) { copy(rec[off:off+4], v[:]) }
	put(41, encode(in.Day))
	put(85, encode(8))
	put(89, timestamp)
	for _, off := range []int{45, 49, 53} {
		put(off, [4]byte{0, 0x50, 0x43, 0x91})
	}
	for _, off := range []int{57, 61, 65, 69} {
		put(off, [4]byte{0, 0, 0x70, 0})
	}
	put(73, encode(-1))
	put(77, encode(ground))
	put(117, bank)
	put(125, [4]byte{})
	link := (50+hq)*RecordSize + 93
	v := encode(100)
	copy(out[link:link+4], v[:])
	return out, XannoronStats{HQ: hq, Ground: ground, Draws: 3, Timestamp: timestamp, Bank: bank, FinalState: rng.State()}, nil
}
