package store

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Store) RechargeCloak(token string, points int64, now func() time.Time, deadline time.Time) (out game.CloakReceipt, err error) {
	if s.ship == nil || now == nil {
		return out, errors.New("cloak purchase requires a bound ship and clock")
	}
	err = s.Update(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		p := w.Players[s.ship.id]
		out.Before = p.Cloak
		if e := w.Equip(p.ID, token, "cloak", points, now()); e != nil {
			return e
		}
		out.Points = points
		out.Spent = points * game.CloakPointPrice
		out.Balance = p.Credits
		out.After = p.Cloak
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return nil
	})
	return
}

func (s Store) PrepareAntiCloak(token string, v *game.Visibility, now func() time.Time, deadline time.Time) (entry game.AntiCloakIntent, err error) {
	if s.ship == nil || v == nil || now == nil {
		return entry, errors.New("anti-cloak requires a bound login and clock")
	}
	own, e := s.SessionVisibility()
	if e != nil {
		return entry, e
	}
	if own != v {
		return entry, errors.New("anti-cloak visibility belongs to another login")
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
		staged, finish := v.StageAntiCloak()
		defer finish(false)
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		entry, e = w.PrepareAntiCloak(s.ship.id, token, staged, now())
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
		s.ship.antiActive = entry.Nonce
		s.ship.antiVisibility = v
		return nil
	})
	return
}
func (s Store) CancelAntiCloak(entry game.AntiCloakIntent) {
	if s.ship == nil {
		return
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if s.ship.antiActive == entry.Nonce {
		s.ship.antiActive = ""
		s.ship.antiVisibility = nil
	}
}
func (s Store) ActivateAntiCloak(entry game.AntiCloakIntent, v *game.Visibility, now func() time.Time, deadline time.Time) (out game.AntiCloakReceipt, err error) {
	if s.ship == nil || v == nil || now == nil || entry.Ship.Player != s.ship.id {
		return out, errors.New("anti-cloak requires its bound login and clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if entry.Nonce == "" || entry.Nonce != s.ship.antiActive || v != s.ship.antiVisibility {
		return out, errors.New("anti-cloak confirmation expired or already used")
	}
	s.ship.antiActive = ""
	s.ship.antiVisibility = nil
	var finish func(bool)
	defer func() {
		if finish != nil {
			var committed *DurabilityError
			finish(err == nil || errors.As(err, &committed))
		}
	}()
	err = s.Update(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		staged, done := v.StageAntiCloak()
		finish = done
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		var e error
		out, e = w.CommitAntiCloak(entry, staged, now())
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
