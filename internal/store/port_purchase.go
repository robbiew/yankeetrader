package store

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"time"
)

// PurchasePort binds the confirmation to the login and rechecks expiry under
// the save lock. Settlement and the private seller notice save together.
func (s Store) PurchasePort(id int, quote game.PortPurchaseQuote, now func() time.Time, deadline time.Time) error {
	if s.ship != nil && id != s.ship.id {
		return errors.New("buyer does not match bound login")
	}
	return s.Update(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired; port purchase cancelled")
		}
		if err := w.PurchasePort(id, quote, now()); err != nil {
			return err
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired; port purchase cancelled")
		}
		return nil
	})
}
