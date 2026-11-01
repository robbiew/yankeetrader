package store

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestBroadcastRadioConcurrentRetryRollbackAndDurability(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		if _, err := w.Join("second", "Second"); err != nil {
			return err
		}
		_, err := w.Join("third", "Third")
		return err
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	address, _ := w.FindBroadcastRadioRecipients(1)
	draft, err := w.PrepareBroadcastRadio(1, address, "Exactly once", time.Now())
	if err != nil {
		t.Fatal(err)
	}
	bound := s.ForShip(1, w.Players[1].ShipGeneration, 1)
	abort := errors.New("abort")
	if err := bound.Update(func(w *game.World) error {
		if _, err := w.CommitBroadcastRadio(draft, time.Now()); err != nil {
			return err
		}
		return abort
	}); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	w, _ = s.View()
	if len(w.Radio) != 0 || w.NextRadio != 1 || len(w.News) != 0 || w.NextNews != 1 {
		t.Fatal("aborted broadcast published")
	}
	bound.syncDirectory = func(string) error { return errors.New("injected directory sync failure") }
	err = bound.Update(func(w *game.World) error { _, err := w.CommitBroadcastRadio(draft, time.Now()); return err })
	var durability *DurabilityError
	if !errors.As(err, &durability) {
		t.Fatal(err)
	}
	w, _ = s.View()
	if len(w.Radio) != 3 || w.NextRadio != 4 || len(w.News) != 1 || w.NextNews != 2 || w.News[0].Kind != game.NewsBroadcast || w.News[0].BroadcastText != "Exactly once" {
		t.Fatal("committed broadcast was partial")
	}
	bound.syncDirectory = nil
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results <- bound.Update(func(w *game.World) error { _, err := w.CommitBroadcastRadio(draft, time.Now()); return err })
		}()
	}
	wg.Wait()
	close(results)
	for err := range results {
		if err != nil {
			t.Fatal(err)
		}
	}
	w, _ = s.View()
	if len(w.Radio) != 3 || w.NextRadio != 4 || len(w.News) != 1 || w.NextNews != 2 || w.News[0].Kind != game.NewsBroadcast || w.News[0].BroadcastText != "Exactly once" {
		t.Fatal("concurrent retry duplicated copies")
	}
	receiver := s.ForShip(2, w.Players[2].ShipGeneration, 1)
	if err := receiver.AcknowledgeRadio(2); err != nil {
		t.Fatal(err)
	}
	w, _ = s.View()
	if !w.Radio[0].Unread || w.Radio[1].Unread || !w.Radio[2].Unread {
		t.Fatal("broadcast shared unread state")
	}
}

func TestBroadcastNewsMigrationDoesNotRewriteOrBackfill(t *testing.T) {
	s := create(t)
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	address, _ := w.FindBroadcastRadioRecipients(1)
	draft, err := w.PrepareBroadcastRadio(1, address, "historical private copies", time.Now())
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitBroadcastRadio(draft, time.Now()); err != nil {
		t.Fatal(err)
	}
	w.Version = 26
	w.News = nil
	w.NextNews = 1
	old, err := json.Marshal(w)
	if err != nil {
		t.Fatal(err)
	}
	path := s.Dir + "/world.json"
	if err = os.WriteFile(path, old, 0600); err != nil {
		t.Fatal(err)
	}
	loaded, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	if loaded.Version != game.WorldVersion || len(loaded.News) != 0 || len(loaded.Radio) != 1 {
		t.Fatal("bad migration")
	}
	disk, _ := os.ReadFile(path)
	if !bytes.Equal(old, disk) {
		t.Fatal("read rewrote save")
	}
	if err = s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	disk, _ = os.ReadFile(path)
	var saved game.World
	if err = json.Unmarshal(disk, &saved); err != nil || saved.Version != game.WorldVersion || len(saved.News) != 0 || len(saved.Radio) != 1 {
		t.Fatal("bad persisted migration", err)
	}
}

func TestIndependentConcurrentBroadcastsKeepEveryPublicEntry(t *testing.T) {
	s := create(t)
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	const sends = 8
	drafts := make([]game.BroadcastRadioDraft, sends)
	for i := range drafts {
		address, e := w.FindBroadcastRadioRecipients(1)
		if e != nil {
			t.Fatal(e)
		}
		drafts[i], e = w.PrepareBroadcastRadio(1, address, fmt.Sprintf("Public %d", i), time.Now())
		if e != nil {
			t.Fatal(e)
		}
	}
	bound := s.ForShip(1, w.Players[1].ShipGeneration, w.Season)
	results := make(chan error, sends)
	for _, draft := range drafts {
		go func(d game.BroadcastRadioDraft) {
			results <- bound.Update(func(w *game.World) error { _, err := w.CommitBroadcastRadio(d, time.Now()); return err })
		}(draft)
	}
	for range sends {
		if err := <-results; err != nil {
			t.Fatal(err)
		}
	}
	w, err = s.View()
	if err != nil {
		t.Fatal(err)
	}
	if len(w.Radio) != sends || len(w.News) != sends || w.NextNews != sends+1 {
		t.Fatal("lost concurrent public or private sends")
	}
	for _, e := range w.News {
		count := 0
		for _, m := range w.Radio {
			if m.Text == e.BroadcastText && m.FromAlias == e.Alias {
				count++
			}
		}
		if count != 1 {
			t.Fatal("public entry lost its matching saved copy", e)
		}
	}
}
