package store

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"time"
)

// CreatePlanet rechecks the preview location and real deadline while holding
// the save lock. Creation and its public snapshot share the replacement.
func (s Store) CreatePlanet(id int, name string, sector int, now func() time.Time, deadline time.Time) error {
	if s.ship != nil && id != s.ship.id {
		return errors.New("planet creator does not match bound login")
	}
	return s.Update(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired; planet creation cancelled")
		}
		if w.Players[id] == nil || w.Players[id].Sector != sector {
			return errors.New("sector changed; start planet creation again")
		}
		if err := w.CreatePlanet(id, name, now()); err != nil {
			return err
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired; planet creation cancelled")
		}
		return nil
	})
}
