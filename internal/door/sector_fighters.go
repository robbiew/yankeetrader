package door

import (
	"errors"
	"math/rand"
	"strconv"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) setSectorFighters(id int, args []string, pending *[]string, reinforce bool) error {
	if len(args) > 1 {
		return errors.New("choose one fighter quantity")
	}
	if len(args) == 0 {
		prompt := "Defend this sector with how many fighters in total (0 recovers your group)? "
		if reinforce {
			prompt = "How many fighters do you wish to transfer to the current friendly defense? "
		}
		value, err := s.classicArgument(prompt, pending)
		if err != nil {
			return err
		}
		if strings.TrimSpace(value) == "" {
			return nil
		}
		args = []string{value}
	}
	count, err := strconv.ParseInt(args[0], 10, 64)
	if err != nil {
		return errors.New("choose a whole fighter quantity")
	}
	err = s.Store.Update(func(w *game.World) error {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		var e error
		if reinforce {
			e = w.ReinforceSector(id, count)
		} else {
			e = w.SetSectorFighters(id, count)
		}
		if e != nil {
			return e
		}
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		return nil
	})
	if err != nil {
		return err
	}
	return s.Terminal.Printf("Sector fighter transfer saved.\r\n")
}
func (s Session) defenseEncounter(id int, args []string, pending *[]string, retreat bool) error {
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	var entry game.DefenseIntent
	if retreat {
		if len(args) != 0 {
			return errors.New("use FLEE from the current hostile defense")
		}
		entry, err = w.PrepareDefenseRetreat(id)
	} else {
		if len(args) != 2 {
			return errors.New("use BREACH <current or adjacent sector> <fighters>")
		}
		to, e := strconv.Atoi(args[0])
		if e != nil {
			return errors.New("choose a sector number")
		}
		force, e := strconv.ParseInt(args[1], 10, 64)
		if e != nil {
			return errors.New("choose a whole fighter force")
		}
		entry, err = w.PrepareDefenseFight(id, to, force, true)
	}
	if err != nil {
		return err
	}
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if !retreat {
		if err = s.Terminal.Printf("Accept human surrender if offered during this battle? [Y/n] "); err != nil {
			return err
		}
		choice, e := s.readAttackConfirmation()
		if e != nil {
			return e
		}
		if strings.TrimSpace(choice) != "" && !strings.EqualFold(strings.TrimSpace(choice), "y") && !strings.EqualFold(strings.TrimSpace(choice), "n") {
			return s.Terminal.Printf("Battle cancelled.\r\n")
		}
		entry.AcceptSurrender = !strings.EqualFold(strings.TrimSpace(choice), "n")
	}
	mines := int64(0)
	for _, layer := range entry.Mines {
		mines += layer.Count
	}
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if retreat {
		err = s.Terminal.Printf("Emergency escape from sector %d? Warp may use all remaining turns. [y/N] ", entry.From)
	} else {
		err = s.Terminal.Printf("Fight %d sector fighters with %d fighters in sector %d (%d mines)? Lost forces stay lost; defeat forces emergency escape. [y/N] ", entry.Defense.Fighters, entry.Fighters, entry.To, mines)
	}
	if err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Defense encounter cancelled.\r\n")
	}
	out, err := s.Store.DefenseEncounter(entry, rand.Float64, s.Now(), s.Deadline)
	if handled, e := s.finishArrival(err, pending); handled || e != nil {
		return e
	}
	if err = s.Terminal.Printf("Defense encounter saved: %d attackers lost, %d defenders destroyed, %d surrendered.\r\n", out.Battle.AttackerLosses, out.Battle.DefenderLosses, out.Battle.Joined); err != nil {
		return err
	}
	if out.HQReward != nil {
		if err = s.showHQReward(*out.HQReward); err != nil {
			return err
		}
	}
	if out.Escaped {
		return s.Terminal.Printf("Emergency escape reached safe sector %d.\r\n", out.Sector)
	}
	if err = s.Terminal.Printf("Hostile defense cleared in sector %d.\r\n", entry.To); err != nil {
		return err
	}
	return s.showMineOutcome(out.Mines)
}

// Display only after the store reports success. A committed durability error is
// handled by the existing error path; never promise a rollback or repeat payment.
func (s Session) showHQReward(reward game.XannorHQReward) error {
	if err := s.Terminal.Printf("Xannor HQ victory in sector %d. Credits added: %d.\r\n", reward.Sector, reward.Credits); err != nil {
		return err
	}
	if reward.Credits < game.XannorHQBonus {
		return s.Terminal.Printf("Ship credit limit capped this bonus.\r\n")
	}
	return nil
}
