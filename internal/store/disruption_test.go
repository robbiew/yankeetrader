package store

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"math"
	"os"
	"sync"
	"testing"
	"time"
)

func arrivalStore(t *testing.T) (Store, Store, time.Time) {
	t.Helper()
	s, b, at := travelStore(t)
	if e := s.Update(func(w *game.World) error { w.Sectors[1].Warps = []int{2}; w.Sectors[8].Warps = nil; return nil }); e != nil {
		t.Fatal(e)
	}
	return s, b, at
}
func startArrival(t *testing.T, b Store, at time.Time, rng func() float64) {
	t.Helper()
	if e := b.StartDisruption(rng, func() time.Time { return at }, time.Now().Add(time.Hour)); e != nil {
		t.Fatal(e)
	}
}
func arrivalRandom(t *testing.T, tail ...float64) func() float64 {
	t.Helper()
	values := append([]float64{0, 0}, tail...)
	i := 0
	return func() float64 {
		if i == len(values) {
			t.Fatal("unexpected arrival draw")
			return 0
		}
		v := values[i]
		i++
		return v
	}
}
func TestArrivalAtomicMovementAbortLateRNGAndChainLimit(t *testing.T) {
	for _, mode := range []string{"callback", "validation", "draw", "chain"} {
		t.Run(mode, func(t *testing.T) {
			s, b, at := arrivalStore(t)
			i := 0
			rng := func() float64 {
				i++
				if i <= 2 {
					return 0
				}
				if mode == "chain" && ((i-2)%5) == 3 {
					return .125
				}
				if mode == "draw" && i == 5 {
					return math.NaN()
				}
				if i == 5 {
					return .99
				}
				return 0
			}
			startArrival(t, b, at, rng)
			before := travelBytes(t, s)
			err := b.Update(func(w *game.World) error {
				if e := w.Move(1, 2); e != nil {
					return e
				}
				if mode == "callback" {
					return errors.New("late callback abort")
				}
				if mode == "validation" {
					w.Players[1].Credits = -1
				}
				return nil
			})
			if err == nil || string(before) != string(travelBytes(t, s)) || len(b.TakeArrival().Warps) != 0 {
				t.Fatal("partial origin/aftermath committed", err)
			}
			if mode == "chain" && !errors.Is(err, game.ErrDisruptionLimit) {
				t.Fatal(err)
			}
		})
	}
}
func TestArrivalSequenceReceiptsDurabilityAndNoReplay(t *testing.T) {
	for _, warning := range []bool{false, true} {
		s, b, at := arrivalStore(t)
		startArrival(t, b, at, arrivalRandom(t, 0, 0, .99, 0, .9))
		if warning {
			b.syncDirectory = func(string) error { return errors.New("directory sync") }
		}
		err := b.Update(func(w *game.World) error { return w.Move(1, 2) })
		var committed *DurabilityError
		if warning != errors.As(err, &committed) || (err != nil && !warning) {
			t.Fatal(err)
		}
		out := b.TakeArrival()
		saved, _ := s.View()
		p := saved.Players[1]
		if len(out.Warps) != 1 || out.FinalSector != 8 || out.TurnsSpent != 4 || out.TurnsRemaining != 496 || p.WarpSequence != 1 {
			t.Fatal(out, p)
		}
		if len(b.TakeArrival().Warps) != 0 {
			t.Fatal("receipt replay")
		}
		b.syncDirectory = nil
		if e := b.Update(func(w *game.World) error { return nil }); e != nil {
			t.Fatal(e)
		}
		if len(b.TakeArrival().Warps) != 0 {
			t.Fatal("menu reran arrival")
		}
		raw, _ := os.ReadFile(s.Dir + "/world.json")
		if string(raw) == "" {
			t.Fatal("missing save")
		}
		old := p.Turns
		// A fresh login selects a new pair, without loading or publishing old locations.
		c := s.ForShip(1, p.ShipGeneration, saved.Season)
		startArrival(t, c, at, arrivalRandom(t))
		newer, _ := s.View()
		if newer.Players[1].Turns != old || len(c.TakeArrival().Warps) != 0 {
			t.Fatal("reconnect repayment")
		}
	}
}
func TestArrivalStartupPriorityAndInitializationAbort(t *testing.T) {
	s, b, at := arrivalStore(t)
	if e := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Sector = 2
		p.Turns = 0
		p.Cloak = .5
		w.Sectors[2].Minefield = []game.MineLayer{{Owner: 0, Count: 3}}
		w.Sectors[2].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 100}
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	startArrival(t, b, at, arrivalRandom(t, 0, 0, .99, 0, 0))
	out := b.TakeArrival()
	saved, _ := s.View()
	if len(out.Warps) != 1 || saved.Players[1].Sector != 8 || saved.Players[1].Cloak != .5 || saved.Players[1].Turns != 0 || saved.Sectors[2].Minefield[0].Count != 3 || saved.Sectors[2].Defense.Fighters != 100 {
		t.Fatal(out)
	}
	before := travelBytes(t, s)
	c := s.ForShip(1, 0, 1)
	if e := c.StartDisruption(func() float64 { return math.NaN() }, func() time.Time { return at }, time.Now().Add(time.Hour)); e == nil || c.ship.disruption != nil || string(before) != string(travelBytes(t, s)) {
		t.Fatal("failed init published", e)
	}
}
func TestArrivalLockWaitExpiryAndCapturedIdentity(t *testing.T) {
	for _, mode := range []string{"deadline", "season", "generation"} {
		s, b, at := arrivalStore(t)
		before := travelBytes(t, s)
		if mode != "deadline" {
			if e := s.Update(func(w *game.World) error {
				if mode == "season" {
					w.Season++
					w.SeasonResults = []game.SeasonResult{{Season: 1, Started: w.Created, Ended: w.Created, Winner: "Q", Player: 1, Threshold: 20, Ports: 20}}
				} else {
					w.Players[1].ShipGeneration++
				}
				return nil
			}); e != nil {
				t.Fatal(e)
			}
		}
		deadline := time.Now().Add(20 * time.Millisecond)
		entered, release := make(chan struct{}), make(chan struct{})
		var wg sync.WaitGroup
		if mode == "deadline" {
			wg.Add(1)
			go func() { defer wg.Done(); _ = s.locked(func() error { close(entered); <-release; return nil }) }()
			<-entered
		}
		done := make(chan error, 1)
		go func() {
			done <- b.StartDisruption(func() float64 { t.Error("invalid authority drew RNG"); return 0 }, func() time.Time { return at }, deadline)
		}()
		if mode == "deadline" {
			time.Sleep(40 * time.Millisecond)
			close(release)
			wg.Wait()
		}
		if e := <-done; e == nil || b.ship.disruption != nil {
			t.Fatal("stale startup succeeded", mode, e)
		}
		if mode == "deadline" && string(before) != string(travelBytes(t, s)) {
			t.Fatal("expired startup saved")
		}
	}
}
func TestArrivalConcurrentBoundActionsPublishOnlyOneMove(t *testing.T) {
	s, b, at := arrivalStore(t)
	startArrival(t, b, at, arrivalRandom(t, 0, 0, .99, 0, 0))
	var wg sync.WaitGroup
	errs := make(chan error, 2)
	for range 2 {
		wg.Add(1)
		go func() { defer wg.Done(); errs <- b.Update(func(w *game.World) error { return w.Move(1, 2) }) }()
	}
	wg.Wait()
	close(errs)
	success := 0
	for e := range errs {
		if e == nil {
			success++
		}
	}
	saved, _ := s.View()
	if success != 1 || saved.Players[1].WarpSequence != 1 || saved.Players[1].Turns != 499 {
		t.Fatal("duplicate origin", success)
	}
}

