package qbmbf

import "math/bits"

// MultiplySingle models BRUN30 INT3F/91: left is the initial raw SINGLE FAC,
// right is memory. Zero and underflow clear only the initial FAC exponent;
// overflow returns a zero array and false without claiming native post-error
// FAC contents. This isolated primitive selects no gameplay or generation policy.
func MultiplySingle(left, right [4]byte) ([4]byte, bool) {
	return MultiplySingleWithFAC(left, right, left)
}

// MultiplySingleWithFAC models INT3F/8f memory-times-memory with independent
// initialFAC. INT3F/93 (memory times FAC) passes right as initialFAC. Products
// round to 24 significant bits with ties to even. Native underflow is tested
// before rounding, even when rounding would carry into the minimum binade.
// Exponent-zero operands retain initialFAC's residue rather than either operand
// or a canonical zero. Inline INT3F/95 frames are outside this contract.
func MultiplySingleWithFAC(left, right, initialFAC [4]byte) ([4]byte, bool) {
	zero := func() ([4]byte, bool) { initialFAC[3] = 0; return initialFAC, true }
	if left[3] == 0 || right[3] == 0 {
		return zero()
	}
	mantissa := func(raw [4]byte) uint64 {
		return uint64(raw[0]) | uint64(raw[1])<<8 | uint64(raw[2]&127)<<16 | 1<<23
	}
	// Two 24-bit significands fit exactly in 48 bits, including all guard/sticky
	// information retained by the native partial-product helper.
	product := mantissa(left) * mantissa(right)
	length := bits.Len64(product) // 47 or 48 because both hidden bits are set.
	exponent := int(left[3]) + int(right[3]) - 129 + length - 47
	if exponent <= 0 {
		return zero()
	}
	if exponent > 255 {
		return [4]byte{}, false
	}
	shift := uint(length - 24)
	rounded := product >> shift
	remainder := product & ((uint64(1) << shift) - 1)
	half := uint64(1) << (shift - 1)
	if remainder > half || (remainder == half && rounded&1 != 0) {
		rounded++
	}
	if rounded == 1<<24 {
		rounded >>= 1
		exponent++
	}
	if exponent > 255 {
		return [4]byte{}, false
	}
	encoded := uint32(rounded) & 0x7fffff
	encoded |= uint32((left[2]^right[2])&128) << 16
	return [4]byte{byte(encoded), byte(encoded >> 8), byte(encoded >> 16), byte(exponent)}, true
}
