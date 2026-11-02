package store

import (
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func cloakStore(t *testing.T) (Store, Store, time.Time, string, *game.Visibility) {
	t.Helper()
	s := create(t)
	w, _ := s.View()
	at := w.Created
	token := ""
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Credits = 3 * game.AntiCloakPrice
		p.Cloak = .5
		target, e := w.Join("hidden", "Hidden")
		if e != nil {
			return e
		}
		target.Sector = 2
		target.Cloak = 1
		w.Sectors[1].Warps = []int{2}
		if e = w.Dock(1, at); e != nil {
			return e
		}
		token = p.DockToken
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	b := s.ForShip(1, 0, 1)
	v, _ := b.SessionVisibility()
	return s, b, at, token, v
}
func cloakSeen(t *testing.T, s Store, v *game.Visibility) bool {
	t.Helper()
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	reports, err := w.ScanVisible(1, v, func() float64 { return 0 })
	if err != nil {
		t.Fatal(err)
	}
	for _, r := range reports {
		for _, p := range r.Ships {
			if p.ID == 2 {
				return true
			}
		}
	}
	return false
}
func TestCloakStoreAtomicFailureAndCommittedDurability(t *testing.T) {
	for _, mode := range []string{"deadline", "save", "committed"} {
		t.Run(mode, func(t *testing.T) {
			s, b, at, token, v := cloakStore(t)
			deadline := time.Now().Add(time.Minute)
			e, err := b.PrepareAntiCloak(token, v, func() time.Time { return at }, deadline)
			if err != nil {
				t.Fatal(err)
			}
			before := travelBytes(t, s)
			clock := func() time.Time { return at }
			if mode == "deadline" {
				deadline = time.Now().Add(30 * time.Millisecond)
				clock = func() time.Time { time.Sleep(50 * time.Millisecond); return at }
			}
			if mode == "save" {
				clock = func() time.Time {
					if err := os.Rename(filepath.Join(s.Dir, "world.json"), filepath.Join(s.Dir, "backup")); err != nil {
						t.Fatal(err)
					}
					if err := os.Mkdir(filepath.Join(s.Dir, "world.json"), 0700); err != nil {
						t.Fatal(err)
					}
					return at
				}
			}
			if mode == "committed" {
				b.syncDirectory = func(string) error { return errors.New("sync failed") }
			}
			_, err = b.ActivateAntiCloak(e, v, clock, deadline)
			if err == nil {
				t.Fatal("fault accepted")
			}
			if mode == "save" {
				if err := os.Remove(filepath.Join(s.Dir, "world.json")); err != nil {
					t.Fatal(err)
				}
				if err := os.Rename(filepath.Join(s.Dir, "backup"), filepath.Join(s.Dir, "world.json")); err != nil {
					t.Fatal(err)
				}
			}
			var committed *DurabilityError
			if mode == "committed" {
				if !errors.As(err, &committed) || v.AntiCloakActivations() != 1 || !cloakSeen(t, s, v) {
					t.Fatal("committed cache lost", err)
				}
				w, _ := s.View()
				if w.Players[1].Credits != 2*game.AntiCloakPrice {
					t.Fatal("committed debit lost")
				}
				fresh, _ := w.NewVisibility(1)
				if cloakSeen(t, s, fresh) {
					t.Fatal("activation persisted across login")
				}
			} else if !bytes.Equal(before, travelBytes(t, s)) || v.AntiCloakActivations() != 0 || cloakSeen(t, s, v) {
				t.Fatal("rollback leaked world or visibility", err)
			}
			saved := travelBytes(t, s)
			if _, err = b.ActivateAntiCloak(e, v, func() time.Time { t.Error("nonce replay sampled clock"); return at }, time.Now().Add(time.Minute)); err == nil || !bytes.Equal(saved, travelBytes(t, s)) {
				t.Fatal("replayed failed/committed attempt")
			}
		})
	}
}
func TestCloakStoreConcurrentActivationAndBoundVisibility(t *testing.T) {
	s, a, at, token, va := cloakStore(t)
	b := s.ForShip(1, 0, 1)
	vb, _ := b.SessionVisibility()
	deadline := time.Now().Add(time.Minute)
	clock := func() time.Time { return at }
	ea, _ := a.PrepareAntiCloak(token, va, clock, deadline)
	eb, _ := b.PrepareAntiCloak(token, vb, clock, deadline)
	if _, err := a.ActivateAntiCloak(ea, vb, clock, deadline); err == nil {
		t.Fatal("wrong login cache accepted")
	}
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			bound, e, v := a, ea, va
			if i%2 == 1 {
				bound, e, v = b, eb, vb
			}
			_, err := bound.ActivateAntiCloak(e, v, clock, deadline)
			results <- err
		}(i)
	}
	wg.Wait()
	close(results)
	wins := 0
	for err := range results {
		if err == nil {
			wins++
		}
	}
	w, _ := s.View()
	if wins != 1 || w.Players[1].Credits != 2*game.AntiCloakPrice || va.AntiCloakActivations()+vb.AntiCloakActivations() != 1 {
		t.Fatal("concurrent debit/reveal", wins)
	}
	// A saved target incarnation change invalidates old reveals without granting a new one.
	if err := s.Update(func(w *game.World) error { w.Players[2].ShipGeneration++; return nil }); err != nil {
		t.Fatal(err)
	}
	if cloakSeen(t, s, va) || cloakSeen(t, s, vb) {
		t.Fatal("replacement inherited activation")
	}
	if bytes.Contains(travelBytes(t, s), []byte("antiActivations")) {
		t.Fatal("login activation serialized")
	}
}
func TestCloakStoreRechargeConcurrencyAndRollback(t *testing.T) {
	s, b, at, token, _ := cloakStore(t)
	clock := func() time.Time { return at }
	deadline := time.Now().Add(time.Minute)
	if err := s.Update(func(w *game.World) error { w.Players[1].Cloak = 0; w.Players[1].Credits = 10000; return nil }); err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); _, err := b.RechargeCloak(token, 10, clock, deadline); results <- err }()
	}
	wg.Wait()
	close(results)
	wins := 0
	for e := range results {
		if e == nil {
			wins++
		}
	}
	w, _ := s.View()
	if wins != 1 || w.Players[1].Credits != 0 || w.Players[1].Cloak != .1 || w.Version != game.WorldVersion {
		t.Fatal("concurrent recharge", wins, w.Players[1])
	}
	if err := s.Update(func(w *game.World) error { w.Players[1].Credits = 10000; return nil }); err != nil {
		t.Fatal(err)
	}
	before := travelBytes(t, s)
	deadline = time.Now().Add(30 * time.Millisecond)
	if _, err := b.RechargeCloak(token, 1, func() time.Time { time.Sleep(50 * time.Millisecond); return at }, deadline); err == nil || !bytes.Equal(before, travelBytes(t, s)) {
		t.Fatal("expired recharge saved", err)
	}
}
func TestCloakStorePostLockExpiryAndDockClock(t *testing.T) {
	for _, op := range []string{"quote", "activate", "recharge"} {
		t.Run(op, func(t *testing.T) {
			s, b, at, token, v := cloakStore(t)
			clock := func() time.Time { return at }
			e, err := b.PrepareAntiCloak(token, v, clock, time.Now().Add(time.Minute))
			if err != nil {
				t.Fatal(err)
			}
			before := travelBytes(t, s)
			held, release := make(chan struct{}), make(chan struct{})
			done := make(chan error, 1)
			go func() { done <- s.locked(func() error { close(held); <-release; return nil }) }()
			<-held
			deadline := time.Now().Add(30 * time.Millisecond)
			result := make(chan error, 1)
			go func() {
				clock := func() time.Time { t.Error("expired waiter sampled gameplay clock"); return at }
				var err error
				switch op {
				case "quote":
					_, err = b.PrepareAntiCloak(token, v, clock, deadline)
				case "activate":
					_, err = b.ActivateAntiCloak(e, v, clock, deadline)
				case "recharge":
					_, err = b.RechargeCloak(token, 1, clock, deadline)
				}
				result <- err
			}()
			time.Sleep(50 * time.Millisecond)
			close(release)
			if err := <-done; err != nil {
				t.Fatal(err)
			}
			if err := <-result; err == nil || !bytes.Equal(before, travelBytes(t, s)) || v.AntiCloakActivations() != 0 {
				t.Fatal("post-lock expiry changed state", err)
			}
		})
	}
	s, b, at, token, v := cloakStore(t)
	e, _ := b.PrepareAntiCloak(token, v, func() time.Time { return at }, time.Now().Add(time.Minute))
	before := travelBytes(t, s)
	if _, err := b.ActivateAntiCloak(e, v, func() time.Time { return at.Add(6 * time.Minute) }, time.Now().Add(time.Minute)); err == nil || !bytes.Equal(before, travelBytes(t, s)) || v.AntiCloakActivations() != 0 {
		t.Fatal("expired docking accepted", err)
	}
}

