package store

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

// A quote is login-local and single-use even after an aborted transaction. Full
// equality with this private copy prevents altered/cross-login confirmation.
func (s Store) PreparePlasma(to int, count int64, now func() time.Time, deadline time.Time) (entry game.PlasmaIntent, err error) {
	if s.ship == nil || now == nil {
		return entry, errors.New("plasma requires a bound login and clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	s.ship.plasmaActive = nil
	if !time.Now().Before(deadline) {
		return entry, errors.New("session time expired")
	}
	w, err := s.View()
	if err != nil {
		return entry, err
	}
	at := now()
	if at.IsZero() || at.Before(w.Created) {
		return entry, errors.New("invalid plasma clock")
	}
	entry, err = w.PreparePlasma(s.ship.id, to, count)
	if err != nil {
		return entry, err
	}
	nonce := make([]byte, 16)
	if _, err = rand.Read(nonce); err != nil {
		return entry, err
	}
	if !time.Now().Before(deadline) {
		return entry, errors.New("session time expired")
	}
	entry.Nonce = hex.EncodeToString(nonce)
	saved := entry
	s.ship.plasmaActive = &saved
	return entry, nil
}
func (s Store) CancelPlasma(entry game.PlasmaIntent) {
	if s.ship == nil {
		return
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if s.ship.plasmaActive != nil && s.ship.plasmaActive.Nonce == entry.Nonce {
		s.ship.plasmaActive = nil
	}
}
func (s Store) LaunchPlasma(entry game.PlasmaIntent, rng func() float64, now func() time.Time, deadline time.Time) (out game.PlasmaResult, err error) {
	if s.ship == nil || now == nil || entry.Player != s.ship.id {
		return out, errors.New("plasma requires its bound login and clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if s.ship.plasmaActive == nil || entry != *s.ship.plasmaActive {
		return out, errors.New("plasma confirmation expired, altered or already used")
	}
	s.ship.plasmaActive = nil
	err = s.Update(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		at := now()
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		var e error
		guarded := rng
		if rng != nil {
			guarded = func() float64 {
				if !time.Now().Before(deadline) {
					return -1
				}
				r := rng()
				if !time.Now().Before(deadline) {
					return -1
				}
				return r
			}
		}
		out, e = w.CommitPlasma(entry, guarded, at)
		// The draw guard uses a rejected value to unwind every rules phase.
		// Report the actual expired login instead of an internal RNG fault.
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return e
	})
	var committed *DurabilityError
	if err != nil && !errors.As(err, &committed) {
		out = game.PlasmaResult{}
	}
	return
}
