package qbmbf

// SignZeroSingle models BRUN30 /a7 (memory) and /a9 (SINGLE FAC). It returns
// only the defined CF/PF/ZF/SF/OF flags, not a -1/0/+1 SGN result. Exponent-zero
// residues are zero aliases; for nonzero values CF carries the encoded sign.
// SF/OF retain CPU semantics and must not be interpreted as numeric ordering.
func SignZeroSingle(raw [4]byte) ComparisonFlags {
	return CompareSingle(raw, [4]byte{})
}

// SignZeroDouble models /a8 (memory) and /aa (DOUBLE FAC). The /a9 and /aa
// dispatches share the same FAC high-word entry. All input bytes are readonly;
// AF, arbitrary direction/segment contexts and production integration are excluded.
func SignZeroDouble(raw [8]byte) ComparisonFlags {
	return CompareDouble(raw, [8]byte{})
}
