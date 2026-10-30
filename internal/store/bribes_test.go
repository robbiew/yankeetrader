package store

import (
	"encoding/json"
	"errors"
	"math"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func bribeFixture(t *testing.T) (Store, Store) {
	t.Helper()
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Sector = 8
		p.Credits = 10000
		p.Fighters = 1000
		w.Sectors[8].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 100}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, s.ForShip(1, 0, 1)
}
func bribeDeadline() time.Time { return time.Now().Add(time.Minute) }

func TestBribeConcurrentConfirmationCommitsOnce(t *testing.T) {
	s, b := bribeFixture(t)
	entry, err := b.PrepareBribe(300, bribeDeadline())
	if err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	results := make(chan error, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, e := b.Bribe(entry, func() float64 { return .5 }, time.Now, bribeDeadline())
			results <- e
		}()
	}
	wg.Wait()
	close(results)
	successes := 0
	for e := range results {
		if e == nil {
			successes++
		}
	}
	w, _ := s.View()
	if successes != 1 || w.Players[1].Credits != 9700 || w.Players[1].Fighters != 1100 || w.Sectors[8].Defense != nil {
		t.Fatal(successes, w.Players[1])
	}
}

func TestBribeRefusalIsSingleUseAndBound(t *testing.T) {
	s, b := bribeFixture(t)
	if err := s.Update(func(w *game.World) error { w.Sectors[8].Defense.Owner = game.XannorOwner; return nil }); err != nil {
		t.Fatal(err)
	}
	entry, err := b.PrepareBribe(0, bribeDeadline())
	if err != nil {
		t.Fatal(err)
	}
	if _, err = s.Bribe(entry, func() float64 { t.Fatal("unbound RNG"); return 0 }, time.Now, bribeDeadline()); err == nil {
		t.Fatal("unbound bribe")
	}
	if err = s.Update(func(w *game.World) error { w.Sectors[8].Defense.Owner = 1; return nil }); err != nil {
		t.Fatal(err)
	}
	if _, err = b.Bribe(entry, func() float64 { t.Fatal("changed group RNG"); return 0 }, time.Now, bribeDeadline()); err == nil {
		t.Fatal("changed group")
	}
	if _, err = b.Bribe(entry, func() float64 { t.Fatal("replay RNG"); return 0 }, time.Now, bribeDeadline()); err == nil {
		t.Fatal("replay failed quote")
	}
}

func TestBribeFailureRollsBackWorldAndHostility(t *testing.T) {
	for _, mode := range []string{"rng", "save", "deadline", "escape"} {
		t.Run(mode, func(t *testing.T) {
			s, b := bribeFixture(t)
			entry, _ := b.PrepareBribe(1, bribeDeadline())
			w, _ := s.View()
			before, _ := json.Marshal(w)

			deadline := bribeDeadline()
			if mode == "deadline" {
				deadline = time.Now().Add(-time.Second)
			}
			blocked := false
			draws := 0
			battle, battleErr := game.ResolveSectorBattle(1000, 100, 0, game.MercenaryOwner, false, func() float64 { return 0 })
			if battleErr != nil {
				t.Fatal(battleErr)
			}
			rng := func() float64 {
				draws++
				if mode == "rng" || (mode == "escape" && draws > 2+battle.Rounds) {
					return math.NaN()
				}
				if mode == "escape" {
					return 0
				}
				if mode == "save" && !blocked {
					blocked = true
					if err := os.Rename(filepath.Join(s.Dir, "world.json"), filepath.Join(s.Dir, "saved-world")); err != nil {
						t.Fatal(err)
					}
					if err := os.Mkdir(filepath.Join(s.Dir, "world.json"), 0700); err != nil {
						t.Fatal(err)
					}
				}
				return .5
			}
			_, err := b.Bribe(entry, rng, time.Now, deadline)
			if err == nil {
				t.Fatal("failure accepted")
			}
			if blocked {
				if err := os.Remove(filepath.Join(s.Dir, "world.json")); err != nil {
					t.Fatal(err)
				}
				if err := os.Rename(filepath.Join(s.Dir, "saved-world"), filepath.Join(s.Dir, "world.json")); err != nil {
					t.Fatal(err)
				}
			}
			w, _ = s.View()
			after, _ := json.Marshal(w)
			if string(before) != string(after) || b.ship.mercenaryHostile {
				t.Fatal("failed bribe committed resources or hostility")
			}
		})
	}
}

