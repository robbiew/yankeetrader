package game

import (
	"errors"
	"math"
	"time"
)

const maxDuelRounds = 1_000_000

// ShipDuelResult describes only committed fighters and the defending ship.
// Uncommitted fighters, turns, inventories and rewards are not mutated here.
type ShipDuelResult struct {
	Survivors, DefenderFighters, DefenderShields int64
	AttackerLosses, DefenderLosses               int64
	Rounds                                       int
	Destroyed                                    bool
}

// ResolveShipDuel implements the recovered DOS fighter/shield stages with an
// injected RNG returning [0,1). It is not a QuickBASIC RNG/MBF emulator. A bounded
// calculation returns no partial result on error, so it cannot partly commit.
func ResolveShipDuel(committed, defenders, shields int64, attackerCloak float64, rng func() float64) (ShipDuelResult, error) {
	if committed < 1 || committed > MaxQuantity || defenders < 0 || defenders > MaxQuantity || shields < 0 || shields > MaxQuantity || math.IsNaN(attackerCloak) || math.IsInf(attackerCloak, 0) || attackerCloak < 0 || attackerCloak > 1 || rng == nil {
		return ShipDuelResult{}, errors.New("invalid ship duel inputs")
	}
	a, d, s := committed, defenders, shields
	rounds := 0
	draw := func() (float64, error) {
		if rounds >= maxDuelRounds {
			return 0, errors.New("ship duel calculation limit reached")
		}
		rounds++
		r := rng()
		if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
			return 0, errors.New("combat RNG must return a finite value in [0,1)")
		}
		return r, nil
	}
	for a > 0 && d > 0 {
		batch := min(a, d) / 20
		if batch < 1 {
			batch = 1
		}
		r, err := draw()
		if err != nil {
			return ShipDuelResult{}, err
		}
		if r+attackerCloak/10 < .45 {
			a -= batch
		} else {
			d -= batch
		}
	}
	if d == 0 {
		for a > 0 && s > 0 {
			batch := int64(1)
			if a > 100 && s > 100 {
				batch = 100
			}
			r, err := draw()
			if err != nil {
				return ShipDuelResult{}, err
			}
			if r >= .5 {
				a -= batch
			} else {
				s -= batch
			}
		}
	}
	return ShipDuelResult{Survivors: a, DefenderFighters: d, DefenderShields: s, AttackerLosses: committed - a, DefenderLosses: defenders - d, Rounds: rounds, Destroyed: d == 0 && s == 0}, nil
}

// SettleCreditSalvage atomically attributes death and transfers a precomputed
// credit salvage amount, consuming it from the victim's frozen inventory. It is
// an internal building block, not a loot formula or a player-facing attack.
// Estate cleanup is shared with RecordDeath. Prefer SettleShipSalvage for the
// recovered full inventory sampler; use this helper only for explicit amounts.
func (w *World) SettleCreditSalvage(context DeathContext, credits int64, now time.Time) error {
	if context.Cause != "combat" && context.Cause != "retaliation" {
		return errors.New("credit salvage requires an enemy combat death")
	}
	killer, err := w.player(context.Killer)
	if err != nil {
		return err
	}
	victim, err := w.player(context.Victim)
	if err != nil {
		return err
	}
	if killer.ID == victim.ID || victim.Fighters != 0 || victim.Shields != 0 {
		return errors.New("credit salvage requires a defeated enemy ship")
	}
	if credits < 0 || credits > victim.Credits || credits > MaxMoney-killer.Credits {
		return errors.New("invalid salvage amount or recipient credit limit exceeded")
	}
	// RecordDeath performs generation, sector, attacker and team revalidation.
	// Nothing changes if it rejects. Nothing below can fail after it succeeds.
	if err = w.RecordDeath(context, now); err != nil {
		return err
	}
	victim.Credits -= credits
	killer.Credits += credits
	return nil
}
