package qbmbf

// SubtractDouble models BRUN30 INT3F/9a: left is the initial raw DOUBLE FAC
// and right is memory. All 56 significand bits and native zero aliases are
// retained. This isolated API selects no gameplay or save policy.
func SubtractDouble(left, right [8]byte) ([8]byte, bool) {
	return SubtractDoubleWithFAC(left, right, left)
}

// SubtractDoubleWithFAC models INT3F/98 memory minus memory with independent
// initialFAC. INT3F/9c memory minus FAC passes right as initialFAC. The native
// wrapper flips right's sign in a register, even for exponent-zero encodings,
// before entering addition. Cancellation/underflow keeps initialFAC's original
// seven residue bytes. Inputs are copied by value; memory is not negated.
// Overflow returns a zero array and false without a native post-error FAC claim.
// Inline /9e and general error/unwind contexts remain outside this contract.
func SubtractDoubleWithFAC(left, right, initialFAC [8]byte) ([8]byte, bool) {
	right[6] ^= 0x80
	return AddDoubleWithFAC(left, right, initialFAC)
}
