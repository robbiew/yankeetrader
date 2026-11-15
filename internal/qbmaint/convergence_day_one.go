package qbmaint

import (
	"fmt"
	"github.com/robbiew/yankeetrader/internal/qbmbf"
	"github.com/robbiew/yankeetrader/internal/qbrng"
)

// ConvergenceDayOneInputs supplies the three explicit creation DATE observations,
// raw Xannoron TIMER, modeled post-economy state and source-labelled helper prefix.
type ConvergenceDayOneInputs struct {
	State                             uint32
	WandererDay, XannoronDay, BaseDay int
	XannoronTimer                     [4]byte
	Helpers                           []ContinuationClock
}

// ConvergenceBirthStats contains model-derived creation receipts only.
type ConvergenceBirthStats struct {
	Created         [3]string
	InitialGround   int
	Bank, Timestamp [4]byte
	BaseAttempts    []int
}

// ReplayConvergenceDayOneHomes explicitly admits the retained day-one profile
// after planet economy and before the NPC tail. Ordinary and existing-home APIs
// stay strict. It never masks an active planet to pass another API's validation.
func ReplayConvergenceDayOneHomes(before []byte, in ConvergenceDayOneInputs) ([]byte, ContinuationStats, error) {
	fail := func(s string) ([]byte, ContinuationStats, error) {
		return nil, ContinuationStats{}, fmt.Errorf("convergence day one: %s", s)
	}
	if in.WandererDay != 306 || in.XannoronDay != 306 || in.BaseDay != 306 {
		return fail("all three source creation dates must be day 306")
	}
	v := portSingleValue(in.XannoronTimer)
	if v < 0 || v >= 86400 || v > 0 && v < portSingleValue([4]byte{0x0a, 0xd7, 0x23, 0x7a}) {
		return fail("zero or bounded centisecond creation TIMER")
	}
	return replayHomeContinuation(before, ContinuationInputs{State: in.State, Helpers: in.Helpers}, &in)
}

// These writers reuse the recovered assignment lists, including unassigned
// reserved-slot bytes and distinct FAC zeros. They do not reset whole records.
func restoreConvergenceWanderer(work []byte, day int) {
	rec := work[4051*RecordSize : 4052*RecordSize]
	for i := 0; i < 41; i++ {
		rec[i] = ' '
	}
	copy(rec, "The Wanderer")
	put := func(o int, b [4]byte) { copy(rec[o:o+4], b[:]) }
	put(41, encode(day-10))
	put(85, encode(12))
	put(73, [4]byte{})
	for _, o := range []int{45, 49, 53} {
		put(o, [4]byte{0, 0x40, 0x1c, 0x8d})
	}
	for _, o := range []int{57, 61, 65, 69, 77, 125} {
		put(o, [4]byte{0, 0, 0x1c, 0})
	}
	put(117, [4]byte{0, 0x24, 0x74, 0x92})
}
func restoreConvergenceXannoron(work []byte, in ConvergenceDayOneInputs, hq int, rng *qbrng.Generator) (int, [4]byte, [4]byte, error) {
	fail := func(s string) (int, [4]byte, [4]byte, error) {
		return 0, [4]byte{}, [4]byte{}, fmt.Errorf("Xannoron creation: %s", s)
	}
	var stamp [4]byte
	if in.XannoronTimer[3] == 0 {
		stamp = in.XannoronTimer
	} else {
		minutes, e := qbmbf.DivideSingle(in.XannoronTimer, encode(60))
		if e != nil {
			return fail("TIMER division")
		}
		stamp = qbmbf.IntSingle(minutes)
	}
	product, ok := qbmbf.MultiplySingle(portSingleBytes(rng.Float32()), encode(250))
	if !ok {
		return fail("ground product")
	}
	ground, ok := integer(qbmbf.IntSingle(product))
	if !ok {
		return fail("ground INT")
	}
	product, ok = qbmbf.MultiplySingle(portSingleBytes(rng.Float32()), encode(10000000))
	if !ok {
		return fail("bank product")
	}
	bank, ok := qbmbf.AddSingle(product, encode(100000))
	if !ok {
		return fail("bank sum")
	}
	rec := work[4150*RecordSize : 4151*RecordSize]
	for i := 0; i < 41; i++ {
		rec[i] = ' '
	}
	copy(rec, "Xannoron")
	put := func(o int, b [4]byte) { copy(rec[o:o+4], b[:]) }
	put(41, encode(in.XannoronDay))
	put(85, encode(8))
	put(89, stamp)
	for _, o := range []int{45, 49, 53} {
		put(o, [4]byte{0, 0x50, 0x43, 0x91})
	}
	for _, o := range []int{57, 61, 65, 69} {
		put(o, [4]byte{0, 0, 0x70, 0})
	}
	put(73, encode(-1))
	put(77, encode(ground))
	put(117, bank)
	put(125, [4]byte{})
	at := (50+hq)*RecordSize + 93
	b := encode(100)
	copy(work[at:at+4], b[:])
	return ground, bank, stamp, nil
}
func restoreConvergenceBase(work []byte, day int) {
	rec := work[4149*RecordSize : 4150*RecordSize]
	for i := 0; i < 41; i++ {
		rec[i] = ' '
	}
	copy(rec, "Mercenary Base")
	put := func(o int, b [4]byte) { copy(rec[o:o+4], b[:]) }
	put(41, encode(day-10))
	put(85, encode(14))
	for _, o := range []int{45, 49, 53} {
		put(o, [4]byte{0, 0x50, 0x43, 0x91})
	}
	for _, o := range []int{57, 61, 65, 69} {
		put(o, [4]byte{0, 0, 0xa0, 0})
	}
	put(73, [4]byte{0, 0, 0x80, 0x82})
	put(77, [4]byte{0, 0x7c, 0x12, 0x92})
	put(117, [4]byte{0x20, 0xbc, 0x3e, 0x99})
	put(125, [4]byte{0, 0, 0x3e, 0})
}
