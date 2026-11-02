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
	"sync"
	"testing"
	"time"
)

func TestSeasonExportAndReset(t *testing.T) {
	s, _, at := genesisStore(t)
	before := travelBytes(t, s)
	w, _ := s.View()
	old := s.ForShip(1, w.Players[1].ShipGeneration, w.Season)
	inode, _ := os.Stat(filepath.Join(s.Dir, "world.lock"))
	path := filepath.Join(t.TempDir(), "season.json")
	receipt, err := s.ExportSeason(path, 0, at, 100)
	if err != nil || receipt.NewSeason != 0 {
		t.Fatal(receipt, err)
	}
	if !bytes.Equal(before, travelBytes(t, s)) {
		t.Fatal("export mutated world")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var archive SeasonArchive
	if err = json.Unmarshal(data, &archive); err != nil {
		t.Fatal(err)
	}
	sum := sha256.Sum256(archive.World)
	if archive.Format != 1 || hex.EncodeToString(sum[:]) != archive.WorldSHA256 {
		t.Fatal("bad archive hash")
	}
	var restored game.World
	if err = json.Unmarshal(archive.World, &restored); err != nil {
		t.Fatal(err)
	}
	if err = restored.Validate(); err != nil || restored.Players[1].Identity != w.Players[1].Identity {
		t.Fatal("incomplete snapshot", err)
	}
	info, _ := os.Stat(path)
	if info.Mode().Perm() != 0600 {
		t.Fatal("private archive permissions", info.Mode())
	}
	if _, err = s.ExportSeason(path, 1, at, 100); err == nil {
		t.Fatal("overwrote archive")
	}
	if !bytes.Equal(before, travelBytes(t, s)) {
		t.Fatal("failed archive reset world")
	}
	receipt, err = s.ExportSeason(filepath.Join(t.TempDir(), "reset.json"), 1, at.Add(time.Hour), 100)
	if err != nil || receipt.NewSeason != 2 {
		t.Fatal(receipt, err)
	}
	next, _ := s.View()
	if len(next.Players) != 0 || next.Season != 2 || !next.SeasonResults[0].Administrative || next.SeasonResults[0].Winner != "" || next.GenesisThreshold() != w.GenesisThreshold() {
		t.Fatal("incorrect reset")
	}
	afterInode, _ := os.Stat(filepath.Join(s.Dir, "world.lock"))
	if !os.SameFile(inode, afterInode) {
		t.Fatal("lock inode replaced")
	}
	if _, err = old.View(); !errors.Is(err, game.ErrSeasonChanged) {
		t.Fatal("stale login accepted", err)
	}
	if _, err = s.ExportSeason(filepath.Join(t.TempDir(), "retry.json"), 1, at.Add(time.Hour), 100); err == nil {
		t.Fatal("replayed reset")
	}
}

func TestSeasonAdminConcurrentAndFailure(t *testing.T) {
	s, _, at := genesisStore(t)
	var wg sync.WaitGroup
	successes := make(chan bool, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := s.ExportSeason(filepath.Join(t.TempDir(), "archive.json"), 1, at, 36)
			successes <- err == nil
		}()
	}
	wg.Wait()
	close(successes)
	n := 0
	for ok := range successes {
		if ok {
			n++
		}
	}
	if n != 1 {
		t.Fatalf("%d resets committed", n)
	}
	s, _, at = genesisStore(t)
	before := travelBytes(t, s)
	if _, err := s.ExportSeason(filepath.Join(s.Dir, "missing", "archive"), 1, at, 36); err == nil {
		t.Fatal("missing directory accepted")
	}
	if !bytes.Equal(before, travelBytes(t, s)) {
		t.Fatal("failure mutated world")
	}
	s.syncDirectory = func(string) error { return errors.New("sync failure") }
	out, err := s.ExportSeason(filepath.Join(t.TempDir(), "archive"), 1, at, 36)
	var committed *DurabilityError
	if !errors.As(err, &committed) || out.NewSeason != 2 {
		t.Fatal("lost committed receipt", out, err)
	}
}
