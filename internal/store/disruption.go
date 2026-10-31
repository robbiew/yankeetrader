package store

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"time"
)

// StartDisruption samples once under both locks. Locations and receipts become
// visible to this login only after its startup arrival has committed.
func (s Store) StartDisruption(rng func() float64, now func() time.Time, deadline time.Time) error {
	if s.ship == nil || now == nil {
		return errors.New("disruption requires a bound login and clock")
	}
	s.ship.arrivalMu.Lock()
	defer s.ship.arrivalMu.Unlock()
	if s.ship.disruption != nil {
		return errors.New("disruption already initialized for this login")
	}
	return s.locked(func() error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		w, err := s.load()
		if err != nil {
			return err
		}
		if err = s.checkShip(w); err != nil {
			return err
		}
		d, err := w.NewDisruption(s.ship.id, rng)
		if err != nil {
			return err
		}
		if err = w.BindDisruption(d, rng, now); err != nil {
			return err
		}
		if err = w.FinishArrival(); err != nil {
			return err
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		err = s.save(w)
		var committed *DurabilityError
		if err != nil && !errors.As(err, &committed) {
			return err
		}
		s.ship.disruption = &d
		s.ship.arrivalRNG = rng
		s.ship.arrivalNow = now
		s.ship.arrivalDeadline = deadline
		s.ship.arrivalReceipt = w.ArrivalOutcome()
		return err
	})
}

// TakeArrival returns one committed private receipt, even if that action killed
// the ship. It never exposes location pairs or publishes an aborted result.
func (s Store) TakeArrival() game.ArrivalOutcome {
	if s.ship == nil {
		return game.ArrivalOutcome{}
	}
	s.ship.arrivalMu.Lock()
	defer s.ship.arrivalMu.Unlock()
	out := s.ship.arrivalReceipt
	s.ship.arrivalReceipt = game.ArrivalOutcome{}
	return out
}
