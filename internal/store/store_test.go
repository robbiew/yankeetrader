package store

import (
	"encoding/json"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"os"
	"os/exec"
	"sync"
	"testing"
	"time"
)

func create(t *testing.T) Store {
	t.Helper()
	s := Store{Dir: t.TempDir()}
	w, e := game.New(time.Now(), 36, 8)
	if e != nil {
		t.Fatal(e)
	}
	_, _ = w.Join("local:q", "Q")
	if e = s.Create(w); e != nil {
		t.Fatal(e)
	}
	return s
}
func TestRollbackAndRefuseOverwrite(t *testing.T) {
	s := create(t)
	before, _ := os.ReadFile(s.Dir + "/world.json")
	e := s.Update(func(w *game.World) error { w.Players[1].Credits = 0; return errors.New("abort") })
	if e == nil {
		t.Fatal("missing abort")
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("aborted transaction committed")
	}
	w, _ := s.View()
	if s.Create(w) == nil {
		t.Fatal("initialization overwrote world")
	}
	if e = s.Update(func(w *game.World) error { w.Players[1].Credits = -1; return nil }); e == nil {
		t.Fatal("invalid state committed")
	}
}
func TestConcurrentNodesDoNotLoseUpdates(t *testing.T) {
	s := create(t)
	var wg sync.WaitGroup
	errs := make(chan error, 40)
	for i := 0; i < 40; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- s.Update(func(w *game.World) error { w.Players[1].Credits++; return nil })
		}()
	}
	wg.Wait()
	close(errs)
	for e := range errs {
		if e != nil {
			t.Fatal(e)
		}
	}
	w, e := s.View()
	if e != nil || w.Players[1].Credits != 1045 {
		t.Fatalf("lost updates: %v %v", w, e)
	}
}
func TestMoneyPersistsOneCreditAndCorruptionIsNotReinitialized(t *testing.T) {
	s := create(t)
	_ = s.Update(func(w *game.World) error { w.Players[1].Credits = 100000000; return nil })
	for i := 0; i < 2; i++ {
		if e := s.Update(func(w *game.World) error { w.Players[1].Credits--; return nil }); e != nil {
			t.Fatal(e)
		}
	}
	w, e := s.View()
	if e != nil || w.Players[1].Credits != 99999998 {
		t.Fatal("small debit lost across reloads")
	}
	if e = os.WriteFile(s.Dir+"/world.json", []byte("{bad"), 0600); e != nil {
		t.Fatal(e)
	}
	if _, e = s.View(); e == nil {
		t.Fatal("corruption ignored")
	}
	if s.Create(w) == nil {
		t.Fatal("corruption overwritten")
	}
}
func TestProcessWorker(t *testing.T) {
	if os.Getenv("YT_STORE_WORKER") == "" {
		return
	}
	s := Store{Dir: os.Getenv("YT_STORE_DIR")}
	for i := 0; i < 10; i++ {
		if e := s.Update(func(w *game.World) error { w.Players[1].Credits++; return nil }); e != nil {
			t.Fatal(e)
		}
	}
}
func TestMultipleProcesses(t *testing.T) {
	s := create(t)
	var cmds []*exec.Cmd
	for i := 0; i < 3; i++ {
		c := exec.Command(os.Args[0], "-test.run=^TestProcessWorker$")
		c.Env = append(os.Environ(), "YT_STORE_WORKER=1", "YT_STORE_DIR="+s.Dir)
		if e := c.Start(); e != nil {
			t.Fatal(e)
		}
		cmds = append(cmds, c)
	}
	for _, c := range cmds {
		if e := c.Wait(); e != nil {
			t.Fatal(e)
		}
	}
	w, e := s.View()
	if e != nil || w.Players[1].Credits != 1035 {
		t.Fatal("cross-process lost update")
	}
}

