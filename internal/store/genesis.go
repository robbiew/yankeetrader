package store

import (
	"crypto/rand"
	"encoding/binary"
	"encoding/hex"
	"errors"
	"reflect"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Store) PrepareGenesis(now func() time.Time, deadline time.Time) (entry game.GenesisIntent, err error) {
	if s.ship == nil || now == nil {
		return entry, errors.New("Genesis requires a bound login and clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	s.ship.genesisActive = nil // A fresh attempt revokes any unanswered quote.
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
		entry, e = w.PrepareGenesis(s.ship.id, now())
		if e != nil {
			return e
		}
		var nonce [16]byte
		if _, e = rand.Read(nonce[:]); e != nil {
			return e
		}
		entry.Nonce = hex.EncodeToString(nonce[:])
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		saved := entry
		saved.Ports = append([]int(nil), entry.Ports...)
		s.ship.genesisActive = &saved
		return nil
	})
	return
}
func (s Store) CancelGenesis(entry game.GenesisIntent) {
	if s.ship == nil {
		return
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if s.ship.genesisActive != nil && s.ship.genesisActive.Nonce == entry.Nonce {
		s.ship.genesisActive = nil
	}
}
func (s Store) ResetSeason(entry game.GenesisIntent, now func() time.Time, deadline time.Time) (out game.GenesisReceipt, err error) {
	if s.ship == nil || now == nil || entry.Player != s.ship.id {
		return out, errors.New("Genesis requires its bound login and clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	active := s.ship.genesisActive
	s.ship.genesisActive = nil // Every submission consumes this login's confirmation.
	if active == nil || !reflect.DeepEqual(entry, *active) {
		return out, errors.New("Genesis confirmation expired, altered or already used")
	}
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
		var entropy [8]byte
		if _, e = rand.Read(entropy[:]); e != nil {
			return e
		}
		candidate, receipt, e := w.GenesisCandidate(entry, now(), int64(binary.LittleEndian.Uint64(entropy[:])))
		if e != nil {
			return e
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		// This preserves world.lock's inode and commits archive+epoch+world together.
		e = s.save(candidate)
		var committed *DurabilityError
		if e == nil || errors.As(e, &committed) {
			out = receipt
		}
		return e
	})
	return
}
