package game

import (
	"fmt"
	"math/big"
	"sort"
)

// Ranking rows intentionally contain public scoreboard fields only.
type PlayerRank struct {
	Rank, ID, Team, Ports int
	Alias                 string
	Score                 int64
	Percent               string
}
type TeamRank struct {
	Rank, ID int
	Name     string
	Score    int64
	Percent  string
}
type Rankings struct {
	Players []PlayerRank
	Teams   []TeamRank
}

// scoreAdd saturates at the existing save's score bound. No valid balance or
// inventory can overflow the accumulator or make the scoreboard unavailable.
func scoreAdd(total, quantity, weight int64) int64 {
	if quantity > (MaxMoney-total)/weight {
		return MaxMoney
	}
	return total + quantity*weight
}

func rankPercent(score, leader int64) string {
	if score <= 0 || leader <= 0 {
		return "0.00%"
	}
	n := new(big.Int).Mul(big.NewInt(score), big.NewInt(10000))
	n.Quo(n, big.NewInt(leader))
	value := n.Int64()
	return fmt.Sprintf("%d.%02d%%", value/100, value%100)
}

// PlayerRankings computes a detached, coherent report. With stored=true, scores
// come from the last published cache; ownership and membership remain current.
// Unsupported scanners/NPCs and private planetary assets are not synthesized.
func (w *World) PlayerRankings(id int, stored bool) (Rankings, error) {
	if _, err := w.player(id); err != nil {
		return Rankings{}, err
	}
	return w.rankingSnapshot(stored), nil
}

// rankingSnapshot also serves maintenance, which may run without any live caller.
func (w *World) rankingSnapshot(stored bool) Rankings {
	ports := map[int]int{}
	defenses := map[int]int64{}
	for _, port := range w.Ports {
		if port.ID != 1 && port.Owner > 0 {
			ports[port.Owner]++
		}
	}
	for _, sector := range w.Sectors {
		if sector.Defense != nil && sector.Defense.Owner > 0 {
			owner := sector.Defense.Owner
			defenses[owner] = scoreAdd(defenses[owner], sector.Defense.Fighters, 100)
		}
	}
	report := Rankings{}
	totals := map[int]int64{}
	for _, p := range w.Players {
		score := int64(0)
		if p.Death == nil {
			if stored {
				score = p.StoredScore
			} else {
				score = defenses[p.ID]
				for _, part := range [][2]int64{{p.Shields, 50}, {p.Fighters, 100}, {p.Holds, 2500},
					{p.Cargo[0], 20}, {p.Cargo[1], 30}, {p.Cargo[2], 40}, {p.Credits, 1},
					{p.Missiles, 1000}, {p.Plasma, 1000000}, {int64(ports[p.ID]), 50000}, {p.Ground, 750}, {p.Mines, 2500}} {
					score = scoreAdd(score, part[0], part[1])
				}
			}
		}
		report.Players = append(report.Players, PlayerRank{ID: p.ID, Alias: p.Alias, Team: p.Team, Ports: ports[p.ID], Score: score})
		if p.Team != 0 {
			totals[p.Team] += score
		}
	}
	sort.Slice(report.Players, func(i, j int) bool {
		a, b := report.Players[i], report.Players[j]
		if a.Score != b.Score {
			return a.Score > b.Score
		}
		return a.ID < b.ID
	})
	leader := int64(0)
	if len(report.Players) > 0 {
		leader = report.Players[0].Score
	}
	for i := range report.Players {
		report.Players[i].Rank = i + 1
		report.Players[i].Percent = rankPercent(report.Players[i].Score, leader)
	}
	for team, total := range totals {
		t := w.Teams[team]
		report.Teams = append(report.Teams, TeamRank{ID: team, Name: t.Name, Score: total})
	}
	sort.Slice(report.Teams, func(i, j int) bool {
		a, b := report.Teams[i], report.Teams[j]
		if a.Score != b.Score {
			return a.Score > b.Score
		}
		return a.ID < b.ID
	})
	leader = 0
	if len(report.Teams) > 0 {
		leader = report.Teams[0].Score
	}
	for i := range report.Teams {
		report.Teams[i].Rank = i + 1
		report.Teams[i].Percent = rankPercent(report.Teams[i].Score, leader)
	}
	return report
}

func (w *World) publishRankings(report Rankings) {
	for _, row := range report.Players {
		w.Players[row.ID].StoredScore = row.Score
	}
}

// RefreshRankings publishes every account score from the same world snapshot.
// Execute inside Store.Update; no partial cache is visible to retaliation.
func (w *World) RefreshRankings(id int) (Rankings, error) {
	report, err := w.PlayerRankings(id, false)
	if err != nil {
		return Rankings{}, err
	}
	w.publishRankings(report)
	return report, nil
}
