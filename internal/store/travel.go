package store

import (
	crand "crypto/rand"
	"encoding/hex"
	"errors"
	"math/rand"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

// PrepareWarp binds one warning to this live login after checking the world lock.
func (s Store) PrepareWarp(deadline time.Time) (entry game.WarpIntent, err error) {
	if s.ship == nil {
		return entry, errors.New("emergency warp requires a bound ship session")
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
		entry, e = w.PrepareWarp(s.ship.id)
		if e != nil {
			return e
		}
		token := make([]byte, 16)
		if _, e = crand.Read(token); e != nil {
			return e
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		s.ship.warpActive = hex.EncodeToString(token)
		entry.Nonce = s.ship.warpActive
		return nil
	})
	return
}

// CancelWarp discards a refused/disconnected warning without changing the save.
func (s Store) CancelWarp(entry game.WarpIntent) {
	if s.ship == nil {
		return
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if s.ship.warpActive == entry.Nonce {
		s.ship.warpActive = ""
	}
}

// Warp consumes the confirmation even on rollback. A committed durability warning
// retains the saved sequence; neither nonce reuse nor another login can replay it.
func (s Store) Warp(entry game.WarpIntent, rng func() float64, now func() time.Time, deadline time.Time) (out game.WarpOutcome, err error) {
	if s.ship == nil || entry.Ship.Player != s.ship.id || now == nil {
		return out, errors.New("emergency warp requires its bound player and clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if entry.Nonce == "" || entry.Nonce != s.ship.warpActive {
		return out, errors.New("emergency warp confirmation expired or already used; confirm again")
	}
	s.ship.warpActive = ""
	err = s.updateState(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		var e error
		out, e = w.CommitWarp(entry, rng, now())
		if e != nil {
			return e
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return nil
	}, false, true, func(w *game.World, n *game.SpyNetwork) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		if w.CheckSession(s.ship.id, s.ship.generation, s.ship.season) != nil {
			return nil
		}
		if e := n.Advance(w, now(), rand.Float64); e != nil {
			return e
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return nil
	})
	return
}
