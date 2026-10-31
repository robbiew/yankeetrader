package door

import (
	"errors"
	"math/rand"
	"strconv"
	"strings"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) bribe(id int, args []string, pending *[]string) error {
	if len(args) > 2 {
		return errors.New("use BRIBE [whole credits] or BRIBE <adjacent sector> <whole credits>")
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	p := w.Players[id]
	target := p.Sector
	if len(args) == 2 {
		target, err = strconv.Atoi(args[0])
		if err != nil || target < 1 {
			return errors.New("choose a sector number")
		}
		args = args[1:]
	}
	sector := w.Sectors[target]
	if !w.HostileDefense(id, target) {
		return errors.New("no hostile sector fighter group here")
	}
	offer := int64(0)
	if len(args) == 0 && sector.Defense.Owner == game.MercenaryOwner && sector.Planet == 0 {
		value, e := s.classicArgument("Offer how many whole credits to the Mercenaries (blank cancels)? ", pending)
		if e != nil {
			return e
		}
		if strings.TrimSpace(value) == "" {
			*pending = nil
			return s.Terminal.Printf("Bribe cancelled.\r\n")
		}
		args = []string{value}
	}
	if len(args) == 1 {
		offer, err = strconv.ParseInt(args[0], 10, 64)
		if err != nil || offer < 1 {
			return errors.New("choose a positive whole-credit offer; blank cancels")
		}
	}
	entry, err := s.Store.PrepareBribeAt(target, offer, s.Deadline)
	if err != nil {
		return err
	}
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if entry.Hostile && entry.Defense.Owner == game.MercenaryOwner && entry.Planet == 0 {
		if err = s.Terminal.Printf("The Mercenaries remember your attacks and refuse to negotiate.\r\n"); err != nil {
			return err
		}
	}
	mines := int64(0)
	for _, layer := range entry.Mines {
		mines += layer.Count
	}
	if entry.From != entry.Sector {
		if err = s.Terminal.Printf("Entering sector %d spends one turn and may encounter %d mines after negotiations.\r\n", entry.Sector, mines); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("Attempt bribery of %d fighters in sector %d with %d credits? Refusal or insult may commit ALL %d ship fighters; defeat forces emergency escape. [y/N] ", entry.Defense.Fighters, entry.Sector, entry.Offer, entry.Fighters); err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Bribe cancelled.\r\n")
	}
	out, err := s.Store.Bribe(entry, rand.Float64, s.Now, s.Deadline)
	if handled, e := s.finishArrival(err, pending); handled || e != nil {
		return e
	}
	if out.Joined > 0 {
		if err = s.Terminal.Printf("Bribe saved: paid %d credits; %d Mercenary fighters joined your ship.\r\n", out.Paid, out.Joined); err != nil {
			return err
		}
		return s.showMineOutcome(out.Defense.Mines)
	}
	if err = s.Terminal.Printf("Bribe saved: %s; no credits paid.\r\n", out.Reason); err != nil {
		return err
	}
	if out.Combat {
		if err = s.Terminal.Printf("Forced defense combat: %d attackers lost, %d defenders destroyed.\r\n", out.Defense.Battle.AttackerLosses, out.Defense.Battle.DefenderLosses); err != nil {
			return err
		}
		if out.Defense.HQReward != nil {
			if err = s.showHQReward(*out.Defense.HQReward); err != nil {
				return err
			}
		}
		if out.Defense.Escaped {
			return s.Terminal.Printf("Emergency escape reached safe sector %d.\r\n", out.Defense.Sector)
		}
		return s.showMineOutcome(out.Defense.Mines)
	}
	return s.showMineOutcome(out.Defense.Mines)
}