func TestCloakStoreActivationDoesNotExposeStagedCache(t *testing.T) {
	for _, abort := range []bool{false, true} {
		t.Run(map[bool]string{false: "commit", true: "rollback"}[abort], func(t *testing.T) {
			s, b, at, token, v := cloakStore(t)
			w, _ := s.View()
			clock := func() time.Time { return at }
			deadline := time.Now().Add(time.Minute)
			e, err := b.PrepareAntiCloak(token, v, clock, deadline)
			if err != nil {
				t.Fatal(err)
			}
			staged, release := make(chan struct{}), make(chan struct{})
			done := make(chan error, 1)
			go func() {
				_, err := b.ActivateAntiCloak(e, v, func() time.Time {
					close(staged)
					<-release
					if abort {
						return at.Add(6 * time.Minute)
					}
					return at
				}, deadline)
				done <- err
			}()
			<-staged
			observed := make(chan bool, 1)
			go func() {
				reports, err := w.ScanVisible(1, v, func() float64 { return 0 })
				if err != nil {
					t.Error(err)
				}
				found := false
				for _, r := range reports {
					for _, p := range r.Ships {
						found = found || p.ID == 2
					}
				}
				observed <- found
			}()
			select {
			case <-observed:
				t.Error("staged visibility was readable before save outcome")
			case <-time.After(50 * time.Millisecond):
			}
			close(release)
			err = <-done
			if (err != nil) != abort {
				t.Fatal("activation outcome", err)
			}
			select {
			case found := <-observed:
				if found == abort {
					t.Fatal("wrong published cache", abort, found)
				}
			case <-time.After(time.Second):
				t.Fatal("cache lock not released")
			}
		})
	}
}

func TestCloakStoreCacheLockWaitExpiresBeforeClock(t *testing.T) {
	for _, prepare := range []bool{false, true} {
		t.Run(map[bool]string{false: "activation", true: "quote"}[prepare], func(t *testing.T) {
			s, b, at, token, v := cloakStore(t)
			e, err := b.PrepareAntiCloak(token, v, func() time.Time { return at }, time.Now().Add(time.Minute))
			if err != nil {
				t.Fatal(err)
			}
			before := travelBytes(t, s)
			_, release := v.StageAntiCloak()
			deadline := time.Now().Add(30 * time.Millisecond)
			done := make(chan error, 1)
			go func() {
				clock := func() time.Time { t.Error("expired cache waiter sampled gameplay clock"); return at }
				var err error
				if prepare {
					_, err = b.PrepareAntiCloak(token, v, clock, deadline)
				} else {
					_, err = b.ActivateAntiCloak(e, v, clock, deadline)
				}
				done <- err
			}()
			time.Sleep(50 * time.Millisecond)
			release(false)
			if err := <-done; err == nil || !bytes.Equal(before, travelBytes(t, s)) || v.AntiCloakActivations() != 0 {
				t.Fatal("expired cache waiter changed state", err)
			}
		})
	}
}
