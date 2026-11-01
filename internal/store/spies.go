package store

import (
	"errors"
	"math/rand"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

// UpdateWithSpies advances this login's spies once per supported successful
// action. Failures before replacement and expired sessions publish no reports.
// A post-replacement durability warning preserves committed spy state.
func (s Store) UpdateWithSpies(fn func(*game.World) error, now, deadline time.Time) error {
	return s.updateState(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return fn(w)
	}, false, false, func(w *game.World, n *game.SpyNetwork) error { return s.advanceSpies(w, n, now, deadline) })
}
func (s Store) advanceSpies(w *game.World, n *game.SpyNetwork, now, deadline time.Time) error {
	if !time.Now().Before(deadline) {
		return errors.New("session time expired")
	}
	// Fatal actions commit but cannot confer access on the obsolete login.
	if w.CheckSession(s.ship.id, s.ship.generation, s.ship.season) != nil {
		return nil
	}
	rng := s.ship.spyRNG
	if rng == nil {
		rng = rand.Float64
	}
	if err := n.Advance(w, now, rng); err != nil {
		return err
	}
	if !time.Now().Before(deadline) {
		return errors.New("session time expired")
	}
	return nil
}

// SessionVisibility creates one private cache per bound login. It cannot bind a
// cache borrowed from another login, even for the same account/incarnation.
func (s Store) SessionVisibility() (v *game.Visibility, err error) {
	if s.ship == nil {
		return nil, errors.New("visibility requires a bound login")
	}
	s.ship.arrivalMu.Lock()
	defer s.ship.arrivalMu.Unlock()
	s.ship.spyMu.Lock()
	defer s.ship.spyMu.Unlock()
	err = s.locked(func() error {
		w, e := s.load()
		if e != nil {
			return e
		}
		if e = s.checkShip(w); e != nil {
			return e
		}
		if s.ship.visibility == nil {
			s.ship.visibility, e = w.NewVisibility(s.ship.id)
			if e != nil {
				return e
			}
		}
		v = s.ship.visibility
		s.ship.spies.PublishVisibility(v)
		return nil
	})
	return
}

// HireSpies samples its clock after both session and world locks are held so
// waiting for either lock cannot extend the lifetime of a docking token.
func (s Store) HireSpies(token string, sectors []int, now func() time.Time, deadline time.Time) error {
	if now == nil {
		return errors.New("spy hiring requires a clock")
	}
	return s.updateState(func(w *game.World) error { return nil }, false, false, func(w *game.World, n *game.SpyNetwork) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		if err := n.Hire(w, token, sectors, now()); err != nil {
			return err
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return nil
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
		if e = s.checkShip(w); e != nil {
			return e
		}
		return s.ship.spies.Acknowledge(w, report)
	})
}
