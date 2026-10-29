package door

import (
	"errors"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) newspaper(id int, args []string, pending *[]string) error {
	if len(args) > 1 {
		return errors.New("use NEWS [TODAY|YESTERDAY]")
	}
	choice := "today"
	if len(args) == 1 {
		choice = strings.ToLower(args[0])
	} else if s.Classic {
		for {
			answer, err := s.classicArgument("Do you want to read [T]oday's or [Y]esterday's news? [T/Y] -=> ", pending)
			if err != nil {
				return err
			}
			answer = strings.ToLower(strings.TrimSpace(answer))
			if answer == "t" || answer == "today" || answer == "y" || answer == "yesterday" {
				choice = answer
				break
			}
			if err = s.Terminal.Printf("Choose T or Y.\r\n"); err != nil {
				return err
			}
		}
	}
	yesterday := choice == "yesterday" || choice == "y"
	if choice != "today" && choice != "t" && !yesterday {
		return errors.New("use NEWS [TODAY|YESTERDAY]")
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	report, err := w.ReadNewspaper(id, s.Now(), yesterday)
	if err != nil {
		return err
	}
	if !time.Now().Before(s.Deadline) {
		return errors.New("session time expired")
	}
	label := "Today"
	if yesterday {
		label = "Yesterday"
	}
	if err = s.Terminal.Printf("\r\nGalactic Newspaper - %s (%s UTC)\r\n", label, report.Date); err != nil {
		return err
	}
	if len(report.Entries) == 0 {
		return s.Terminal.Printf("No news retained for this date.\r\n")
	}
	for offset := 0; offset < len(report.Entries); {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		// Stable public snapshot, but access must remain bound to this live ship.
		if _, err = s.Store.View(); err != nil {
			return err
		}
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		end := min(offset+5, len(report.Entries))
		for _, entry := range report.Entries[offset:end] {
			if entry.Kind == game.NewsLogin {
				err = s.Terminal.Printf("%s %s  Logged on\r\n", entry.At.Format("15:04:05"), entry.Alias)
			} else if entry.Kind == game.NewsXannorDeath {
				err = s.Terminal.Printf("%s %s  Destroyed by the Xannor\r\n", entry.At.Format("15:04:05"), entry.Alias)
			} else if entry.Kind == game.NewsXannorPlanet {
				err = s.Terminal.Printf("%s Xannor assault on %s: %s.\r\n", entry.At.Format("15:04:05"), entry.PlanetName, entry.Outcome)
			} else {
				err = s.Terminal.Printf("%s %s  Created Team %d -=- %s\r\n", entry.At.Format("15:04:05"), entry.Alias, entry.Team, entry.TeamName)
			}
			if err != nil {
				return err
			}
		}
		offset = end
		if offset < len(report.Entries) {
			if err = s.Terminal.Printf("More news? [Enter=more, Q=stop] "); err != nil {
				return err
			}
			answer, err := s.readLiteralLine()
			if err != nil {
				return err
			}
			if strings.TrimSpace(answer) != "" {
				return nil
			}
		}
	}
	return nil
}
