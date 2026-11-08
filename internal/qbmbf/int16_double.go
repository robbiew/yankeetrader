package qbmbf

// Int16Double converts raw eight-byte MBF DOUBLE to signed16 using the measured
// default-mode BRUN30 INT3F/76 and /78 paths. Fractions round to nearest, with
// halves away from zero. Overflow returns (0, false); exponent-zero aliases
// convert to zero. The 56-bit significand is retained without float64 demotion.
// This operation does not select runtime mode 4 or change gameplay policies.
func Int16Double(raw [8]byte) (int16, bool) {
	if raw[7] == 0 || raw[7] < 128 {
		return 0, true
	}
	if raw[7] > 144 {
		return 0, false
	}
	mantissa := doubleBits(raw)&((uint64(1)<<55)-1) | uint64(1)<<55
	shift := uint(184 - raw[7])
	magnitude := (mantissa + uint64(1)<<(shift-1)) >> shift
	negative := raw[6]&128 != 0
	limit := uint64(32767)
	if negative {
		limit++
	}
	if magnitude > limit {
		return 0, false
	}
	if negative {
		return int16(-int32(magnitude)), true
	}
	return int16(magnitude), true
}
