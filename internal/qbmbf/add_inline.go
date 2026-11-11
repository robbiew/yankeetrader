package qbmbf

// SingleAddInlineOffset applies the shared INT3F/85, INT3F/9d and INT3F/95 address resolver
// to the selector byte, the descriptor's first word (its segment is at SS:[BP-2]),
// and the opcode caller's header words at 0010/0012. Descriptor word 7a62 selects
// base12; every other word selects
// base10. The selector's high bit is discarded, slots have stride eight, and
// addition wraps at 16 bits as in the original runtime.
// This computes an offset only: it does not walk a host stack, validate a module,
// read operand memory, or qualify a four-byte read crossing a segment boundary.
func SingleAddInlineOffset(selector byte, descriptorWord, base10, base12 uint16) uint16 {
	base := base10
	if descriptorWord == 0x7a62 {
		base = base12
	}
	return base + uint16(selector&0x7f)*8
}
