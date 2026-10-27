package store

import (
	"github.com/robbiew/yankeetrader/internal/game"
	"sync"
	"testing"
	"time"
)

func TestConcurrentBuyoutAndCollection(t *testing.T) {
	s := create(t)
	now := time.Now()
	var quotes [2]game.PortPurchaseQuote
	if err := s.Update(func(w *game.World) error {
		seller, err := w.Join("seller", "Seller")
		if err != nil {
			return err
		}
		other, err := w.Join("other", "Other")
		if err != nil {
			return err
		}
		seller.Credits = 2000
		w.Ports[2].Owner, w.Ports[2].Treasury = seller.ID, 777
		for i, id := range []int{1, other.ID} {
			w.Players[id].Sector, w.Players[id].Credits = 2, 100000
			quotes[i], err = w.QuotePortPurchase(id, now)
			if err != nil {
				return err
			}
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	results := make(chan error, 2)
	for i, id := range []int{1, 3} {
		wg.Add(1)
		go func(i, id int) {
			defer wg.Done()
			results <- s.Update(func(w *game.World) error { return w.PurchasePort(id, quotes[i], now) })
		}(i, id)
	}
	wg.Wait()
	close(results)
	success := 0
	for err := range results {
		if err == nil {
			success++
		}
	}
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	if success != 1 || w.Players[2].Credits != 2808 || w.Ports[2].Treasury != 0 {
		t.Fatalf("duplicate/lost buyout: successes=%d world=%+v", success, w)
	}
	owner := w.Ports[2].Owner
	if err = s.Update(func(w *game.World) error { w.Ports[2].Treasury = 777; return nil }); err != nil {
		t.Fatal(err)
	}
	amounts := make(chan int64, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			err := s.Update(func(w *game.World) error {
				n, e := w.CollectPortTreasury(owner)
				if e == nil {
					amounts <- n
				}
				return e
			})
			if err != nil {
				t.Error(err)
			}
		}()
	}
	wg.Wait()
	close(amounts)
	var total int64
	for n := range amounts {
		total += n
	}
	w, err = s.View()
	if err != nil {
		t.Fatal(err)
	}
	if total != 777 || w.Players[owner].Credits != 100746 || w.Ports[2].Treasury != 0 {
		t.Fatal("collection duplicated funds", total, w.Players[owner])
	}
}
