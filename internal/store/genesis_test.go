package store

import (
	"bytes"
	"encoding/json"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"testing"
	"time"
)

func genesisStore(t *testing.T) (Store, Store, time.Time) {
	t.Helper()
	at := time.Now().UTC()
	w, err := game.New(at, 36, 32)
	if err != nil {
		t.Fatal(err)
	}
	_, _ = w.Join("private", "Winner")
	_, _ = w.Join("other", "Other")
	n := 20
	w.GenesisPorts = &n
	for i := 2; i <= 21; i++ {
		w.Ports[i].Owner = 1
	}
	s := Store{Dir: t.TempDir()}
	if err = s.Create(w); err != nil {
		t.Fatal(err)
	}
	return s, s.ForShip(1, 0, w.Season), at
}
func TestGenesisStoreAtomicResetDurabilityAndReplay(t *testing.T) {
	for _, mode := range []string{"success", "committed", "save-failure", "expired", "ownership", "cancel", "altered"} {
		t.Run(mode, func(t *testing.T) {
			s, b, at := genesisStore(t)
			deadline := time.Now().Add(time.Minute)
			now := func() time.Time { return at }
			entry, err := b.PrepareGenesis(now, deadline)
			if err != nil {
				t.Fatal(err)
			}
			inode, _ := os.Stat(filepath.Join(s.Dir, "world.lock"))
			before := travelBytes(t, s)
			switch mode {
			case "committed":
				b.syncDirectory = func(string) error { return errors.New("injected directory sync failure") }
			case "save-failure":
				now = func() time.Time {
					if err := os.Rename(s.Dir+"/world.json", s.Dir+"/backup"); err != nil {
						t.Fatal(err)
					}
					if err := os.Mkdir(s.Dir+"/world.json", 0700); err != nil {
						t.Fatal(err)
					}
					return at
				}
			case "expired":
				now = func() time.Time { return at.Add(game.GenesisQuoteLifetime) }
			case "ownership":
				if err := s.Update(func(w *game.World) error { w.Ports[2].Owner = 0; return nil }); err != nil {
					t.Fatal(err)
				}
				before = travelBytes(t, s)
			case "cancel":
				b.CancelGenesis(entry)
			case "altered":
				entry.Ports[0] = 32
			}
			out, err := b.ResetSeason(entry, now, deadline)
			if mode == "save-failure" {
				_ = os.Remove(s.Dir + "/world.json")
				if e := os.Rename(s.Dir+"/backup", s.Dir+"/world.json"); e != nil {
					t.Fatal(e)
				}
			}
			committed := mode == "success" || mode == "committed"
			var durable *DurabilityError
			if mode == "success" && err != nil || mode == "committed" && !errors.As(err, &durable) || !committed && err == nil {
				t.Fatal(mode, err)
			}
			loaded, e := s.View()
			if e != nil {
				t.Fatal(e)
			}
			if committed {
				if out.NewSeason != 2 || loaded.Season != 2 || len(loaded.SeasonResults) != 1 || len(loaded.Players) != 0 {
					t.Fatal("partial commit", out, loaded)
				}
			} else {
				if !bytes.Equal(before, travelBytes(t, s)) || out.NewSeason != 0 {
					t.Fatal("rollback changed world or false receipt", out)
				}
			}
			afterInode, _ := os.Stat(s.Dir + "/world.lock")
			if !os.SameFile(inode, afterInode) {
				t.Fatal("lock inode replaced")
			}
			if committed {
				if _, e = b.View(); !errors.Is(e, game.ErrSeasonChanged) {
					t.Fatal(e)
				}
			}
			if _, e = b.ResetSeason(entry, func() time.Time { return at }, deadline); e == nil {
				t.Fatal("confirmation replay")
			}
		})
	}
}
func TestGenesisCompetingLoginsCommitOneResult(t *testing.T) {
	s, a, at := genesisStore(t)
	b := s.ForShip(1, 0, 1)
	deadline := time.Now().Add(time.Minute)
	now := func() time.Time { return at }
	ea, e := a.PrepareGenesis(now, deadline)
	if e != nil {
		t.Fatal(e)
	}
	eb, e := b.PrepareGenesis(now, deadline)
	if e != nil {
		t.Fatal(e)
	}
	var wg sync.WaitGroup
	results := make(chan error, 2)
	for _, p := range []struct {
		b Store
		e game.GenesisIntent
	}{{a, ea}, {b, eb}} {
		wg.Add(1)
		go func(b Store, e game.GenesisIntent) {
			defer wg.Done()
			_, err := b.ResetSeason(e, now, deadline)
			results <- err
		}(p.b, p.e)
	}
	wg.Wait()
	close(results)
	wins := 0
	for e := range results {
		if e == nil {
			wins++
		} else if !errors.Is(e, game.ErrSeasonChanged) {
			t.Fatal(e)
		}
	}
	w, _ := s.View()
	if wins != 1 || w.Season != 2 || len(w.SeasonResults) != 1 {
		t.Fatal(wins, w)
	}
}
func TestGenesisOldSessionCannotAccessReusedIdentity(t *testing.T) {
	s, b, at := genesisStore(t)
	deadline := time.Now().Add(time.Minute)
	now := func() time.Time { return at }
	entry, e := b.PrepareGenesis(now, deadline)
	if e != nil {
		t.Fatal(e)
	}
	// Simulate a login paused after its authenticated transaction and before binding.
	var id int
	var generation, epoch uint64
	if e = s.Update(func(w *game.World) error {
		id = 1
		generation = w.Players[id].ShipGeneration
		epoch = w.Season
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	if _, e = b.ResetSeason(entry, now, deadline); e != nil {
		t.Fatal(e)
	}
	if e = s.Update(func(w *game.World) error {
		p, err := w.Join("entirely-new-person", "New Person")
		if err != nil {
			return err
		}
		if p.ID != id || p.ShipGeneration != generation {
			t.Fatal("incarnation not reused")
		}
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	old := s.ForShip(id, generation, epoch)
	before := travelBytes(t, s)
	checks := map[string]func() error{
		"view":     func() error { _, e := old.View(); return e },
		"mutation": func() error { return old.Update(func(w *game.World) error { t.Fatal("old callback ran"); return nil }) },
		"score":    func() error { return old.RefreshScoresOnLogout(deadline) },
		"radio":    func() error { return old.AcknowledgeRadio(1) },
		"battle":   func() error { return old.AcknowledgeBattleReport(1) },
		"spy-ack":  func() error { return old.AcknowledgeSpy(1) },
		"spy-view": func() error { _, _, e := old.SpySnapshot(false); return e },
		"spy-hire": func() error { return old.HireSpies("", []int{1}, now, deadline) },
		"spied-mutation": func() error {
			return old.UpdateWithSpies(func(w *game.World) error { t.Fatal("old callback ran"); return nil }, at, deadline)
		},
		"genesis": func() error { _, e := old.PrepareGenesis(now, deadline); return e },
		"lottery": func() error { _, e := old.PrepareLottery("", "111111", now, deadline); return e },
		"warp":    func() error { _, e := old.PrepareWarp(deadline); return e },
	}
	for name, check := range checks {
		if e := check(); !errors.Is(e, game.ErrSeasonChanged) {
			t.Fatalf("%s: %v", name, e)
		}
	}
	if !bytes.Equal(before, travelBytes(t, s)) {
		t.Fatal("old login changed replacement")
	}
	if _, e = s.ForShip(id, generation, 2).View(); e != nil {
		t.Fatal("new login rejected", e)
	}
}
func TestGenesisPostWorldLockExpiryAndQuoteIsolation(t *testing.T) {
	s, b, at := genesisStore(t)
	now := func() time.Time { return at }
	entry, err := b.PrepareGenesis(now, time.Now().Add(time.Minute))
	if err != nil {
		t.Fatal(err)
	}
	locked := make(chan struct{})
	release := make(chan struct{})
	done := make(chan error, 1)
	go func() { done <- s.locked(func() error { close(locked); <-release; return nil }) }()
	<-locked
	deadline := time.Now().Add(30 * time.Millisecond)
	result := make(chan error, 1)
	before := travelBytesUnlocked(t, s)
	go func() { _, e := b.ResetSeason(entry, now, deadline); result <- e }()
	time.Sleep(60 * time.Millisecond)
	close(release)
	if e := <-done; e != nil {
		t.Fatal(e)
	}
	if e := <-result; e == nil {
		t.Fatal("wait extended deadline")
	}
	if !bytes.Equal(before, travelBytes(t, s)) {
		t.Fatal("expired reset committed")
	}
	entry, err = b.PrepareGenesis(now, time.Now().Add(time.Minute))
	if err != nil {
		t.Fatal(err)
	}
	entry.Ports[0] = 32
	if _, err = b.ResetSeason(entry, now, time.Now().Add(time.Minute)); err == nil {
		t.Fatal("caller altered saved quote through slice alias")
	}
}
func travelBytesUnlocked(t *testing.T, s Store) []byte {
	t.Helper()
	b, e := os.ReadFile(s.Dir + "/world.json")
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func TestGenesisVersion22MigrationNoResetOrBackfill(t *testing.T) {
	s, _, _ := genesisStore(t)
	w, _ := s.View()
	w.Version = 22
	w.Season = 0
	w.GenerationSeed = nil
	w.GenesisPorts = nil
	raw, _ := json.Marshal(w)
	if e := os.WriteFile(s.Dir+"/world.json", raw, 0600); e != nil {
		t.Fatal(e)
	}
	loaded, e := s.View()
	if e != nil || loaded.Season != 1 || loaded.Version != 23 || loaded.GenerationSeed != nil || loaded.GenesisPorts != nil || len(loaded.SeasonResults) != 0 || len(loaded.Players) != 2 {
		t.Fatal(loaded, e)
	}
	if !bytes.Equal(raw, travelBytes(t, s)) {
		t.Fatal("read migration wrote")
	}
	if e = s.Update(func(*game.World) error { return nil }); e != nil {
		t.Fatal(e)
	}
	if bytes.Equal(raw, travelBytes(t, s)) {
		t.Fatal("write did not migrate")
	}
	w.Season = 1
	bad, _ := json.Marshal(w)
	_ = os.WriteFile(s.Dir+"/world.json", bad, 0600)
	if _, e = s.View(); e == nil {
		t.Fatal("legacy future state accepted")
	}
}
func TestGenesisCrashWorker(t *testing.T) {
	mode := os.Getenv("YT_GENESIS_CRASH")
	if mode == "" {
		return
	}
	s := Store{Dir: os.Getenv("YT_GENESIS_DIR")}
	w, e := s.View()
	if e != nil {
		t.Fatal(e)
	}
	at := w.Created
	b := s.ForShip(1, 0, w.Season)
	now := func() time.Time { return at }
	deadline := time.Now().Add(time.Minute)
	entry, e := b.PrepareGenesis(now, deadline)
	if e != nil {
		t.Fatal(e)
	}
	pause := func() {
		if e := os.WriteFile(s.Dir+"/ready", []byte("ready"), 0600); e != nil {
			t.Fatal(e)
		}
		select {}
	}
	if mode == "before" {
		now = func() time.Time { pause(); return at }
	} else {
		b.syncDirectory = func(string) error { pause(); return nil }
	}
	_, _ = b.ResetSeason(entry, now, deadline)
	t.Fatal("worker unexpectedly returned")
}
func TestGenesisProcessInterruptionBeforeAndAfterReplacement(t *testing.T) {
	for _, mode := range []string{"before", "after"} {
		t.Run(mode, func(t *testing.T) {
			s, _, _ := genesisStore(t)
			before := travelBytes(t, s)
			c := exec.Command(os.Args[0], "-test.run=^TestGenesisCrashWorker$")
			c.Env = append(os.Environ(), "YT_GENESIS_CRASH="+mode, "YT_GENESIS_DIR="+s.Dir)
			var output bytes.Buffer
			c.Stdout = &output
			c.Stderr = &output
			if e := c.Start(); e != nil {
				t.Fatal(e)
			}
			defer func() { _ = c.Process.Kill(); _ = c.Wait() }()
			until := time.Now().Add(8 * time.Second)
			for {
				if _, e := os.Stat(s.Dir + "/ready"); e == nil {
					break
				}
				if time.Now().After(until) {
					t.Fatal("worker stalled", output.String())
				}
				time.Sleep(10 * time.Millisecond)
			}
			_ = c.Process.Kill()
			_ = c.Wait()
			w, e := s.View()
			if e != nil {
				t.Fatal(e)
			}
			if mode == "before" {
				if !bytes.Equal(before, travelBytes(t, s)) || w.Season != 1 {
					t.Fatal("precommit interruption changed save")
				}
			} else if w.Season != 2 || len(w.SeasonResults) != 1 || len(w.Players) != 0 {
				t.Fatal("postrename interruption lost reset")
			}
		})
	}
}

func TestGenesisNewAttemptRevokesPriorConfirmationEvenOnFailure(t *testing.T) {
	_, b, at := genesisStore(t)
	deadline := time.Now().Add(time.Minute)
	now := func() time.Time { return at }
	entry, err := b.PrepareGenesis(now, deadline)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = b.PrepareGenesis(func() time.Time { return at.Add(-time.Minute) }, deadline); err == nil {
		t.Fatal("invalid clock accepted")
	}
	if _, err = b.ResetSeason(entry, now, deadline); err == nil {
		t.Fatal("old unanswered quote survived a new attempt")
	}
}
