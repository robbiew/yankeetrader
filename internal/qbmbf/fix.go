package qbmbf

// FixSingle applies the recovered BRUN30 SINGLE FIX path to four raw MBF bytes.
// It removes fractional bits without rounding away from zero. Exponent-zero
// inputs retain every byte. Subunit results clear only the exponent, preserving
// the sign and mantissa residue even when their numeric value becomes zero.
func FixSingle(raw [4]byte) [4]byte {
	if raw[3] == 0 || raw[3] >= 152 {
		return raw
	}
	if raw[3] <= 128 {
		raw[3] = 0
		return raw
	}
	shift := uint(152 - raw[3])
	mantissa := uint32(raw[0]) | uint32(raw[1])<<8 | uint32(raw[2])<<16
	mantissa &^= (uint32(1) << shift) - 1
	return [4]byte{byte(mantissa), byte(mantissa >> 8), byte(mantissa >> 16), raw[3]}
}
