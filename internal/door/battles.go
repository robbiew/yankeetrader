package door

import (
	"errors"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) displayBattle(r game.BattleReport) error {
	if _, err := s.Store.View(); err != nil {
		return err
	}
	if !time.Now().Before(s.Deadline) {
		return errors.New("session time expired")
	}
	outcome := "Your ship survived."
	if r.Destroyed {
		outcome = "Your ship was destroyed by the Xannor."
	}
	if err := s.Terminal.Printf("\r\nPrivate Xannor battle report #%d | %s | Sector %d\r\nXannor lost %d fighters. You lost %d fighters and %d shields.\r\n%s\r\n", r.ID, r.At.Format("2006-01-02 15:04 UTC"), r.Sector, r.XannorLost, r.FightersLost, r.ShieldsLost, outcome); err != nil {
		return err
	}
	if r.Unread {
		return s.Store.AcknowledgeBattleReport(r.ID)
	}
	return nil
}

func (s Session) battleReports(id int, unreadOnly bool) error {
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	reports, err := w.BattleHistory(id, unreadOnly)
	if err != nil {
		return err
	}
	if len(reports) == 0 {
		if unreadOnly {
			return nil
		}
		return s.Terminal.Printf("No retained battle reports.\r\n")
	}
	for i, r := range reports {
		if i > 0 && i%5 == 0 {
			if unreadOnly {
				return s.Terminal.Printf("More unread battle reports remain. Use BATTLES (last 32 retained).\r\n")
			}
			if err := s.Terminal.Printf("More battle reports? [Enter=more, Q=stop] "); err != nil {
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
		if err := s.displayBattle(r); err != nil {
			return err
		}
	}
	return nil
}
