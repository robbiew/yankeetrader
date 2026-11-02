package game

import (
	"encoding/json"
	"math"
	"testing"
)

func TestExtendedNewsValidationAndLegacyRejection(t *testing.T) {
	w, p := setup(t)
	w.combatNews(p.Alias, CombatNews{Operation: "missile-planet", Target: "Public Planet", Sector: 8, ProductionLoss: 1, ProductionRemaining: 3, GroundLoss: 2, GroundRemaining: 4}, clock)
	raw, err := json.Marshal(w)
	if err != nil {
		t.Fatal(err)
	}
	for _, edit := range []func(*World){
		func(w *World) { w.News[0].Combat = nil },
		func(w *World) { w.News[0].Combat.Operation = "invented" },
		func(w *World) { w.News[0].Combat.Resource = "private-password" },
		func(w *World) { w.News[0].Combat.Target = "\x1b[2J" },
		func(w *World) { w.News[0].Combat.ProductionRemaining = math.NaN() },
		func(w *World) { w.News[0].Combat.ProductionRemaining = math.Inf(1) },
		func(w *World) { w.News[0].Combat.Amount = -1 },
		func(w *World) { w.News[0].TeamName = "Private" },
		func(w *World) { w.News[0].Kind = NewsLogin },
	} {
		var changed World
		if err = json.Unmarshal(raw, &changed); err != nil {
			t.Fatal(err)
		}
		edit(&changed)
		if changed.Validate() == nil {
			t.Fatal("accepted malformed combat news")
		}
	}
	w.Version = 30
	if w.Upgrade() == nil {
		t.Fatal("legacy combat news accepted")
	}
	for _, kind := range []NewsKind{NewsRegistration, NewsTeamJoined} {
		w.News[0].Kind = kind
		w.News[0].Combat = nil
		if w.Upgrade() == nil {
			t.Fatal("legacy membership news accepted")
		}
	}
	w.News = nil
	w.NextNews = 1
	if err = w.Upgrade(); err != nil || w.Version != WorldVersion || len(w.News) != 0 {
		t.Fatal("migration backfilled", err)
	}
}

func TestCombatNewsReportDoesNotShareMutablePayload(t *testing.T) {
	w, p := setup(t)
	w.combatNews(p.Alias, CombatNews{Operation: "ship-death", Target: "Victim"}, clock)
	report, err := w.ReadNewspaper(p.ID, clock, false)
	if err != nil {
		t.Fatal(err)
	}
	report.Entries[0].Combat.Target = "Changed"
	if w.News[0].Combat.Target != "Victim" {
		t.Fatal("report mutated retained news")
	}
}
