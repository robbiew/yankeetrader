package game

import (
	"fmt"
	"math"
	"sort"
	"strings"
	"time"
)

const MaxActivePlayers = 50

// A finite lifetime identity archive preserves private history and attribution.
// Refuse new identities at capacity rather than reuse another caller's ID.
const MaxPlayerIdentities = 256
const InactiveRetirementDays = 14

func (w *World) activePlayers() int {
	n := 0
	for _, p := range w.Players {
		if p != nil && p.RetiredAt.IsZero() {
			n++
		}
	}
	return n
}

// Retain identity/death/history, but release assets before production and NPCs.
// Waiting since BOTH login and death avoids retiring a newly killed old ship.
func (w *World) retireInactivePlayers(now time.Time) {
	cutoff := day(now.UTC().AddDate(0, 0, -InactiveRetirementDays))
	ids := make([]int, 0, len(w.Players))
	for id := range w.Players {
		ids = append(ids, id)
	}
	sort.Ints(ids)
	for _, id := range ids {
		p := w.Players[id]
		if !p.RetiredAt.IsZero() || p.Death == nil || day(p.Death.At) > cutoff {
			continue
		}
		last := max(p.LastLogin, p.LastActivity)
		if last == "" {
			last = day(w.Created)
		}
		if last > cutoff || w.prepareNews(now) != nil {
			continue
		}
		for _, port := range w.Ports {
			if port.Owner == id {
				port.Owner = 0
				port.Treasury = 0
			}
		}
		for _, planet := range w.Planets {
			if planet.Owner == id {
				planet.Owner = 0
				planet.Ground = 0
			}
		}
		for _, s := range w.Sectors {
			if s.Defense != nil && s.Defense.Owner == id {
				s.Defense = nil
			}
			// Remove this account's attributed field; retain every other source/order.
			layers := s.Minefield[:0]
			for _, layer := range s.Minefield {
				if layer.Owner != id {
					layers = append(layers, layer)
				}
			}
			s.Minefield = layers
		}
		teamID := p.Team
		p.Team = 0
		if team := w.Teams[teamID]; team != nil {
			if len(w.teamMembers(teamID)) == 0 {
				delete(w.Teams, teamID)
			} else if team.Captain == id {
				team.Captain = 0
			}
		}
		w.revokeTeamAccess()
		if w.Xannor != nil && w.Xannor.Revenge != nil && w.Xannor.Revenge.Player == id {
			w.Xannor.Revenge = nil
		}
		p.RetiredAt = now.UTC()
		p.Credits, p.Turns, p.Holds, p.Fighters, p.Shields, p.Ground = 0, 0, 0, 0, 0, 0
		p.Cargo = [3]int64{}
		p.Missiles, p.Mines, p.Plasma = 0, 0, 0
		p.Cloak = 0
		p.StoredScore = 0
		p.DockToken, p.PlanetToken, p.LandedPlanet = "", "", 0
		p.DockUntil = time.Time{}
		p.DockPrices = [3]int64{}
		p.MineGraceSector = 0
		w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsRetirement, Alias: p.Alias})
	}
}

// One gate, one living player, one ordinary slot and one non-Union sector.
// No retries on occupied/reserved/hazardous placement or exhausted metadata.
func (w *World) superPlanetLottery(now time.Time, rng func() float64) {
	if rng() < .5 {
		return
	}
	ids := make([]int, 0, len(w.Players))
	for id, p := range w.Players {
		if p.Death == nil && p.RetiredAt.IsZero() {
			ids = append(ids, id)
		}
	}
	if len(ids) == 0 || len(w.Radio) >= MaxRadioMessages || w.NextRadio == 0 || w.NextRadio == math.MaxUint64 || w.prepareNews(now) != nil {
		return
	}
	sort.Ints(ids)
	winner := w.Players[ids[int(rng()*float64(len(ids)))]]
	slot := 2 + int(rng()*97) // Slots99/100 remain available for faction homes.
	if w.Planets[slot] != nil {
		return
	}
	sectors := make([]int, 0, len(w.Sectors))
	for id := range w.Sectors {
		if id > 7 {
			sectors = append(sectors, id)
		}
	}
	if len(sectors) == 0 {
		return
	}
	sort.Ints(sectors)
	sector := w.Sectors[sectors[int(rng()*float64(len(sectors)))]]
	if sector.Planet != 0 || sector.Defense != nil || len(sector.Minefield) > 0 || (w.Xannor != nil && sector.ID == w.Xannor.HQ) {
		return
	}
	alias := strings.TrimSpace(winner.Alias)
	if len(alias) > 32 {
		alias = alias[:32]
	}
	planet := &Planet{ID: slot, Sector: sector.ID, Owner: winner.ID, Name: alias + "'s Planet", Updated: now.UTC()}
	for i := range planet.Production {
		planet.Production[i] = rng() * rng() * 3000
	}
	planet.Ground = int64(rng()*100) + 1
	planet.Bank = int64(rng() * 1000000)
	w.Planets[slot] = planet
	sector.Planet = slot
	message := RadioMessage{System: "super-planet", ID: w.NextRadio, RequestID: fmt.Sprintf("%032x", w.NextRadio), From: 0, To: winner.ID, FromAlias: "Super Lottery", ToAlias: winner.Alias, Text: fmt.Sprintf("You won a PLANET in the SUPER-LOTTERY! Look in sector %d!", sector.ID), Sent: now.UTC(), Unread: true}
	w.Radio = append(w.Radio, message)
	w.NextRadio++
	w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsSuperPlanet, Alias: winner.Alias})
}
