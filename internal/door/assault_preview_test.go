package door

import (
	"github.com/robbiew/yankeetrader/internal/game"
	"strings"
	"testing"
	"time"
)

// Changes while choosing consent/troops must not become a silently newer quote.
func TestGroundActionBindsInitialDisplayedTargetBeforeFinalPrompt(t *testing.T) {
	for _, classic := range []bool{false, true} {
		for _, stage := range []int{1, 2} {
			for _, mode := range []string{"garrison", "replacement", "rename", "growth", "governor", "carried"} {
				t.Run(mode+map[bool]string{true: "-classic", false: "-compact"}[classic]+string(rune('0'+stage)), func(t *testing.T) {
					term := &portInput{scripted: scripted{lines: []string{"y", "10", "y"}}}
					s, id, _ := mobilitySession(t, term)
					s.Classic = classic
					if err := s.Store.Update(func(w *game.World) error {
						enemy, _ := w.Join("enemy", "Enemy")
						w.Planets[2].Owner = enemy.ID
						w.Players[id].PlanetToken = ""
						w.Players[id].LandedPlanet = 0
						return nil
					}); err != nil {
						t.Fatal(err)
					}
					if mode == "growth" {
						if err := s.Store.Update(func(w *game.World) error { w.Planets[2].Ground = 100000; return nil }); err != nil {
							t.Fatal(err)
						}
					}
					start := s.Now()
					clock := start
					s.Now = func() time.Time { return clock }
					reads := 0
					term.beforeRead = func() {
						reads++
						if reads != stage {
							return
						}
						if mode == "growth" {
							clock = clock.Add(time.Hour)
							return
						}
						if err := s.Store.Update(func(w *game.World) error {
							p := w.Planets[2]
							switch mode {
							case "carried":
								w.Players[id].Ground = 14
							case "garrison":
								p.Ground = 1000
							case "replacement":
								p.Generation = w.NextPlanetGeneration
								w.NextPlanetGeneration++
							case "rename":
								p.Name = "Renamed"
							case "governor":
								other, _ := w.Join("other", "Other")
								p.Owner = other.ID
							}
							return nil
						}); err != nil {
							t.Fatal(err)
						}
					}
					pending := []string{}
					draws := 0
					token, err := s.forceLandingWithRandom(id, &pending, func() float64 { draws++; return 0 })
					w, e := s.Store.View()
					if e != nil {
						t.Fatal(e)
					}
					text := term.output.String()
					if err == nil || token != "" || draws != 0 || w.Players[id].Ground != map[bool]int64{true: 14, false: 15}[mode == "carried"] || strings.Contains(text, "Force landing on ") || strings.Contains(text, "Ground action saved") {
						t.Fatalf("preview change accepted: err=%v draws=%d troops=%d output=%s", err, draws, w.Players[id].Ground, text)
					}
				})
			}
		}
	}
}
