package game

import (
	"testing"
	"time"
)

func TestLandingPreviewUsesProjectedDefensesAndVacantStatus(t *testing.T) {
	w, p, _ := mobilityWorld(t)
	enemy, _ := w.Join("enemy", "Enemy")
	planet := w.Planets[w.Sectors[p.Sector].Planet]
	planet.Owner = enemy.ID
	planet.Ground = 100000
	target, adopt, err := w.LandingTarget(p.ID, clock)
	if err != nil {
		t.Fatal(err)
	}
	entry, err := w.PreparePlanetAction(p.ID, "assault", "", 0, 10, clock)
	if err != nil {
		t.Fatal(err)
	}
	if err = entry.CheckLandingPreview(target, adopt); err != nil {
		t.Fatal("unchanged preview rejected", err)
	}
	// A later quote is okay only while the integer projected defense is unchanged.
	entry.QuotedAt = clock.Add(time.Millisecond)
	if err = entry.CheckLandingPreview(target, adopt); err != nil {
		t.Fatal(err)
	}
	entry.QuotedAt = clock.Add(time.Hour)
	if entry.CheckLandingPreview(target, adopt) == nil {
		t.Fatal("elapsed garrison growth silently changed quote")
	}
	entry.QuotedAt = clock
	entry.OwnerDead = true
	if entry.CheckLandingPreview(target, adopt) == nil {
		t.Fatal("assault silently became adoption")
	}
	entry.OwnerDead = false
	if entry.CheckLandingPreview(target, true) == nil {
		t.Fatal("adoption silently became assault")
	}
}
