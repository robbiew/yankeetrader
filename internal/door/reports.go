package door

import (
	"errors"
	"strconv"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func (s Session) computerReport(id int, command string, args []string, pending *[]string) error {
	if command == "myplanets" {
		if len(args) != 0 {
			return errors.New("use MYPLANETS")
		}
		w, err := s.Store.View()
		if err != nil {
			return err
		}
		planets, err := w.OwnPlanets(id)
		if err != nil {
			return err
		}
		if err = s.Terminal.Printf("\r\nScanning...\r\n\r\n"); err != nil {
			return err
		}
		if len(planets) == 0 {
			return s.Terminal.Printf("None found.\r\n")
		}
		for _, planet := range planets {
			if err = s.Terminal.Printf("Planet: %-41s Sector: %d\r\n", planet.Name, planet.Sector); err != nil {
				return err
			}
		}
		return nil
	}
	if len(args) > 1 {
		return errors.New("use PORTREPORT [sector] or PLANETREPORT [sector]")
	}
	if len(args) == 0 {
		prompt := "Enter sector number port is in -=> "
		if command == "planetreport" {
			prompt = "What sector number is the planet in? "
		}
		value, err := s.classicArgument(prompt, pending)
		if err != nil {
			return err
		}
		if strings.TrimSpace(value) == "" {
			return s.Terminal.Printf("Report cancelled.\r\n")
		}
		args = []string{value}
	}
	sector, err := strconv.Atoi(args[0])
	if err != nil {
		return errors.New("choose a whole sector number")
	}
	if !time.Now().Before(s.Deadline) {
		return errors.New("session time expired")
	}
	if command == "planetreport" {
		report, caller, err := s.Store.PlanetReport(sector, s.Now, s.Deadline)
		return s.planetReportReceipt(report, &caller, err)
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	report, err := w.RemotePortReport(id, sector, s.Now())
	if err != nil {
		return err
	}
	if !report.Available {
		return s.Terminal.Printf("No information available.\r\n")
	}
	if err = s.portColor(6); err != nil {
		return err
	}
	if err = s.Terminal.Printf("\r\nCommerce report for %s: %s\r\n\r\n Items         Status      # units    in holds   Cost\r\n=======       =========   =========   ========   ====\r\n", report.Name, s.Now().Format("01-02-2006 15:04:05")); err != nil {
		return err
	}
	for i, name := range game.Goods {
		status, color := "Buying", 6
		if report.Selling[i] {
			status, color = "Selling", 2
		}
		if err = s.portColor(color); err != nil {
			return err
		}
		label := strings.ToUpper(name[:1]) + name[1:] + strings.Repeat(".", 13-len(name))
		if err = s.Terminal.Printf("%s  %-7s   %9d   %8d   %4d\r\n", label, status, int64(report.Supply[i]), report.Cargo[i], report.Prices[i]); err != nil {
			return err
		}
	}
	return s.portColor(6)
}

func (s Session) planetReportReceipt(report game.PlanetReport, caller *game.Player, saved error) error {
	var warning *store.DurabilityError
	if saved != nil && !errors.As(saved, &warning) {
		return saved
	}
	return errors.Join(saved, s.showPlanetReport(report, caller))
}
func (s Session) showPlanetReport(report game.PlanetReport, caller *game.Player) error {
	if !report.Available {
		if report.TurnSpent {
			return s.Terminal.Printf("Planet report saved: No information available. One turn spent: %s. Turns remaining: %d.\r\n", report.Unavailable, caller.Turns)
		}
		return s.Terminal.Printf("No information available.\r\n")
	}
	if report.Details == nil {
		return s.Terminal.Printf("\r\nPlanet: %s -*- Ground Forces: %d\r\n", report.Name, report.Ground)
	}
	if err := s.planetColor(3); err != nil {
		return err
	}
	return s.planetDisplay(caller, *report.Details)
}
