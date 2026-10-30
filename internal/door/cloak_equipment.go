package door

import (
	"errors"
	"fmt"
	"strconv"
	"strings"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) buyCloak(token string, points int64) error {
	out, err := s.Store.RechargeCloak(token, points, s.Now, s.Deadline)
	if err != nil {
		return err
	}
	return s.Terminal.Printf("Cloak energy purchased and saved: %d points; credits spent: %d. Balance: %d. Energy: %.2f%% -> %.2f%%.\r\n", out.Points, out.Spent, out.Balance, out.Before*100, out.After*100)
}
func (s Session) classicRecharge(id int, token string, pending *[]string) error {
	for {
		w, p, _, err := s.portView(id, token)
		if err != nil {
			return err
		}
		limit, err := w.CloakPurchaseLimit(id, token, s.Now())
		if err != nil {
			return err
		}
		answer, err := s.portArgument(fmt.Sprintf("Cloak energy is down by %.2f%%.\r\nBuy how many points of Cloak Energy? [ %d ] (0 cancels)? ", 100-p.Cloak*100, limit), pending)
		if err != nil {
			return err
		}
		points := limit
		if answer != "" {
			points, err = strconv.ParseInt(answer, 10, 64)
		}
		if err != nil || points < 0 {
			return errors.New("enter whole cloak points; zero cancels")
		}
		if points == 0 {
			return s.Terminal.Printf("Cloak purchase cancelled; no credits spent.\r\n")
		}
		err = s.buyCloak(token, points)
		if !errors.Is(err, game.ErrCloakCapacity) {
			return err
		}
		if err = s.Terminal.Printf("Purchase rejected: cloak energy cannot exceed 100 percent.\r\n"); err != nil {
			return err
		}
		*pending = nil
		if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
			if err = terminal.DiscardTypeahead(); err != nil {
				return err
			}
		}
	}
}
func (s Session) activateAntiCloak(token string, args []string, pending *[]string) error {
	if len(args) != 0 {
		return errors.New("use ANTICLOAK (one paid activation for this login)")
	}
	entry, err := s.Store.PrepareAntiCloak(token, s.visibility, s.Now, s.Deadline)
	if err != nil {
		return err
	}
	defer s.Store.CancelAntiCloak(entry)
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("Anti-cloak costs %d credits and works for this login only. Repeat activation charges again, even if no new ships are revealed. Activate? [y/N] ", game.AntiCloakPrice); err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Anti-cloak cancelled; no credits spent.\r\n")
	}
	out, err := s.Store.ActivateAntiCloak(entry, s.visibility, s.Now, s.Deadline)
	if err != nil {
		return err
	}
	if err = s.Terminal.Printf("Anti-cloak activation saved for this login. Credits spent: %d. Balance: %d. Newly revealed: %d.\r\n", out.Spent, out.Balance, len(out.Revealed)); err != nil {
		return err
	}
	for _, target := range out.Revealed {
		if err = s.Terminal.Printf("%d: %s is revealed to this login.\r\n", target.ID, terminalLabel(target.Alias)); err != nil {
			return err
		}
	}
	return nil
}
