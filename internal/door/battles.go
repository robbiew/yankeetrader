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
	if r.Planet != nil {
		p := r.Planet
		outcome := "Planet survived."
		if p.Neutralized {
			outcome = "Planet neutralized."
		}
		if r.Destroyed {
			outcome = "Planet destroyed."
		}
		if p.Interrupted {
			outcome += " Assault work limit reached."
		}
		if err := s.Terminal.Printf("\r\nPrivate Xannor planetary report #%d | %s | Sector %d\r\n%s: Xannor lost %d fighters; ground %d -> %d.\r\nProduction %.3f/%.3f/%.3f -> %.3f/%.3f/%.3f\r\nCargo %.3f/%.3f/%.3f -> %.3f/%.3f/%.3f\r\n%s\r\n", r.ID, r.At.Format("2006-01-02 15:04 UTC"), r.Sector, p.Name, r.XannorLost, p.GroundBefore, p.GroundAfter, p.ProductionBefore[0], p.ProductionBefore[1], p.ProductionBefore[2], p.ProductionAfter[0], p.ProductionAfter[1], p.ProductionAfter[2], p.CargoBefore[0], p.CargoBefore[1], p.CargoBefore[2], p.CargoAfter[0], p.CargoAfter[1], p.CargoAfter[2], outcome); err != nil {
			return err
		}
		if r.Unread {
			return s.Store.AcknowledgeBattleReport(r.ID)
		}
		return nil
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
