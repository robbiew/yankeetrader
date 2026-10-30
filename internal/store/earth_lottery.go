package store

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"math/big"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

// LotteryDigit uses OS entropy, independently of world-generation/animation RNG.
func LotteryDigit() (int, error) {
	n, err := rand.Int(rand.Reader, big.NewInt(10))
	if err != nil {
		return 0, err
	}
	return int(n.Int64()), nil
}
func (s Store) PrepareLottery(token, ticket string, now func() time.Time, deadline time.Time) (entry game.LotteryIntent, err error) {
	if s.ship == nil || now == nil {
		return entry, errors.New("lottery requires a bound login and clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	// A new attempt revokes any previous unanswered confirmation for this login.
	s.ship.lotteryActive = nil
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
		entry, e = w.PrepareLottery(s.ship.id, token, ticket, now())
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
		saved := entry
		s.ship.lotteryActive = &saved
		return nil
	})
	return
}
func (s Store) CancelLottery(entry game.LotteryIntent) {
	if s.ship == nil {
		return
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if s.ship.lotteryActive != nil && s.ship.lotteryActive.Nonce == entry.Nonce {
		s.ship.lotteryActive = nil
	}
}
func (s Store) PlayLottery(entry game.LotteryIntent, draw func() (int, error), now func() time.Time, deadline time.Time) (out game.LotteryReceipt, err error) {
	if s.ship == nil || now == nil || entry.Ship.Player != s.ship.id {
		return out, errors.New("lottery requires its bound login and clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if s.ship.lotteryActive == nil || entry != *s.ship.lotteryActive {
		return out, errors.New("lottery confirmation expired, altered or already used")
	}
	// Consume even on rollback. A committed directory-sync warning also retains the
	// persisted sequence, blocking another login's stale quote after a net-zero win.
	s.ship.lotteryActive = nil
	err = s.Update(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		var e error
		at := now()
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		guardedDraw := draw
		if draw != nil {
			guardedDraw = func() (int, error) {
				if !time.Now().Before(deadline) {
					return 0, errors.New("session time expired")
				}
				digit, e := draw()
				if !time.Now().Before(deadline) {
					return 0, errors.New("session time expired")
				}
				return digit, e
			}
		}
		out, e = w.CommitLottery(entry, guardedDraw, at)
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
