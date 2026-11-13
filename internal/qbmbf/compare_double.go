package qbmbf

import "math/bits"

// CompareDouble models the ordered raw operands of BRUN30 INT3F/a0 (memory
// versus memory), /a2 (FAC left), and /a4 (FAC right). It compares all four words
// in descending order after the shared zero/sign exits, preserving the native
// CF/PF/ZF/SF/OF rather than synthesizing flags from a three-way numeric result.
// Exponent-zero residues are zero aliases. Inputs are readonly. Inline /a6,
// arbitrary segment/direction contexts and production integration are separate.
func CompareDouble(left, right [8]byte) ComparisonFlags {
	logical := func(v byte) ComparisonFlags {
		return ComparisonFlags{Parity: bits.OnesCount8(v)%2 == 0, Zero: v == 0, Sign: v&128 != 0}
	}
	rotate := func(v byte, f ComparisonFlags) ComparisonFlags {
		f.Carry = v&128 != 0
		f.Overflow = ((v>>6)^(v>>7))&1 != 0
		return f
	}
	if right[7] == 0 {
		f := logical(left[7])
		if left[7] != 0 {
			f = rotate(left[6], f)
		}
		return f
	}
	if left[7] == 0 {
		f := rotate(right[6], logical(right[7]))
		f.Carry = !f.Carry
		return f
	}
	f := rotate(left[6], logical(left[6]^right[6]))
	if f.Sign {
		return f
	}
	if left[6]&128 != 0 {
		left, right = right, left
	}
	word := func(v [8]byte, i int) uint16 { return uint16(v[i]) | uint16(v[i+1])<<8 }
	var x, y uint16
	for offset := 6; offset >= 0; offset -= 2 {
		x, y = word(left, offset), word(right, offset)
		if x != y {
			break
		}
	}
	d := x - y
	return ComparisonFlags{Carry: x < y, Parity: bits.OnesCount8(byte(d))%2 == 0, Zero: d == 0, Sign: d&0x8000 != 0, Overflow: (x^y)&(x^d)&0x8000 != 0}
}
