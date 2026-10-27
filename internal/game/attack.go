package game

import (
	"errors"
	"sort"
	"time"
)

// AttackIntent binds confirmation to both ship incarnations and the encounter.
// This is an internal foundation. A frontend must establish cloak visibility
// before offering an intent; no public attack command uses this API yet.
type AttackIntent struct {
	Attacker, Target, Sector             int
	AttackerGeneration, TargetGeneration uint64
	Fighters                             int64
}

func (w *World) attackPair(attacker, target int) (*Player, *Player, error) {
	a, err := w.player(attacker)
	if err != nil {
		return nil, nil, err
	}
	d, err := w.player(target)
	if err != nil {
		return nil, nil, err
	}
	if a.ID == d.ID || a.Sector != d.Sector {
		return nil, nil, errors.New("choose another ship in your current sector")
	}
	if a.Team != 0 && a.Team == d.Team {
		return nil, nil, errors.New("teammates cannot be attacked")
	}
	return a, d, nil
}

// AttackCandidates returns current local identities in stable order. It is not
// a visibility decision: cloak/session detection must filter these candidates.
func (w *World) AttackCandidates(id int) ([]SensorShip, error) {
	if _, err := w.player(id); err != nil {
		return nil, err
	}
	var result []SensorShip
	for other := range w.Players {
		_, d, err := w.attackPair(id, other)
		if err == nil {
			result = append(result, SensorShip{ID: d.ID, Team: d.Team, Alias: d.Alias, Fighters: d.Fighters, Shields: d.Shields})
		}
	}
	sort.Slice(result, func(i, j int) bool { return result[i].ID < result[j].ID })
	return result, nil
}

func (w *World) PrepareAttack(attacker, target int, fighters int64) (AttackIntent, error) {
	a, d, err := w.attackPair(attacker, target)
	if err != nil {
		return AttackIntent{}, err
	}
	if fighters < 1 || fighters > a.Fighters {
		return AttackIntent{}, errors.New("choose available fighters to commit")
	}
	return AttackIntent{Attacker: a.ID, Target: d.ID, Sector: a.Sector, AttackerGeneration: a.ShipGeneration, TargetGeneration: d.ShipGeneration, Fighters: fighters}, nil
}

// CommitAttack must run inside a store Update whose caller returns every error.
// Final damage and salvage share that transaction, including failures during loot.
// Cloak is not yet persisted; only the recovered zero-cloak duel is integrated.
// Direct fighter duels do not trigger missile retaliation or consume turns.
func (w *World) CommitAttack(intent AttackIntent, rng func() float64, now time.Time) (ShipDuelResult, error) {
	a, d, err := w.attackPair(intent.Attacker, intent.Target)
	if err != nil {
		return ShipDuelResult{}, err
	}
	if a.Sector != intent.Sector || a.ShipGeneration != intent.AttackerGeneration || d.ShipGeneration != intent.TargetGeneration {
		return ShipDuelResult{}, errors.New("attack confirmation is stale")
	}
	if now.IsZero() || now.Before(w.Created) {
		return ShipDuelResult{}, errors.New("invalid attack time")
	}
	if intent.Fighters < 1 || intent.Fighters > a.Fighters {
		return ShipDuelResult{}, errors.New("committed fighters are no longer available")
	}
	result, err := ResolveShipDuel(intent.Fighters, d.Fighters, d.Shields, 0, rng)
	if err != nil {
		return ShipDuelResult{}, err
	}
	a.Fighters -= result.AttackerLosses
	d.Fighters, d.Shields = result.DefenderFighters, result.DefenderShields
	if result.Destroyed {
		_, err = w.SettleShipSalvage(DeathContext{Victim: d.ID, Generation: d.ShipGeneration, Sector: d.Sector, Killer: a.ID, Cause: "combat"}, rng, now)
		if err != nil {
			return ShipDuelResult{}, err
		}
	}
	return result, nil
}
