// Package qbmbf implements the recovered raw MBF SINGLE/DOUBLE INT and FIX operations. It is not a
// complete MBF arithmetic runtime. Existing gameplay and generation arithmetic
// retain their current policies and do not select this primitive automatically.
package qbmbf

import "math/bits"

// IntSingle applies the recovered BRUN30 SINGLE INT path to four raw MBF bytes.
// It floors negative fractions toward negative infinity. Exponent-zero inputs
// retain all original bytes. Positive subunit values become numeric zero by
// clearing only the exponent; their mantissa residue must not be normalized.
func IntSingle(raw [4]byte) [4]byte {
	if raw[3] == 0 || raw[3] >= 152 {
		return raw
	}
	negative := raw[2]&128 != 0
	if raw[3] <= 128 {
		if negative {
			return [4]byte{0, 0, 128, 129}
		}
		raw[3] = 0
		return raw
	}
	shift := uint(152 - raw[3])
	mantissa := uint32(raw[0]) | uint32(raw[1])<<8 | uint32(raw[2]&127)<<16
	mask := uint32(1)<<shift - 1
	if !negative {
		mantissa &^= mask
		return [4]byte{byte(mantissa), byte(mantissa >> 8), byte(mantissa >> 16), raw[3]}
	}
	mantissa |= 1 << 23
	whole := mantissa >> shift
	if mantissa&mask != 0 {
		whole++
	}
	length := bits.Len32(whole)
	encoded := (whole << uint(24-length)) & 0x7fffff
	encoded |= 0x800000
	return [4]byte{byte(encoded), byte(encoded >> 8), byte(encoded >> 16), byte(128 + length)}
}