func TestLockCrashWorker(t *testing.T) {
	if os.Getenv("YT_LOCK_CRASH") == "" {
		return
	}
	s := Store{Dir: os.Getenv("YT_STORE_DIR")}
	if e := s.locked(func() error {
		if e := os.WriteFile(s.Dir+"/ready", []byte("ready"), 0600); e != nil {
			return e
		}
		time.Sleep(time.Hour)
		return nil
	}); e != nil {
		t.Fatal(e)
	}
}
func TestKilledNodeDoesNotStrandWorldLock(t *testing.T) {
	s := create(t)
	c := exec.Command(os.Args[0], "-test.run=^TestLockCrashWorker$")
	c.Env = append(os.Environ(), "YT_LOCK_CRASH=1", "YT_STORE_DIR="+s.Dir)
	if e := c.Start(); e != nil {
		t.Fatal(e)
	}
	defer func() { _ = c.Process.Kill(); _ = c.Wait() }()
	deadline := time.Now().Add(5 * time.Second)
	for {
		if _, e := os.Stat(s.Dir + "/ready"); e == nil {
			break
		}
		if time.Now().After(deadline) {
			t.Fatal("child did not acquire lock")
		}
		time.Sleep(10 * time.Millisecond)
	}
	_ = c.Process.Kill()
	_ = c.Wait()
	done := make(chan error, 1)
	go func() { done <- s.Update(func(w *game.World) error { w.Players[1].Credits--; return nil }) }()
	select {
	case e := <-done:
		if e != nil {
			t.Fatal(e)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("dead process stranded lock")
	}
}

func TestVersionOneUpgradePreservesExistingPlayers(t *testing.T) {
	s := create(t)
	w, _ := s.View()
	w.NextRadio = 0
	w.Version = 1
	w.NextNews = 0
	for _, p := range w.Players {
		p.Cloak = 0
	}
	w.Planets = nil
	b, _ := json.Marshal(w)
	if e := os.WriteFile(s.Dir+"/world.json", b, 0600); e != nil {
		t.Fatal(e)
	}
	w, e := s.View()
	if e != nil {
		t.Fatal(e)
	}
	if w.Version != 12 || w.Planets == nil || w.Players[1].Credits != 1005 || w.Players[1].Identity != "local:q" {
		t.Fatal("migration changed existing player")
	}
	if e = s.Update(func(w *game.World) error { return nil }); e != nil {
		t.Fatal(e)
	}
	b, _ = os.ReadFile(s.Dir + "/world.json")
	var saved game.World
	_ = json.Unmarshal(b, &saved)
	if saved.Version != 12 || saved.Planets == nil {
		t.Fatal("migration not persisted")
	}
}
func TestPlanetTransfersSerializeAndRejectedActionsRollback(t *testing.T) {
	s := create(t)
	now := time.Now()
	var token string
	if e := s.Update(func(w *game.World) error {
		w.Players[1].Credits = 100000
		if e := w.CreatePlanet(1, "Home", now); e != nil {
			return e
		}
		if e := w.Land(1, now); e != nil {
			return e
		}
		token = w.Players[1].PlanetToken
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	var wg sync.WaitGroup
	errs := make(chan error, 20)
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- s.Update(func(w *game.World) error { planet := w.Planets[2]; return w.Bank(1, token, planet.Bank+1, now) })
		}()
	}
	wg.Wait()
	close(errs)
	for e := range errs {
		if e != nil {
			t.Fatal(e)
		}
	}
	w, e := s.View()
	if e != nil {
		t.Fatal(e)
	}
	if w.Players[1].Credits != 74980 || w.Planets[2].Bank != 20 {
		t.Fatal("concurrent bank transfers lost or minted credits")
	}
	before, _ := os.ReadFile(s.Dir + "/world.json")
	if e = s.Update(func(w *game.World) error { return w.Bank(1, token, MaxTestInvalidBank, now.Add(time.Hour)) }); e == nil {
		t.Fatal("invalid transfer accepted")
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("failed transfer committed production or money")
	}
}

const MaxTestInvalidBank int64 = 100000000

func TestConcurrentPlanetPickupCannotDuplicateStock(t *testing.T) {
	s := create(t)
	now := time.Now()
	tokens := map[int]string{}
	if e := s.Update(func(w *game.World) error {
		w.Players[1].Credits = 100000
		if e := w.CreatePlanet(1, "Shared", now); e != nil {
			return e
		}
		w.Planets[2].Ground = 0
		other, e := w.Join("local:other", "Other")
		if e != nil {
			return e
		}
		for _, id := range []int{1, other.ID} {
			if e = w.Land(id, now); e != nil {
				return e
			}
			tokens[id] = w.Players[id].PlanetToken
		}
		return nil
	}); e != nil {
		t.Fatal(e)
	}
	var wg sync.WaitGroup
	errs := make(chan error, 2)
	for id, token := range tokens {
		wg.Add(1)
		go func(id int, token string) {
			defer wg.Done()
			errs <- s.Update(func(w *game.World) error { return w.TakeAll(id, token, now) })
		}(id, token)
	}
	wg.Wait()
	close(errs)
	for e := range errs {
		if e != nil {
			t.Fatal(e)
		}
	}
	w, e := s.View()
	if e != nil {
		t.Fatal(e)
	}
	p := w.Planets[2]
	if w.Players[1].Fighters+w.Players[2].Fighters+int64(p.Fighters) != 80 {
		t.Fatal("fighters duplicated")
	}
	for i := 0; i < 3; i++ {
		if w.Players[1].Cargo[i]+w.Players[2].Cargo[i]+int64(p.Cargo[i]) != 10 {
			t.Fatal("cargo duplicated")
		}
	}
}
