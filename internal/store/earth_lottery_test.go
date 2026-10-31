package store

import (
	"bytes"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func paidStore(t *testing.T) (Store, Store, time.Time, string) {
	t.Helper()
	s := create(t)
	w, _ := s.View()
	at := w.Created
	token := ""
	if err := s.Update(func(w *game.World) error {
		p := w.Players[1]
		p.Credits = 100000
		if err := w.Dock(1, at); err != nil {
			return err
		}
		token = p.DockToken
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	return s, s.ForShip(1, 0, 1), at, token
}
func jackpotDigit() (int, error) { return 1, nil }
func TestPaidLotteryStoreRollbackDurabilityAndReplay(t *testing.T) {
	for _, mode := range []string{"entropy", "deadline", "save", "committed"} {
		t.Run(mode, func(t *testing.T) {
			s, b, at, token := paidStore(t)
			clock := func() time.Time { return at }
			deadline := time.Now().Add(time.Minute)
			entry, err := b.PrepareLottery(token, "111111", clock, deadline)
			if err != nil {
				t.Fatal(err)
			}
			before := travelBytes(t, s)
			draw := jackpotDigit
			switch mode {
			case "entropy":
				draw = func() (int, error) { return 0, errors.New("no entropy") }
			case "deadline":
				deadline = time.Now().Add(20 * time.Millisecond)
				draw = func() (int, error) { time.Sleep(10 * time.Millisecond); return 1, nil }
			case "save":
				clock = func() time.Time {
					if err := os.Rename(filepath.Join(s.Dir, "world.json"), filepath.Join(s.Dir, "backup")); err != nil {
						t.Fatal(err)
					}
					if err := os.Mkdir(filepath.Join(s.Dir, "world.json"), 0700); err != nil {
						t.Fatal(err)
					}
					return at
				}
			case "committed":
				b.syncDirectory = func(string) error { return errors.New("directory sync") }
			}
			out, err := b.PlayLottery(entry, draw, clock, deadline)
			if err == nil {
				t.Fatal("fault accepted")
			}
			if mode == "save" {
				if e := os.Remove(filepath.Join(s.Dir, "world.json")); e != nil {
					t.Fatal(e)
				}
				if e := os.Rename(filepath.Join(s.Dir, "backup"), filepath.Join(s.Dir, "world.json")); e != nil {
					t.Fatal(e)
				}
			}
			var durable *DurabilityError
			if mode == "committed" {
				w, e := s.View()
				if e != nil {
					t.Fatal(e)
				}
				p := w.Players[1]
				if !errors.As(err, &durable) || p.Credits != 100099995 || p.LotterySequence != 1 || p.LotteryPlays != 1 || len(w.News) != 1 || w.News[0].LotteryPrize != 100000000 || out.Balance != p.Credits {
					t.Fatal("committed settlement lost", out, err)
				}
			} else if !bytes.Equal(before, travelBytes(t, s)) {
				t.Fatal("partial lottery persisted", err)
			}
			saved := travelBytes(t, s)
			if _, err = b.PlayLottery(entry, func() (int, error) { t.Error("replay drew digits"); return 1, nil }, func() time.Time { return at }, time.Now().Add(time.Minute)); err == nil || !bytes.Equal(saved, travelBytes(t, s)) {
				t.Fatal("nonce replay")
			}
		})
	}
}
func TestPaidLotteryConcurrentNetZeroAndIdentityBinding(t *testing.T) {
	s, a, at, token := paidStore(t)
	one := 1
	if err := s.Update(func(w *game.World) error {
		w.LotteryDailyLimit = &one
		w.Players[1].Credits = game.MaxMoney
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	clock := func() time.Time { return at }
	deadline := time.Now().Add(time.Minute)
	b := s.ForShip(1, 0, 1)
	ea, err := a.PrepareLottery(token, "111111", clock, deadline)
	if err != nil {
		t.Fatal(err)
	}
	eb, err := b.PrepareLottery(token, "111111", clock, deadline)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = b.PlayLottery(ea, jackpotDigit, clock, deadline); err == nil {
		t.Fatal("cross-login nonce")
	}
	altered := ea
	altered.Ticket = "222222"
	if _, err = a.PlayLottery(altered, jackpotDigit, clock, deadline); err == nil {
		t.Fatal("altered ticket")
	}
	var wg sync.WaitGroup
	var draws atomic.Int32
	results := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			bound, entry := a, ea
			if i%2 == 1 {
				bound, entry = b, eb
			}
			_, e := bound.PlayLottery(entry, func() (int, error) { draws.Add(1); return 1, nil }, clock, deadline)
			results <- e
		}(i)
	}
	wg.Wait()
	close(results)
	wins := 0
	for e := range results {
		if e == nil {
			wins++
		}
	}
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	p := w.Players[1]
	if wins != 1 || draws.Load() != 6 || p.Credits != game.MaxMoney || p.LotteryPlays != 1 || p.LotterySequence != 1 || len(w.News) != 1 || w.News[0].LotteryPrize != 5 {
		t.Fatal("concurrent replay", wins, draws.Load(), p)
	}
	if _, err = s.ForShip(1, 0, 1).PrepareLottery(token, "111111", clock, deadline); err == nil {
		t.Fatal("reconnect quota reset")
	}
}
func TestPaidLotteryCancelledStaleAndPostLockDeadlines(t *testing.T) {
	for _, mode := range []string{"cancel", "new-attempt", "ship", "day", "prepare-lock", "commit-lock"} {
		t.Run(mode, func(t *testing.T) {
			s, b, at, token := paidStore(t)
			clock := func() time.Time { return at }
			deadline := time.Now().Add(time.Minute)
			entry, err := b.PrepareLottery(token, "111111", clock, deadline)
			if err != nil {
				t.Fatal(err)
			}
			switch mode {
			case "cancel":
				b.CancelLottery(entry)
			case "new-attempt":
				_, _ = b.PrepareLottery(token, "000000", clock, deadline)
			case "ship":
				if err = s.Update(func(w *game.World) error { w.Players[1].ShipGeneration++; return nil }); err != nil {
					t.Fatal(err)
				}
			case "day":
				clock = func() time.Time { return at.AddDate(0, 0, 1) }
			}
			before := travelBytes(t, s)
			if mode == "prepare-lock" || mode == "commit-lock" {
				locked := make(chan struct{})
				release := make(chan struct{})
				done := make(chan error, 1)
				go func() { done <- s.locked(func() error { close(locked); <-release; return nil }) }()
				<-locked
				deadline = time.Now().Add(20 * time.Millisecond)
				result := make(chan error, 1)
				go func() {
					if mode == "prepare-lock" {
						_, e := b.PrepareLottery(token, "000000", clock, deadline)
						result <- e
					} else {
						_, e := b.PlayLottery(entry, func() (int, error) { t.Error("expired draw"); return 0, nil }, clock, deadline)
						result <- e
					}
				}()
				time.Sleep(40 * time.Millisecond)
				close(release)
				if e := <-done; e != nil {
					t.Fatal(e)
				}
				err = <-result
			} else {
				_, err = b.PlayLottery(entry, func() (int, error) { t.Error("invalid attempt drew"); return 0, nil }, clock, deadline)
			}
			if err == nil || !bytes.Equal(before, travelBytes(t, s)) {
				t.Fatal("invalid attempt saved", mode, err)
			}
		})
	}
}
func TestPaidLotteryMigrationReadOnlyThenWrite(t *testing.T) {
	s, _, _, _ := paidStore(t)
	w, err := s.View()
	if err != nil {
		t.Fatal(err)
	}
	w.Version = 21
	w.Season = 0
	w.GenerationSeed = nil
	raw, err := marshalHistoricalWorld(w)
	if err != nil {
		t.Fatal(err)
	}
	raw = append(raw, '\n')
	path := filepath.Join(s.Dir, "world.json")
	if err = os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	loaded, err := s.View()
	if err != nil || loaded.Version != game.WorldVersion || loaded.Players[1].LotterySequence != 0 {
		t.Fatal(loaded, err)
	}
	saved, _ := os.ReadFile(path)
	if !bytes.Equal(raw, saved) {
		t.Fatal("read rewrote save")
	}
	if err = s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	saved, _ = os.ReadFile(path)
	var upgraded game.World
	if err = json.Unmarshal(saved, &upgraded); err != nil || upgraded.Version != game.WorldVersion || upgraded.Players[1].Credits != 100000 {
		t.Fatal("migration gifts", err)
	}
}
