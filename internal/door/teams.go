package door

import (
	"errors"
	"io"
	"strconv"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) teamSecret(pending *[]string) (string, error) {
	// Passwords are not command arguments: no command-repeat buffer or queued echo.
	if len(*pending) > 0 {
		*pending = nil
		return "", errors.New("enter the password separately at the password prompt")
	}
	if err := s.Terminal.Printf("Team password (4 characters; entered separately): "); err != nil {
		return "", err
	}
	if terminal, ok := s.Terminal.(interface {
		ReadSecret(time.Time) (string, error)
	}); ok {
		value, err := terminal.ReadSecret(s.Deadline)
		if g, ok := s.Terminal.(*GoDoors); ok && g.escaped {
			return "", io.EOF
		}
		return value, err
	}
	return s.Terminal.ReadLine(s.Deadline)
}
func (s Session) teamMenu(id int, pending *[]string) error {
	for {
		var team game.TeamSummary
		err := s.Store.Update(func(w *game.World) error {
			if w.Players[id].Team != 0 {
				var e error
				team, e = w.VisitTeam(id)
				return e
			}
			return nil
		})
		if err != nil {
			return err
		}
		w, err := s.Store.View()
		if err != nil {
			return err
		}
		if err = s.Terminal.Printf("\r\nTeam menu\r\n1) Exit Team menu\r\n"); err != nil {
			return err
		}
		if team.ID == 0 {
			if err = s.Terminal.Printf("2) Create a Team\r\n3) Join a Team\r\n"); err != nil {
				return err
			}
			for _, row := range w.ListTeams() {
				if err = s.Terminal.Printf("Team %d: %s (%d/4 members)\r\n", row.ID, row.Name, len(row.Members)); err != nil {
					return err
				}
			}
		} else {
			if err = s.Terminal.Printf("Team %d: %s\r\n", team.ID, team.Name); err != nil {
				return err
			}
			for _, member := range team.Members {
				role := "member"
				if member == team.Captain {
					role = "captain"
				}
				if err = s.Terminal.Printf("%d: %s (%s)\r\n", member, w.Players[member].Alias, role); err != nil {
					return err
				}
			}
			if err = s.Terminal.Printf("4) Quit a Team\r\n5) Search for Team Members & Resources\r\n"); err != nil {
				return err
			}
			if team.Captain == id {
				if err = s.Terminal.Printf("7) Banish a Team Member\r\n8) Change Team Password\r\n9) Change Team Name\r\n"); err != nil {
					return err
				}
			}
		}
		choice, err := s.classicArgument("Team Command? ", pending)
		if err != nil {
			return err
		}
		w, err = s.Store.View()
		if err != nil {
			return err
		}
		if choice == "1" || strings.EqualFold(choice, "exit") {
			return nil
		}
		switch choice {
		case "2":
			if team.ID != 0 {
				err = errors.New("leave your current team first")
				break
			}
			var name, password string
			name, err = s.classicArgument("Team name? ", pending)
			if err != nil {
				return err
			}
			if name == "" {
				continue
			}
			password, err = s.teamSecret(pending)
			if err != nil {
				break
			}
			err = s.Store.Update(func(w *game.World) error { return w.CreateTeam(id, name, password) })
		case "3":
			if team.ID != 0 {
				err = errors.New("leave your current team first")
				break
			}
			var value, password string
			value, err = s.classicArgument("Team number? ", pending)
			if err != nil {
				return err
			}
			var target int
			target, err = strconv.Atoi(value)
			if err != nil {
				err = errors.New("enter a team number")
				break
			}
			password, err = s.teamSecret(pending)
			if err != nil {
				break
			}
			err = s.Store.Update(func(w *game.World) error { return w.JoinTeam(id, target, password) })
		case "4":
			var answer string
			answer, err = s.classicArgument("Quit your team (Y/[N])? ", pending)
			if err != nil {
				return err
			}
			if !strings.EqualFold(answer, "y") {
				continue
			}
			err = s.Store.Update(func(w *game.World) error { return w.LeaveTeam(id, team.ID) })
		case "5":
			var planets []game.Planet
			planets, err = w.TeamPlanetResources(id)
			if err == nil {
				if len(planets) == 0 {
					err = s.Terminal.Printf("No other team planets.\r\n")
				}
				for _, planet := range planets {
					if err = s.Terminal.Printf("Sector %d: %s (owner %s)\r\n", planet.Sector, planet.Name, w.Players[planet.Owner].Alias); err != nil {
						return err
					}
				}
			}
		case "7":
			if team.Captain != id {
				err = errors.New("only the current team captain may do that")
				break
			}
			var value, answer string
			value, err = s.classicArgument("Member number to remove? ", pending)
			if err != nil {
				return err
			}
			var target int
			target, err = strconv.Atoi(value)
			if err != nil {
				err = errors.New("enter a member number")
				break
			}
			answer, err = s.classicArgument("Remove this member (Y/[N])? ", pending)
			if err != nil {
				return err
			}
			if !strings.EqualFold(answer, "y") {
				continue
			}
			err = s.Store.Update(func(w *game.World) error { return w.BanishTeamMember(id, team.ID, target) })
			if err == nil {
				err = s.Terminal.Printf("Done. Now change your Team Password! Removal does not prevent rejoining.\r\n")
			}
		case "8":
			if team.Captain != id {
				err = errors.New("only the current team captain may do that")
				break
			}
			var password string
			password, err = s.teamSecret(pending)
			if err != nil {
				break
			}
			err = s.Store.Update(func(w *game.World) error { return w.ChangeTeamPassword(id, team.ID, password) })
		case "9":
			if team.Captain != id {
				err = errors.New("only the current team captain may do that")
				break
			}
			var name string
			name, err = s.classicArgument("New team name? ", pending)
			if err != nil {
				return err
			}
			if name == "" {
				continue
			}
			err = s.Store.Update(func(w *game.World) error { return w.RenameTeam(id, team.ID, name) })
		default:
			err = errors.New("Invalid Choice")
		}
		if err != nil {
			if errors.Is(err, io.EOF) {
				return err
			}
			if err = s.Terminal.Printf("%s\r\n", err); err != nil {
				return err
			}
		} else if choice != "5" {
			if err = s.Terminal.Printf("Team change saved.\r\n"); err != nil {
				return err
			}
		}
	}
}
