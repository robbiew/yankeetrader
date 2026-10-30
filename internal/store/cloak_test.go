package store

import (
	"encoding/json"
	"github.com/robbiew/yankeetrader/internal/game"
	"os"
	"testing"
)

func TestCloakPersistsAndLegacyUpgradeDoesNotInventEnergy(t *testing.T) {
	s := create(t)
	if err := s.Update(func(w *game.World) error { w.Players[1].Cloak = .37; return nil }); err != nil {
		t.Fatal(err)
	}
	w, err := s.View()
	if err != nil || w.Players[1].Cloak != .37 {
		t.Fatal(w, err)
	}
	w.NextRadio = 0
	w.Version = 5
	w.Season = 0
	w.GenerationSeed = nil
	w.NextBattleReport = 0 // This fixture represents a pre-report save.
	w.NextNews = 0
	w.Players[1].Cloak = 0
	data, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	if err = os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	current, err := s.View()
	if err != nil || current.Version != game.WorldVersion || current.Players[1].Cloak != 0 {
		t.Fatal(current, err)
	}
	unchanged, _ := os.ReadFile(path)
	if string(unchanged) != string(data) {
		t.Fatal("read rewrote migration")
	}
	if err = s.Update(func(w *game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	saved, _ := os.ReadFile(path)
	var header struct{ Version int }
	json.Unmarshal(saved, &header)
	if header.Version != game.WorldVersion {
		t.Fatal("migration not saved")
	}
	w.NextRadio = 0
	w.Version = 5
	w.Season = 0
	w.GenerationSeed = nil
	w.NextBattleReport = 0 // This fixture represents a pre-report save.
	w.NextNews = 0
	w.Players[1].Cloak = .1
	data, _ = json.Marshal(w)
	os.WriteFile(path, data, 0600)
	if _, err = s.View(); err == nil {
		t.Fatal("malformed legacy cloak accepted")
	}
}
