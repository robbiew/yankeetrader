package qbmbf

// SubtractSingle models BRUN30 INT3F/99: left is the initial raw SINGLE FAC and
// right is a memory operand. The native wrapper flips right's sign in a register,
// including exponent-zero encodings, then uses the qualified addition kernel.
// Cancellation and underflow retain left's first three bytes and clear its
// exponent. Overflow returns a zero array and false, without a post-error FAC claim.
func SubtractSingle(left, right [4]byte) ([4]byte, bool) {
	return SubtractSingleWithFAC(left, right, left)
}

// SubtractSingleWithFAC models INT3F/97 memory-minus-memory with independent
// initialFAC state. INT3F/9b (memory minus FAC) is represented by passing right
// as initialFAC. Raw zero selection, gap skipping and rounding reuse addition;
// cancellation/underflow retains initialFAC's original residue, not a negated
// operand's residue. Inputs are passed by value. This does not qualify inline9d
// frames or select a gameplay, generation or save policy.
func SubtractSingleWithFAC(left, right, initialFAC [4]byte) ([4]byte, bool) {
	right[2] ^= 0x80
	return AddSingleWithFAC(left, right, initialFAC)
}
