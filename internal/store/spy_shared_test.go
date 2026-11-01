package store

import (
	"errors"
	"math"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func sharedSpyStore(t *testing.T) (Store, Store, *game.Visibility) {
	t.Helper()
	s, b, token := spyStore(t)
	if err := s.Update(func(w *game.World) error {
		p, e := w.Join("secret-target-key", "Hidden")
		if e != nil {
			return e
		}
		p.Sector = 2
		p.Cloak = .5
		p.Fighters = 42
		p.Shields = 100
		p.Missiles = 0
		w.Sectors[1].Warps = []int{2}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := b.HireSpies(token, []int{2}, time.Now, time.Now().Add(time.Hour)); err != nil {
		t.Fatal(err)
	}
	b.ship.spyRNG = func() float64 { return .9 }
	v, err := b.SessionVisibility()
	if err != nil {
		t.Fatal(err)
	}
	return s, b, v
}
func sharedTargetVisible(t *testing.T, s Store, v *game.Visibility) bool {
	t.Helper()
	w, e := s.View()
	if e != nil {
		t.Fatal(e)
	}
	reports, e := w.ScanVisible(1, v, nil)
	if e != nil {
		t.Fatal(e)
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
func TestSharedSpyVisibilityAtomicPublication(t *testing.T) {
	for _, mode := range []string{"saved", "abort", "invalid-world", "invalid-rng", "expired", "committed-warning"} {
		t.Run(mode, func(t *testing.T) {
			s, b, v := sharedSpyStore(t)
			before, _ := os.ReadFile(s.Dir + "/world.json")
			deadline := time.Now().Add(time.Hour)
			if mode == "invalid-rng" {
				b.ship.spyRNG = func() float64 { return math.NaN() }
			}
			if mode == "expired" {
				deadline = time.Now().Add(-time.Second)
			}
			if mode == "committed-warning" {
				b.syncDirectory = func(string) error { return errors.New("sync after replacement") }
			}
			err := b.UpdateWithSpies(func(w *game.World) error {
				if mode == "abort" {
					return errors.New("abort")
				}
				if mode == "invalid-world" {
					w.Players[1].Credits = -1
				} else {
					w.Players[1].Credits++
				}
				return nil
			}, time.Now(), deadline)
			committed := mode == "saved" || mode == "committed-warning"
			var warning *DurabilityError
			if mode == "committed-warning" && !errors.As(err, &warning) {
				t.Fatal(err)
			}
			if mode == "saved" && err != nil || !committed && err == nil {
				t.Fatal("wrong settlement", err)
			}
			_, reports, e := b.SpySnapshot(false)
			if e != nil {
				t.Fatal(e)
			}
			if sharedTargetVisible(t, b, v) != committed || (len(reports) > 0) != committed {
				t.Fatal("partial private publication")
			}
			after, _ := os.ReadFile(s.Dir + "/world.json")
			if !committed && string(before) != string(after) {
				t.Fatal("failed transaction changed save")
			}
			w, _ := s.View()
			if w.Players[2].Cloak != .5 || len(w.Radio) != 0 || len(w.News) != 0 {
				t.Fatal("target cloak/private notification changed")
			}
			fresh := s.ForShip(1, w.Players[1].ShipGeneration, w.Season)
			other, e := fresh.SessionVisibility()
			if e != nil {
				t.Fatal(e)
			}
			if other == v || sharedTargetVisible(t, fresh, other) {
				t.Fatal("another login inherited reveal")
			}
		})
	}
}
func TestSensorDetectionFeedsSpiesAndGenerationGuard(t *testing.T) {
	s, b, v := sharedSpyStore(t)
	w, _ := b.View()
	if _, err := w.ScanVisible(1, v, func() float64 { return .9 }); err != nil {
		t.Fatal(err)
	}
	b.ship.spyRNG = func() float64 { t.Fatal("spy redrew a known target"); return 0 }
	if err := b.UpdateWithSpies(func(*game.World) error { return nil }, time.Now(), time.Now().Add(time.Hour)); err != nil {
		t.Fatal(err)
	}
	_, reports, e := b.SpySnapshot(false)
	if e != nil || len(reports) != 1 || len(reports[0].Ships) != 1 || reports[0].Ships[0].Shimmering {
		t.Fatal(reports, e)
	}
	if err := s.Update(func(w *game.World) error { w.Players[2].ShipGeneration++; return nil }); err != nil {
		t.Fatal(err)
	}
	if sharedTargetVisible(t, b, v) {
		t.Fatal("replacement inherited old detection")
	}
	if err := s.Update(func(w *game.World) error { w.Players[1].ShipGeneration++; return nil }); err != nil {
		t.Fatal(err)
	}
	if _, err := b.SessionVisibility(); err == nil {
		t.Fatal("obsolete observer got visibility")
	}
}
func TestSpyReportsShareVisibilityWithAttackEligibility(t *testing.T) {
	s, b, v := sharedSpyStore(t)
	if err := s.Update(func(w *game.World) error {
		w.Sectors[2].Defense = nil
		w.Sectors[2].Minefield = nil
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	if err := b.UpdateWithSpies(func(w *game.World) error { return w.Move(1, 2) }, time.Now(), time.Now().Add(time.Hour)); err != nil {
		t.Fatal(err)
	}
	w, err := b.View()
	if err != nil {
		t.Fatal(err)
	}
	candidates, err := w.VisibleAttackCandidates(1, v)
	if err != nil || len(candidates) != 1 {
		t.Fatal(candidates, err)
	}
	quote, err := w.PrepareVisibleAttack(1, 2, 1, v)
	if err != nil {
		t.Fatal("shared reveal not usable for current target", err)
	}
	if err := b.Update(func(w *game.World) error {
		_, e := w.CommitVisibleAttack(quote, v, func() float64 { return .5 }, time.Now())
		return e
	}); err != nil {
		t.Fatal("committed spy reveal did not authorize actual attack", err)
	}
	if err := s.Update(func(w *game.World) error { w.Players[2].ShipGeneration++; return nil }); err != nil {
		t.Fatal(err)
	}
	before, err := os.ReadFile(s.Dir + "/world.json")
	if err != nil {
		t.Fatal(err)
	}
	if err := b.Update(func(w *game.World) error {
		_, e := w.CommitVisibleAttack(quote, v, func() float64 { return .5 }, time.Now())
		return e
	}); err == nil {
		t.Fatal("stale target generation authorized saved attack")
	}
	after, err := os.ReadFile(s.Dir + "/world.json")
	if err != nil || string(before) != string(after) {
		t.Fatal("stale attack changed saved state", err)
	}
}
func TestConcurrentSpyReportsPreserveVisibilityAndUnread(t *testing.T) {
	_, b, v := sharedSpyStore(t)
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results <- b.UpdateWithSpies(func(*game.World) error { return nil }, time.Now(), time.Now().Add(time.Hour))
		}()
	}
	wg.Wait()
	close(results)
	for err := range results {
		if err != nil {
			t.Fatal(err)
		}
	}
	_, reports, err := b.SpySnapshot(true)
	if err != nil || len(reports) != 1 || !sharedTargetVisible(t, b, v) {
		t.Fatal("concurrent publication duplicated or lost report", reports, err)
	}
	if err = b.AcknowledgeSpy(reports[0].ID); err != nil {
		t.Fatal(err)
	}
	if !sharedTargetVisible(t, b, v) {
		t.Fatal("acknowledging intelligence consumed detection")
	}
}

func TestAntiCloakDetectionFeedsSpyWithoutNewDraw(t *testing.T) {
	s, b, v := sharedSpyStore(t)
	var token string
	if err := s.Update(func(w *game.World) error {
		w.Players[2].Cloak = 1
		if e := w.Dock(1, time.Now()); e != nil {
			return e
		}
		token = w.Players[1].DockToken
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	deadline := time.Now().Add(time.Hour)
	entry, err := b.PrepareAntiCloak(token, v, time.Now, deadline)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = b.ActivateAntiCloak(entry, v, time.Now, deadline); err != nil {
		t.Fatal(err)
	}
	b.ship.spyRNG = func() float64 { t.Fatal("known full cloak redrawn"); return 0 }
	if err = b.UpdateWithSpies(func(*game.World) error { return nil }, time.Now(), deadline); err != nil {
		t.Fatal(err)
	}
	_, reports, err := b.SpySnapshot(false)
	if err != nil || len(reports) != 1 || len(reports[0].Ships) != 1 || reports[0].Ships[0].Shimmering || v.AntiCloakActivations() != 1 {
		t.Fatal(reports, err)
	}
	w, _ := s.View()
	if w.Players[2].Cloak != 1 || len(w.Radio) != 0 || len(w.News) != 0 {
		t.Fatal("target state changed")
	}
}
