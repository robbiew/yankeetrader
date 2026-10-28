package game

import (
	"errors"
	"math"
	"math/bits"
	"time"
)

type Salvage struct {
	Holds, Credits, Missiles, Plasma, Ground, Mines int64
	Cargo                                           [3]int64
}

// scaledSalvageDraw computes floor(quantity * the exact binary RNG value),
// without converting money to floating point. The 128-bit product also handles
// values near MaxMoney without rounding the result up to the whole stock.
func scaledSalvageDraw(quantity int64, rng func() float64) (int64, error) {
	r := rng()
	if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
		return 0, errors.New("salvage RNG must return a finite value in [0,1)")
	}
	encoded := math.Float64bits(r)
	exponent := int((encoded >> 52) & 0x7ff)
	if exponent == 0 {
		return 0, nil
	} // zero/subnormal times any valid inventory is <1
	mantissa := (encoded & ((1 << 52) - 1)) | (1 << 52)
	hi, lo := bits.Mul64(uint64(quantity), mantissa)
	shift := 1075 - exponent
	if shift >= 128 {
		return 0, nil
	}
	if shift >= 64 {
		return int64(hi >> uint(shift-64)), nil
	}
	return int64((hi << uint(64-shift)) | (lo >> uint(shift))), nil
}

// SampleSalvage is a pure calculation. Random draws follow DOS's six-stock
// ordering and cargo sampling without replacement; original MBF rounding and
// seeded RNG equivalence are intentionally not reproduced.
func SampleSalvage(victim Player, winnerHolds int64, rng func() float64) (Salvage, error) {
	if rng == nil || victim.Holds < 0 || victim.Holds > 1000 || winnerHolds < 1 || winnerHolds > 1000 || victim.Credits < 0 || victim.Credits > MaxMoney {
		return Salvage{}, errors.New("invalid salvage inputs")
	}
	for _, q := range []int64{victim.Missiles, victim.Plasma, victim.Ground, victim.Mines} {
		if q < 0 || q > MaxQuantity {
			return Salvage{}, errors.New("invalid salvage weapons")
		}
	}
	cargo := victim.Cargo
	used := int64(0)
	for _, q := range cargo {
		if q < 0 || q > 1000 {
			return Salvage{}, errors.New("invalid salvage cargo")
		}
		used += q
	}
	if used > victim.Holds {
		return Salvage{}, errors.New("victim cargo exceeds holds")
	}
	var sampled [6]int64
	for i, q := range []int64{victim.Holds, victim.Credits, victim.Missiles, victim.Plasma, victim.Ground, victim.Mines} {
		value, err := scaledSalvageDraw(q, rng)
		if err != nil {
			return Salvage{}, err
		}
		sampled[i] = value
	}
	result := Salvage{Holds: min(sampled[0], 1000-winnerHolds), Credits: sampled[1], Missiles: sampled[2], Plasma: sampled[3], Ground: sampled[4], Mines: sampled[5]}
	remainingHolds := victim.Holds
	for i := int64(0); i < result.Holds; i++ {
		index, err := scaledSalvageDraw(remainingHolds, rng)
		if err != nil {
			return Salvage{}, err
		}
		boundary := int64(0)
		for good, q := range cargo {
			boundary += q
			if index < boundary {
				cargo[good]--
				result.Cargo[good]++
				break
			}
		}
		remainingHolds--
	}
	return result, nil
}

// SettleShipSalvage commits loot, death, team revocation and estate changes
// together. Call from the same store Update as final damage; return any error
// from the callback so damage also rolls back. CommitVisibleAttack uses this path.
func (w *World) SettleShipSalvage(context DeathContext, rng func() float64, now time.Time) (Salvage, error) {
	if context.Cause != "combat" && context.Cause != "retaliation" && context.Cause != "missile" {
		return Salvage{}, errors.New("salvage requires an enemy combat death")
	}
	victim, err := w.deathTarget(context, now)
	if err != nil {
		return Salvage{}, err
	}
	killer, err := w.player(context.Killer)
	if err != nil {
		return Salvage{}, err
	}
	if victim.Fighters != 0 || victim.Shields != 0 {
		return Salvage{}, errors.New("salvage requires a defeated ship")
	}
	result, err := SampleSalvage(*victim, killer.Holds, rng)
	if err != nil {
		return Salvage{}, err
	}
	if result.Credits > MaxMoney-killer.Credits || result.Missiles > MaxQuantity-killer.Missiles || result.Plasma > MaxQuantity-killer.Plasma || result.Ground > MaxQuantity-killer.Ground || result.Mines > MaxQuantity-killer.Mines {
		return Salvage{}, errors.New("salvage exceeds recipient capacity")
	}
	if err = w.RecordDeath(context, now); err != nil {
		return Salvage{}, err
	}
	killer.Holds += result.Holds
	victim.Holds -= result.Holds
	killer.Credits += result.Credits
	victim.Credits -= result.Credits
	killer.Missiles += result.Missiles
	victim.Missiles -= result.Missiles
	killer.Plasma += result.Plasma
	victim.Plasma -= result.Plasma
	killer.Ground += result.Ground
	victim.Ground -= result.Ground
	killer.Mines += result.Mines
	victim.Mines -= result.Mines
	for good, q := range result.Cargo {
		killer.Cargo[good] += q
		victim.Cargo[good] -= q
	}
	return result, nil
}
