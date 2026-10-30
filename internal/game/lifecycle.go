package game

import (
	"errors"
	"math"
	"time"
)

var ErrShipDestroyed = errors.New("your ship was destroyed; reconnect for a replacement")
var ErrShipChanged = errors.New("this ship session is no longer current; reconnect")

// Death records attribution once; replacement clears it. Account assets are not
// loot. Settlement consumes awards separately; death handles titles and access.
type Death struct {
	At     time.Time
	Cause  string
	Killer int
	Sector int
}

type DeathContext struct {
	Victim       int
	Generation   uint64
	Sector       int
	Killer       int
	Cause        string
	MissileRoute []int
}

func (w *World) CheckShip(id int, generation uint64) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	if p.ShipGeneration != generation {
		return ErrShipChanged
	}
	return nil
}

// deathTarget validates the current target before randomness or mutation.
func (w *World) deathTarget(context DeathContext, now time.Time) (*Player, error) {
	p, err := w.player(context.Victim)
	if err != nil {
		return nil, err
	}
	if p.ShipGeneration != context.Generation || p.Sector != context.Sector {
		return nil, errors.New("target ship or location changed")
	}
	if now.IsZero() || now.Before(w.Created) || p.ShipGeneration >= math.MaxUint64-1 {
		return nil, errors.New("invalid death time or exhausted ship generation")
	}
	switch context.Cause {
	case "combat", "retaliation", "missile":
		if context.Killer == p.ID || w.Players[context.Killer] == nil {
			return nil, errors.New("enemy death requires a different existing killer")
		}
		killer := w.Players[context.Killer]
		if killer.Death != nil {
			return nil, errors.New("destroyed killer cannot receive an estate")
		}
		if p.Team != 0 && p.Team == killer.Team {
			return nil, errors.New("teammates cannot be attacked")
		}
		if context.Cause == "combat" && killer.Sector != p.Sector {
			return nil, errors.New("attacker ship or location changed")
		}

		if context.Cause == "missile" {
			if len(context.MissileRoute) == 0 {
				if !contains(w.Sectors[killer.Sector].Warps, p.Sector) || !contains(w.Sectors[p.Sector].Warps, killer.Sector) {
					return nil, errors.New("missile launch corridor changed")
				}
			} else {
				route := context.MissileRoute
				if len(route) < 2 || route[0] != killer.Sector || route[len(route)-1] != p.Sector {
					return nil, errors.New("missile launch route changed")
				}
				for i := 1; i < len(route); i++ {
					if w.Sectors[route[i-1]] == nil || w.Sectors[route[i]] == nil || !contains(w.Sectors[route[i-1]].Warps, route[i]) {
						return nil, errors.New("missile launch route changed")
					}
				}
			}
		}
	case "mines":
		if context.Killer < 0 || (context.Killer > 0 && w.Players[context.Killer] == nil) {
			return nil, errors.New("invalid mine source")
		}
	case "self":
		if context.Killer != p.ID {
			return nil, errors.New("self death requires the ship's own player")
		}
	case "xannor":
		if context.Killer != XannorOwner || context.Sector <= 7 {
			return nil, errors.New("invalid Xannor death source or protected sector")
		}
	case "hazard":
		if context.Killer != 0 {
			return nil, errors.New("environmental death has no player killer")
		}
	default:
		return nil, errors.New("unknown death cause")
	}
	return p, nil
}

// RecordDeath applies generation invalidation and estate/access cleanup together.
// Compose it with damage/awards inside one store Update, as CommitVisibleAttack does.
func (w *World) RecordDeath(context DeathContext, now time.Time) error {
	p, err := w.deathTarget(context, now)
	if err != nil {
		return err
	}
	w.recordDeath(p, context, now)
	return nil
}

// recordDeath is infallible after deathTarget validates the locked live ship.
func (w *World) recordDeath(p *Player, context DeathContext, now time.Time) {
	if w.Xannor != nil && w.Xannor.Revenge != nil && w.Xannor.Revenge.Player == p.ID {
		w.Xannor.Revenge = nil
	}
	p.Death = &Death{At: now.UTC(), Cause: context.Cause, Killer: context.Killer, Sector: p.Sector}
	p.ShipGeneration++
	p.Sector = 0
	p.MineGraceSector = 0
	p.DockToken, p.PlanetToken, p.LandedPlanet = "", "", 0
	p.DockUntil = time.Time{}
	p.DockPrices = [3]int64{}
	w.applyDeathEstate(p, context)
	if context.Cause == "xannor" {
		p.Credits, p.Holds, p.Fighters, p.Shields, p.Ground = 0, 0, 0, 0, 0
		p.Cargo = [3]int64{}
		p.Missiles, p.Mines, p.Plasma = 0, 0, 0
	}
}

