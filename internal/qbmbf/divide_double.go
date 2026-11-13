package qbmbf

import (
	"errors"
	"math/bits"
)

// ErrDoubleDivisionByZero denotes an exponent-zero divisor, including raw zero
// aliases. It takes precedence over an exponent-zero numerator.
var ErrDoubleDivisionByZero = errors.New("DOUBLE division by zero")

// ErrDoubleDivisionOverflow denotes a quotient outside the native DOUBLE range.
var ErrDoubleDivisionOverflow = errors.New("DOUBLE division overflow")

// DivideDouble models BRUN30 INT3F/8a: the numerator is the initial raw DOUBLE
// FAC and the divisor is memory. This isolated API selects no gameplay policy.
func DivideDouble(left, right [8]byte) ([8]byte, error) {
	return DivideDoubleWithFAC(left, right, left)
}

// DivideDoubleWithFAC models INT3F/88 memory divided by memory with independent
// initialFAC. INT3F/8c memory divided by FAC passes right as initialFAC. Zero
// numerators and early underflow clear only initialFAC's exponent. Late
// normalization underflow (raw exponent difference -128, numerator significand
// smaller) clears the staged-divisor FAC exponent and retains its shifted
// residue. Quotients round to nearest with ties to even using
// the exact remainder, without float64 demotion. Distinct errors return a zero
// array as an API convention without a native post-error FAC claim.
// Inline /8e and arbitrary error/unwind contexts are outside this contract.
func DivideDoubleWithFAC(left, right, initialFAC [8]byte) ([8]byte, error) {
	if right[7] == 0 {
		return [8]byte{}, ErrDoubleDivisionByZero
	}
	zero := func() ([8]byte, error) { initialFAC[7] = 0; return initialFAC, nil }
	if left[7] == 0 {
		return zero()
	}
	const hidden = uint64(1) << 55
	mantissa := func(raw [8]byte) uint64 { return doubleBits(raw)&(hidden-1) | hidden }
	numerator, divisor := mantissa(left), mantissa(right)
	exponent := int(left[7]) - int(right[7]) + 128
	shift := uint(56)
	if numerator >= divisor {
		exponent++
		shift = 55
	}
	if exponent <= 0 {
		if int(left[7])-int(right[7]) == -128 {
			var staged [8]byte
			copy(staged[1:7], right[:6])
			return staged, nil
		}
		return zero()
	}
	if exponent > 255 {
		return [8]byte{}, ErrDoubleDivisionOverflow
	}
	// Scaling a 56-bit numerator requires at most 112 bits. The high word is
	// smaller than the 56-bit divisor, so Div64 cannot overflow. Doubling its
	// remainder also fits uint64 and retains the native guard/sticky decision.
	hi, lo := numerator>>(64-shift), numerator<<shift
	rounded, remainder := bits.Div64(hi, lo, divisor)
	if remainder*2 > divisor || (remainder*2 == divisor && rounded&1 != 0) {
		rounded++
	}
	if rounded == 1<<56 {
		rounded >>= 1
		exponent++
	}
	if exponent > 255 {
		return [8]byte{}, ErrDoubleDivisionOverflow
	}
	encoded := rounded & (hidden - 1)
	encoded |= uint64((left[6]^right[6])&128) << 48
	return doubleRaw(encoded, byte(exponent)), nil
}
