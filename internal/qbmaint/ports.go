// Package qbmaint contains bounded research replays of original DOS maintenance.
// It does not load modern saves or select playable maintenance policy.
package qbmaint

import (
	"fmt"
	"math/bits"

	"github.com/robbiew/yankeetrader/internal/qbmbf"
)

const (
	RecordSize   = 137
	WorldRecords = 4151
	PortCount    = 1000
	PortStart    = 3051 * RecordSize // Zero-based start of the first non-Earth port.
)

// PortSchedule carries explicit source-qualified calendar and raw TIMER/60
// observations. Capped admits the saved-base-year matrix's at-least-ten-day
// ports and one midnight timer wrap; otherwise all dates must be one DOY.
// The caller authenticates observations; this API checks values and ordering.
type PortSchedule struct {
	Days         []int
	TimerMinutes [][4]byte
	Capped       bool
}

type PortStats struct {
	Ports, Bytes, Day, ElapsedDays int
	ClassCounts                    [3]int
}

// ReplayCleanPorts synthesizes only the complete 137000-byte port block from a
// before-world and explicit schedule. It accepts no after-world or correction
// table. Populated ports, fractional rates, arbitrary elapsed production and
// other maintenance phases are outside its contract. Errors return no block;
// inputs are readonly and raw zero aliases/timer residues are not normalized.
func ReplayCleanPorts(before []byte, schedule PortSchedule) ([]byte, PortStats, error) {
	fail := func(message string) ([]byte, PortStats, error) {
		return nil, PortStats{}, fmt.Errorf("clean-port replay: %s", message)
	}
	if len(before) != WorldRecords*RecordSize || len(schedule.Days) != PortCount || len(schedule.TimerMinutes) != PortCount {
		return fail("default world and 1000 calendar/timer inputs required")
	}
	read := func(rec []byte, off int) [4]byte { return [4]byte(rec[off : off+4]) }
	for off, want := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
		v, ok := integer(read(before, off))
		if !ok || v != want {
			return fail("default record geometry required")
		}
	}
	first := schedule.Days[0]
	last := first
	drops := 0
	for i, day := range schedule.Days {
		if day < 1 || day > 732 {
			return fail("calendar day outside admitted range")
		}
		if !schedule.Capped && (day != first || day > 366) {
			return fail("strict profile requires one Gregorian day")
		}
		if schedule.Capped && (day < last || day-first > 1) {
			return fail("matrix calendar may advance at most one day")
		}
		last = day
		timer := schedule.TimerMinutes[i]
		if qbmbf.SignZeroSingle(timer).Carry || !qbmbf.CompareSingle(timer, encode(1440)).Carry {
			return fail("timer outside [0,1440)")
		}
		if i > 0 && qbmbf.CompareSingle(timer, schedule.TimerMinutes[i-1]).Carry {
			drops++
			previous := qbmbf.CompareSingle(schedule.TimerMinutes[i-1], encode(1439))
			if !schedule.Capped || drops > 1 || previous.Carry || previous.Zero || !qbmbf.CompareSingle(timer, encode(1)).Carry {
				return fail("unadmitted timer rollback")
			}
		}
	}
	block := append([]byte(nil), before[PortStart:PortStart+PortCount*RecordSize]...)
	stats := PortStats{Ports: PortCount, Bytes: len(block), ElapsedDays: 10}
	if first == last {
		stats.Day = first
	}
	for i := 0; i < PortCount; i++ {
		rec := block[i*RecordSize : (i+1)*RecordSize]
		day := schedule.Days[i]
		old, ok := integer(read(rec, 45))
		if !ok || old < -9 || old > 722 || (!schedule.Capped && old != day-10) || (schedule.Capped && old > day-10) {
			return fail("only clean ten-day/capped initial ports admitted")
		}
		for _, off := range []int{49, 53, 57, 89, 97, 101} {
			if read(rec, off)[3] != 0 {
				return fail("nonempty port outside profile")
			}
		}
		var stocks, coefficients [3]int
		for j := 0; j < 3; j++ {
			rate, ok := integer(read(rec, 61+4*j))
			if !ok || rate < 1000 || rate > 32766 {
				return fail("initial integer rate bounds")
			}
			stocks[j] = rate * 10
			coefficient, ok := integer(read(rec, 73+4*j))
			if !ok || coefficient == 0 || coefficient < -100 || coefficient > 100 {
				return fail("initial integer coefficient bounds")
			}
			if coefficient < 0 {
				coefficient = -coefficient
			}
			coefficients[j] = coefficient
		}
		selected := 0
		for j := 1; j < 3; j++ {
			if stocks[j] > stocks[selected] {
				selected = j
			}
		}
		class := 3 - selected
		stats.ClassCounts[class-1]++
		put := func(off, value int) { raw := encode(value); copy(rec[off:off+4], raw[:]) }
		put(41, class)
		put(45, day)
		for j := 0; j < 3; j++ {
			put(49+4*j, stocks[j])
			sign := -1
			if j == selected {
				sign = 1
			}
			put(73+4*j, sign*coefficients[j])
		}
		copy(rec[101:105], schedule.TimerMinutes[i][:])
	}
	return block, stats, nil
}

// integer admits only exactly integral raw MBF values in a bounded signed range.
// Exponent-zero aliases ignore their sign/fraction residue.
func integer(raw [4]byte) (int, bool) {
	if raw[3] == 0 {
		return 0, true
	}
	m := uint64(raw[0]) | uint64(raw[1])<<8 | uint64(raw[2]&127)<<16 | 1<<23
	shift := int(raw[3]) - 152
	if shift >= 0 {
		if shift > 7 {
			return 0, false
		}
		m <<= uint(shift)
	} else {
		n := uint(-shift)
		if n > 23 || m&((uint64(1)<<n)-1) != 0 {
			return 0, false
		}
		m >>= n
	}
	v := int(m)
	if raw[2]&128 != 0 {
		v = -v
	}
	return v, true
}

// All values written by this profile are exact integers below 2^24.
func encode(value int) [4]byte {
	if value == 0 {
		return [4]byte{}
	}
	negative := value < 0
	if negative {
		value = -value
	}
	length := bits.Len(uint(value))
	m := uint32(value) << uint(24-length) & 0x7fffff
	if negative {
		m |= 0x800000
	}
	return [4]byte{byte(m), byte(m >> 8), byte(m >> 16), byte(128 + length)}
}
