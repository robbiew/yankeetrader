package game

import (
	"errors"
	"math"
	"time"
)

var ErrShipDestroyed = errors.New("your ship was destroyed; reconnect for a replacement")
var ErrShipChanged = errors.New("this ship session is no longer current; reconnect")

// Death records attribution once; replacement clears it. Account assets are not
// loot: this foundation neither awards salvage nor changes planet/port owners.
type Death struct {
	At     time.Time
	Cause  string
	Killer int
	Sector int
}

type DeathContext struct {
	Victim     int
	Generation uint64
	Sector     int
	Killer     int
	Cause      string
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

// RecordDeath must be composed with combat settlement inside one store Update.
// Target position/generation are rechecked rather than trusting a target menu.
// No player command exposes this method before combat settlement is implemented.
func (w *World) RecordDeath(context DeathContext, now time.Time) error {
	p, err := w.player(context.Victim)
	if err != nil {
		return err
	}
	if p.ShipGeneration != context.Generation || p.Sector != context.Sector {
		return errors.New("target ship or location changed")
	}
	if now.IsZero() || now.Before(w.Created) || p.ShipGeneration >= math.MaxUint64-1 {
		return errors.New("invalid death time or exhausted ship generation")
	}
	switch context.Cause {
	case "combat", "retaliation":
		if context.Killer == p.ID || w.Players[context.Killer] == nil {
			return errors.New("enemy death requires a different existing killer")
		}
		killer := w.Players[context.Killer]
		if p.Team != 0 && p.Team == killer.Team {
			return errors.New("teammates cannot be attacked")
		}
		if context.Cause == "combat" && (killer.Death != nil || killer.Sector != p.Sector) {
			return errors.New("attacker ship or location changed")
		}

	case "self":
		if context.Killer != p.ID {
			return errors.New("self death requires the ship's own player")
		}
	case "hazard":
		if context.Killer != 0 {
			return errors.New("environmental death has no player killer")
		}
	default:
		return errors.New("unknown death cause")
	}
	p.Death = &Death{At: now.UTC(), Cause: context.Cause, Killer: context.Killer, Sector: p.Sector}
	p.ShipGeneration++
	p.Sector = 0
	p.DockToken, p.PlanetToken, p.LandedPlanet = "", "", 0
	p.DockUntil = time.Time{}
	p.DockPrices = [3]int64{}
	if team := w.Teams[p.Team]; team != nil && team.Captain == p.ID {
		team.Captain = 0
	}
	return nil
}

// ReplaceShip is a login-only transition. It preserves the account's remaining
// daily turns, identity, membership and personal assets. No death refills turns.
func (w *World) ReplaceShip(id int, now time.Time) error {
	p := w.Players[id]
	if p == nil {
		return errors.New("player no longer exists")
	}
	if p.Death == nil {
		return errors.New("this ship is still alive")
	}
	if now.Before(p.Death.At) || p.ShipGeneration == math.MaxUint64 {
		return errors.New("invalid replacement time or exhausted ship generation")
	}
	if p.Death.Cause == "self" && day(now) <= day(p.Death.At) {
		return errors.New("self-destroyed ships may be replaced tomorrow (UTC)")
	}
	p.ShipGeneration++
	p.Death = nil
	p.Sector = 1
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
		if p.Death == nil {
			continue
		}
		death := p.Death
		if p.ShipGeneration == 0 || p.Sector != 0 || w.Sectors[death.Sector] == nil || death.At.IsZero() || death.At.Before(w.Created) || p.DockToken != "" || p.PlanetToken != "" || p.LandedPlanet != 0 || !p.DockUntil.IsZero() || p.DockPrices != [3]int64{} {
			return errors.New("invalid destroyed ship")
		}
		switch death.Cause {
		case "combat", "retaliation":
			if death.Killer == p.ID || w.Players[death.Killer] == nil {
				return errors.New("invalid enemy killer")
			}
		case "self":
			if death.Killer != p.ID {
				return errors.New("invalid self killer")
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
