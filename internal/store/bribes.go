package store

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

// PrepareBribe binds a quote to this login and invalidates any older quote.
func (s Store) PrepareBribe(offer int64, deadline time.Time) (entry game.BribeIntent, err error) {
	return s.PrepareBribeAt(0, offer, deadline)
}

func (s Store) PrepareBribeAt(sector int, offer int64, deadline time.Time) (entry game.BribeIntent, err error) {
	if s.ship == nil {
		return entry, errors.New("bribery requires a bound ship session")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	err = s.locked(func() error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		w, e := s.load()
		if e != nil {
			return e
		}
		if e = s.checkShip(w); e != nil {
			return e
		}
		entry, e = w.PrepareBribeAt(s.ship.id, sector, offer, s.ship.mercenaryHostile)
		if e != nil {
			return e
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		token := make([]byte, 16)
		if _, e = rand.Read(token); e != nil {
			return e
		}
		s.ship.bribeActive = hex.EncodeToString(token)
		entry.Nonce = s.ship.bribeActive
		return nil
	})
	return
}

// Bribe consumes a confirmation once even when it is refused or rolls back.
// Hostility is session-only and publishes only with a committed world update.
func (s Store) Bribe(entry game.BribeIntent, rng func() float64, now func() time.Time, deadline time.Time) (out game.BribeOutcome, err error) {
	if s.ship == nil || entry.Player != s.ship.id || now == nil {
		return out, errors.New("bribery requires the bound player and a clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if entry.Nonce == "" || entry.Nonce != s.ship.bribeActive {
		return out, errors.New("bribe confirmation expired or already used; confirm again")
	}
	s.ship.bribeActive = ""
	err = s.update(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		var e error
		out, e = w.CommitBribe(entry, s.ship.mercenaryHostile, rng, now())
		if e == nil && !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return e
	}, false, true)
	var durability *DurabilityError
	if err == nil || errors.As(err, &durability) {
		if entry.Defense.Owner == game.MercenaryOwner && out.Defense.Battle.DefenderLosses > 0 {
			s.ship.mercenaryHostile = true
		}
	}
	return
}
