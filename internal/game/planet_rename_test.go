package game

import (
	"errors"
	"reflect"
	"strings"
	"testing"
)

func TestDOSPlanetRenameNames(t *testing.T) {
	for _, tc := range []struct{ input, want string }{
		{"New Eden", "New Eden"}, {"mIxEd nAME", "Mixed Name"}, {"   Test  Name   ", "Test Name"},
		{"o'brien alpha-beta x_Y 42base", "O'brien Alpha-Beta X_Y 42Base"},
		{"12345678901234567890123456789012345678901234567890", "12345678901234567890123456789012345678901"},
		{strings.Repeat("a", 40) + " b", "A" + strings.Repeat("a", 39) + " "},
	} {
		got, err := PlanetRenameName(tc.input)
		if err != nil || got != tc.want {
			t.Fatalf("%q => %q, %v; want %q", tc.input, got, err, tc.want)
		}
	}
	for _, name := range []string{"The Wanderer", "THE WANDERER", "Xannoron", "xAnNoRoN", "Mercenary Base", "  mercenary  base "} {
		if _, err := PlanetRenameName(name); !errors.Is(err, ErrReservedPlanetName) {
			t.Fatalf("reserved %q: %v", name, err)
		}
	}
	for _, name := range []string{"", "   ", "\x1b[31mBad", "Na\nme", "é", strings.Repeat("a", 50) + "\x00"} {
		if _, err := PlanetRenameName(name); err == nil {
			t.Fatalf("accepted invalid %q", name)
		}
	}
}

func TestRenameUsesLandingPermissionAndOnlyChangesName(t *testing.T) {
	for _, mode := range []string{"owner", "team", "unguarded", "unowned", "defended", "stale", "last-slot"} {
		t.Run(mode, func(t *testing.T) {
			w, p := setup(t)
			p.Sector = 2
			other, err := w.Join("other", "Other")
			if err != nil {
				t.Fatal(err)
			}
			planet := &Planet{ID: 2, Sector: 2, Owner: p.ID, Name: "Old Name", Updated: clock, Production: [3]float64{10, 20, 30}, Cargo: [3]float64{100, 200, 300}, Ground: 100, Bank: 10000}
			w.Planets[2] = planet
			w.Sectors[2].Planet = 2
			switch mode {
			case "team":
				planet.Owner = other.ID
				p.Team = 1
				hash, _ := hashTeamPassword("ABCD")
				w.Teams[1] = &Team{ID: 1, Name: "Team", Captain: p.ID, PasswordHash: hash}
				other.Team = 1
			case "unguarded":
				planet.Owner = other.ID
				planet.Ground = 0
			case "unowned":
				planet.Owner = 0
				planet.Ground = 0
			case "last-slot":
				delete(w.Planets, 2)
				planet.ID = 100
				w.Planets[100] = planet
				w.Sectors[2].Planet = 100
			}
			if err = w.Land(p.ID, clock); err != nil {
				t.Fatal(err)
			}
			token := p.PlanetToken
			if mode == "defended" {
				planet.Owner = other.ID
			}
			if mode == "stale" {
				if err = w.Land(p.ID, clock); err != nil {
					t.Fatal(err)
				}
			}
			beforePlayer := *p
			beforePlanet := *planet
			err = w.RenamePlanet(p.ID, token, "new eden", clock)
			rejected := mode == "defended" || mode == "stale" || mode == "last-slot"
			if rejected {
				if err == nil {
					t.Fatal("accepted forbidden rename")
				}
				if !reflect.DeepEqual(*planet, beforePlanet) {
					t.Fatal("rejected rename changed planet")
				}
			} else {
				if err != nil {
					t.Fatal(err)
				}
				expected := beforePlanet
				expected.Name = "New Eden"
				if !reflect.DeepEqual(*planet, expected) {
					t.Fatalf("rename changed non-name data: %+v", planet)
				}
			}
			if !reflect.DeepEqual(*p, beforePlayer) {
				t.Fatal("rename changed player assets/session")
			}
		})
	}
}
