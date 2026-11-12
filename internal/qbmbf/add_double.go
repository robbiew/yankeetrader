package qbmbf

import "math/big"

// AddDouble models BRUN30 INT3F/82: left is the initial raw DOUBLE FAC and
// right is memory. It retains all 56 significand bits, native zero selection
// and the exponent-gap shortcut. This isolated API selects no gameplay policy.
func AddDouble(left, right [8]byte) ([8]byte, bool) {
	return AddDoubleWithFAC(left, right, left)
}

// AddDoubleWithFAC models INT3F/80 memory plus memory with independent initialFAC.
// INT3F/84 memory plus FAC passes right as initialFAC; swapping operands is not
// equivalent for directional zero aliases. Cancellation/underflow clears only
// initialFAC's exponent. Overflow returns a zero array and false as an API
// convention, without claiming native post-error FAC state. Inline /86 and
// other DOUBLE arithmetic remain outside this contract.
func AddDoubleWithFAC(left, right, initialFAC [8]byte) ([8]byte, bool) {
	if left[7] == 0 {
		return right, true
	}
	if right[7] == 0 {
		return left, true
	}
	difference := int(left[7]) - int(right[7])
	if difference > 56 {
		return left, true
	}
	if difference < -56 {
		return right, true
	}
	const hidden = uint64(1) << 55
	mantissa := func(raw [8]byte) *big.Int {
		n := new(big.Int).SetUint64(doubleBits(raw)&(hidden-1) | hidden)
		if raw[6]&128 != 0 {
			n.Neg(n)
		}
		return n
	}
	base := int(left[7])
	if int(right[7]) < base {
		base = int(right[7])
	}
	// The native gap guard bounds exact alignment to at most 112 bits. Using
	// integers avoids float64's loss of the bottom three DOUBLE significand bits.
	l, r := mantissa(left), mantissa(right)
	l.Lsh(l, uint(int(left[7])-base))
	r.Lsh(r, uint(int(right[7])-base))
	sum := new(big.Int).Add(l, r)
	negative := sum.Sign() < 0
	sum.Abs(sum)
	length := sum.BitLen()
	exponent := base + length - 56
	if sum.Sign() == 0 || exponent <= 0 {
		initialFAC[7] = 0
		return initialFAC, true
	}
	var rounded uint64
	if length <= 56 {
		rounded = sum.Uint64() << uint(56-length)
	} else {
		shift := uint(length - 56)
		rounded = new(big.Int).Rsh(new(big.Int).Set(sum), shift).Uint64()
		remainder := new(big.Int).Sub(sum, new(big.Int).Lsh(new(big.Int).SetUint64(rounded), shift))
		half := new(big.Int).Lsh(big.NewInt(1), shift-1)
		cmp := remainder.Cmp(half)
		if cmp > 0 || (cmp == 0 && rounded&1 != 0) {
			rounded++
		}
		if rounded == 1<<56 {
			rounded >>= 1
			exponent++
		}
	}
	if exponent > 255 {
		return [8]byte{}, false
	}
	encoded := rounded & (hidden - 1)
	if negative {
		encoded |= hidden
	}
	return doubleRaw(encoded, byte(exponent)), true
}
