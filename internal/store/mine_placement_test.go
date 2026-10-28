package store

import (
	"encoding/json"
	"errors"
	"os"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestMinePlacementGraceAtomicPersistence(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error {
		w.Players[1].Sector, w.Players[1].Mines = 8, 10
		w.Sectors[8].Warps = []int{7}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, _ := s.View()
	bound := s.ForShip(1, w.Players[1].ShipGeneration)
	intent, _ := w.PrepareMinePlacement(1, 5)
	abort := errors.New("abort placement")
	if err := bound.Update(func(w *game.World) error {
		if _, err := w.CommitMinePlacement(intent); err != nil {
			return err
		}
		return abort
	}); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	w, _ = s.View()
	if w.Players[1].Mines != 10 || w.Players[1].MineGraceSector != 0 || len(w.Sectors[8].Minefield) != 0 {
		t.Fatal("placement partly saved")
	}
	results := make(chan error, 2)
	for i := 0; i < 2; i++ {
		go func() {
			results <- bound.Update(func(w *game.World) error { _, err := w.CommitMinePlacement(intent); return err })
		}()
	}
	wins := 0
	for i := 0; i < 2; i++ {
		if <-results == nil {
			wins++
		}
	}
	w, _ = s.View()
	if wins != 1 || w.Players[1].Mines != 5 || w.Players[1].MineGraceSector != 8 || w.HasMineEncounter(1) {
		t.Fatal("deployment replayed or grace not persisted", wins)
	}
	if err := bound.Update(func(w *game.World) error { return w.Move(1, 7) }); err != nil {
		t.Fatal("bound action guard prevented departure", err)
	}
	w, _ = s.View()
	if w.Players[1].MineGraceSector != 0 || w.Sectors[8].Minefield[0].Count != 5 {
		t.Fatal("departure failed to clear grace or consumed field")
	}
}

func TestVersionNineMineGraceUpgradeAndInvalidLegacyState(t *testing.T) {
	s := create(t)
	w, _ := s.View()
	w.NextRadio = 0
	w.Version = 9
	data, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	upgraded, err := s.View()
	if err != nil || upgraded.Version != 11 || upgraded.Players[1].MineGraceSector != 0 {
		t.Fatal("version-nine upgrade failed", err)
	}
	unchanged, _ := os.ReadFile(path)
	if string(data) != string(unchanged) {
		t.Fatal("read rewrote legacy save")
	}
	w.Players[1].Sector, w.Players[1].MineGraceSector = 8, 8
	data, _ = json.Marshal(w)
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := s.View(); err == nil {
		t.Fatal("version-nine save carried unversioned departure grace")
	}
}
