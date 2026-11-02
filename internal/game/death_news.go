package game

import (
	"errors"
	"math"
	"time"
)

// deathNews captures public names and the actual estate transfer before death
// clears location/ownership. Dedicated Xannor death news is published by its caller.
func (w *World) deathNews(context DeathContext) []NewsEvent {
	if context.Cause == "xannor" {
		return nil
	}
	victim := w.Players[context.Victim]
	if victim == nil {
		return nil
	}
	entry := NewsEvent{Kind: NewsCombat, Alias: victim.Alias, Combat: &CombatNews{Operation: "ship-death"}}
	killer := w.Players[context.Killer]
	if killer != nil && killer.ID != victim.ID {
		entry.Alias = killer.Alias
		entry.Combat.Target = victim.Alias
	}
	events := []NewsEvent{entry}
	inherits := context.Cause == "combat" || context.Cause == "retaliation" || context.Cause == "missile" || context.Cause == "plasma" && killer != nil && killer.ID != victim.ID && killer.Death == nil
	if inherits {
		count := int64(0)
		for _, port := range w.Ports {
			if port.ID != 1 && port.Owner == victim.ID {
				count++
			}
		}
		if count > 0 {
			events = append(events, NewsEvent{Kind: NewsCombat, Alias: killer.Alias, Combat: &CombatNews{Operation: "ports-captured", Target: victim.Alias, Amount: count}})
		}
	}
	return events
}

// prepareDeathNews reserves the complete sequence range without mutating the
// world. Retention is bounded separately and must not prevent publication.
func (w *World) prepareDeathNews(events []NewsEvent, now time.Time) error {
	if len(events) == 0 {
		return nil
	}
	if err := w.prepareNews(now); err != nil {
		return err
	}
	if uint64(len(events)) > math.MaxUint64-w.NextNews {
		return errors.New("newspaper sequence exhausted")
	}
	return nil
}
func (w *World) appendDeathNews(events []NewsEvent, now time.Time) {
	for _, entry := range events {
		entry.At = now.UTC()
		w.appendNews(entry)
	}
}

// salvageNews mirrors DOS's public header and positive acquired inventory lines;
// holds are the empty portion, while filled salvaged holds are reported by cargo.
func (w *World) salvageNews(winner, victim string, loot Salvage) []NewsEvent {
	makeEvent := func(resource string, amount int64) NewsEvent {
		return NewsEvent{Kind: NewsCombat, Alias: winner, Combat: &CombatNews{Operation: "salvage", Target: victim, Resource: resource, Amount: amount}}
	}
	events := []NewsEvent{makeEvent("summary", 0)}
	quantities := []struct {
		resource string
		amount   int64
	}{
		{"credits", loot.Credits}, {"missiles", loot.Missiles}, {"plasma", loot.Plasma}, {"ground", loot.Ground}, {"mines", loot.Mines},
		{"empty-holds", loot.Holds - loot.Cargo[0] - loot.Cargo[1] - loot.Cargo[2]},
		{"ore", loot.Cargo[0]}, {"organics", loot.Cargo[1]}, {"equipment", loot.Cargo[2]},
	}
	for _, q := range quantities {
		if q.amount > 0 {
			events = append(events, makeEvent(q.resource, q.amount))
		}
	}
	if len(events) == 1 {
		events = append(events, makeEvent("nothing", 0))
	}
	return events
}
