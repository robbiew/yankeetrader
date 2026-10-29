package store

import (
	"errors"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestXannorMobileAtomicMoveConcurrentDailyAndReload(t *testing.T) {
	now := time.Now().UTC()
	w, err := game.New(now, 36, 12)
	if err != nil {
		t.Fatal(err)
	}
	p, _ := w.Join("captain", "Captain")
	p.StoredScore = 4000
	w.Xannor = &game.XannorState{HQ: 8}
	w.Sectors[8].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 1}
	w.Sectors[9].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 100}
	w.Sectors[9].Warps = []int{8}
	s := Store{Dir: t.TempDir()}
	if err := s.Create(w); err != nil {
		t.Fatal(err)
	}
	path := s.Dir + "/world.json"
	before, _ := os.ReadFile(path)
	next := now.Add(24 * time.Hour)
	abort := errors.New("abort after mobile route")
	if err := s.Update(func(w *game.World) error { w.Maintain(next); return abort }); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("aborted movement published a partial departure/arrival")
	}
	var wg sync.WaitGroup
	errs := make(chan error, 6)
	for i := 0; i < 6; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); errs <- s.Update(func(w *game.World) error { w.Maintain(next); return nil }) }()
	}
	wg.Wait()
	close(errs)
	for err := range errs {
		if err != nil {
			t.Fatal(err)
		}
	}
	saved, err := (Store{Dir: s.Dir}).View()
	if err != nil {
		t.Fatal(err)
	}
	if saved.Version != game.WorldVersion || saved.Sectors[9].Defense != nil || saved.Sectors[8].Defense == nil || saved.Sectors[8].Defense.Owner != game.XannorOwner || saved.Sectors[8].Defense.Fighters != 101 || saved.Xannor.Reserve != 0 {
		t.Fatal("mobile route lost force, repeated splits or failed to persist")
	}
	before, _ = os.ReadFile(path)
	if err := s.Update(func(w *game.World) error {
		if w.Maintain(next) || w.Maintain(now) {
			return errors.New("phase repeated")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	after, _ = os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("daily replay/rollback changed deployed force")
	}
	if err := s.Update(func(w *game.World) error { w.Sectors[8].Defense.Fighters = game.MaxQuantity + 1; return nil }); err == nil {
		t.Fatal("invalid moved force published")
	}
	after, _ = os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("failed validation damaged moved group")
	}
}
