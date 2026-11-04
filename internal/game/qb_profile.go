package game

import (
	"encoding/hex"
	"errors"
	"fmt"
	"time"

	"github.com/robbiew/yankeetrader/internal/qbinit"
)

const QB36Profile = "qb36-v1"

// QBRecipe records initializer provenance, not a checksum of the evolving save.
// State is a pointer so omitted input cannot be mistaken for valid raw state zero.
type QBRecipe struct {
	Profile      string
	State        *uint32
	Date         string
	SourceSHA256 string
}

func cloneQBRecipe(r *QBRecipe) *QBRecipe {
	if r == nil {
		return nil
	}
	c := *r
	if r.State != nil {
		s := *r.State
		c.State = &s
	}
	return &c
}

func (w *World) validateQBRecipe() error {
	r := w.QBRecipe
	if r == nil {
		return nil
	}
	if r.Profile != QB36Profile || r.State == nil || *r.State > 0xffffff {
		return errors.New("invalid QB recipe profile or state")
	}
	d, err := time.Parse("2006-01-02", r.Date)
	if err != nil || d.Format("2006-01-02") != r.Date || d.Year() < 2026 || d.Year() > 2028 || d.YearDay() == 10 {
		return errors.New("invalid or unverified QB recipe date")
	}
	hash, err := hex.DecodeString(r.SourceSHA256)
	if err != nil || len(hash) != 32 || hex.EncodeToString(hash) != r.SourceSHA256 {
		return errors.New("invalid QB source fingerprint")
	}
	if w.PortGeneration != "dos" || w.WarpGeneration != "dos" || len(w.Sectors) != 3000 || len(w.Ports) != 1000 {
		return errors.New("inconsistent QB recipe geometry or generation rules")
	}
	return nil
}

// NewQB36 generates and admits a fresh world without publishing any save.
// modernSeed affects only modern bootstrap, never the QB initializer stream.
func NewQB36(now time.Time, modernSeed int64, state uint32, date string) (*World, error) {
	c, err := prepareQBWorld(now, modernSeed, qbinit.Options{State: state, Date: date})
	if err != nil {
		return nil, err
	}
	c.world.QBRecipe = &QBRecipe{Profile: QB36Profile, State: &state, Date: date, SourceSHA256: hex.EncodeToString(c.sourceSHA256[:])}
	if err := c.world.Validate(); err != nil {
		return nil, err
	}
	return c.world, nil
}

func (w *World) newSeasonWorld(now time.Time, seed int64) (*World, error) {
	if w.QBRecipe == nil {
		return NewWithGeneration(now, seed, len(w.Sectors), w.PortGeneration, w.WarpGeneration)
	}
	if err := w.validateQBRecipe(); err != nil {
		return nil, err
	}
	c, err := NewQB36(now, seed, *w.QBRecipe.State, w.QBRecipe.Date)
	if err != nil {
		return nil, err
	}
	if c.QBRecipe.SourceSHA256 != w.QBRecipe.SourceSHA256 {
		return nil, fmt.Errorf("QB source fingerprint mismatch; no reset")
	}
	return c, nil
}
