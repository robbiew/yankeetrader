package store

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func planetDigest(e game.PlanetIntent) [32]byte {
	b, _ := json.Marshal(e)
	return sha256.Sum256(b)
}

func (s Store) PreparePlanetAction(kind, token string, destination int, quantity int64, now func() time.Time, deadline time.Time) (entry game.PlanetIntent, err error) {
	if s.ship == nil || now == nil {
		return entry, errors.New("planet action requires a bound login and clock")
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
		entry, e = w.PreparePlanetAction(s.ship.id, kind, token, destination, quantity, now())
		if e != nil {
			return e
		}
		nonce := make([]byte, 16)
		if _, e = rand.Read(nonce); e != nil {
			return e
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		entry.Nonce = hex.EncodeToString(nonce)
		s.ship.planetActive = entry.Nonce
		s.ship.planetDigest = planetDigest(entry)
		return nil
	})
	return
}
func (s Store) CancelPlanetAction(entry game.PlanetIntent) {
	if s.ship == nil {
		return
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if s.ship.planetActive == entry.Nonce {
		s.ship.planetActive = ""
	}
}
func (s Store) CommitPlanetAction(entry game.PlanetIntent, rng func() float64, now func() time.Time, deadline time.Time) (out game.PlanetReceipt, err error) {
	if s.ship == nil || now == nil || entry.Ship.Player != s.ship.id {
		return out, errors.New("planet action requires its bound login and clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if entry.Nonce == "" || entry.Nonce != s.ship.planetActive {
		return out, errors.New("planet confirmation expired or already used")
	}
	s.ship.planetActive = ""
	if planetDigest(entry) != s.ship.planetDigest {
		return out, errors.New("planet confirmation was modified; confirm again")
	}
	err = s.Update(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		var e error
		out, e = w.CommitPlanetAction(entry, rng, now())
		if e != nil {
			return e
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return nil
	})
	return
}
