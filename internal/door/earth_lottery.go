package door

import (
	"errors"
	"strings"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func (s Session) paidLottery(token string, args []string, pending *[]string) error {
	return s.lotteryWithDraw(token, args, pending, store.LotteryDigit)
}
func (s Session) lotteryWithDraw(token string, args []string, pending *[]string, draw func() (int, error)) error {
	if len(args) > 1 {
		return errors.New("use LOTTERY [six digits]")
	}
	ticket := ""
	if len(args) == 1 {
		ticket = args[0]
	} else {
		var err error
		ticket, err = s.portArgument("Enter six digits for the paid lottery (blank cancels): ", pending)
		if err != nil {
			return err
		}
	}
	if ticket == "" {
		return s.Terminal.Printf("Lottery cancelled; no credits or plays spent.\r\n")
	}
	entry, err := s.Store.PrepareLottery(token, ticket, s.Now, s.Deadline)
	if err != nil {
		return err
	}
	defer s.Store.CancelLottery(entry)
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("Ticket %s costs %d credits; %d plays remaining today (UTC). Buy this ticket? [y/N] ", ticket, game.LotteryPrice, entry.Limit-entry.Used); err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Lottery cancelled; no credits or plays spent.\r\n")
	}
	out, err := s.Store.PlayLottery(entry, draw, s.Now, s.Deadline)
	return s.lotteryReceipt(out, err)
}

func (s Session) lotteryReceipt(out game.LotteryReceipt, err error) error {
	var committed *store.DurabilityError
	if err != nil && !errors.As(err, &committed) {
		return err
	}
	if e := s.Terminal.Printf("Lottery saved: ticket %s; drawn %s; matches %d. Fee: %d. Gross prize: %d. Awarded: %d. Credit cap reduction: %d. Balance: %d. Plays remaining: %d (UTC).\r\n", out.Ticket, out.Draw, out.Matches, out.Fee, out.Gross, out.Award, out.Capped, out.Balance, out.Remaining); e != nil {
		// The receipt may fail after a visible save with uncertain durability. Keep
		// that warning discoverable even when the output error is also EOF.
		return errors.Join(err, e)
	}
	// Return the committed storage warning after the exact saved receipt; the main
	// session ends instead of presenting an unsaved failure or retrying the ticket.
	return err
}
