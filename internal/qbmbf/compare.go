package qbmbf

import "math/bits"

// ComparisonFlags contains only the defined CF/PF/ZF/SF/OF outputs of the
// raw SINGLE/DOUBLE comparison core. AF and reserved flags are outside this contract.
type ComparisonFlags struct {
	Carry, Parity, Zero, Sign, Overflow bool
}

// Bits returns the five defined flags in their x86 FLAGS positions (mask 08c5).
func (f ComparisonFlags) Bits() uint16 {
	var v uint16
	for i, b := range []bool{f.Carry, f.Parity, f.Zero, f.Sign, f.Overflow} {
		if b {
			v |= []uint16{1, 4, 64, 128, 2048}[i]
		}
	}
	return v
}

// Jumps returns the sixteen short Jcc conditions, in opcode 70..7f order:
// JO,JNO,JB,JAE,JE,JNE,JBE,JA,JS,JNS,JP,JNP,JL,JGE,JLE,JG.
// Signed CPU conditions must not be interpreted as numeric MBF ordering.
func (f ComparisonFlags) Jumps() [16]bool {
	c, p, z, s, o := f.Carry, f.Parity, f.Zero, f.Sign, f.Overflow
	return [16]bool{o, !o, c, !c, z, !z, c || z, !c && !z, s, !s, p, !p, s != o, s == o, z || s != o, !z && s == o}
}

// CompareSingle models the raw ordered operands of BRUN30 INT3F/9f, /a1
// (FAC left) and /a3 (FAC right). These entries share the same flag core and
// leave inputs untouched. Exponent-zero residues are zero aliases. Inline /a5,
// DOUBLE comparisons and arbitrary segment/direction contexts are not admitted.
func CompareSingle(left, right [4]byte) ComparisonFlags {
	logical := func(v byte) ComparisonFlags {
		return ComparisonFlags{Parity: bits.OnesCount8(v)%2 == 0, Zero: v == 0, Sign: v&128 != 0}
	}
	rotate := func(v byte, f ComparisonFlags) ComparisonFlags {
		f.Carry = v&128 != 0
		f.Overflow = ((v>>6)^(v>>7))&1 != 0
		return f
	}
	if right[3] == 0 {
		f := logical(left[3])
		if left[3] != 0 {
			f = rotate(left[2], f)
		}
		return f
	}
	if left[3] == 0 {
		f := rotate(right[2], logical(right[3]))
		f.Carry = !f.Carry
		return f
	}
	f := rotate(left[2], logical(left[2]^right[2]))
	if f.Sign {
		return f
	}
	if left[2]&128 != 0 {
		left, right = right, left
	}
	word := func(v [4]byte, i int) uint16 { return uint16(v[i]) | uint16(v[i+1])<<8 }
	x, y := word(left, 2), word(right, 2)
	if x == y {
		x, y = word(left, 0), word(right, 0)
	}
	d := x - y
	return ComparisonFlags{Carry: x < y, Parity: bits.OnesCount8(byte(d))%2 == 0, Zero: d == 0, Sign: d&0x8000 != 0, Overflow: (x^y)&(x^d)&0x8000 != 0}
}
