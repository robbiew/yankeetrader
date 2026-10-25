package game

import (
	"errors"
	"strings"
	"time"
)

var ErrProtectedPlanetRename = errors.New("You can't re-name this planet!")
var ErrReservedPlanetName = errors.New("I Don't think so!")

// PlanetRenameName reproduces the DOS name cleaner: collapse spaces and use
// word casing (apostrophes stay within a word), then limit to 41 ASCII bytes.
// Input controls/non-ASCII are rejected before truncation for terminal safety.
func PlanetRenameName(name string) (string, error) {
	for _, c := range name {
		if c < 32 || c > 126 {
			return "", errors.New("use a printable planet name")
		}
	}
	name = strings.Join(strings.Fields(name), " ")
	if name == "" {
		return "", errors.New("use a printable planet name")
	}
	bytes := []byte(name)
	word := false
	for i, c := range bytes {
		letter := c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z'
		if !word && c >= 'a' && c <= 'z' {
			bytes[i] = c - 32
		}
		if word && c >= 'A' && c <= 'Z' {
			bytes[i] = c + 32
		}
		word = letter || c == '\''
	}
	name = string(bytes)
	switch name {
	case "The Wanderer", "Xannoron", "Mercenary Base":
		return "", ErrReservedPlanetName
	}
	if len(name) > 41 {
		name = name[:41]
	}
	return name, nil
}

// Renaming uses ordinary landing permission, including shared/unguarded access.
// DOS reserves its first and final planet slots for special planets.
func (w *World) CanRenamePlanet(id int, token string, now time.Time) error {
	_, planet, err := w.landed(id, token, now)
	if err != nil {
		return err
	}
	if planet.ID == 1 || planet.ID == 100 {
		return ErrProtectedPlanetRename
	}
	return nil
}

func (w *World) RenamePlanet(id int, token, name string, now time.Time) error {
	if err := w.CanRenamePlanet(id, token, now); err != nil {
		return err
	}
	name, err := PlanetRenameName(name)
	if err != nil {
		return err
	}
	w.Planets[w.Players[id].LandedPlanet].Name = name
	return nil
}
