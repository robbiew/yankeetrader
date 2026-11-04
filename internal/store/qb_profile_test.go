package store

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"
)

func qbStore(t *testing.T) (Store, Store, time.Time) {
	t.Helper()
	at := time.Now().UTC()
	w, err := game.NewQB36(at, 36, 0xc805, "2027-01-01")
	if err != nil {
		t.Fatal(err)
	}
	p, err := w.Join("private", "Winner")
	if err != nil {
		t.Fatal(err)
	}
	n := 20
	w.GenesisPorts = &n
	for i := 2; i <= 21; i++ {
		w.Ports[i].Owner = p.ID
	}
	s := Store{Dir: t.TempDir()}
	if err = s.Create(w); err != nil {
		t.Fatal(err)
	}
	return s, s.ForShip(p.ID, p.ShipGeneration, w.Season), at
}
func TestQBStoreResetTransactionsAndArchiveRestore(t *testing.T) {
	for _, kind := range []string{"genesis", "admin"} {
		for _, mode := range []string{"success", "committed", "before-save", "provenance"} {
			t.Run(kind+"/"+mode, func(t *testing.T) {
				s, b, at := qbStore(t)
				old, err := s.View()
				if err != nil {
					t.Fatal(err)
				}
				deadline := time.Now().Add(time.Minute)
				entry, err := b.PrepareGenesis(func() time.Time { return at }, deadline)
				if err != nil {
					t.Fatal(err)
				}
				if mode == "provenance" {
					if err = s.Update(func(w *game.World) error { w.QBRecipe.SourceSHA256 = strings.Repeat("0", 64); return nil }); err != nil {
						t.Fatal(err)
					}
				}
				before := travelBytes(t, s)
				archive := filepath.Join(t.TempDir(), "archive.json")
				if mode == "committed" {
					s.syncDirectory = func(string) error { return errors.New("injected directory sync failure") }
					b.syncDirectory = s.syncDirectory
				}
				// A nonempty directory at the save target forces replacement failure after generation.
				block := func() {
					if err := os.Rename(s.Dir+"/world.json", s.Dir+"/backup"); err != nil {
						t.Fatal(err)
					}
					if err := os.Mkdir(s.Dir+"/world.json", 0700); err != nil {
						t.Fatal(err)
					}
					if err := os.WriteFile(s.Dir+"/world.json/block", []byte("x"), 0600); err != nil {
						t.Fatal(err)
					}
				}
				var season uint64
				if kind == "genesis" {
					now := func() time.Time {
						if mode == "before-save" {
							block()
						}
						return at.Add(time.Second)
					}
					receipt, e := b.ResetSeason(entry, now, deadline)
					season, err = receipt.NewSeason, e
				} else {
					if mode == "before-save" { // Archive failure is pre-replacement and must leave the world intact.
						archive = filepath.Join(s.Dir, "missing", "archive.json")
					}
					receipt, e := s.ExportSeason(archive, 1, at.Add(time.Second), 77)
					season, err = receipt.NewSeason, e
				}
				if kind == "genesis" && mode == "before-save" {
					os.RemoveAll(s.Dir + "/world.json")
					if e := os.Rename(s.Dir+"/backup", s.Dir+"/world.json"); e != nil {
						t.Fatal(e)
					}
				}
				committed := mode == "success" || mode == "committed"
				var durable *DurabilityError
				if mode == "success" && err != nil || mode == "committed" && !errors.As(err, &durable) || !committed && err == nil {
					t.Fatal("incorrect commit result", season, err)
				}
				saved, e := s.View()
				if e != nil {
					t.Fatal(e)
				}
				if committed {
					if season != 2 || saved.Season != 2 || len(saved.SeasonResults) != 1 || !reflect.DeepEqual(saved.QBRecipe, old.QBRecipe) || saved.LastMaintenance != at.Add(time.Second).Format("2006-01-02") {
						t.Fatal("committed reset lost provenance/history")
					}
					for id, p := range saved.Ports {
						op := old.Ports[id]
						if p.Sector != op.Sector || p.Name != op.Name || p.Production != op.Production || p.Coefficient != op.Coefficient {
							t.Fatal("layout changed")
						}
					}
					if _, e = b.View(); !errors.Is(e, game.ErrSeasonChanged) {
						t.Fatal("old login retained", e)
					}
				} else if season != 0 || !bytes.Equal(before, travelBytes(t, s)) {
					t.Fatal("pre-commit failure changed save")
				}
				if kind == "admin" && committed {
					raw, e := os.ReadFile(archive)
					if e != nil {
						t.Fatal(e)
					}
					var a SeasonArchive
					if e = json.Unmarshal(raw, &a); e != nil {
						t.Fatal(e)
					}
					sum := sha256.Sum256(a.World)
					if a.WorldSHA256 != hex.EncodeToString(sum[:]) {
						t.Fatal("archive checksum")
					}
					restore := Store{Dir: t.TempDir()}
					if e = os.WriteFile(filepath.Join(restore.Dir, "world.json"), a.World, 0600); e != nil {
						t.Fatal(e)
					}
					restored, e := restore.View()
					if e != nil || restored.Season != 1 || !reflect.DeepEqual(restored.QBRecipe, old.QBRecipe) {
						t.Fatal("restore lost recipe", e)
					}
					if _, e = s.ExportSeason(filepath.Join(t.TempDir(), "retry.json"), 1, at, 77); e == nil {
						t.Fatal("old season reset replayed")
					}
				}
				if kind == "genesis" {
					if _, e = b.ResetSeason(entry, func() time.Time { return at }, deadline); e == nil {
						t.Fatal("confirmation replayed")
					}
				}
			})
		}
	}
}

func TestQBGenesisConfirmationOwnsRecipeSnapshot(t *testing.T) {
	for _, mode := range []string{"recipe", "state"} {
		t.Run(mode, func(t *testing.T) {
			s, b, at := qbStore(t)
			deadline := time.Now().Add(time.Minute)
			entry, err := b.PrepareGenesis(func() time.Time { return at }, deadline)
			if err != nil {
				t.Fatal(err)
			}
			original, _ := json.Marshal(b.ship.genesisActive.QBRecipe)
			state := uint32(0xc805)
			date := "2026-11-02"
			if mode == "state" {
				state = 0x61b205
				date = "2027-01-01"
			}
			replacement, err := game.NewQB36(at, 36, state, date)
			if err != nil {
				t.Fatal(err)
			}
			if mode == "recipe" {
				*entry.QBRecipe = *replacement.QBRecipe
			} else {
				*entry.QBRecipe.State = state
				entry.QBRecipe.SourceSHA256 = replacement.QBRecipe.SourceSHA256
			}
			retained, _ := json.Marshal(b.ship.genesisActive.QBRecipe)
			if !bytes.Equal(original, retained) {
				t.Fatal("caller mutation changed stored confirmation recipe/state")
			}
			// Even changing the active world's provenance to match the altered caller
			// intent must not make that stale confirmation usable.
			if err = s.Update(func(w *game.World) error { w.QBRecipe = replacement.QBRecipe; return nil }); err != nil {
				t.Fatal(err)
			}
			before := travelBytes(t, s)
			receipt, err := b.ResetSeason(entry, func() time.Time { return at }, deadline)
			if err == nil || receipt.NewSeason != 0 || !bytes.Equal(before, travelBytes(t, s)) {
				t.Fatal("altered recipe bypassed sealed confirmation", err)
			}
		})
	}
}
