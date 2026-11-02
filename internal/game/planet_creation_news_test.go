package game

import (
	"encoding/json"
	"math"
	"strings"
	"testing"
	"time"
)

func creationWorld(t *testing.T) (*World, *Player) {
	t.Helper()
	w, p := setup(t)
	p.Sector = 8
	p.Credits = 50000
	return w, p
}
func TestPlanetCreationNewsSnapshotAndRetry(t *testing.T) {
	w, p := creationWorld(t)
	turns := p.Turns
	if err := w.CreatePlanet(p.ID, "  Accepted; literal/  ", clock); err != nil {
		t.Fatal(err)
	}
	planet := w.Planets[w.Sectors[8].Planet]
	if p.Credits != 25000 || p.Turns != turns || len(w.News) != 1 || w.News[0].Kind != NewsPlanetCreated || w.News[0].PlanetName != "Accepted; literal/" || w.News[0].Alias != p.Alias {
		t.Fatal(p, w.News)
	}
	before := string(worldJSON(t, w))
	if w.CreatePlanet(p.ID, "Other", clock) == nil || string(worldJSON(t, w)) != before {
		t.Fatal("retry changed creation")
	}
	alias := p.Alias
	planet.Name = "Renamed"
	p.Alias = "New Alias"
	w.destroyPlanet(planet)
	other, _ := w.Join("public-reader", "Reader")
	report, err := w.ReadNewspaper(other.ID, clock, false)
	if err != nil || len(report.Entries) != 1 || report.Entries[0].Alias != alias || report.Entries[0].PlanetName != "Accepted; literal/" {
		t.Fatal(report, err)
	}
	raw, _ := json.Marshal(report)
	if strings.Contains(string(raw), p.Identity) || strings.Contains(string(raw), "Sector") || strings.Contains(string(raw), "Credits") {
		t.Fatal(string(raw))
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}
func TestPlanetCreationNewsRejectsWithoutMutation(t *testing.T) {
	for _, mode := range []string{"name", "control", "credits", "occupied", "capacity", "generation", "sequence", "clock", "dead"} {
		t.Run(mode, func(t *testing.T) {
			w, p := creationWorld(t)
			name := "Test"
			now := clock
			switch mode {
			case "name":
				name = strings.Repeat("x", 42)
			case "control":
				name = "bad\x1bname"
			case "credits":
				p.Credits = 24999
			case "occupied":
				w.Sectors[8].Planet = 1
			case "capacity":
				for i := 2; i <= 100; i++ {
					w.Planets[i] = &Planet{ID: i}
				}
			case "generation":
				w.NextPlanetGeneration = math.MaxUint64
			case "sequence":
				w.NextNews = math.MaxUint64
			case "clock":
				now = clock.Add(-time.Second)
			case "dead":
				p.Death = &Death{Cause: "mines"}
			}
			before := string(worldJSON(t, w))
			if w.CreatePlanet(p.ID, name, now) == nil || string(worldJSON(t, w)) != before {
				t.Fatal("rejected creation mutated", mode)
			}
		})
	}
}
func TestPlanetCreationNewsValidationAndMigration(t *testing.T) {
	w, p := creationWorld(t)
	if err := w.CreatePlanet(p.ID, "Test", clock); err != nil {
		t.Fatal(err)
	}
	good := w.News[0]
	for _, mutate := range []func(*NewsEvent){func(e *NewsEvent) { e.Alias = "" }, func(e *NewsEvent) { e.PlanetName = "" }, func(e *NewsEvent) { e.Outcome = "created" }, func(e *NewsEvent) { e.Team = 1 }, func(e *NewsEvent) { e.TeamName = "Secret" }, func(e *NewsEvent) { e.BroadcastText = "secret" }, func(e *NewsEvent) { e.GroundCommitted = 1 }, func(e *NewsEvent) { e.PortCount = 1 }, func(e *NewsEvent) { e.LotteryPrize = 1 }} {
		w.News[0] = good
		mutate(&w.News[0])
		if w.Validate() == nil {
			t.Fatal(w.News[0])
		}
	}
	w.News[0] = good
	w.Version = 27
	if w.Upgrade() == nil {
		t.Fatal("future event accepted in old save")
	}
	w.News = nil
	next := w.NextNews
	planet := *w.Planets[w.Sectors[8].Planet]
	if err := w.Upgrade(); err != nil || w.Version != WorldVersion || len(w.News) != 0 || w.NextNews != next || *w.Planets[planet.ID] != planet {
		t.Fatal("migration backfilled/mutated", err)
	}
}

func TestPlanetCreationNewsUsesBoundedJournal(t *testing.T) {
	w, p := creationWorld(t)
	for i := 0; i < MaxNewsEvents; i++ {
		w.appendNews(NewsEvent{At: clock, Kind: NewsLogin, Alias: p.Alias})
	}
	if err := w.CreatePlanet(p.ID, "Newest", clock); err != nil {
		t.Fatal(err)
	}
	if len(w.News) != MaxNewsEvents || w.News[0].ID != 2 || w.News[len(w.News)-1].Kind != NewsPlanetCreated {
		t.Fatal("creation bypassed bounded journal")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	w.Sectors[8].Planet = 0
	w.Planets = map[int]*Planet{}
	p.Credits = 25000
	if err := w.CreatePlanet(p.ID, "Later", clock.AddDate(0, 0, 3)); err != nil {
		t.Fatal(err)
	}
	if len(w.News) != 1 || w.News[0].PlanetName != "Later" {
		t.Fatal("old journal not pruned", w.News)
	}
}
