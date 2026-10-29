package store

import (
	"encoding/json"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"os"
	"sync"
	"testing"
	"time"
)

func TestNewspaperVersionElevenMigrationDoesNotBackfill(t *testing.T) {
	s := create(t)
	w, _ := s.View()
	w.Players[1].LastLogin = "2026-10-24"
	w.Version = 11
	w.NextNews = 0
	old, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	if err := os.WriteFile(path, old, 0600); err != nil {
		t.Fatal(err)
	}
	current, err := s.View()
	if err != nil || current.Version != game.WorldVersion || current.NextNews != 1 || len(current.News) != 0 || current.Players[1].LastLogin != "2026-10-24" {
		t.Fatal(current, err)
	}
	unchanged, _ := os.ReadFile(path)
	if string(old) != string(unchanged) {
		t.Fatal("migration view rewrote save")
	}
	if err = s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	saved, err := s.View()
	if err != nil || saved.Version != game.WorldVersion || saved.NextNews != 1 || len(saved.News) != 0 {
		t.Fatal(saved, err)
	}
	w.NextNews = 7
	malformed, _ := json.Marshal(w)
	if err = os.WriteFile(path, malformed, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = s.View(); err == nil {
		t.Fatal("legacy header discarded journal fields")
	}
}
func TestNewspaperEventsRollbackWithTheirActions(t *testing.T) {
	s := create(t)
	before, _ := os.ReadFile(s.Dir + "/world.json")
	for _, kind := range []string{"login", "team", "validation"} {
		t.Run(kind, func(t *testing.T) {
			err := s.Update(func(w *game.World) error {
				if kind == "team" {
					if err := w.CreateTeamWithNews(1, "News Team", "ABCD", time.Now()); err != nil {
						return err
					}
				} else {
					if err := w.RecordLogin(1, time.Now()); err != nil {
						return err
					}
				}
				if kind == "validation" {
					w.Players[1].Credits = -1
					return nil
				}
				return errors.New("abort")
			})
			if err == nil {
				t.Fatal("aborted transaction succeeded")
			}
			after, _ := os.ReadFile(s.Dir + "/world.json")
			if string(before) != string(after) {
				t.Fatal("failed action recorded public news")
			}
		})
	}
}
func TestConcurrentNewspaperWritersAndCommittedDurabilityWarning(t *testing.T) {
	s := create(t)
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results <- s.Update(func(w *game.World) error { return w.RecordLogin(1, time.Now()) })
		}()
	}
	wg.Wait()
	close(results)
	for err := range results {
		if err != nil {
			t.Fatal(err)
		}
	}
	w, err := s.View()
	if err != nil || len(w.News) != 8 || w.NextNews != 9 {
		t.Fatal("concurrent news lost", w, err)
	}
	for i, e := range w.News {
		if e.ID != uint64(i+1) {
			t.Fatal("duplicate event IDs", w.News)
		}
	}
	failure := errors.New("directory sync failed")
	s.syncDirectory = func(string) error { return failure }
	err = s.Update(func(w *game.World) error { return w.RecordLogin(1, time.Now()) })
	var committed *DurabilityError
	if !errors.Is(err, failure) || !errors.As(err, &committed) {
		t.Fatal("durability warning lost", err)
	}
	current, err := s.View()
	if err != nil || len(current.News) != 9 || current.NextNews != 10 {
		t.Fatal("committed login lost its event", err)
	}
}
