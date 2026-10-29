package door

import (
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func (s Session) hireSpies(token string, args []string, pending *[]string) error {
	if len(args) == 0 {
		answer, err := s.classicArgument("Hire how many spies? [0]? ", pending)
		if err != nil {
			return err
		}
		if answer == "" || answer == "0" {
			return nil
		}
		count, err := strconv.Atoi(answer)
		if err != nil || count < 1 || count > game.MaxSpies {
			return errors.New("max spies allowed is 3; choose at least one")
		}
		locations, _, err := s.Store.SpySnapshot(false)
		if err != nil {
			return err
		}
		if count > game.MaxSpies-len(locations) {
			return errors.New("max spies allowed is 3")
		}
		for i := 0; i < count; i++ {
			sector, err := s.classicArgument(fmt.Sprintf("Start spy # %d in what sector? ", len(locations)+i+1), pending)
			if err != nil {
				return err
			}
			args = append(args, sector)
		}
	}
	sectors := make([]int, len(args))
	for i, arg := range args {
		var err error
		sectors[i], err = strconv.Atoi(arg)
		if err != nil {
			return errors.New("choose an existing starting sector for every spy")
		}
	}
	if err := s.Store.HireSpies(token, sectors, s.Now, s.Deadline); err != nil {
		var durability *store.DurabilityError
		if !errors.As(err, &durability) {
			return err
		}
		if err = s.Terminal.Printf("Spies hired. %s\r\n", err); err != nil {
			return err
		}
	}
	return s.listSpies()
}
func (s Session) listSpies() error {
	locations, _, err := s.Store.SpySnapshot(false)
	if err != nil {
		return err
	}
	if len(locations) == 0 {
		return s.Terminal.Printf("You do not have any spies!\r\n")
	}
	for i, sector := range locations {
		if err := s.Terminal.Printf("Spy # %d will hunt in sector %d.\r\n", i+1, sector); err != nil {
			return err
		}
	}
	return nil
}
func (s Session) intelligence(unread bool) error {
	_, reports, err := s.Store.SpySnapshot(unread)
	if err != nil {
		return err
	}
	if len(reports) == 0 && !unread {
		return s.Terminal.Printf("No intelligence reports this login.\r\n")
	}
	for i, report := range reports {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		if !unread && i > 0 && i%5 == 0 {
			if err = s.Terminal.Printf("More intelligence? [Enter=more, Q=stop] "); err != nil {
				return err
			}
			answer, e := s.readLiteralLine()
			if e != nil {
				return e
			}
			if strings.TrimSpace(answer) != "" {
				return nil
			}
		}
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		// Recheck the generation immediately before each report, including history.
		if _, err = s.Store.View(); err != nil {
			return err
		}
		if err = s.Terminal.Printf("\r\n*** RADIO MESSAGE FROM SPY #%d! The following was found in sector %d:\r\n", report.Spy, report.Sector); err != nil {
			return err
		}
		if report.Mines > 0 {
			if err = s.Terminal.Printf("** WARNING! SECTOR HAS %d MINES! **\r\n", report.Mines); err != nil {
				return err
			}
		}
		if report.Planet != "" {
			if err = s.Terminal.Printf("Planet: %s * Forces: %d\r\n", report.Planet, report.Ground); err != nil {
				return err
			}
		}
		if report.DefenseFighters > 0 {
			if err = s.Terminal.Printf("Fighters in sector: %d (Belong to %s)\r\n", report.DefenseFighters, report.DefenseOwner); err != nil {
				return err
			}
		}
		if report.Unread {
			if err = s.Store.AcknowledgeSpy(report.ID); err != nil {
				return err
			}
		}
	}
	return nil
}
