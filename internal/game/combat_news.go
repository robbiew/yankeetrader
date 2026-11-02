package game

import (
	"errors"
	"math"
	"time"
)

// Reserve IDs for the entire bounded action before its first mutation. The
// retained journal may prune old rows, but ID exhaustion must not silence a hit.
func (w *World) prepareCombatNews(now time.Time, slots uint64) error {
	if err := w.prepareNews(now); err != nil {
		return err
	}
	if slots > math.MaxUint64-w.NextNews {
		return errors.New("newspaper sequence cannot record this combat action")
	}
	return nil
}
func (w *World) combatNews(alias string, details CombatNews, now time.Time) {
	w.appendNews(NewsEvent{Kind: NewsCombat, At: now.UTC(), Alias: alias, Combat: &details})
}
func productionTotal(rates [3]float64) float64 { return rates[0] + rates[1] + rates[2] }
func (w *World) defenseNewsOwner(id int) string {
	if p := w.Players[id]; p != nil {
		return p.Alias
	}
	switch id {
	case XannorOwner:
		return "The Xannor"
	case MercenaryOwner:
		return "The Mercenaries"
	}
	return "Unknown"
}
