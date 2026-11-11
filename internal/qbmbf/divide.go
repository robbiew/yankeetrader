package qbmbf

import "errors"

// ErrSingleDivisionByZero denotes a divisor with a zero exponent, including
// noncanonical zero residues. It takes precedence over a zero numerator.
var ErrSingleDivisionByZero = errors.New("SINGLE division by zero")

// ErrSingleDivisionOverflow denotes a quotient outside the native SINGLE range.
var ErrSingleDivisionOverflow = errors.New("SINGLE division overflow")

// DivideSingle models BRUN30 INT3F/89: the numerator is the initial FAC and the
// divisor is memory. It is an isolated primitive, with no gameplay policy.
func DivideSingle(left, right [4]byte) ([4]byte, error) {
	return DivideSingleWithFAC(left, right, left)
}

// DivideSingleWithFAC models INT3F/87 memory divided by memory with independent
// initialFAC. INT3F/8b memory divided by FAC passes right as initialFAC. Zero
// results clear only initialFAC's exponent. Underflow is checked before rounding.
// Errors are distinct and return a zero array as an API convention, without
// claiming native post-error FAC state. Inline INT3F/8d is outside this contract.
func DivideSingleWithFAC(left, right, initialFAC [4]byte) ([4]byte, error) {
	if right[3] == 0 {
		return [4]byte{}, ErrSingleDivisionByZero
	}
	zero := func() ([4]byte, error) { initialFAC[3] = 0; return initialFAC, nil }
	if left[3] == 0 {
		return zero()
	}
	mantissa := func(raw [4]byte) uint64 {
		return uint64(raw[0]) | uint64(raw[1])<<8 | uint64(raw[2]&127)<<16 | 1<<23
	}
	numerator, divisor := mantissa(left), mantissa(right)
	exponent := int(left[3]) - int(right[3]) + 128
	shift := uint(24)
	if numerator >= divisor {
		exponent++
		shift = 23
	}
	if exponent <= 0 {
		return zero()
	}
	if exponent > 255 {
		return [4]byte{}, ErrSingleDivisionOverflow
	}
	// At most 48 bits are required. The exact remainder retains all native
	// guard/sticky information, independently of the partial-quotient helper.
	scaled := numerator << shift
	rounded, remainder := scaled/divisor, scaled%divisor
	if remainder*2 > divisor || (remainder*2 == divisor && rounded&1 != 0) {
		rounded++
	}
	if rounded == 1<<24 {
		rounded >>= 1
		exponent++
	}
	if exponent > 255 {
		return [4]byte{}, ErrSingleDivisionOverflow
	}
	encoded := uint32(rounded) & 0x7fffff
	encoded |= uint32((left[2]^right[2])&128) << 16
	return [4]byte{byte(encoded), byte(encoded >> 8), byte(encoded >> 16), byte(exponent)}, nil
}
