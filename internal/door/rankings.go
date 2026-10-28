package door

import (
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) rankings(id int, args []string, pending *[]string) error {
	stored := false
	if s.Classic && len(args) == 0 {
		answer, err := s.classicArgument("Enter 'O' for stored scores or [ENTER] for UPDATED rankings: ", pending)
		if err != nil {
			return err
		}
		answer = strings.ToLower(strings.TrimSpace(answer))
		if answer != "" && answer != "o" {
			return errors.New("choose O or Enter")
		}
		stored = answer == "o"
	} else if len(args) == 1 && strings.EqualFold(args[0], "old") {
		stored = true
	} else if len(args) != 0 {
		return errors.New("use RANK [OLD]")
	}
	if !time.Now().Before(s.Deadline) {
		return errors.New("session time expired")
	}
	var report game.Rankings
	if stored {
		w, err := s.Store.View()
		if err != nil {
			return err
		}
		report, err = w.PlayerRankings(id, true)
		if err != nil {
			return err
		}
	} else {
		err := s.Store.Update(func(w *game.World) error {
			if !time.Now().Before(s.Deadline) {
				return errors.New("session time expired")
			}
			var err error
			report, err = w.RefreshRankings(id)
			if err == nil && !time.Now().Before(s.Deadline) {
				return errors.New("session time expired")
			}
			return err
		})
		if err != nil {
			return err
		}
	}
	label := "Updated scores saved"
	if stored {
		label = "Stored scores; current aliases, teams and port counts"
	}
	if err := s.Terminal.Printf("\r\nYankee Trader Scoreboard - %s\r\n", label); err != nil {
		return err
	}
	rows := []string{"Player Rankings\r\nRank  Rank%              Score  Team  Ports  Player\r\n"}
	for _, p := range report.Players {
		team := "None"
		if p.Team != 0 {
			team = fmt.Sprint(p.Team)
		}
		rows = append(rows, fmt.Sprintf("%4d %7s %18d %5s %6d  %s\r\n", p.Rank, p.Percent, p.Score, team, p.Ports, p.Alias))
	}
	rows = append(rows, "Team Rankings\r\nRank  Rank%              Score  Team  Team Name\r\n")
	if len(report.Teams) == 0 {
		rows = append(rows, "No teams found.\r\n")
	}
	for _, t := range report.Teams {
		rows = append(rows, fmt.Sprintf("%4d %7s %18d %5d  %s\r\n", t.Rank, t.Percent, t.Score, t.ID, t.Name))
	}
	for offset := 0; offset < len(rows); {
		// Keep one report snapshot while verifying this session before every page.
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		if _, err := s.Store.View(); err != nil {
			return err
		}
		end := min(offset+10, len(rows))
		for _, row := range rows[offset:end] {
			if err := s.Terminal.Printf("%s", row); err != nil {
				return err
			}
		}
		offset = end
		if offset == len(rows) {
			return s.Terminal.Printf("End of rankings.\r\n")
		}
		if err := s.Terminal.Printf("More rankings? [Enter=more, Q=stop] "); err != nil {
			return err
		}
		answer, err := s.readLiteralLine()
		if err != nil {
			return err
		}
		if strings.TrimSpace(answer) != "" && !strings.EqualFold(strings.TrimSpace(answer), "y") {
			return nil
		}
	}
	return nil
}
