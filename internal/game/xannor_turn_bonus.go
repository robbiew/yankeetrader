package game

import "time"

// The current reconstruction uses a fixed 500-turn daily allowance. Xannor
// casualties replenish at most that allowance; they do not create banked turns.
const xannorBonusTurnCap int64 = 500

func xannorTurnBonus(owner int, destroyed, turns int64) int64 {
	if owner != XannorOwner || destroyed < 200 || turns < 0 || turns >= xannorBonusTurnCap {
		return 0
	}
	return min(destroyed/200, xannorBonusTurnCap-turns)
}

// Called only by confirmed direct sector-fighter battles, after the battle and
// entry turn, before emergency escape and mine aftermath consume further turns.
func (w *World) awardXannorTurns(p *Player, owner, sector int, destroyed int64, now time.Time) int64 {
	bonus := xannorTurnBonus(owner, destroyed, p.Turns)
	if bonus > 0 {
		p.Turns += bonus
		w.combatNews(p.Alias, CombatNews{Operation: "xannor-turn-bonus", Sector: sector, Amount: bonus, Secondary: destroyed}, now)
	}
	return bonus
}
