package store

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"sync"
	"testing"
	"time"
)

func TestRadioDocumentStoreAtomicPublicationAndConcurrentRetry(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error { _, err := w.Join("recipient", "Recipient"); return err }); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	a, _ := w.FindBroadcastRadioRecipients(1)
	d, err := w.PrepareRadioDocument(1, game.RadioDocumentTarget{Broadcast: &a}, []string{"FIRST", "SECOND"}, time.Now())
	if err != nil {
		t.Fatal(err)
	}
	bound := s.ForShip(1, w.Players[1].ShipGeneration, 1)
	abort := errors.New("abort")
	if err := bound.Update(func(w *game.World) error {
		if _, err := w.CommitRadioDocument(d, time.Now()); err != nil {
			return err
		}
		return abort
	}); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	w, _ = s.View()
	if len(w.Radio) != 0 || len(w.News) != 0 {
		t.Fatal("aborted document persisted")
	}
	bound.syncDirectory = func(string) error { return errors.New("sync failure") }
	err = bound.Update(func(w *game.World) error { _, err := w.CommitRadioDocument(d, time.Now()); return err })
	var durability *DurabilityError
	if !errors.As(err, &durability) {
		t.Fatal(err)
	}
	bound.syncDirectory = nil
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results <- bound.Update(func(w *game.World) error { _, err := w.CommitRadioDocument(d, time.Now()); return err })
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
	if len(w.Radio) != 4 || len(w.News) != 2 {
		t.Fatal("partial or duplicated document", len(w.Radio), len(w.News))
	}
}