// ReplaceShip is a login-only transition. It preserves the account's remaining
// daily turns, identity and retained planet assets. No death refills turns.
func (w *World) ReplaceShip(id int, now time.Time) error {
	p := w.Players[id]
	if p == nil {
		return errors.New("player no longer exists")
	}
	if p.Death == nil {
		return errors.New("this ship is still alive")
	}
	retired := !p.RetiredAt.IsZero()
	if retired && (w.activePlayers() >= MaxActivePlayers || now.Before(p.RetiredAt)) {
		return errors.New("no active player slot is available or login predates retirement")
	}
	if now.Before(p.Death.At) || p.ShipGeneration == math.MaxUint64 {
		return errors.New("invalid replacement time or exhausted ship generation")
	}
	if p.Death.Cause == "self" && day(now) <= day(p.Death.At) {
		return errors.New("self-destroyed ships may be replaced tomorrow (UTC)")
	}
	p.ShipGeneration++
	p.Death = nil
	p.RetiredAt = time.Time{}
	if retired {
		p.Turns = 500
	}
	p.Cloak = 1
	p.Sector = 1
	p.MineGraceSector = 0
	p.Credits, p.Holds, p.Fighters, p.Shields = 1005, 10, 25, 100
	p.Ground = 0
	p.Cargo = [3]int64{}
	p.Missiles, p.Mines, p.Plasma = 1, 0, 0
	p.DockToken, p.PlanetToken, p.LandedPlanet = "", "", 0
	p.DockUntil = time.Time{}
	p.DockPrices = [3]int64{}
	return nil
}

// LoginShip constructs a replacement only at a fresh authenticated login.
func (w *World) LoginShip(id int, now time.Time) error {
	p := w.Players[id]
	if p == nil {
		return errors.New("player no longer exists")
	}
	if p.Death != nil {
		return w.ReplaceShip(id, now)
	}
	return nil
}

func (w *World) validateLifecycle() error {
	for _, p := range w.Players {
		if p == nil {
			return errors.New("invalid player")
		}
		if !p.RetiredAt.IsZero() {
			_, offset := p.RetiredAt.Zone()
			if p.Death == nil || p.RetiredAt.Before(p.Death.At) || offset != 0 || p.Team != 0 || p.Credits != 0 || p.Turns != 0 || p.Holds != 0 || p.Fighters != 0 || p.Shields != 0 || p.Ground != 0 || p.Cargo != [3]int64{} || p.Missiles != 0 || p.Mines != 0 || p.Plasma != 0 || p.Cloak != 0 || p.StoredScore != 0 {
				return errors.New("invalid retired player")
			}
		}
		if p.Death == nil {
			continue
		}
		death := p.Death
		if p.ShipGeneration == 0 || p.Sector != 0 || w.Sectors[death.Sector] == nil || death.At.IsZero() || death.At.Before(w.Created) || p.DockToken != "" || p.PlanetToken != "" || p.LandedPlanet != 0 || !p.DockUntil.IsZero() || p.DockPrices != [3]int64{} {
			return errors.New("invalid destroyed ship")
		}
		switch death.Cause {
		case "combat", "retaliation", "missile":
			if death.Killer == p.ID || w.Players[death.Killer] == nil {
				return errors.New("invalid enemy killer")
			}
		case "mines":
			if death.Killer < 0 || (death.Killer > 0 && w.Players[death.Killer] == nil) {
				return errors.New("invalid mine source")
			}
		case "self":
			if death.Killer != p.ID {
				return errors.New("invalid self killer")
			}
		case "xannor":
			if death.Killer != XannorOwner || death.Sector <= 7 || p.Fighters != 0 || p.Shields != 0 {
				return errors.New("invalid Xannor death")
			}
		case "hazard":
			if death.Killer != 0 {
				return errors.New("invalid hazard killer")
			}
		default:
			return errors.New("invalid death cause")
		}
	}
	return nil
}
