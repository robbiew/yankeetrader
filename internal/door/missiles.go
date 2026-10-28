package door

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"math/rand"
	"strconv"
	"strings"
	"time"
)

func (s Session) launchMissiles(id int, args []string, pending *[]string, v *game.Visibility) error {
	if len(args) != 0 && len(args) != 2 {
		return errors.New("use MISSILE [<adjacent sector> <quantity>]")
	}
	if len(args) == 0 {
		sector, err := s.classicArgument("Fire missiles into which adjacent sector (blank cancels)? ", pending)
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
	name := "minefield only"
	if intent.Target != 0 {
		name = w.Players[intent.Target].Alias
	}
	mines := int64(0)
	for _, layer := range intent.Mines {
		mines += layer.Count
	}
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("Launch %d missiles into sector %d (%s; %d mines)? Your shields: %d. A surviving enemy may retaliate. [y/N] ", count, to, name, mines, w.Players[id].Shields); err != nil {
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
	if out.Target == 0 {
		return s.Terminal.Printf("%s: %d missiles fired, %d mines destroyed. No ship struck.\r\n", label, out.Launched, out.MinesDestroyed)
	}
	if err := s.Terminal.Printf("%s: %d missiles fired, %d mines destroyed; %s lost %d fighters and %d shields.\r\n", label, out.Launched, out.MinesDestroyed, name, out.Damage.Fighters, out.Damage.Shields); err != nil {
		return err
	}
	if out.Destroyed {
		if out.LostEscorts > 0 {
			if err := s.Terminal.Printf("%d remaining fighters were lost with the ship.\r\n", out.LostEscorts); err != nil {
				return err
			}
		}
		if err := s.Terminal.Printf("%s destroyed. %s recovered %d credits, %d holds, %d missiles, %d plasma, %d ground forces, %d mines; cargo %d/%d/%d.\r\n", name, recipient, out.Salvage.Credits, out.Salvage.Holds, out.Salvage.Missiles, out.Salvage.Plasma, out.Salvage.Ground, out.Salvage.Mines, out.Salvage.Cargo[0], out.Salvage.Cargo[1], out.Salvage.Cargo[2]); err != nil {
			return err
		}
	}
	if out.Dropped > 0 {
		if err := s.Terminal.Printf("Wreck dropped %d unsalvaged mines.\r\n", out.Dropped); err != nil {
			return err
		}
	}
	if out.Disarmed > 0 {
		return s.Terminal.Printf("Earth protection safely disposed of %d unsalvaged mines.\r\n", out.Disarmed)
	}
	return nil
}
