package qbmbf

import "math/bits"

// FixDouble applies BRUN30 DOUBLE FIX to raw eight-byte MBF data. MBF DOUBLE
// has a 56-bit significand; converting through float64 would lose input bits.
// Numeric zeros preserve sign/mantissa residue, including subunit results.
func FixDouble(raw [8]byte) [8]byte {
	if raw[7] == 0 || raw[7] >= 184 {
		return raw
	}
	if raw[7] <= 128 {
		raw[7] = 0
		return raw
	}
	shift := uint(184 - raw[7])
	encoded := doubleBits(raw) &^ ((uint64(1) << shift) - 1)
	return doubleRaw(encoded, raw[7])
}

// IntDouble applies BRUN30 DOUBLE INT, flooring negative fractions instead of
// truncating them toward zero. Exponent-zero inputs preserve all eight bytes.
// This primitive does not select a new gameplay or source-generation policy.
func IntDouble(raw [8]byte) [8]byte {
	if raw[7] == 0 || raw[7] >= 184 {
		return raw
	}
	if raw[6]&128 == 0 {
		return FixDouble(raw)
	}
	if raw[7] <= 128 {
		return [8]byte{0, 0, 0, 0, 0, 0, 128, 129}
	}
	const hidden = uint64(1) << 55
	shift := uint(184 - raw[7])
	mantissa := (doubleBits(raw) & (hidden - 1)) | hidden
	whole := mantissa >> shift
	if mantissa&((uint64(1)<<shift)-1) != 0 {
		whole++
	}
	length := bits.Len64(whole)
	encoded := ((whole << uint(56-length)) & (hidden - 1)) | hidden
	return doubleRaw(encoded, byte(128+length))
}

func doubleBits(raw [8]byte) uint64 {
	var value uint64
	for i := 0; i < 7; i++ {
		value |= uint64(raw[i]) << uint(8*i)
	}
	return value
}

func doubleRaw(value uint64, exponent byte) [8]byte {
	var result [8]byte
	for i := 0; i < 7; i++ {
		result[i] = byte(value >> uint(8*i))
	}
	result[7] = exponent
	return result
}
