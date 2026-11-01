package store

import (
	"errors"
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
	if len(w.Radio) != 0 || w.NextRadio != 1 {
		t.Fatal("aborted broadcast published")
	}
	bound.syncDirectory = func(string) error { return errors.New("injected directory sync failure") }
	err = bound.Update(func(w *game.World) error { _, err := w.CommitBroadcastRadio(draft, time.Now()); return err })
	var durability *DurabilityError
	if !errors.As(err, &durability) {
		t.Fatal(err)
	}
	w, _ = s.View()
	if len(w.Radio) != 3 || w.NextRadio != 4 {
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
	if len(w.Radio) != 3 || w.NextRadio != 4 {
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
