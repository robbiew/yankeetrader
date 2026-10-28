package store

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"os"
	"sync"
	"testing"
	"time"
)

func spyStore(t *testing.T) (Store, Store, string) {
	t.Helper()
	s := create(t)
	token := ""
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Credits = 2000000
		w.Sectors[2].Warps = nil
		w.Sectors[2].Minefield = []game.MineLayer{{Count: 7}}
		if err := w.Dock(1, time.Now()); err != nil {
			return err
		}
		token = p.DockToken
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	return s, s.ForShip(1, w.Players[1].ShipGeneration), token
}
func TestSpyTransactionsRollbackAndReconnectIsolation(t *testing.T) {
	s, bound, token := spyStore(t)
	deadline := time.Now().Add(time.Minute)
	if err := bound.HireSpies(token, []int{2}, time.Now(), deadline); err != nil {
		t.Fatal(err)
	}
	original, _ := os.ReadFile(s.Dir + "/world.json")
	for _, mode := range []string{"abort", "validation", "deadline"} {
		t.Run(mode, func(t *testing.T) {
			until := deadline
			if mode == "deadline" {
				until = time.Now().Add(-time.Second)
			}
			err := bound.UpdateWithSpies(func(w *game.World) error {
				if mode == "abort" {
					return errors.New("abort")
				}
				w.Players[1].Credits = -1
				return nil
			}, time.Now(), until)
			if err == nil {
				t.Fatal("failed transaction accepted")
			}
			positions, reports, _ := bound.SpySnapshot(false)
			after, _ := os.ReadFile(s.Dir + "/world.json")
			if len(reports) != 0 || positions[0] != 2 || string(original) != string(after) {
				t.Fatal("failed save leaked reports or world changes")
			}
		})
	}
	if err := bound.UpdateWithSpies(func(w *game.World) error { return w.SetSectorFighters(1, 0) }, time.Now(), deadline); err != nil {
		t.Fatal(err)
	}
	_, reports, err := bound.SpySnapshot(true)
	if err != nil || len(reports) != 1 || reports[0].Mines != 7 {
		t.Fatal(reports, err)
	}
	fresh := s.ForShip(1, 0)
	positions, other, err := fresh.SpySnapshot(false)
	if err != nil || len(positions) != 0 || len(other) != 0 {
		t.Fatal("reconnect inherited spies")
	}
	if err = fresh.AcknowledgeSpy(reports[0].ID); err == nil {
		t.Fatal("other login acknowledged report")
	}
	if err = bound.AcknowledgeSpy(reports[0].ID); err != nil {
		t.Fatal(err)
	}
	_, reports, err = bound.SpySnapshot(true)
	if err != nil || len(reports) != 0 {
		t.Fatal("acknowledgement lost")
	}
	if err = s.Update(func(w *game.World) error { w.Players[1].ShipGeneration++; return nil }); err != nil {
		t.Fatal(err)
	}
	if _, _, err = bound.SpySnapshot(false); err == nil {
		t.Fatal("stale connection read report")
	}
	if err = bound.HireSpies(token, []int{3}, time.Now(), deadline); err == nil {
		t.Fatal("stale connection hired")
	}
}
func TestConcurrentSpyHiresRespectSessionCapAndFunds(t *testing.T) {
	s, bound, token := spyStore(t)
	var wg sync.WaitGroup
	results := make(chan error, 10)
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results <- bound.HireSpies(token, []int{2}, time.Now(), time.Now().Add(time.Minute))
		}()
	}
	wg.Wait()
	close(results)
	success := 0
	for err := range results {
		if err == nil {
			success++
		}
	}
	positions, _, err := bound.SpySnapshot(false)
	w, _ := s.View()
	if err != nil || success != 3 || len(positions) != 3 || w.Players[1].Credits != 1001000 || w.Players[1].Turns != 499 {
		t.Fatalf("cap/funds %v %d %+v", err, success, w.Players[1])
	}
}

func TestSpyAdvanceDoesNotRollBackFatalAction(t *testing.T) {
	s, bound, token := spyStore(t)
	deadline := time.Now().Add(time.Minute)
	if err := bound.HireSpies(token, []int{2}, time.Now(), deadline); err != nil {
		t.Fatal(err)
	}
	if err := bound.UpdateWithSpies(func(w *game.World) error {
		p := w.Players[1]
		return w.RecordDeath(game.DeathContext{Victim: 1, Generation: p.ShipGeneration, Sector: p.Sector, Cause: "hazard"}, time.Now())
	}, time.Now(), deadline); err != nil {
		t.Fatal(err)
	}
	w, err := s.View()
	if err != nil || w.Players[1].Death == nil {
		t.Fatal("fatal action rolled back", err)
	}
	if _, _, err = bound.SpySnapshot(false); err == nil {
		t.Fatal("dead login read spies")
	}
}

func TestSpyStateNotPublishedOnDiskSaveFailure(t *testing.T) {
	s, bound, token := spyStore(t)
	deadline := time.Now().Add(time.Minute)
	if err := bound.HireSpies(token, []int{2}, time.Now(), deadline); err != nil {
		t.Fatal(err)
	}
	path := s.Dir + "/world.json"
	backup := s.Dir + "/saved-world.json"
	err := bound.UpdateWithSpies(func(w *game.World) error {
		// Loading has completed. Obstruct only the atomic rename, in this test dir.
		if err := os.Rename(path, backup); err != nil {
			return err
		}
		if err := os.Mkdir(path, 0700); err != nil {
			return err
		}
		w.Players[1].Credits--
		return nil
	}, time.Now(), deadline)
	if err == nil {
		t.Fatal("obstructed save succeeded")
	}
	if err = os.Remove(path); err != nil {
		t.Fatal(err)
	}
	if err = os.Rename(backup, path); err != nil {
		t.Fatal(err)
	}
	positions, reports, err := bound.SpySnapshot(false)
	w, _ := s.View()
	if err != nil || len(positions) != 1 || positions[0] != 2 || len(reports) != 0 || w.Players[1].Credits != 1667000 {
		t.Fatal("failed disk save published spy state", positions, reports, err)
	}
}