func TestArrivalFatalAftermathCommitsTheDeathGeneration(t *testing.T) {
	s, b, at := arrivalStore(t)
	if e := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Cloak = 0
		p.Shields = 0
		p.Holds = 1
		p.Fighters = 0
		p.Mines = 0
		p.Missiles = 0
		p.Plasma = 0
		p.Cargo = [3]int64{}
		w.Sectors[8].Minefield = []game.MineLayer{{Owner: 0, Count: 1}}
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	i := 0
	startArrival(t, b, at, func() float64 {
		i++
		if i <= 2 {
			return 0
		}
		if i == 5 {
			return .99
		}
		if i <= 7 {
			return 0
		}
		return .5
	})
	if e := b.Update(func(w *game.World) error { return w.Move(1, 2) }); e != nil {
		t.Fatal("valid death rolled back", e)
	}
	saved, e := s.View()
	if e != nil {
		t.Fatal(e)
	}
	p := saved.Players[1]
	out := b.TakeArrival()
	if p.Death == nil || p.Death.Cause != "mines" || p.Death.Killer != 0 || p.ShipGeneration != 1 || p.Turns != 499 || len(out.Warps) != 1 || len(out.Mines) != 1 || !out.Mines[0].Destroyed || out.FinalSector != 0 {
		t.Fatal(p, out)
	}
	if e = b.Update(func(w *game.World) error { t.Fatal("dead session callback ran"); return nil }); !errors.Is(e, game.ErrShipDestroyed) {
		t.Fatal(e)
	}
}
