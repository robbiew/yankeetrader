package door

import (
	"errors"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/game"
	"math/rand"
	"strconv"
	"strings"
	"time"
)

func (s Session) launchMissiles(id int, args []string, pending *[]string, v *game.Visibility) error {
	if len(args) != 0 && len(args) != 2 {
		return errors.New("use MISSILE [<sector> <quantity>]")
	}
	if len(args) == 0 {
		sector, err := s.classicArgument("Fire missiles into which sector (blank cancels)? ", pending)
		if err != nil {
			return err
		}
		if strings.TrimSpace(sector) == "" {
			return s.Terminal.Printf("Missile launch cancelled.\r\n")
		}
		quantity, err := s.classicArgument("How many missiles will you launch? ", pending)
		if err != nil {
			return err
		}
		args = []string{sector, quantity}
	}
	to, err := strconv.Atoi(args[0])
	if err != nil {
		return errors.New("choose a sector number")
	}
	count, err := strconv.ParseInt(args[1], 10, 64)
	if err != nil {
		return errors.New("choose a whole number of missiles")
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	intent, err := w.PrepareMissile(id, to, count, v)
	if err != nil {
		return err
	}
	name := missileTargetSummary(w, id, intent)
	route := make([]string, len(intent.Route))
	for i, sector := range intent.Route {
		route[i] = strconv.Itoa(sector)
	}
	if err = s.Terminal.Printf("Missile course (%d warps): %s\r\n", len(intent.Route)-1, strings.Join(route, " -> ")); err != nil {
		return err
	}
	mines := int64(0)
	for _, sector := range intent.Sectors {
		for _, layer := range sector.Mines {
			mines += layer.Count
		}
	}
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	consequence := "A surviving ship with a route back may retaliate."
	for _, sector := range intent.Sectors {
		if planet := sector.Planet; planet != nil {
			actor, owner := w.Players[id], w.Players[planet.Owner]
			friendly := planet.Owner == id || actor.Team != 0 && owner != nil && owner.Team == actor.Team
			if !friendly {
				consequence += " Hostile planets along the course may be damaged or destroyed."
				break
			}
		}
	}
	if err = s.Terminal.Printf("Launch %d missiles into sector %d (%s; %d route mines)? Your shields: %d. %s [y/N] ", count, to, name, mines, w.Players[id].Shields, consequence); err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Missile launch cancelled.\r\n")
	}
	var result game.MissileResult
	err = s.Store.Update(func(w *game.World) error {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired; missile launch cancelled")
		}
		var err error
		result, err = w.CommitMissile(intent, v, rand.Float64, s.Now())
		if err == nil && !time.Now().Before(s.Deadline) {
			return errors.New("session time expired; missile launch cancelled")
		}
		return err
	})
	if err != nil {
		return err
	}
	if err = s.showMissileImpact("Missile launch saved", name, "You", result.Primary); err != nil {
		return err
	}
	if result.Counter.Launched == 0 {
		return nil
	}
	if err = s.showMissileImpact("Enemy retaliation saved", "your ship", name, result.Counter); err != nil {
		return err
	}
	if result.Counter.Destroyed {
		return game.ErrShipDestroyed
	}
	return nil
}
func (s Session) showMissileImpact(label, name, recipient string, out game.MissileImpact) error {
	if len(out.ShipImpacts) == 0 {
		if err := s.Terminal.Printf("%s: %d missiles fired, %d mines destroyed. No ship struck.\r\n", label, out.Launched, out.MinesDestroyed); err != nil {
			return err
		}
	} else if err := s.Terminal.Printf("%s: %d missiles fired, %d mines destroyed; %d ships struck.\r\n", label, out.Launched, out.MinesDestroyed, len(out.ShipImpacts)); err != nil {
		return err
	}
	for _, impact := range out.Interceptions {
		if impact.Missiles > 0 {
			if err := s.Terminal.Printf("Sector interception: %d missiles, %d fighters destroyed in sector %d.\r\n", impact.Missiles, impact.FightersDestroyed, impact.Sector); err != nil {
				return err
			}
		}
		if impact.MinesDestroyed > 0 {
			if err := s.Terminal.Printf("Mines in sector %d destroyed: %d.\r\n", impact.Sector, impact.MinesDestroyed); err != nil {
				return err
			}
		}
	}
	for _, impact := range out.ShipImpacts {
		if impact.Destroyed {
			if impact.LostEscorts > 0 {
				if err := s.Terminal.Printf("%d remaining fighters were lost with the ship.\r\n", impact.LostEscorts); err != nil {
					return err
				}
			}
			if err := s.Terminal.Printf("%s destroyed. %s recovered %d credits, %d holds, %d missiles, %d plasma, %d ground forces, %d mines; cargo %d/%d/%d (sector %d).\r\n", impact.Alias, recipient, impact.Salvage.Credits, impact.Salvage.Holds, impact.Salvage.Missiles, impact.Salvage.Plasma, impact.Salvage.Ground, impact.Salvage.Mines, impact.Salvage.Cargo[0], impact.Salvage.Cargo[1], impact.Salvage.Cargo[2], impact.Sector); err != nil {
				return err
			}
		} else if err := s.Terminal.Printf("%s in sector %d lost %d fighters and %d shields.\r\n", impact.Alias, impact.Sector, impact.Damage.Fighters, impact.Damage.Shields); err != nil {
			return err
		}
	}
	for _, impact := range out.PlanetImpacts {
		if err := s.Terminal.Printf("Planet bombardment saved: %d missiles reached planet %d in sector %d; ground forces %d -> %d; production %.2f/%.2f/%.2f -> %.2f/%.2f/%.2f; warehouses %.2f/%.2f/%.2f -> %.2f/%.2f/%.2f.\r\n", impact.Missiles, impact.PlanetID, impact.Sector, impact.GroundBefore, impact.GroundAfter, impact.ProductionBefore[0], impact.ProductionBefore[1], impact.ProductionBefore[2], impact.ProductionAfter[0], impact.ProductionAfter[1], impact.ProductionAfter[2], impact.CargoBefore[0], impact.CargoBefore[1], impact.CargoBefore[2], impact.CargoAfter[0], impact.CargoAfter[1], impact.CargoAfter[2]); err != nil {
			return err
		}
		if impact.Destroyed {
			if err := s.Terminal.Printf("Planet %d destroyed; surviving ships and the sector remain. No planetary bank or inventory was salvaged.\r\n", impact.PlanetID); err != nil {
				return err
			}
		}
	}
	if out.Dropped > 0 {
		if err := s.Terminal.Printf("Wrecks dropped %d unsalvaged mines.\r\n", out.Dropped); err != nil {
			return err
		}
	}
	if out.Disarmed > 0 {
		return s.Terminal.Printf("Earth protection safely disposed of %d unsalvaged mines.\r\n", out.Disarmed)
	}
	return nil
}

func missileTargetSummary(w *game.World, shooter int, intent game.MissileIntent) string {
	var names []string
	for _, sector := range intent.Sectors {
		for _, ship := range sector.Ships {
			names = append(names, ship.Alias)
		}
		if planet := sector.Planet; planet != nil {
			actor, owner := w.Players[shooter], w.Players[planet.Owner]
			friendly := planet.Owner == shooter || actor != nil && actor.Team != 0 && owner != nil && owner.Team == actor.Team
			if friendly {
				continue
			}
			if len(intent.Sectors) == 1 && len(sector.Ships) == 0 {
				return fmt.Sprintf("planet %s; %d ground forces; production %g/%g/%g", planet.Name, planet.Ground, planet.Production[0], planet.Production[1], planet.Production[2])
			}
			names = append(names, "planet "+planet.Name)
		}
	}
	if len(names) == 0 {
		return "sector defenses or mines"
	}
	return strings.Join(names, ", ")
}
