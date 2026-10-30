package store

import (
	"encoding/json"
	"errors"
	"os"
	"reflect"
	"sync"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func xannorShipStore(t *testing.T) (Store, time.Time) {
	t.Helper()
	now := time.Now().UTC()
	w, err := game.New(now, 36, 12)
	if err != nil {
		t.Fatal(err)
	}
	p, _ := w.Join("captain", "Captain")
	p.Sector, p.Cloak, p.Fighters, p.Shields, p.StoredScore, p.Turns, p.Mines = 10, 0, 0, 0, 4000, 37, 5
	w.Xannor = &game.XannorState{HQ: 8}
	for i := 8; i <= 12; i++ {
		w.Sectors[i].Warps = nil
	}
	w.Sectors[9].Warps = []int{10}
	w.Sectors[10].Warps = []int{8}
	w.Sectors[8].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 1}
	w.Sectors[9].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 100}
	for _, home := range []struct {
		id, sector, owner int
		kind, name        string
	}{{99, 11, game.MercenaryOwner, game.MercenaryHome, "Mercenary Base"}, {100, 8, game.XannorOwner, game.XannorHome, "Xannoron"}} {
		w.Planets[home.id] = &game.Planet{ID: home.id, Sector: home.sector, Owner: home.owner, FactionHome: home.kind, Name: home.name, Updated: now.Add(48 * time.Hour), Ground: 100, Bank: 1}
		w.Sectors[home.sector].Planet = home.id
	}
	s := Store{Dir: t.TempDir()}
	if err := s.Create(w); err != nil {
		t.Fatal(err)
	}
	return s, now.Add(24 * time.Hour)
}

