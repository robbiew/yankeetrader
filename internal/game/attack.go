package game

import (
	"errors"
	"sort"
	"time"
)

// AttackIntent binds confirmation to both ship incarnations and the encounter.
// Frontends must use visible candidates and recheck this intent on commit.
type AttackIntent struct {
	Season                               uint64
	Attacker, Target, Sector             int
	AttackerGeneration, TargetGeneration uint64
	AttackerSequence, TargetSequence     uint64
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
	if w.HostileDefense(a.ID, a.Sector) {
		return nil, nil, ErrDefenseEncounter
	}
	if w.HasMineEncounter(a.ID) {
		return nil, nil, ErrMineEncounter
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
	return AttackIntent{Season: w.Season, Attacker: a.ID, Target: d.ID, Sector: a.Sector, AttackerGeneration: a.ShipGeneration, TargetGeneration: d.ShipGeneration, AttackerSequence: a.WarpSequence, TargetSequence: d.WarpSequence, Fighters: fighters}, nil
}

// CommitAttack must run inside a store Update whose caller returns every error.
// Final damage and salvage share that transaction, including failures during loot.
// The attacker's current persisted cloak supplies the recovered duel advantage.
// Direct fighter duels do not trigger missile retaliation or consume turns.
func (w *World) CommitAttack(intent AttackIntent, rng func() float64, now time.Time) (ShipDuelResult, error) {
	return w.CommitVisibleAttack(intent, nil, rng, now)
}

// CommitVisibleAttack rechecks visibility inside the same transaction as damage.
// Nil visibility only permits an uncloaked target; reveals never survive replacement.
func (w *World) CommitVisibleAttack(intent AttackIntent, visibility *Visibility, rng func() float64, now time.Time) (ShipDuelResult, error) {
	a, d, err := w.attackPair(intent.Attacker, intent.Target)
	if err != nil {
		return ShipDuelResult{}, err
	}
	if a.WarpSequence != intent.AttackerSequence || d.WarpSequence != intent.TargetSequence || w.Season != intent.Season || a.Sector != intent.Sector || a.ShipGeneration != intent.AttackerGeneration || d.ShipGeneration != intent.TargetGeneration {
		return ShipDuelResult{}, errors.New("attack confirmation is stale")
	}
	if visibility != nil {
		if err := w.checkVisibility(intent.Attacker, visibility); err != nil {
			return ShipDuelResult{}, err
		}
	}
	if d.Cloak > 0 && (visibility == nil || !visibility.sees(d)) {
		return ShipDuelResult{}, errors.New("target ship is cloaked")
	}

	if now.IsZero() || now.Before(w.Created) {
		return ShipDuelResult{}, errors.New("invalid attack time")
	}
	if intent.Fighters < 1 || intent.Fighters > a.Fighters {
		return ShipDuelResult{}, errors.New("committed fighters are no longer available")
	}
	result, err := ResolveShipDuel(intent.Fighters, d.Fighters, d.Shields, a.Cloak, rng)
	if err != nil {
		return ShipDuelResult{}, err
	}
	a.Fighters -= result.AttackerLosses
	d.Fighters, d.Shields = result.DefenderFighters, result.DefenderShields
	if result.Destroyed {
		result.Salvage, err = w.SettleShipSalvage(DeathContext{Victim: d.ID, Generation: d.ShipGeneration, Sector: d.Sector, Killer: a.ID, Cause: "combat"}, rng, now)
		if err != nil {
			return ShipDuelResult{}, err
		}
		// Salvage consumes awarded mines first. Earth safely destroys the
		// remainder; no duplicate stock can become a protected-spawn hazard.
		if intent.Sector == 1 {
			result.DisarmedMines = d.Mines
			d.Mines = 0
		} else {
			result.DroppedMines = d.Mines
			if err = w.dropMines(intent.Sector, d.ID, d.Mines); err != nil {
				return ShipDuelResult{}, err
			}
			d.Mines = 0
			result.MineAftermath, err = w.ResolveMinefield(a.ID, rng, now)
			if err != nil {
				return ShipDuelResult{}, err
			}
		}
	}
	return result, nil
}
