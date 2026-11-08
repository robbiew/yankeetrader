package qbmbf

// Int16Single converts raw MBF SINGLE to a signed 16-bit integer using the
// recovered BRUN30 INT3F/75 and /77 path in its measured default mode (zero).
// Fractions round to nearest, with exact halves away from zero. The boolean
// reports whether the rounded value fits; overflow returns (0, false).
// Exponent-zero encodings all convert to zero. This isolated operation does
// not select runtime mode 4, convert DOUBLE, or change gameplay/save policies.
func Int16Single(raw [4]byte) (int16, bool) {
	if raw[3] == 0 || raw[3] < 128 {
		return 0, true
	}
	if raw[3] > 144 {
		return 0, false
	}
	mantissa := uint32(raw[0]) | uint32(raw[1])<<8 | uint32(raw[2]&127)<<16 | 1<<23
	shift := uint(152 - raw[3])
	magnitude := (mantissa + 1<<(shift-1)) >> shift
	negative := raw[2]&128 != 0
	limit := uint32(32767)
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
