package door

import (
	"github.com/robbiew/yankeetrader/internal/game"
	"strings"
	"testing"
)

func TestCombatNewsRendersPublicSnapshot(t *testing.T) {
	cases := []struct {
		detail game.CombatNews
		want   string
	}{
		{game.CombatNews{Operation: "ship-death", Target: "Victim"}, "Captain killed Victim"},
		{game.CombatNews{Operation: "ship-death"}, "Captain was killed"},
		{game.CombatNews{Operation: "salvage", Target: "Victim", Resource: "nothing"}, "NOTHING"},
		{game.CombatNews{Operation: "wreck-mines", Sector: 8, Amount: 4}, "EXPLODED"},
		{game.CombatNews{Operation: "missile-planet", Target: "Atlas", Sector: 9, Destroyed: true}, "Planet destroyed"},
		{game.CombatNews{Operation: "plasma-ship", Target: "Victim", Sector: 10, Amount: 123, Secondary: 4}, "shields 123, fighters destroyed 4"},
	}
	for _, tc := range cases {
		text := combatNewsText(game.NewsEvent{Alias: "Captain", Combat: &tc.detail})
		if !strings.Contains(text, tc.want) || strings.Contains(text, "plasma-ship") || strings.Contains(text, "missile-planet") {
			t.Fatal(text)
		}
	}
}
