package qbmbf

// AddSingleWithFAC models BRUN30 INT3F/7f memory-to-memory addition with an
// independent prior raw FAC. Numeric arithmetic and operand-zero selection are
// shared with AddSingle. Cancellation/underflow instead clears only initialFAC's
// exponent, preserving its other bytes. Overflow returns a zero array and false.
// INT3F/83 (memory plus FAC) is represented by passing right as initialFAC;
// swapping operands to AddSingle is not equivalent for directional zero aliases.
// The inline-address-resolving entry INT3F/85 is not qualified by this API.
func AddSingleWithFAC(left, right, initialFAC [4]byte) ([4]byte, bool) {
	result, ok := AddSingle(left, right)
	if ok && left[3] != 0 && right[3] != 0 && result[3] == 0 {
		initialFAC[3] = 0
		return initialFAC, true
	}
	return result, ok
}
