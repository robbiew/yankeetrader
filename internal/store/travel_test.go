package store

import (
	"errors"
	"math"
	"os"
	"reflect"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func travelStore(t *testing.T) (Store, Store, time.Time) {
	t.Helper()
	s := create(t)
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	return s, s.ForShip(1, 0, 1), w.Created
}
func travelBytes(t *testing.T, s Store) []byte {
	t.Helper()
	b, e := os.ReadFile(s.Dir + "/world.json")
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func TestTravelAtomicAbortValidationAndLateMineFailure(t *testing.T) {
	for _, invalid := range []bool{false, true} {
		s, b, at := travelStore(t)
		w, _ := s.View()
		e, _ := w.PrepareWarp(1)
		before := travelBytes(t, s)
		err := b.Update(func(w *game.World) error {
			if _, err := w.CommitWarp(e, func() float64 { return 0 }, at); err != nil {
				return err
			}
			if invalid {
				w.Players[1].Credits = -1
				return nil
			}
			return errors.New("abort after warp")
		})
		if err == nil || string(before) != string(travelBytes(t, s)) {
			t.Fatal("partial warp saved", err)
		}
	}
	s, b, at := travelStore(t)
	if err := s.Update(func(w *game.World) error {
		w.Players[1].DangerScanner = true
		w.Players[1].Shields = 1000
		w.Sectors[2].Minefield = []game.MineLayer{{Owner: 0, Count: 1}}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	e, err := b.PrepareWarp(time.Now().Add(time.Minute))
	if err != nil {
		t.Fatal(err)
	}
	before := travelBytes(t, s)
	i := 0
	_, err = b.Warp(e, func() float64 {
		i++
		if i == 3 {
			return .2
		}
		if i == 6 {
			return math.NaN()
		}
		return 0
	}, func() time.Time { return at }, time.Now().Add(time.Minute))
	if err == nil || string(before) != string(travelBytes(t, s)) {
		t.Fatal("late mine failure partly saved", err)
	}
	if _, err = b.Warp(e, func() float64 { t.Fatal("failed nonce reused"); return 0 }, func() time.Time { return at }, time.Now().Add(time.Minute)); err == nil {
		t.Fatal("aborted warning reusable")
	}
}
func TestTravelConcurrentZeroCostSameSectorAndCommittedDurability(t *testing.T) {
	s, a, at := travelStore(t)
	b := s.ForShip(1, 0, 1)
	deadline := time.Now().Add(time.Minute)
	ea, err := a.PrepareWarp(deadline)
	if err != nil {
		t.Fatal(err)
	}
	eb, err := b.PrepareWarp(deadline)
	if err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func(second bool) {
			defer wg.Done()
			bound, e := a, ea
			if second {
				bound, e = b, eb
			}
			_, err := bound.Warp(e, func() float64 { return 0 }, func() time.Time { return at }, deadline)
			results <- err
		}(i%2 == 1)
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
	if wins != 1 || w.Players[1].WarpSequence != 1 || w.Players[1].Turns != 500 || w.Players[1].Sector != 1 {
		t.Fatal("zero-cost replay or competing confirmation", wins, w.Players[1])
	}
	e, err := a.PrepareWarp(deadline)
	if err != nil {
		t.Fatal(err)
	}
	a.syncDirectory = func(string) error { return errors.New("directory sync failed") }
	_, err = a.Warp(e, func() float64 { return 0 }, func() time.Time { return at }, deadline)
	var committed *DurabilityError
	if !errors.As(err, &committed) {
		t.Fatal(err)
	}
	fresh := Store{Dir: s.Dir}
	saved, err := fresh.View()
	if err != nil || saved.Players[1].WarpSequence != 2 {
		t.Fatal("committed warp lost", err)
	}
	raw := travelBytes(t, s)
	if _, err = a.Warp(e, func() float64 { t.Fatal("durability replay drew"); return 0 }, func() time.Time { return at }, deadline); err == nil || string(raw) != string(travelBytes(t, s)) {
		t.Fatal("committed warp repeated", err)
	}
}
func TestTravelPurchaseConcurrencyAndMigration(t *testing.T) {
	s, _, at := travelStore(t)
	token := ""
	if err := s.Update(func(w *game.World) error {
		w.Players[1].Credits = game.DangerScannerPrice + 1
		if e := w.Dock(1, at); e != nil {
			return e
		}
		token = w.Players[1].DockToken
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results <- s.ForShip(1, 0, 1).Update(func(w *game.World) error { return w.Equip(1, token, "scanner", 1, at) })
		}()
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
	if wins != 1 || !w.Players[1].DangerScanner || w.Players[1].Credits != 1 || w.Ports[1].Treasury != 0 {
		t.Fatal("duplicate purchase", wins)
	}
	w.Players[1].DangerScanner = false
	w.Version = 20
	w.Season = 0
	w.GenerationSeed = nil
	expected := *w
	expected.Version = game.WorldVersion
	expected.Season = 1
	raw, _ := marshalHistoricalWorld(w)
	if err := os.WriteFile(s.Dir+"/world.json", raw, 0600); err != nil {
		t.Fatal(err)
	}
	loaded, err := s.View()
	if err != nil || !reflect.DeepEqual(&expected, loaded) || string(raw) != string(travelBytes(t, s)) {
		t.Fatal("read-only migration changed old state", err)
	}
	if err = s.Update(func(*game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	saved, _ := s.View()
	if saved.Version != game.WorldVersion || saved.Players[1].DangerScanner {
		t.Fatal("migration granted scanner")
	}
	for _, scanner := range []bool{false, true} {
		w.Version = 20
		w.Season = 0
		w.GenerationSeed = nil
		w.Players[1].DangerScanner = scanner
		if !scanner {
			w.Players[1].WarpSequence = 1
		}
		raw, _ = marshalHistoricalWorld(w)
		_ = os.WriteFile(s.Dir+"/world.json", raw, 0600)
		if _, e := s.View(); e == nil {
			t.Fatal("legacy accepted future state")
		}
	}
}
func TestTravelWarningExpiresDuringWorldLockWait(t *testing.T) {
	s, b, _ := travelStore(t)
	held := make(chan struct{})
	release := make(chan struct{})
	done := make(chan error, 1)
	go func() { done <- s.locked(func() error { close(held); <-release; return nil }) }()
	<-held
	deadline := time.Now().Add(30 * time.Millisecond)
	result := make(chan error, 1)
	go func() { _, e := b.PrepareWarp(deadline); result <- e }()
	time.Sleep(50 * time.Millisecond)
	close(release)
	if e := <-done; e != nil {
		t.Fatal(e)
	}
	if e := <-result; e == nil {
		t.Fatal("expired lock wait authorized warp")
	}
}
func TestTravelFatalWarpArrivalReloadAndGenerationInvalidation(t *testing.T) {
	s, b, at := travelStore(t)
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Holds = 1
		p.Cargo = [3]int64{}
		p.Shields = 0
		p.Fighters = 0
		p.Missiles = 0
		p.Cloak = 0
		p.DangerScanner = true
		w.Sectors[2].Minefield = []game.MineLayer{{Owner: 0, Count: 1}}
		w.Ports[2].Owner = 1
		w.Ports[2].Treasury = 123
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	deadline := time.Now().Add(time.Minute)
	e, err := b.PrepareWarp(deadline)
	if err != nil {
		t.Fatal(err)
	}
	i := 0
	out, err := b.Warp(e, func() float64 {
		i++
		if i == 3 {
			return .2
		}
		return 0
	}, func() time.Time { return at }, deadline)
	if err != nil || !out.Mines.Destroyed {
		t.Fatal(out, err)
	}
	saved, err := (Store{Dir: s.Dir}).View()
	if err != nil || saved.Players[1].Death == nil || saved.Players[1].DangerScanner || saved.Ports[2].Owner != 0 {
		t.Fatal("fatal arrival not atomic", err)
	}
	if _, err = b.PrepareWarp(deadline); !errors.Is(err, game.ErrShipDestroyed) {
		t.Fatal("dead generation could warp", err)
	}
	if err = s.Update(func(w *game.World) error { return w.LoginShip(1, at) }); err != nil {
		t.Fatal(err)
	}
	if _, err = b.PrepareWarp(deadline); !errors.Is(err, game.ErrShipChanged) {
		t.Fatal("old login regained authority", err)
	}
	saved, _ = s.View()
	if saved.Players[1].DangerScanner || saved.Players[1].WarpSequence != 1 {
		t.Fatal("replacement retained scanner or erased replay sequence")
	}
}

func TestTravelStaleWarpWarningsPreserveCurrentSave(t *testing.T) {
	for _, mode := range []string{"position", "turns", "generation", "scanner", "sequence", "maintenance"} {
		s, b, at := travelStore(t)
		if err := s.Update(func(w *game.World) error { w.Players[1].Sector = 8; w.Players[1].DangerScanner = true; return nil }); err != nil {
			t.Fatal(err)
		}
		deadline := time.Now().Add(time.Minute)
		e, err := b.PrepareWarp(deadline)
		if err != nil {
			t.Fatal(err)
		}
		if err = s.Update(func(w *game.World) error {
			p := w.Players[1]
			switch mode {
			case "position":
				p.Sector = 7
			case "turns":
				p.Turns--
			case "generation":
				p.ShipGeneration++
			case "scanner":
				p.DangerScanner = false
			case "sequence":
				p.WarpSequence++
			case "maintenance":
				w.LastMaintenance = at.AddDate(0, 0, 1).UTC().Format("2006-01-02")
			}
			return nil
		}); err != nil {
			t.Fatal(err)
		}
		before := travelBytes(t, s)
		if _, err = b.Warp(e, func() float64 { t.Fatal("stale warning drew", mode); return 0 }, func() time.Time { return at }, deadline); err == nil || string(before) != string(travelBytes(t, s)) {
			t.Fatal("stale warp changed state", mode, err)
		}
	}
}
func TestTravelWarpCommitExpiresDuringWorldLockWait(t *testing.T) {
	s, b, at := travelStore(t)
	e, err := b.PrepareWarp(time.Now().Add(time.Minute))
	if err != nil {
		t.Fatal(err)
	}
	before := travelBytes(t, s)
	held := make(chan struct{})
	release := make(chan struct{})
	done := make(chan error, 1)
	go func() { done <- s.locked(func() error { close(held); <-release; return nil }) }()
	<-held
	deadline := time.Now().Add(30 * time.Millisecond)
	result := make(chan error, 1)
	go func() {
		_, err := b.Warp(e, func() float64 { t.Error("expired warp drew"); return 0 }, func() time.Time { t.Error("expired warp sampled gameplay time"); return at }, deadline)
		result <- err
	}()
	time.Sleep(50 * time.Millisecond)
	close(release)
	if e := <-done; e != nil {
		t.Fatal(e)
	}
	if e := <-result; e == nil || string(before) != string(travelBytes(t, s)) {
		t.Fatal("expired warp committed", e)
	}
}
