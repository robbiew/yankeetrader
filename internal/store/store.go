package store

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/game"
	"io"
	"os"
	"path/filepath"
	"time"
)

type Store struct {
	Dir  string
	ship *shipSession
}
type shipSession struct {
	id         int
	generation uint64
}

// ForShip binds only this copy of the store to a login's ship generation.
// Administrative maintenance and fresh login use the unbound store.
func (s Store) ForShip(id int, generation uint64) Store {
	s.ship = &shipSession{id, generation}
	return s
}
func (s Store) checkShip(w *game.World) error {
	if s.ship != nil {
		return w.CheckShip(s.ship.id, s.ship.generation)
	}
	return nil
}

func (s Store) locked(fn func() error) error {
	if err := os.MkdirAll(s.Dir, 0700); err != nil {
		return err
	}
	f, err := os.OpenFile(filepath.Join(s.Dir, "world.lock"), os.O_CREATE|os.O_RDWR, 0600)
	if err != nil {
		return err
	}
	defer f.Close()
	if err = lock(f); err != nil {
		return err
	}
	defer unlock(f)
	return fn()
}
func (s Store) load() (*game.World, error) {
	f, e := os.Open(filepath.Join(s.Dir, "world.json"))
	if e != nil {
		return nil, e
	}
	defer f.Close()
	var w game.World
	d := json.NewDecoder(io.LimitReader(f, 32<<20))
	d.DisallowUnknownFields()
	if e = d.Decode(&w); e != nil {
		return nil, fmt.Errorf("read world: %w", e)
	}
	var extra any
	if e = d.Decode(&extra); e != io.EOF {
		return nil, errors.New("trailing or oversized world data")
	}
	if e = w.Upgrade(); e != nil {
		return nil, e
	}
	if e = w.Validate(); e != nil {
		return nil, fmt.Errorf("invalid saved world: %w", e)
	}
	return &w, nil
}
func (s Store) save(w *game.World) error {
	if e := w.Validate(); e != nil {
		return e
	}
	b, e := json.MarshalIndent(w, "", "  ")
	if e != nil {
		return e
	}
	f, e := os.CreateTemp(s.Dir, ".world-*")
	if e != nil {
		return e
	}
	name := f.Name()
	defer os.Remove(name)
	defer f.Close()
	if _, e = f.Write(append(b, '\n')); e != nil {
		return e
	}
	if e = f.Sync(); e != nil {
		return e
	}
	if e = f.Close(); e != nil {
		return e
	}
	if e = os.Rename(name, filepath.Join(s.Dir, "world.json")); e != nil {
		return e
	}
	return syncDir(s.Dir)
}
func (s Store) Create(w *game.World) error {
	return s.locked(func() error {
		_, e := os.Stat(filepath.Join(s.Dir, "world.json"))
		if e == nil {
			return errors.New("world already exists; initialization will not overwrite it")
		}
		if !os.IsNotExist(e) {
			return e
		}
		return s.save(w)
	})
}
func (s Store) Update(fn func(*game.World) error) error { return s.update(fn, false, false) }
func (s Store) update(fn func(*game.World) error, allowMines, allowDefense bool) error {
	return s.locked(func() error {
		w, e := s.load()
		if e != nil {
			return e
		}
		if e = s.checkShip(w); e != nil {
			return e
		}
		if s.ship != nil && !allowMines && w.HasMineEncounter(s.ship.id) {
			return game.ErrMineEncounter
		}
		if s.ship != nil && !allowDefense && w.HostileDefense(s.ship.id, w.Players[s.ship.id].Sector) {
			return game.ErrDefenseEncounter
		}
		if e = fn(w); e != nil {
			return e
		}
		return s.save(w)
	})
}
func (s Store) View() (*game.World, error) {
	var w *game.World
	err := s.locked(func() error { var e error; w, e = s.load(); return e })
	if err == nil {
		err = s.checkShip(w)
	}
	if err != nil {
		return nil, err
	}
	return w, err
}

// AcknowledgeRadio only changes this bound recipient's read flag. This metadata
// update remains available during an encounter without opening a mutation bypass.
func (s Store) AcknowledgeRadio(messageID uint64) error {
	if s.ship == nil {
		return errors.New("radio acknowledgement requires a bound ship session")
	}
	return s.update(func(w *game.World) error { return w.AcknowledgeRadio(s.ship.id, messageID) }, true, true)
}

// RefreshScoresOnLogout publishes only score metadata from the current world.
// It cannot mutate encounter resources, and always checks the bound generation.
func (s Store) RefreshScoresOnLogout(deadline time.Time) error {
	if s.ship == nil {
		return errors.New("score publication requires a bound ship session")
	}
	return s.update(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		if _, err := w.RefreshRankings(s.ship.id); err != nil {
			return err
		}
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return nil
	}, true, true)
}

// ResolveMines is the bound-session entry point for resolving a minefield.
// Death is saved successfully before the caller observes its invalid generation.
func (s Store) ResolveMines(now time.Time, rng func() float64) (game.MineOutcome, error) {
	if s.ship == nil {
		return game.MineOutcome{}, errors.New("mine resolution requires a bound ship session")
	}
	var result game.MineOutcome
	err := s.update(func(w *game.World) error {
		var err error
		result, err = w.ResolveMinefield(s.ship.id, rng, now)
		return err
	}, true, true)
	return result, err
}

// DefenseEncounter is the bound entry point permitted to fight or flee a current
// hostile group. Ordinary account mutations remain blocked there.
func (s Store) DefenseEncounter(entry game.DefenseIntent, rng func() float64, now, deadline time.Time) (game.DefenseOutcome, error) {
	if s.ship == nil || entry.Player != s.ship.id {
		return game.DefenseOutcome{}, errors.New("defense encounter requires the bound player")
	}
	var out game.DefenseOutcome
	err := s.update(func(w *game.World) error {
		if !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		var err error
		out, err = w.CommitDefense(entry, rng, now)
		if err == nil && !time.Now().Before(deadline) {
			return errors.New("session time expired")
		}
		return err
	}, false, true)
	return out, err
}
