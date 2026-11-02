package store

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"reflect"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

// PrepareMissiles seals the complete quote to this login and a fresh single-use
// nonce. A committed warning or an aborted attempt cannot replay the dialog.
func (s Store) PrepareMissiles(to int, count int64, v *game.Visibility, now func() time.Time, deadline time.Time) (entry game.MissileIntent, view *game.World, err error) {
	if s.ship == nil || now == nil {
		return entry, nil, errors.New("missiles require a bound login and clock")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	s.ship.missileActive = ""
	if !time.Now().Before(deadline) {
		return entry, nil, errors.New("session time expired")
	}
	own, e := s.SessionVisibility()
	if e != nil {
		return entry, nil, e
	}
	if v != own {
		return entry, nil, errors.New("missile visibility belongs to another login")
	}
	w, e := s.View()
	if e != nil {
		return entry, nil, e
	}
	at := now()
	if at.IsZero() || at.Before(w.Created) {
		return entry, nil, errors.New("invalid missile clock")
	}
	entry, e = w.PrepareMissile(s.ship.id, to, count, v)
	if e != nil {
		return entry, nil, e
	}
	nonce := make([]byte, 16)
	if _, e = rand.Read(nonce); e != nil {
		return entry, nil, e
	}
	entry.Nonce = hex.EncodeToString(nonce)
	data, e := json.Marshal(entry)
	if e != nil {
		return entry, nil, e
	}
	if !time.Now().Before(deadline) {
		return game.MissileIntent{}, nil, errors.New("session time expired")
	}
	s.ship.missileActive = entry.Nonce
	s.ship.missileDigest = sha256.Sum256(data)
	return entry, w, nil
}
func (s Store) CancelMissiles(entry game.MissileIntent) {
	if s.ship == nil {
		return
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	if s.ship.missileActive == entry.Nonce {
		s.ship.missileActive = ""
	}
}

// LaunchMissiles stages the pre-impact spy scan only after checking the quoted
// target snapshot. New grants publish after the volley, never expanding it.
func (s Store) LaunchMissiles(entry game.MissileIntent, v *game.Visibility, rng func() float64, now func() time.Time, deadline time.Time) (out game.MissileResult, err error) {
	if s.ship == nil || entry.Player != s.ship.id || now == nil || rng == nil {
		return out, errors.New("missiles require the bound login, clock and RNG")
	}
	s.ship.encounterMu.Lock()
	defer s.ship.encounterMu.Unlock()
	data, e := json.Marshal(entry)
	if e != nil {
		return out, e
	}
	if entry.Nonce == "" || s.ship.missileActive != entry.Nonce || s.ship.missileDigest != sha256.Sum256(data) {
		return out, errors.New("missile confirmation expired, altered or already used")
	}
	s.ship.missileActive = ""
	var at time.Time
	check := func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		if s.ship.visibility == nil || s.ship.visibility != v {
			return errors.New("missile visibility belongs to another login")
		}
		at = now()
		if at.IsZero() || at.Before(w.Created) {
			return errors.New("invalid missile clock")
		}
		fresh, e := w.PrepareMissile(entry.Player, entry.To, entry.Count, v)
		if e != nil {
			return e
		}
		fresh.Nonce = entry.Nonce
		if !reflect.DeepEqual(fresh, entry) {
			return errors.New("missile target or mine warning changed; confirm again")
		}
		return nil
	}
	err = s.updateStatePhase(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		guarded := func() float64 {
			if !time.Now().Before(deadline) {
				return -1
			}
			return rng()
		}
		var e error
		out, e = w.CommitMissile(entry, v, guarded, at)
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return e
	}, false, false, func(w *game.World, n *game.SpyNetwork) error { return s.advanceSpies(w, n, at, deadline) }, check)
	var committed *DurabilityError
	if err != nil && !errors.As(err, &committed) {
		out = game.MissileResult{}
	}
	return
}

// PlanetReport distinguishes a successful free read from a charged unavailable
// query. Its saved turn, spy state and returned snapshot share one transaction.
func (s Store) PlanetReport(sector int, now func() time.Time, deadline time.Time) (report game.PlanetReport, caller game.Player, err error) {
	if s.ship == nil || now == nil {
		return report, caller, errors.New("planet reports require a bound login and clock")
	}
	var at time.Time
	err = s.updateState(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		at = now()
		var e error
		report, e = w.RemotePlanetReport(s.ship.id, sector, at)
		if e != nil {
			return e
		}
		caller = *w.Players[s.ship.id]
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return nil
	}, false, false, func(w *game.World, n *game.SpyNetwork) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		if report.TurnSpent {
			return s.advanceSpies(w, n, at, deadline)
		}
		return nil
	})
	var committed *DurabilityError
	if err != nil && !errors.As(err, &committed) {
		report = game.PlanetReport{}
		caller = game.Player{}
	}
	return
}