func TestMercenaryHostilityPublishesWithCommitAndResetsOnReconnect(t *testing.T) {
	for _, durability := range []bool{false, true} {
		t.Run(map[bool]string{false: "normal", true: "durability"}[durability], func(t *testing.T) {
			s, b := bribeFixture(t)
			w, _ := s.View()
			fight, _ := w.PrepareDefenseFight(1, 8, 1000, false)
			if durability {
				b.syncDirectory = func(string) error { return errors.New("sync failure") }
			}
			_, err := b.DefenseEncounter(fight, func() float64 { return .5 }, time.Now(), bribeDeadline())
			var warning *DurabilityError
			if (!durability && err != nil) || (durability && !errors.As(err, &warning)) {
				t.Fatal(err)
			}
			if !b.ship.mercenaryHostile {
				t.Fatal("committed mercenary loss did not publish hostility")
			}
			if err = s.Update(func(w *game.World) error {
				w.Sectors[8].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 100}
				return nil
			}); err != nil {
				t.Fatal(err)
			}
			entry, err := b.PrepareBribe(300, bribeDeadline())
			if err != nil || !entry.Hostile {
				t.Fatal(entry, err)
			}
			fresh := s.ForShip(1, 0, 1)
			entry, err = fresh.PrepareBribe(300, bribeDeadline())
			if err != nil || entry.Hostile {
				t.Fatal("reconnect retained hostility", err)
			}
			out, err := fresh.Bribe(entry, func() float64 { return .5 }, time.Now, bribeDeadline())
			if err != nil || out.Joined != 100 {
				t.Fatal(out, err)
			}
		})
	}
}

func TestBribeDurabilityWarningKeepsRecruitment(t *testing.T) {
	s, b := bribeFixture(t)
	entry, _ := b.PrepareBribe(300, bribeDeadline())
	b.syncDirectory = func(string) error { return errors.New("sync failure") }
	out, err := b.Bribe(entry, func() float64 { return .5 }, time.Now, bribeDeadline())
	var warning *DurabilityError
	w, _ := s.View()
	if !errors.As(err, &warning) || out.Joined != 100 || w.Players[1].Credits != 9700 || w.Sectors[8].Defense != nil {
		t.Fatal(out, err)
	}
	if _, err = b.Bribe(entry, func() float64 { t.Fatal("durable replay RNG"); return 0 }, time.Now, bribeDeadline()); err == nil {
		t.Fatal("replayed committed warning")
	}
}

func TestBribeSessionTokenAndUnchangedRefusalCannotReplay(t *testing.T) {
	s, b := bribeFixture(t)
	if err := s.Update(func(w *game.World) error {
		other, e := w.Join("enemy", "Enemy")
		if e != nil {
			return e
		}
		w.Sectors[8].Defense.Owner = other.ID
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	entry, err := b.PrepareBribe(0, bribeDeadline())
	if err != nil {
		t.Fatal(err)
	}
	second := s.ForShip(1, 0, 1)
	fresh, err := second.PrepareBribe(0, bribeDeadline())
	if err != nil {
		t.Fatal(err)
	}
	if _, err = second.Bribe(entry, func() float64 { t.Fatal("cross-login RNG"); return 0 }, time.Now, bribeDeadline()); err == nil {
		t.Fatal("another login's quote accepted")
	}
	out, err := second.Bribe(fresh, func() float64 { return .5 }, time.Now, bribeDeadline())
	if err != nil || out.Combat || out.Paid != 0 {
		t.Fatal(out, err)
	}
	if _, err = second.Bribe(fresh, func() float64 { t.Fatal("refusal replay RNG"); return 0 }, time.Now, bribeDeadline()); err == nil {
		t.Fatal("unchanged refusal replayed")
	}
}

func TestBribeLockWaitCannotOutliveDeadline(t *testing.T) {
	s, b := bribeFixture(t)
	entry, _ := b.PrepareBribe(300, bribeDeadline())
	held := make(chan struct{})
	release := make(chan struct{})
	done := make(chan error, 1)
	go func() { done <- s.locked(func() error { close(held); <-release; return nil }) }()
	<-held
	deadline := time.Now().Add(50 * time.Millisecond)
	go func() { time.Sleep(time.Until(deadline) + 20*time.Millisecond); close(release) }()
	if _, err := b.Bribe(entry, func() float64 { t.Fatal("expired lock wait used RNG"); return 0 }, time.Now, deadline); err == nil {
		t.Fatal("expired bribe committed")
	}
	if err := <-done; err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	if w.Players[1].Credits != 10000 || w.Sectors[8].Defense.Fighters != 100 {
		t.Fatal("expired resources changed")
	}
}

func TestAdjacentBribeMineAftermathFailureRollsBackEntryAndPayment(t *testing.T) {
	s, b := bribeFixture(t)
	if err := s.Update(func(w *game.World) error {
		w.Players[1].Sector = 7
		w.Sectors[7].Warps = []int{8}
		w.Sectors[8].Minefield = []game.MineLayer{{Count: 1}}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	entry, err := b.PrepareBribeAt(8, 300, bribeDeadline())
	if err != nil {
		t.Fatal(err)
	}
	before, _ := os.ReadFile(filepath.Join(s.Dir, "world.json"))
	draws := 0
	_, err = b.Bribe(entry, func() float64 {
		draws++
		if draws > 3 {
			return math.NaN()
		}
		return .5
	}, time.Now, bribeDeadline())
	after, _ := os.ReadFile(filepath.Join(s.Dir, "world.json"))
	if err == nil || draws != 4 || string(before) != string(after) || b.ship.mercenaryHostile {
		t.Fatal("failed mine aftermath committed entry/payment", draws, err)
	}
}