func TestXannorShipMaintenanceAtomicDeathConcurrentReplayAndReload(t *testing.T) {
	s, next := xannorShipStore(t)
	stale := s.ForShip(1, 0, 1)
	path := s.Dir + "/world.json"
	before, _ := os.ReadFile(path)
	abort := errors.New("abort after death and report")
	if err := s.Update(func(w *game.World) error {
		w.Maintain(next)
		if w.Players[1].Death == nil {
			t.Fatal("fixture did not kill")
		}
		return abort
	}); !errors.Is(err, abort) {
		t.Fatal(err)
	}
	after, _ := os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("partial death/report saved on callback failure")
	}
	// A validation failure after the entire maintenance phase must also roll back.
	if err := s.Update(func(w *game.World) error { w.Maintain(next); w.NextBattleReport = 0; return nil }); err == nil {
		t.Fatal("invalid report saved")
	}
	after, _ = os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("failed validation partially saved death")
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
	p := saved.Players[1]
	if p.Death == nil || p.Death.Cause != "xannor" || p.Death.Killer != game.XannorOwner || p.Sector != 0 || p.ShipGeneration != 1 || p.Mines != 0 || p.Shields != 0 || len(p.BattleReports) != 1 || !p.BattleReports[0].Unread || len(saved.News) != 1 || saved.NextBattleReport != 2 || saved.Sectors[8].Defense.Fighters != 101 {
		t.Fatal("atomic death lost attribution, force or reports", p)
	}
	if _, err := stale.View(); !errors.Is(err, game.ErrShipDestroyed) {
		t.Fatal("dead session survived", err)
	}
	before, _ = os.ReadFile(path)
	if err := s.Update(func(w *game.World) error {
		if w.Maintain(next) || w.Maintain(next.Add(-time.Hour)) {
			return errors.New("maintenance replay")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	after, _ = os.ReadFile(path)
	if string(before) != string(after) {
		t.Fatal("same-day/rollback changed aftermath")
	}
	if err := s.Update(func(w *game.World) error { return w.LoginShip(1, next) }); err != nil {
		t.Fatal(err)
	}
	if _, err := stale.View(); !errors.Is(err, game.ErrShipChanged) {
		t.Fatal("old generation survived replacement", err)
	}
	live := s.ForShip(1, 2, 1)
	if err := live.AcknowledgeBattleReport(1); err != nil {
		t.Fatal(err)
	}
	current, _ := s.View()
	if current.Players[1].BattleReports[0].Unread || current.Players[1].Turns != 500 {
		t.Fatal("report read changed replacement")
	}
}

func TestXannorReportAcknowledgementIsBoundAndDoesNotBypassEncounters(t *testing.T) {
	s, next := xannorShipStore(t)
	if err := s.Update(func(w *game.World) error {
		w.Maintain(next)
		if err := w.LoginShip(1, next); err != nil {
			return err
		}
		other, _ := w.Join("other", "Other")
		other.Sector = 1
		w.Players[1].Sector = 9
		w.Sectors[9].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 37}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	bound := s.ForShip(1, 2, 1)
	wrong := s.ForShip(2, 0, 1)
	if err := wrong.AcknowledgeBattleReport(1); err == nil {
		t.Fatal("wrong recipient read report")
	}
	if err := s.AcknowledgeBattleReport(1); err == nil {
		t.Fatal("unbound read accepted")
	}
	if err := bound.Update(func(w *game.World) error { w.Players[1].Credits++; return nil }); !errors.Is(err, game.ErrDefenseEncounter) {
		t.Fatal("encounter gate bypass", err)
	}
	before, _ := s.View()
	assets := *before.Players[1]
	if err := bound.AcknowledgeBattleReport(1); err != nil {
		t.Fatal(err)
	}
	after, _ := s.View()
	assets.BattleReports[0].Unread = false
	if !reflect.DeepEqual(assets, *after.Players[1]) {
		t.Fatal("report acknowledgement changed assets")
	}
}

func TestVersionFourteenReportMigrationAndFutureStateRejection(t *testing.T) {
	s, _ := xannorShipStore(t)
	w, _ := s.View()
	w.Version = 14
	w.Season = 0
	w.GenerationSeed = nil
	w.NextBattleReport = 0
	raw, _ := json.Marshal(w)
	path := s.Dir + "/world.json"
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	upgraded, err := s.View()
	if err != nil || upgraded.Version != game.WorldVersion || upgraded.NextBattleReport != 1 || len(upgraded.Players[1].BattleReports) != 0 {
		t.Fatal("migration", err)
	}
	unchanged, _ := os.ReadFile(path)
	if string(unchanged) != string(raw) {
		t.Fatal("read-only migration rewrote save")
	}
	if err := s.Update(func(*game.World) error { return nil }); err != nil {
		t.Fatal(err)
	}
	for _, mode := range []string{"counter", "report", "death", "news"} {
		candidate, _ := s.View()
		candidate.Version = 14
		candidate.Season = 0
		candidate.GenerationSeed = nil
		candidate.NextBattleReport = 0
		switch mode {
		case "counter":
			candidate.NextBattleReport = 1
		case "report":
			candidate.Players[1].BattleReports = []game.BattleReport{{ID: 1}}
		case "death":
			candidate.Players[1].Death = &game.Death{Cause: "xannor"}
		case "news":
			candidate.News = []game.NewsEvent{{Kind: game.NewsXannorDeath}}
		}
		bad, _ := json.Marshal(candidate)
		if err := os.WriteFile(path, bad, 0600); err != nil {
			t.Fatal(err)
		}
		if _, err := s.View(); err == nil {
			t.Fatal("v14 accepted future battle state", mode)
		}
		if err := os.WriteFile(path, raw, 0600); err != nil {
			t.Fatal(err)
		}
	}
}

func TestXannorShipCommittedDurabilityFailureDoesNotReplay(t *testing.T) {
	s, next := xannorShipStore(t)
	s.syncDirectory = func(string) error { return errors.New("simulated directory sync failure") }
	err := s.Update(func(w *game.World) error { w.Maintain(next); return nil })
	var committed *DurabilityError
	if !errors.As(err, &committed) {
		t.Fatal("expected committed durability error", err)
	}
	normal := Store{Dir: s.Dir}
	if err := normal.Update(func(w *game.World) error {
		if w.Maintain(next) {
			t.Fatal("committed maintenance replayed")
		}
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	w, err := normal.View()
	if err != nil || len(w.Players[1].BattleReports) != 1 || w.NextBattleReport != 2 || len(w.News) != 1 {
		t.Fatal("retry duplicated committed aftermath", err)
	}
}

func TestXannorShipConcurrentFreshLoginKeepsOneDeathAndReport(t *testing.T) {
	for i := 0; i < 6; i++ {
		s, next := xannorShipStore(t)
		errs := make(chan error, 2)
		go func() { errs <- s.Update(func(w *game.World) error { w.Maintain(next); return nil }) }()
		go func() { errs <- s.Update(func(w *game.World) error { return w.LoginShip(1, next) }) }()
		for j := 0; j < 2; j++ {
			if err := <-errs; err != nil {
				t.Fatal(err)
			}
		}
		w, err := s.View()
		if err != nil {
			t.Fatal(err)
		}
		p := w.Players[1]
		if len(p.BattleReports) != 1 || w.NextBattleReport != 2 || len(w.News) != 1 {
			t.Fatal("login race duplicated aftermath")
		}
		if p.Death != nil {
			if p.ShipGeneration != 1 || p.Credits != 0 || p.Sector != 0 {
				t.Fatal("invalid dead race result")
			}
		} else if p.ShipGeneration != 2 || p.Sector != 1 || p.Credits != 1005 {
			t.Fatal("invalid replaced race result")
		}
	}
}
