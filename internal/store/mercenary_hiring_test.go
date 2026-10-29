package store

import (
	"errors"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestMercenaryHiringAtomicDailyPersistence(t *testing.T) {
	s := create(t) // Eight sectors: only sector 8 is eligible.
	if err := s.Update(func(w *game.World) error { w.Ports[2].Treasury = 1990; return nil }); err != nil {
		t.Fatal(err)
	}
	now := time.Now().Add(24 * time.Hour)
	before, _ := os.ReadFile(s.Dir + "/world.json")
	abort := errors.New("later daily phase failed")
	if err := s.Update(func(w *game.World) error { w.Maintain(now); return abort }); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("aborted hiring saved force, taxes or date")
	}
	// Validation failure after hiring must also leave the published file intact.
	if err := s.Update(func(w *game.World) error { w.Maintain(now); w.Ports[2].Treasury = -1; return nil }); err == nil {
		t.Fatal("invalid daily world accepted")
	}
	after, _ = os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("invalid daily world partially saved")
	}
	var wg sync.WaitGroup
	errs := make(chan error, 8)
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			errs <- s.Update(func(w *game.World) error { w.Maintain(now); return nil })
		}()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	// Reload through a fresh store, as a reconnect does.
	w, err := (Store{Dir: s.Dir}).View()
	if err != nil {
		t.Fatal(err)
	}
	d := w.Sectors[8].Defense
	if d == nil || d.Owner != game.MercenaryOwner || d.Fighters != 1 || w.Ports[2].Treasury != 1791 {
		t.Fatal("daily hire duplicated or not persisted", d, w.Ports[2].Treasury)
	}
	// A full eligible universe still commits the next day's tax exactly once.
	if err := s.Update(func(w *game.World) error { w.Maintain(now.Add(24 * time.Hour)); return nil }); err != nil {
		t.Fatal(err)
	}
	w, _ = s.View()
	if w.Ports[2].Treasury != 1612 || *w.Sectors[8].Defense != *d {
		t.Fatal("capacity exhaustion lost taxes or overwrote a group")
	}
}

func TestMercenaryHiringCommittedDurabilityWarningDoesNotReplay(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error { w.Ports[2].Treasury = 1000; return nil }); err != nil {
		t.Fatal(err)
	}
	now := time.Now().Add(24 * time.Hour)
	s.syncDirectory = func(string) error { return errors.New("directory sync failed") }
	err := s.Update(func(w *game.World) error { w.Maintain(now); return nil })
	var committed *DurabilityError
	if !errors.As(err, &committed) {
		t.Fatal("expected committed warning", err)
	}
	s.syncDirectory = nil
	if err := s.Update(func(w *game.World) error {
		if w.Maintain(now) {
			t.Fatal("committed maintenance repeated")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	if w.Ports[2].Treasury != 900 || w.Sectors[8].Defense.Fighters != 1 {
		t.Fatal("committed hire or tax was replayed")
	}
}
