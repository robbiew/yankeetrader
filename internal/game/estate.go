package game

import "errors"

var errInvalidDefense = errors.New("invalid sector defense or protected Earth defense")

const MercenaryOwner = -2
const XannorOwner = -1

// SectorDefense is stored independently of ships. Placement and fighting remain
// unavailable; movement refuses hostile defenses rather than bypassing them.
type SectorDefense struct {
	Owner    int
	Fighters int64
}

func (w *World) applyDeathEstate(victim *Player, context DeathContext) {
	recipient := 0
	if context.Cause == "combat" || context.Cause == "retaliation" {
		recipient = context.Killer
	}
	affected := map[int]bool{}
	for _, port := range w.Ports {
		if port.ID != 1 && port.Owner == victim.ID {
			port.Owner = recipient
			if recipient == 0 {
				port.Treasury = 0
			}
			affected[port.Sector] = true
		}
	}
	for _, p := range w.Players {
		if affected[p.Sector] {
			p.DockToken = ""
		}
	}
	for _, sector := range w.Sectors {
		if sector.Defense != nil && sector.Defense.Owner == victim.ID {
			sector.Defense.Owner = MercenaryOwner
		}
	}
	teamID := victim.Team
	victim.Team = 0
	if team := w.Teams[teamID]; team != nil {
		if len(w.teamMembers(teamID)) == 0 {
			delete(w.Teams, teamID)
		} else if team.Captain == victim.ID {
			team.Captain = 0
		}
	}
	w.revokeTeamAccess()
}

func (w *World) validateDefenses() error {
	for _, sector := range w.Sectors {
		if sector == nil {
			continue
		}
		d := sector.Defense
		if d == nil {
			continue
		}
		if sector.ID == 1 || d.Fighters < 1 || d.Fighters > MaxQuantity || d.Owner < MercenaryOwner || d.Owner == 0 || (d.Owner > 0 && (w.Players[d.Owner] == nil || w.Players[d.Owner].Death != nil)) {
			return errInvalidDefense
		}
	}
	return nil
}
