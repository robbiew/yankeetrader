package store

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/game"
	"io"
	"os"
	"path/filepath"
)

type Store struct{ Dir string }

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
func (s Store) Update(fn func(*game.World) error) error {
	return s.locked(func() error {
		w, e := s.load()
		if e != nil {
			return e
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
	return w, err
}
