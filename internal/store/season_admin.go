package store

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

// SeasonArchive is a private, complete snapshot, including identities and mail.
// WorldSHA256 hashes the compact JSON encoding of World.
type SeasonArchive struct {
	Format      int
	Exported    time.Time
	WorldSHA256 string
	World       json.RawMessage
}

type SeasonAdminReceipt struct {
	ArchivedSeason uint64
	NewSeason      uint64
	Archive        string
	SHA256         string
}

// ExportSeason exports a consistent private snapshot. With resetSeason nonzero,
// it also replaces exactly that season, only after the archive is durable.
// The archive path must not exist. Failure after export may leave a valid archive
// with the old world still active; callers must inspect the world before retrying.
func (s Store) ExportSeason(path string, resetSeason uint64, now time.Time, seed int64) (out SeasonAdminReceipt, err error) {
	if s.ship != nil {
		return out, errors.New("season administration requires an unbound store")
	}
	if path == "" || now.IsZero() {
		return out, errors.New("archive path and clock are required")
	}
	err = s.locked(func() error {
		w, e := s.load()
		if e != nil {
			return e
		}
		var candidate *game.World
		if resetSeason != 0 {
			candidate, e = w.AdministrativeCandidate(resetSeason, now, seed)
			if e != nil {
				return e
			}
		}
		raw, e := json.Marshal(w)
		if e != nil {
			return e
		}
		sum := sha256.Sum256(raw)
		archive := SeasonArchive{Format: 1, Exported: now.UTC(), WorldSHA256: hex.EncodeToString(sum[:]), World: raw}
		data, e := json.Marshal(archive)
		if e != nil {
			return e
		}
		// Exclusive creation prevents overwrite, including world.json and symlinks.
		f, e := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if e != nil {
			return e
		}
		complete := false
		defer func() {
			f.Close()
			if !complete {
				os.Remove(path)
			}
		}()
		if _, e = f.Write(append(data, '\n')); e != nil {
			return e
		}
		if e = f.Sync(); e != nil {
			return e
		}
		if e = f.Close(); e != nil {
			return e
		}
		if e = syncDir(filepath.Dir(path)); e != nil {
			return fmt.Errorf("archive directory sync: %w", e)
		}
		complete = true
		out = SeasonAdminReceipt{ArchivedSeason: w.Season, Archive: path, SHA256: archive.WorldSHA256}
		if candidate != nil {
			e = s.save(candidate)
			var committed *DurabilityError
			if e == nil || errors.As(e, &committed) {
				out.NewSeason = candidate.Season
			}
			return e
		}
		return nil
	})
	return
}
