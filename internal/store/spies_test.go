package store

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"os"
	"sync"
	"sync/atomic"
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
	return s, s.ForShip(1, w.Players[1].ShipGeneration, 1), token
}
func TestSpyTransactionsRollbackAndReconnectIsolation(t *testing.T) {
	s, bound, token := spyStore(t)
	deadline := time.Now().Add(time.Minute)
	if err := bound.HireSpies(token, []int{2}, time.Now, deadline); err != nil {
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
	fresh := s.ForShip(1, 0, 1)
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
	if err = bound.HireSpies(token, []int{3}, time.Now, deadline); err == nil {
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
			results <- bound.HireSpies(token, []int{2}, time.Now, time.Now().Add(time.Minute))
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
	if err := bound.HireSpies(token, []int{2}, time.Now, deadline); err != nil {
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
	if err := bound.HireSpies(token, []int{2}, time.Now, deadline); err != nil {
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
	var durability *DurabilityError
	if err == nil || errors.As(err, &durability) {
		t.Fatal("obstructed replacement was reported as committed", err)
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

func TestSpyHireRechecksDockExpiryAfterLocks(t *testing.T) {
	for _, kind := range []string{"spy-mutex", "world-lock"} {
		t.Run(kind, func(t *testing.T) {
			s, bound, token := spyStore(t)
			beforeExpiry := time.Now()
			expiry := beforeExpiry.Add(time.Minute)
			if err := s.Update(func(w *game.World) error { w.Players[1].DockUntil = expiry; return nil }); err != nil {
				t.Fatal(err)
			}
			var current atomic.Int64
			current.Store(beforeExpiry.UnixNano())
			clock := func() time.Time { return time.Unix(0, current.Load()) }
			var release func()
			if kind == "spy-mutex" {
				bound.ship.spyMu.Lock()
				release = bound.ship.spyMu.Unlock
			} else {
				held := make(chan struct{})
				unblock := make(chan struct{})
				done := make(chan error, 1)
				go func() { done <- s.locked(func() error { close(held); <-unblock; return nil }) }()
				<-held
				release = func() {
					close(unblock)
					if err := <-done; err != nil {
						t.Error(err)
					}
				}
			}
			started := make(chan struct{})
			result := make(chan error, 1)
			go func() { close(started); result <- bound.HireSpies(token, []int{2}, clock, time.Now().Add(time.Hour)) }()
			<-started
			// Simulate docking expiration while the request is queued, without waiting
			// for the actual multi-minute docking lifetime or changing the login deadline.
			time.Sleep(20 * time.Millisecond)
			current.Store(expiry.UnixNano())
			release()
			if err := <-result; err == nil {
				t.Fatal("hire accepted docking token expired while waiting for", kind)
			}
			locations, _, err := bound.SpySnapshot(false)
			w, _ := s.View()
			if err != nil || len(locations) != 0 || w.Players[1].Credits != 2000000 {
				t.Fatal("expired queued hire changed assets", locations, err)
			}
		})
	}
}

func TestSpyHirePublishesAfterReplacementSyncFailure(t *testing.T) {
	s, bound, token := spyStore(t)
	failure := errors.New("injected directory sync failure")
	bound.syncDirectory = func(path string) error {
		// This hook runs only after the real atomic replacement is visible.
		world, err := s.load()
		if err != nil {
			t.Fatal(err)
		}
		if path != s.Dir || world.Players[1].Credits != 1667000 {
			t.Fatal("sync ran before replacement", world.Players[1])
		}
		return failure
	}
	err := bound.HireSpies(token, []int{2}, time.Now, time.Now().Add(time.Minute))
	var durability *DurabilityError
	if !errors.Is(err, failure) || !errors.As(err, &durability) {
		t.Fatal("committed durability failure was not identified", err)
	}
	w, _ := s.View()
	locations, _, viewErr := bound.SpySnapshot(false)
	if viewErr != nil || w.Players[1].Credits != 1667000 || len(locations) != 1 || locations[0] != 2 {
		t.Fatal("visible credit deduction lost its granted spy", locations, viewErr)
	}
}

func TestSpyAdvancePublishesAfterReplacementSyncFailure(t *testing.T) {
	s, bound, token := spyStore(t)
	deadline := time.Now().Add(time.Minute)
	if err := s.Update(func(w *game.World) error { w.Sectors[1].Warps = []int{3}; w.Sectors[2].Warps = []int{4}; return nil }); err != nil {
		t.Fatal(err)
	}
	if err := bound.HireSpies(token, []int{2}, time.Now, deadline); err != nil {
		t.Fatal(err)
	}
	failure := errors.New("injected directory sync failure")
	bound.syncDirectory = func(string) error { return failure }
	err := bound.UpdateWithSpies(func(w *game.World) error { return w.Move(1, 3) }, time.Now(), deadline)
	var durability *DurabilityError
	if !errors.Is(err, failure) || !errors.As(err, &durability) {
		t.Fatal("committed durability warning missing", err)
	}
	w, viewErr := s.View()
	locations, reports, spyErr := bound.SpySnapshot(true)
	if viewErr != nil || spyErr != nil || w.Players[1].Sector != 3 || w.Players[1].Turns != 498 || len(locations) != 1 || locations[0] != 4 || len(reports) != 1 || reports[0].Mines != 7 || reports[0].Sector != 2 {
		t.Fatal("committed movement lost spy movement/reports", locations, reports, viewErr, spyErr)
	}
}

func TestSpyShipReportsSaveFailureAndSnapshotIsolation(t *testing.T) {
	s, bound, token := spyStore(t)
	if err := s.Update(func(w *game.World) error {
		p, e := w.Join("private-enemy-account", "Enemy")
		if e != nil {
			return e
		}
		p.Sector = 2
		p.Cloak = 0
		p.Fighters = 42
		p.Shields = 10
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	deadline := time.Now().Add(time.Minute)
	if err := bound.HireSpies(token, []int{2}, time.Now, deadline); err != nil {
		t.Fatal(err)
	}
	// The report is staged but the invalid world cannot replace the saved world.
	if err := bound.UpdateWithSpies(func(w *game.World) error { w.Players[1].Credits = -1; return nil }, time.Now(), deadline); err == nil {
		t.Fatal("invalid world saved")
	}
	_, reports, err := bound.SpySnapshot(false)
	if err != nil || len(reports) != 0 {
		t.Fatal(reports, err)
	}
	if err := bound.UpdateWithSpies(func(w *game.World) error { return nil }, time.Now(), deadline); err != nil {
		t.Fatal(err)
	}
	_, reports, err = bound.SpySnapshot(false)
	if err != nil || len(reports) != 1 || len(reports[0].Ships) != 1 || reports[0].Ships[0].Alias != "Enemy" {
		t.Fatal(reports, err)
	}
	reports[0].Ships[0].Alias = "tampered"
	_, again, err := bound.SpySnapshot(false)
	if err != nil || again[0].Ships[0].Alias != "Enemy" {
		t.Fatal(again, err)
	}
	fresh := s.ForShip(1, 0, 1)
	_, reports, err = fresh.SpySnapshot(false)
	if err != nil || len(reports) != 0 {
		t.Fatal("report leaked across logins", reports, err)
	}
}
