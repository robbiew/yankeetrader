package game

import "github.com/robbiew/yankeetrader/internal/qbrng"

// Startup prices precede RANDOMIZE in YT.EXE main003a..00ac. BRUN30 uses
// state5 and a24-bit LCG (fileb4d6..b509; constants1022c..10237).
// Retained DOS controls distinguish these from fixed20/30/40 references.
// We model single-precision references; subsequent price arithmetic remains
// float64, not a complete emulation of QuickBASIC's MBF arithmetic.
var dosReferencePrices = recoveredDOSReferences()

func recoveredDOSReferences() [3]float64 {
	rng := qbrng.New(qbrng.DefaultSeed)
	var prices [3]float64
	for i, base := range [3]float32{20, 30, 40} {
		scale := [3]float32{5, 7, 10}[i]
		minus := float32(scale * rng.Float32())
		plus := float32(scale * rng.Float32())
		partial := float32(base - minus)
		prices[i] = float64(float32(partial + plus))
	}
	return prices
}
