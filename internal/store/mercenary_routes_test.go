package store

import (
	"errors"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestMercenaryRoutesAtomicConcurrentDailyMineConsumption(t *testing.T) {
	s := Store{Dir: t.TempDir()}
	created := time.Now().UTC()
	w, err := game.New(created, 36, 12)
	if err != nil {
		t.Fatal(err)
	}
	_, _ = w.Join("owner", "Captain")
	for id := 8; id <= 12; id++ {
		w.Sectors[id].Warps = nil
		if id < 12 {
			w.Sectors[id].Warps = []int{id + 1}
		}
	}
	w.Sectors[8].Defense = &game.SectorDefense{Owner: game.MercenaryOwner, Fighters: 1}
	w.Sectors[9].Minefield = []game.MineLayer{{Owner: 1, Count: 3}}
	if err := s.Create(w); err != nil {
		t.Fatal(err)
	}
	now := created.Add(24 * time.Hour)
	before, _ := os.ReadFile(s.Dir + "/world.json")
	abort := errors.New("abort route aftermath")
	if err := s.Update(func(w *game.World) error { w.Maintain(now); return abort }); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(s.Dir + "/world.json")
	if string(before) != string(after) {
		t.Fatal("aborted route published group removal, mine debit or date")
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
	w, err = (Store{Dir: s.Dir}).View()
	if err != nil {
		t.Fatal(err)
	}
	for _, sector := range w.Sectors {
		if sector.Defense != nil {
			t.Fatal("destroyed Mercenary force persisted")
		}
	}
	if len(w.Sectors[9].Minefield) != 1 || w.Sectors[9].Minefield[0] != (game.MineLayer{Owner: 1, Count: 2}) || w.Players[1].Death != nil {
		t.Fatal("mine replay, source loss or invented player death", w.Sectors[9].Minefield)
	}
}
