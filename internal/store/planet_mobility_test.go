package store

import (
	"bytes"
	"encoding/json"
	"errors"
	"math"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func mobilityStore(t *testing.T) (Store, Store, time.Time) {
	t.Helper()
	now := time.Now().UTC()
	w, e := game.New(now, 36, 32)
	if e != nil {
		t.Fatal(e)
	}
	p, _ := w.Join("mover", "Mover")
	p.Sector = 8
	p.Credits = 100000
	p.Ground = 1000
	p.Fighters = 1000
	p.Shields = 100000
	_ = w.CreatePlanet(p.ID, "Mobile", now)
	planet := w.Planets[w.Sectors[8].Planet]
	planet.Production = [3]float64{}
	planet.Ground = 100
	w.Sectors[8].Warps = []int{9}
	w.Sectors[9].Warps = []int{10}
	if e = w.Land(p.ID, now); e != nil {
		t.Fatal(e)
	}
	s := Store{Dir: t.TempDir()}
	if e = s.Create(w); e != nil {
		t.Fatal(e)
	}
	return s, s.ForShip(p.ID, p.ShipGeneration, w.Season), now
}
func prepareMobility(t *testing.T, b Store, now time.Time) game.PlanetIntent {
	t.Helper()
	w, e := b.View()
	if e != nil {
		t.Fatal(e)
	}
	entry, e := b.PreparePlanetAction("thrusters", w.Players[1].PlanetToken, 10, 0, func() time.Time { return now }, time.Now().Add(time.Minute))
	if e != nil {
		t.Fatal(e)
	}
	return entry
}
func TestPlanetActionAtomicLateFailureTamperAndReplay(t *testing.T) {
	for _, mode := range []string{"rng", "validation", "callback", "tamper", "clock"} {
		s, b, now := mobilityStore(t)
		e := prepareMobility(t, b, now)
		before := travelBytes(t, s)
		calls := 0
		rng := func() float64 {
			calls++
			if mode == "rng" && calls == 2 {
				return math.NaN()
			}
			return 0
		}
		var err error
		switch mode {
		case "validation", "callback":
			err = b.Update(func(w *game.World) error {
				if _, err := w.CommitPlanetAction(e, rng, now); err != nil {
					return err
				}
				if mode == "callback" {
					return errors.New("abort after movement")
				}
				w.Players[1].Credits = -1
				return nil
			})
		case "tamper":
			e.Path[1] = 11
			_, err = b.CommitPlanetAction(e, rng, func() time.Time { return now }, time.Now().Add(time.Minute))
		case "clock":
			_, err = b.CommitPlanetAction(e, rng, func() time.Time { return now.Add(game.PlanetActionLifetime) }, time.Now().Add(time.Minute))
		default:
			_, err = b.CommitPlanetAction(e, rng, func() time.Time { return now }, time.Now().Add(time.Minute))
		}
		if err == nil || !bytes.Equal(before, travelBytes(t, s)) {
			t.Fatal("partial outcome saved", mode, err)
		}
		if mode == "rng" || mode == "tamper" || mode == "clock" {
			if _, err = b.CommitPlanetAction(e, func() float64 { t.Fatal("nonce replay"); return 0 }, func() time.Time { return now }, time.Now().Add(time.Minute)); err == nil {
				t.Fatal("replay accepted")
			}
		}
	}
}
func TestPlanetConcurrentMoversAndCommittedDurability(t *testing.T) {
	s, a, now := mobilityStore(t)
	b := s.ForShip(1, 0, 1)
	ea := prepareMobility(t, a, now)
	eb := prepareMobility(t, b, now)
	var wg sync.WaitGroup
	results := make(chan error, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func(second bool) {
			defer wg.Done()
			bound, e := a, ea
			if second {
				bound, e = b, eb
			}
			_, err := bound.CommitPlanetAction(e, func() float64 { return 0 }, func() time.Time { return now }, time.Now().Add(time.Minute))
			results <- err
		}(i == 1)
	}
	wg.Wait()
	close(results)
	wins := 0
	for err := range results {
		if err == nil {
			wins++
		}
	}
	w, err := s.View()
	if err != nil || wins != 1 || w.Players[1].Turns != 480 || w.Planets[2].Sector != 10 {
		t.Fatal(w, err, wins)
	}
	s, a, now = mobilityStore(t)
	e := prepareMobility(t, a, now)
	a.syncDirectory = func(string) error { return errors.New("directory sync failed") }
	out, err := a.CommitPlanetAction(e, func() float64 { return 0 }, func() time.Time { return now }, time.Now().Add(time.Minute))
	var committed *DurabilityError
	if !errors.As(err, &committed) || out.Hops != 2 || out.TurnsSpent != 20 {
		t.Fatal(out, err)
	}
	w, err = s.View()
	if err != nil || w.Planets[2].Sector != 10 || w.Players[1].Turns != 480 {
		t.Fatal(w, err)
	}
	if _, err = a.CommitPlanetAction(e, func() float64 { t.Fatal("durable action replay"); return 0 }, func() time.Time { return now }, time.Now().Add(time.Minute)); err == nil {
		t.Fatal("warning replay")
	}
}
func TestGroundAtomicNewsFailureAndLateRandomRollback(t *testing.T) {
	for _, mode := range []string{"rng", "news", "success"} {
		s, b, now := mobilityStore(t)
		if err := s.Update(func(w *game.World) error {
			enemy, _ := w.Join("enemy", "Enemy")
			w.Planets[2].Owner = enemy.ID
			w.Planets[2].Ground = 10
			w.Players[1].PlanetToken = ""
			w.Players[1].LandedPlanet = 0
			return nil
		}); err != nil {
			t.Fatal(err)
		}
		e, err := b.PreparePlanetAction("assault", "", 0, 100, func() time.Time { return now }, time.Now().Add(time.Minute))
		if err != nil {
			t.Fatal(err)
		}
		if mode == "news" {
			if err = s.Update(func(w *game.World) error { w.NextNews = math.MaxUint64; return nil }); err != nil {
				t.Fatal(err)
			}
		}
		before := travelBytes(t, s)
		calls := 0
		out, err := b.CommitPlanetAction(e, func() float64 {
			calls++
			if mode == "rng" && calls == 2 {
				return math.NaN()
			}
			if calls%2 == 1 {
				return 0
			}
			return .9
		}, func() time.Time { return now }, time.Now().Add(time.Minute))
		if mode != "success" {
			if err == nil || !bytes.Equal(before, travelBytes(t, s)) {
				t.Fatal(mode, out, err)
			}
			continue
		}
		w, loadErr := s.View()
		if loadErr != nil || err != nil || !out.Captured || w.Players[1].Ground != 900 || w.Planets[2].Ground != 100 || len(w.News) != 1 {
			t.Fatal(out, err, loadErr)
		}
	}
}
func TestPlanetVersion23ReadOnlyMigrationAndFutureFieldRejection(t *testing.T) {
	s, _, _ := mobilityStore(t)
	w, _ := s.View()
	w.Version = 23
	raw, err := marshalHistoricalWorld(w)
	if err != nil {
		t.Fatal(err)
	}
	path := s.Dir + "/world.json"
	if err = os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	loaded, err := s.View()
	if err != nil || loaded.Planets[2].Generation != 2 || loaded.NextPlanetGeneration != 101 || loaded.Version != game.WorldVersion {
		t.Fatal(loaded, err)
	}
	if !bytes.Equal(raw, travelBytes(t, s)) {
		t.Fatal("read migration wrote")
	}
	if err = s.Update(func(*game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	var saved game.World
	if err = json.Unmarshal(travelBytes(t, s), &saved); err != nil || saved.Version != game.WorldVersion || saved.Planets[2].Generation != 2 {
		t.Fatal(err)
	}
	// A version23 file must not smuggle new allocator/identity state.
	saved.Version = 23
	raw, _ = json.Marshal(saved)
	_ = os.WriteFile(path, raw, 0600)
	if _, err = s.View(); err == nil {
		t.Fatal("legacy future fields accepted")
	}
}
func TestPlanetDeadlineCheckedAfterLockAndAfterRandom(t *testing.T) {
	for _, late := range []bool{false, true} {
		s, b, now := mobilityStore(t)
		e := prepareMobility(t, b, now)
		before := travelBytes(t, s)
		deadline := time.Now().Add(30 * time.Millisecond)
		if late {
			_, err := b.CommitPlanetAction(e, func() float64 { time.Sleep(40 * time.Millisecond); return 0 }, func() time.Time { return now }, deadline)
			if err == nil || !bytes.Equal(before, travelBytes(t, s)) {
				t.Fatal("post-random deadline", err)
			}
		} else {
			acquired := make(chan struct{})
			release := make(chan struct{})
			done := make(chan error, 1)
			go func() { _ = s.locked(func() error { close(acquired); <-release; return nil }) }()
			<-acquired
			go func() {
				_, err := b.CommitPlanetAction(e, func() float64 { t.Error("expired lock wait drew RNG"); return 0 }, func() time.Time { return now }, deadline)
				done <- err
			}()
			time.Sleep(50 * time.Millisecond)
			close(release)
			if err := <-done; err == nil || !bytes.Equal(before, travelBytes(t, s)) {
				t.Fatal("lock deadline", err)
			}
		}
	}
}

func TestThrusterMineDeathAndLateHazardFailure(t *testing.T) {
	for _, fatal := range []bool{false, true} {
		s, b, now := mobilityStore(t)
		if err := s.Update(func(w *game.World) error {
			w.Sectors[9].Minefield = []game.MineLayer{{Owner: 1, Count: 1000}}
			if fatal {
				w.Players[1].Shields = 0
				w.Players[1].Fighters = 0
				w.Players[1].Holds = 10
			}
			return nil
		}); err != nil {
			t.Fatal(err)
		}
		e := prepareMobility(t, b, now)
		before := travelBytes(t, s)
		calls := 0
		out, err := b.CommitPlanetAction(e, func() float64 {
			calls++
			if calls == 1 {
				return 0
			}
			if !fatal {
				return math.NaN()
			}
			return .99
		}, func() time.Time { return now }, time.Now().Add(time.Minute))
		if !fatal {
			if err == nil || !bytes.Equal(before, travelBytes(t, s)) {
				t.Fatal("late hazard partial save", out, err)
			}
			continue
		}
		w, loadErr := s.View()
		if err != nil || loadErr != nil || !out.Mines.Destroyed || w.Planets[2].Sector != 9 || w.Players[1].Death == nil || w.Players[1].Death.Killer != 1 {
			t.Fatal(out, err, loadErr)
		}
		if _, err = b.View(); !errors.Is(err, game.ErrShipDestroyed) {
			t.Fatal("fatal login continued", err)
		}
	}
}

func TestConcurrentGroundAttackersChargeOnlyTheWinningConfirmation(t *testing.T) {
	s, _, now := mobilityStore(t)
	if err := s.Update(func(w *game.World) error {
		other, _ := w.Join("second", "Second")
		owner, _ := w.Join("owner", "Owner")
		other.Sector = 8
		other.Ground = 1000
		w.Planets[2].Owner = owner.ID
		w.Planets[2].Ground = 10
		w.Players[1].PlanetToken = ""
		w.Players[1].LandedPlanet = 0
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	stores := []Store{s.ForShip(1, 0, 1), s.ForShip(2, 0, 1)}
	entries := make([]game.PlanetIntent, 2)
	for i, b := range stores {
		e, err := b.PreparePlanetAction("assault", "", 0, 100, func() time.Time { return now }, time.Now().Add(time.Minute))
		if err != nil {
			t.Fatal(err)
		}
		entries[i] = e
	}
	// A different login must never accept the first login's nonce.
	if _, err := stores[1].CommitPlanetAction(entries[0], func() float64 { t.Fatal("foreign nonce drew"); return 0 }, func() time.Time { return now }, time.Now().Add(time.Minute)); err == nil {
		t.Fatal("cross-login nonce")
	}
	var wg sync.WaitGroup
	results := make(chan error, 2)
	for i := range stores {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			calls := 0
			_, err := stores[i].CommitPlanetAction(entries[i], func() float64 {
				calls++
				if calls%2 == 1 {
					return 0
				}
				return .99
			}, func() time.Time { return now }, time.Now().Add(time.Minute))
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
	w, err := s.View()
	if err != nil || wins != 1 || w.Players[1].Ground+w.Players[2].Ground != 1900 || w.Planets[2].Ground != 100 || len(w.News) != 1 {
		t.Fatal(w, err, wins)
	}
}
