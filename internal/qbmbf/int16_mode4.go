package qbmbf

// Int16SingleMode4 applies the recovered BRUN30 signed16 conversion branch
// selected by runtime mode 4 to raw MBF SINGLE. It floors negative fractions
// rather than rounding to nearest. Overflow returns (0, false). The native
// evidence uses an explicit diagnostic mode-setting intervention; no normal
// gameplay caller is inferred or selected by this isolated API.
func Int16SingleMode4(raw [4]byte) (int16, bool) {
	mantissa := uint64(raw[0]) | uint64(raw[1])<<8 | uint64(raw[2]&127)<<16 | 1<<23
	return floorInt16(mantissa, raw[3], raw[2]&128 != 0, 24)
}

// Int16DoubleMode4 applies the same measured mode-4 branch to raw MBF DOUBLE,
// preserving its 56-bit significand. It floors toward negative infinity and
// reports signed16 overflow explicitly. It does not change runtime mode or
// gameplay selection, and does not convert through float64.
func Int16DoubleMode4(raw [8]byte) (int16, bool) {
	mantissa := doubleBits(raw)&((uint64(1)<<55)-1) | uint64(1)<<55
	return floorInt16(mantissa, raw[7], raw[6]&128 != 0, 56)
}

func floorInt16(mantissa uint64, exponent byte, negative bool, precision uint) (int16, bool) {
	if exponent == 0 {
		return 0, true
	}
	if exponent <= 128 {
		if negative {
			return -1, true
		}
		return 0, true
	}
	if exponent > 144 {
		return 0, false
	}
	shift := 128 + precision - uint(exponent)
	magnitude := mantissa >> shift
	if negative && mantissa&((uint64(1)<<shift)-1) != 0 {
		magnitude++
	}
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
