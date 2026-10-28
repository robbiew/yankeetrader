package store

import (
	"errors"
	"math/rand"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

// UpdateWithSpies advances this login's spies once per supported successful
// action. Failed actions, failed saves and expired sessions publish no reports.
func (s Store) UpdateWithSpies(fn func(*game.World) error, now, deadline time.Time) error {
	return s.updateState(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return fn(w)
	}, false, false, func(w *game.World, n *game.SpyNetwork) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		// A fatal action must still commit. The obsolete login cannot read its spies.
		if err := w.CheckShip(s.ship.id, s.ship.generation); err != nil {
			return nil
		}
		if err := n.Advance(w, now, rand.Float64); err != nil {
			return err
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return nil
	})
}
func (s Store) HireSpies(token string, sectors []int, now, deadline time.Time) error {
	return s.updateState(func(w *game.World) error { return nil }, false, false, func(w *game.World, n *game.SpyNetwork) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return n.Hire(w, token, sectors, now)
	})
}

// SpySnapshot returns copies under the same lock as commits. It never reads
// another login's memory and remains readable during encounters, like radio.
func (s Store) SpySnapshot(unread bool) (locations []int, reports []game.SpyReport, err error) {
	if s.ship != nil {
		s.ship.spyMu.Lock()
		defer s.ship.spyMu.Unlock()
	}
	err = s.locked(func() error {
		w, e := s.load()
		if e != nil {
			return e
		}
		if s.ship == nil {
			return errors.New("spies require a bound ship session")
		}
		if e = s.checkShip(w); e != nil {
			return e
		}
		locations, e = s.ship.spies.Locations(w)
		if e != nil {
			return e
		}
		reports, e = s.ship.spies.Reports(w, unread)
		return e
	})
	return
}
func (s Store) AcknowledgeSpy(report uint64) error {
	if s.ship != nil {
		s.ship.spyMu.Lock()
		defer s.ship.spyMu.Unlock()
	}
	return s.locked(func() error {
		w, e := s.load()
		if e != nil {
			return e
		}
		if s.ship == nil {
			return errors.New("spies require a bound ship session")
		}
		return s.ship.spies.Acknowledge(w, report)
	})
}
