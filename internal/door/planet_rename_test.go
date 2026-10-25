package door

import (
	"errors"
	"io"
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestPlanetRenameConfirmationAndPersistence(t *testing.T) {
	for _, tc := range []struct {
		name     string
		commands []string
		want     string
	}{
		{"confirm", []string{"n", "new eden", "y", "d", "l"}, "New Eden"},
		{"default", []string{"n", "new eden", "", "l"}, "New Eden"},
		{"cancel", []string{"n", "", "l"}, "Test Planet"},
		{"retry", []string{"n", "First", "n", "Second", "y", "l"}, "Second"},
		{"reserved", []string{"n", "the wanderer", "l"}, "Test Planet"},
		{"long", []string{"n", strings.Repeat("a", 40) + " b", "y", "l"}, "A" + strings.Repeat("a", 39) + " "},
	} {
		t.Run(tc.name, func(t *testing.T) {
			s, id := planetSession(t)
			if err := s.classicLand(id, &tc.commands); err != nil {
				t.Fatal(err)
			}
			w, err := s.Store.View()
			if err != nil {
				t.Fatal(err)
			}
			if w.Planets[2].Name != tc.want || w.Players[id].Credits != 100000 || w.Players[id].Turns != 500 || w.Players[id].PlanetToken != "" {
				t.Fatal(w.Planets[2], w.Players[id])
			}
		})
	}
}

func TestRenameRejectsStalePrompts(t *testing.T) {
	for _, boundary := range []int{2, 3} {
		for _, mode := range []string{"reland", "move", "permission"} {
			t.Run(mode+string(rune('0'+boundary)), func(t *testing.T) {
				s, id := planetSession(t)
				reads := 0
				term := &portInput{scripted: scripted{lines: []string{"n", "New Eden", "y", "l"}}}
				s.Terminal = term
				term.beforeRead = func() {
					reads++
					if reads != boundary {
						return
					}
					err := s.Store.Update(func(w *game.World) error {
						switch mode {
						case "reland":
							return w.Land(id, s.Now())
						case "move":
							return w.Move(id, 3)
						case "permission":
							other, err := w.Join("other", "Other")
							if err != nil {
								return err
							}
							w.Planets[2].Owner = other.ID
						}
						return nil
					})
					if err != nil {
						t.Fatal(err)
					}
				}
				pending := []string{}
				if err := s.classicLand(id, &pending); err == nil {
					t.Fatal("expected lost landing/permission")
				}
				w, _ := s.Store.View()
				turns := int64(500)
				if mode == "move" {
					turns--
				} // Movement has its own existing turn cost.
				if w.Planets[2].Name != "Test Planet" || w.Players[id].Credits != 100000 || w.Players[id].Turns != turns {
					t.Fatal("stale rename committed")
				}
				if mode == "reland" && w.Players[id].PlanetToken == "" {
					t.Fatal("cleared the newer landing")
				}
			})
		}
	}
}

func TestRenameDisconnectAndProtectedSlot(t *testing.T) {
	for _, lines := range [][]string{{"n"}, {"n", "New Eden"}, {"n", "New Eden", "y"}} {
		s, id := planetSession(t)
		s.Terminal = &scripted{lines: lines}
		pending := []string{}
		if err := s.classicLand(id, &pending); !errors.Is(err, io.EOF) {
			t.Fatal(err)
		}
		w, _ := s.Store.View()
		want := "Test Planet"
		if len(lines) == 3 {
			want = "New Eden"
		}
		if w.Planets[2].Name != want || w.Players[id].Credits != 100000 {
			t.Fatal("incorrect disconnect persistence")
		}
	}
	s, id := planetSession(t)
	if err := s.Store.Update(func(w *game.World) error {
		planet := w.Planets[2]
		delete(w.Planets, 2)
		planet.ID = 100
		w.Planets[100] = planet
		w.Sectors[2].Planet = 100
		return nil
	}); err != nil {
		t.Fatal(err)
	}
	pending := []string{"n", "l"}
	if err := s.classicLand(id, &pending); err != nil {
		t.Fatal(err)
	}
	w, _ := s.Store.View()
	out := s.Terminal.(*scripted).output.String()
	if w.Planets[100].Name != "Test Planet" || !strings.Contains(out, "You can't re-name this planet!") || strings.Contains(out, "What do you want to name") {
		t.Fatal("protected planet offered rename", out)
	}
}
