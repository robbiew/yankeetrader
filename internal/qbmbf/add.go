package qbmbf

import "math/bits"

// AddSingle applies the recovered BRUN30 INT3F/81 operation: left is the initial
// raw SINGLE FAC and right is the memory operand. It rounds to 24 significant
// bits with ties to even, but preserves the native exponent-gap shortcut and
// raw zero behavior. Cancellation/underflow clears only the left FAC exponent;
// two exponent-zero inputs return the right encoding. Overflow returns a zero
// array and false, without claiming a native post-error FAC value.
// This isolated primitive does not select a gameplay or generation policy.
func AddSingle(left, right [4]byte) ([4]byte, bool) {
	if left[3] == 0 {
		return right, true
	}
	if right[3] == 0 {
		return left, true
	}
	difference := int(left[3]) - int(right[3])
	if difference > 24 {
		return left, true
	}
	if difference < -24 {
		return right, true
	}
	mantissa := func(raw [4]byte) int64 {
		value := int64(raw[0]) | int64(raw[1])<<8 | int64(raw[2]&127)<<16 | 1<<23
		if raw[2]&128 != 0 {
			return -value
		}
		return value
	}
	base := int(left[3])
	if int(right[3]) < base {
		base = int(right[3])
	}
	// The original gap guard bounds alignment to 24 bits, so signed 64-bit
	// integers retain the exact sum of both 24-bit significands.
	sum := mantissa(left)<<uint(int(left[3])-base) + mantissa(right)<<uint(int(right[3])-base)
	negative := sum < 0
	if negative {
		sum = -sum
	}
	magnitude := uint64(sum)
	length := bits.Len64(magnitude)
	exponent := base + length - 24
	if magnitude == 0 || exponent <= 0 {
		left[3] = 0
		return left, true
	}
	var rounded uint64
	if length <= 24 {
		rounded = magnitude << uint(24-length)
	} else {
		shift := uint(length - 24)
		rounded = magnitude >> shift
		remainder := magnitude & ((uint64(1) << shift) - 1)
		half := uint64(1) << (shift - 1)
		if remainder > half || (remainder == half && rounded&1 != 0) {
			rounded++
		}
		if rounded == 1<<24 {
			rounded >>= 1
			exponent++
		}
	}
	if exponent > 255 {
		return [4]byte{}, false
	}
	encoded := uint32(rounded) & 0x7fffff
	if negative {
		encoded |= 0x800000
	}
	return [4]byte{byte(encoded), byte(encoded >> 8), byte(encoded >> 16), byte(exponent)}, true
}
