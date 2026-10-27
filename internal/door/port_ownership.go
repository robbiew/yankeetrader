package door

import (
	"strings"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) buyPort(id int, pending *[]string) error {
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	quote, err := w.QuotePortPurchase(id, s.Now())
	if err != nil {
		return err
	}
	p := w.Players[id]
	if s.Classic {
		if err = s.portColor(6); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("This port is for sale for %d credits. You have %d credits.\r\n", quote.Price, p.Credits); err != nil {
		return err
	}
	if p.Credits < quote.Price {
		return s.Terminal.Printf("Come back when you can afford it!\r\n")
	}
	if quote.Owner != 0 {
		if err = s.Terminal.Printf("You may buy it from %s if you wish.\r\n", w.Players[quote.Owner].Alias); err != nil {
			return err
		}
	}
	answer, err := s.classicArgument("Do you wish to buy it? [y/N] ", pending)
	if err != nil {
		return err
	}
	if !strings.EqualFold(answer, "y") {
		return s.Terminal.Printf("Port purchase cancelled.\r\n")
	}
	if err = s.Store.Update(func(w *game.World) error { return w.PurchasePort(id, quote, s.Now()) }); err != nil {
		return err
	}
	return s.Terminal.Printf("Sold! Port ownership saved.\r\n")
}

func (s Session) portTreasuryReport(id int) error {
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	accounts, err := w.PortAccounts(id)
	if err != nil {
		return err
	}
	if len(accounts) == 0 {
		return s.Terminal.Printf("You don't OWN any ports!!!\r\n")
	}
	if err = s.Terminal.Printf("Port treasury report (%d personally owned):\r\n", len(accounts)); err != nil {
		return err
	}
	for _, account := range accounts {
		if err = s.Terminal.Printf("Sector %d: %s - %d credits\r\n", account.Sector, account.Name, account.Treasury); err != nil {
			return err
		}
	}
	return nil
}

func (s Session) collectPortTreasury(id int) error {
	var amount int64
	err := s.Store.Update(func(w *game.World) error {
		var err error
		amount, err = w.CollectPortTreasury(id)
		return err
	})
	if err != nil {
		return err
	}
	return s.Terminal.Printf("Collected %d credits from your port treasuries.\r\n", amount)
}
