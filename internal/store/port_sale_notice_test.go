package store

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/robbiew/yankeetrader/internal/game"
	"os"
	"sync"
	"testing"
	"time"
)

func saleStore(t *testing.T) (Store, Store, game.PortPurchaseQuote) {
	t.Helper()
	s := create(t)
	var quote game.PortPurchaseQuote
	if err := s.Update(func(w *game.World) error {
		seller, e := w.Join("seller", "Seller")
		if e != nil {
			return e
		}
		seller.Credits = 2000
		w.Players[1].Sector = 2
		w.Players[1].Credits = 100000
		w.Ports[2].Owner = seller.ID
		w.Ports[2].Treasury = 777
		quote, e = w.QuotePortPurchase(1, time.Now())
		return e
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	return s, s.ForShip(1, w.Players[1].ShipGeneration, w.Season), quote
}
func TestPortSaleNoticeRollbackWarningAndConcurrentRetry(t *testing.T) {
	s, b, q := saleStore(t)
	before := travelBytes(t, s)
	abort := errors.New("abort")
	if e := b.Update(func(w *game.World) error {
		if err := w.PurchasePort(1, q, time.Now()); err != nil {
			return err
		}
		return abort
	}); !errors.Is(e, abort) {
		t.Fatal(e)
	}
	if !bytes.Equal(before, travelBytes(t, s)) {
		t.Fatal("aborted sale published")
	}
	b.syncDirectory = func(string) error { return errors.New("sync warning") }
	e := b.PurchasePort(1, q, time.Now, time.Now().Add(time.Minute))
	var warning *DurabilityError
	if !errors.As(e, &warning) {
		t.Fatal(e)
	}
	b.syncDirectory = nil
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if b.PurchasePort(1, q, time.Now, time.Now().Add(time.Minute)) == nil {
				t.Error("retry succeeded")
			}
		}()
	}
	wg.Wait()
	w, _ := s.View()
	if len(w.Radio) != 1 || w.Radio[0].To != 2 || w.Players[1].Credits != 99969 || w.Players[2].Credits != 2808 || w.Ports[2].Owner != 1 || w.Ports[2].Treasury != 0 || len(w.News) != 0 {
		t.Fatal("partial/duplicate sale", w.Radio)
	}
}
func TestPortSaleNoticeExpiryAndStaleIdentity(t *testing.T) {
	for _, mode := range []string{"expired", "late", "lock-wait", "generation", "season", "wrong-login", "moved", "name", "full"} {
		t.Run(mode, func(t *testing.T) {
			s, b, q := saleStore(t)
			deadline := time.Now().Add(time.Minute)
			now := time.Now
			id := 1
			switch mode {
			case "expired":
				deadline = time.Now()
			case "late":
				deadline = time.Now().Add(50 * time.Millisecond)
				now = func() time.Time { time.Sleep(time.Until(deadline)); return time.Now() }
			case "generation":
				b = b.ForShip(1, 9999, 1)
			case "season":
				b = b.ForShip(1, 0, 9999)
			case "wrong-login":
				id = 2
			case "moved":
				_ = s.Update(func(w *game.World) error { w.Players[1].Sector = 3; return nil })
			case "name":
				_ = s.Update(func(w *game.World) error { w.Ports[2].Name = "New quote required"; return nil })
			case "full":
				if err := s.Update(func(w *game.World) error {
					for i := 1; i <= game.MaxRadioMessages; i++ {
						w.Radio = append(w.Radio, game.RadioMessage{ID: uint64(i), RequestID: fmt.Sprintf("%032x", i), From: 1, To: 1, FromAlias: "Q", ToAlias: "Q", Text: "Capacity fixture", Sent: time.Now()})
					}
					w.NextRadio = game.MaxRadioMessages + 1
					return nil
				}); err != nil {
					t.Fatal(err)
				}
			}
			before := travelBytes(t, s)
			var err error
			if mode == "lock-wait" {
				held, release, done := make(chan struct{}), make(chan struct{}), make(chan struct{})
				go func() { _ = s.locked(func() error { close(held); <-release; return nil }); close(done) }()
				<-held
				deadline = time.Now().Add(30 * time.Millisecond)
				result := make(chan error, 1)
				go func() { result <- b.PurchasePort(id, q, now, deadline) }()
				time.Sleep(60 * time.Millisecond)
				close(release)
				<-done
				err = <-result
			} else {
				err = b.PurchasePort(id, q, now, deadline)
			}
			if err == nil || !bytes.Equal(before, travelBytes(t, s)) {
				t.Fatal("rejected purchase saved", err)
			}
		})
	}
}
func TestPortSaleNoticeMigrationDoesNotBackfill(t *testing.T) {
	s, b, q := saleStore(t)
	if e := b.PurchasePort(1, q, time.Now, time.Now().Add(time.Minute)); e != nil {
		t.Fatal(e)
	}
	w, _ := s.View()
	w.Version = 28
	w.Radio = nil
	raw, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	if e := os.WriteFile(path, raw, 0600); e != nil {
		t.Fatal(e)
	}
	migrated, e := s.View()
	disk, _ := os.ReadFile(path)
	if e != nil || !bytes.Equal(raw, disk) || migrated.Version != game.WorldVersion || len(migrated.Radio) != 0 || migrated.Players[2].Credits != 2808 {
		t.Fatal("migration rewrote/backfilled", e)
	}
	if e = s.Update(func(*game.World) error { return nil }); e != nil {
		t.Fatal(e)
	}
	migrated, _ = s.View()
	if migrated.Version != game.WorldVersion || len(migrated.Radio) != 0 {
		t.Fatal("migration invented notice")
	}
}
