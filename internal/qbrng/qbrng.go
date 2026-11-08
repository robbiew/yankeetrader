// Package qbrng implements recovered BRUN30 RND, raw-single RND(argument), and
// RANDOMIZE operations. It does not implement QB's complete math runtime, TIMER
// conversion, or the modern game's choice of random streams.
package qbrng

import "encoding/binary"

const DefaultSeed uint32 = 5
const mask uint32 = 0xffffff

// Generator holds the 24-bit BRUN30 state. It is owned by one caller.
type Generator struct{ state uint32 }

// New constructs a generator with an explicitly supplied raw state.
func New(state uint32) *Generator { return &Generator{state: state & mask} }

// State returns the current raw state without advancing the generator.
func (g *Generator) State() uint32 { return g.state }

// RandomizeMBF uses the actual four bytes of a Microsoft Binary Format single.
// BRUN30 XORs its two words into the upper 16 state bits, preserving the low
// byte. It neither normalizes the argument nor advances RND. In particular,
// exponent-zero singles with different residual mantissas seed differently.
func (g *Generator) RandomizeMBF(raw [4]byte) {
	mixed := binary.LittleEndian.Uint16(raw[:2]) ^ binary.LittleEndian.Uint16(raw[2:])
	g.state = (g.state & 0xff) | (uint32(mixed) << 8)
}

// Float32 advances argumentless RND and returns its exact binary fraction in
// [0,1). Every 24-bit numerator is exactly representable as a float32.
func (g *Generator) Float32() float32 {
	g.state = (214013*g.state + 1744579) & mask
	return float32(g.state) / (1 << 24)
}

// Float32MBF applies RND(argument) to the actual four bytes of an MBF single.
// Any exponent-zero encoding returns the current fraction without advancing,
// including zeros retaining a sign or mantissa. A positive argument advances
// once, regardless of magnitude. A negative argument replaces the entire state
// with its raw 24-bit mantissa/sign plus exponent (with carry), then advances.
// This is distinct from RandomizeMBF, which preserves the old low byte.
func (g *Generator) Float32MBF(raw [4]byte) float32 {
	if raw[3] == 0 {
		return float32(g.state) / (1 << 24)
	}
	if raw[2]&0x80 != 0 {
		g.state = (uint32(raw[0]) | uint32(raw[1])<<8 | uint32(raw[2])<<16) + uint32(raw[3])
		g.state &= mask
	}
	return g.Float32()
}
