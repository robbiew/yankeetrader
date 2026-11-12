package qbmbf

import "math/bits"

// MultiplyDouble models BRUN30 INT3F/92: left is the initial raw DOUBLE FAC,
// and right is memory. This isolated API preserves all 56 significand bits
// without selecting a gameplay, generation or save policy.
func MultiplyDouble(left, right [8]byte) ([8]byte, bool) {
	return MultiplyDoubleWithFAC(left, right, left)
}

// MultiplyDoubleWithFAC models INT3F/90 memory times memory with independent
// initialFAC. INT3F/94 memory times FAC passes right as initialFAC. Zero operands
// and pre-round underflow clear only the original FAC exponent, retaining seven
// residue bytes. Products round to nearest with ties to even. Overflow returns
// a zero array and false without claiming native post-error FAC state.
// Inline /96 and arbitrary error/unwind contexts are outside this contract.
func MultiplyDoubleWithFAC(left, right, initialFAC [8]byte) ([8]byte, bool) {
	zero := func() ([8]byte, bool) { initialFAC[7] = 0; return initialFAC, true }
	if left[7] == 0 || right[7] == 0 {
		return zero()
	}
	const hidden = uint64(1) << 55
	mantissa := func(raw [8]byte) uint64 { return doubleBits(raw)&(hidden-1) | hidden }
	// Two 56-bit significands require 112 exact bits. The shift is 55 or 56,
	// so all discarded guard/sticky information is contained in the low word.
	hi, lo := bits.Mul64(mantissa(left), mantissa(right))
	length := 64 + bits.Len64(hi)
	exponent := int(left[7]) + int(right[7]) - 129 + length - 111
	if exponent <= 0 {
		return zero()
	}
	if exponent > 255 {
		return [8]byte{}, false
	}
	shift := uint(length - 56)
	rounded := hi<<(64-shift) | lo>>shift
	remainder := lo & ((uint64(1) << shift) - 1)
	half := uint64(1) << (shift - 1)
	if remainder > half || (remainder == half && rounded&1 != 0) {
		rounded++
	}
	if rounded == 1<<56 {
		rounded >>= 1
		exponent++
	}
	if exponent > 255 {
		return [8]byte{}, false
	}
	encoded := rounded & (hidden - 1)
	encoded |= uint64((left[6]^right[6])&128) << 48
	return doubleRaw(encoded, byte(exponent)), true
}
