package door

import (
	"fmt"
	"github.com/robbiew/yankeetrader/internal/game"
	"strings"
)

// Render only typed public snapshots. Never resolve current names or read private
// player/planet state while showing historical news.
func combatNewsText(e game.NewsEvent) string {
	c := e.Combat
	if c == nil {
		return ""
	}
	weapon := "missiles"
	if strings.HasPrefix(c.Operation, "plasma-") {
		weapon = "plasma bolts"
	}
	switch c.Operation {
	case "ship-death":
		if c.Target == "" {
			return fmt.Sprintf("%s was killed!", e.Alias)
		}
		return fmt.Sprintf("%s killed %s!", e.Alias, c.Target)
	case "ports-captured":
		return fmt.Sprintf("%s took %d ports from %s.", e.Alias, c.Amount, c.Target)
	case "salvage":
		if c.Resource == "summary" {
			return fmt.Sprintf("%s searched the wreckage of %s.", e.Alias, c.Target)
		}
		if c.Resource == "nothing" {
			return fmt.Sprintf("%s found NOTHING in the wreckage.", e.Alias)
		}
		return fmt.Sprintf("%s salvaged %d %s.", e.Alias, c.Amount, c.Resource)
	case "sector-surrender":
		return fmt.Sprintf("%d fighters in sector %d surrendered to %s.", c.Amount, c.Sector, e.Alias)
	case "sector-destroyed":
		return fmt.Sprintf("%s destroyed %d fighters belonging to %s in sector %d.", e.Alias, c.Amount, c.Target, c.Sector)
	case "xannor-turn-bonus":
		return fmt.Sprintf("%s collected %d turns bonus for destroying %d Xannor!!", e.Alias, c.Amount, c.Secondary)
	case "wreck-mines":
		return fmt.Sprintf("%s had sector mines! They EXPLODED! %d mines in sector %d.", e.Alias, c.Amount, c.Sector)
	case "mine-hit":
		return fmt.Sprintf("%s hit sector mines in sector %d! Shields reduced to %d units.", e.Alias, c.Sector, c.Amount)
	case "missile-defense", "plasma-defense":
		return fmt.Sprintf("%s %s: destroyed %d sector fighters in sector %d.", e.Alias, weapon, c.Amount, c.Sector)
	case "missile-mines", "plasma-mines":
		return fmt.Sprintf("%s %s: destroyed %d mines in sector %d.", e.Alias, weapon, c.Amount, c.Sector)
	case "missile-ship", "plasma-ship":
		return fmt.Sprintf("%s %s hit %s in sector %d: shields %d, fighters destroyed %d.", e.Alias, weapon, c.Target, c.Sector, c.Amount, c.Secondary)
	case "missile-retaliation":
		return fmt.Sprintf("%s fired %d retaliatory missiles at %s.", e.Alias, c.Amount, c.Target)
	case "missile-planet", "plasma-planet":
		status := ""
		if c.Destroyed {
			status = " Planet destroyed!"
		}
		return fmt.Sprintf("%s %s hit %s in sector %d: production lost %.6g, remaining %.6g; ground lost %d, remaining %d.%s", e.Alias, weapon, c.Target, c.Sector, c.ProductionLoss, c.ProductionRemaining, c.GroundLoss, c.GroundRemaining, status)
	case "mobility-explosion":
		return fmt.Sprintf("%s: planet %s exploded during transport! Lost %d fighters.", e.Alias, c.Target, c.Amount)
	}
	return ""
}
