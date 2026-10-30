package door

import (
	"errors"
	"math/rand"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) buyScanner(id int, token string, quantity int64) error {
	var balance int64
	err := s.Store.Update(func(w *game.World) error {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		if err := w.Equip(id, token, "scanner", quantity, s.Now()); err != nil {
			return err
		}
		balance = w.Players[id].Credits
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		return nil
	})
	if err != nil {
		return err
	}
	return s.Terminal.Printf("Danger scanner installed and saved. Credits spent: %d. Balance: %d.\r\n", game.DangerScannerPrice, balance)
}
func (s Session) manualWarp(id int, args []string, pending *[]string) error {
	return s.warpWithRandom(id, args, pending, rand.Float64)
}
func (s Session) warpWithRandom(id int, args []string, pending *[]string, rng func() float64) error {
	if len(args) != 0 {
		return errors.New("use WARP (no destination; emergency landing is random)")
	}
	entry, err := s.Store.PrepareWarp(s.Deadline)
	if err != nil {
		return err
	}
	defer s.Store.CancelWarp(entry)
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("Emergency warp risks engine meltdown and a random dangerous landing, including your current or avoided sectors. Recharge may spend all %d remaining turns. Engage? [y/N] ", entry.Ship.Turns); err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Emergency warp cancelled.\r\n")
	}
	out, err := s.Store.Warp(entry, rng, s.Now, s.Deadline)
	if err != nil {
		return err
	}
	if err = s.Terminal.Printf("Emergency warp saved: landed in sector %d; heat %d/31; recharge %d turns; aftermath %d turns; total spent %d.\r\n", out.Destination, out.Heat, out.RechargeTurns, out.AftermathTurns, out.TurnsSpent); err != nil {
		return err
	}
	if out.Meltdown {
		if err = s.Terminal.Printf("Engine meltdown consumed every remaining turn. Daily maintenance restores turns.\r\n"); err != nil {
			return err
		}
	}
	if err = s.showMineOutcome(out.Mines); err != nil {
		return err
	}
	if out.HostileDefense {
		return s.Terminal.Printf("Hostile fighters guard sector %d. Resolve the defense encounter before normal actions.\r\n", out.FinalSector)
	}
	return nil
}

// scannedMove handles only an installed scanner's dangerous hop. A warning
// always discards the remaining course, including when its one hop is accepted.
func (s Session) scannedMove(id, to int, pending *[]string, course []int) (bool, error) {
	w, err := s.Store.View()
	if err != nil {
		return false, err
	}
	if !w.Players[id].DangerScanner {
		return false, nil
	}
	if len(course) > 0 {
		if err = w.CheckCourse(id, course); err != nil {
			return false, err
		}
	}
	entry, err := w.PrepareScannerEntry(id, to)
	if err != nil {
		return false, err
	}
	if !entry.Dangerous() {
		return false, nil
	}
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return true, err
		}
	}
	if err = s.Terminal.Printf("Danger scanner has detected the following in sector %d!\r\n", to); err != nil {
		return true, err
	}
	var mines int64
	for _, l := range entry.Layers {
		mines += l.Count
	}
	if mines > 0 {
		if err = s.Terminal.Printf("** %d SECTOR MINES! **\r\n", mines); err != nil {
			return true, err
		}
	}
	if entry.Defense != nil {
		owner := "The Xannor"
		if entry.Defense.Owner == game.MercenaryOwner {
			owner = "Mercenaries"
		} else if entry.Defense.Owner > 0 {
			owner = w.Players[entry.Defense.Owner].Alias
		}
		if err = s.Terminal.Printf("*** %d Fighters Belonging to %s\r\n", entry.Defense.Fighters, owner); err != nil {
			return true, err
		}
	}
	if err = s.Terminal.Printf("*** WARP DRIVE DEACTIVATED ***\r\nQueued travel stopped. Move into sector %d? [y/N] ", to); err != nil {
		return true, err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return true, err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return true, s.Terminal.Printf("Scanner entry cancelled. Completed moves remain saved.\r\n")
	}
	var out game.MineOutcome
	err = s.Store.UpdateWithSpies(func(w *game.World) error {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		if len(course) > 0 {
			if e := w.CheckCourse(id, course); e != nil {
				return e
			}
		}
		var e error
		out, e = w.CommitScannerEntry(entry, rand.Float64, s.Now())
		return e
	}, s.Now(), s.Deadline)
	if err != nil {
		return true, err
	}
	if err = s.Terminal.Printf("Scanner entry saved into sector %d. One movement turn spent.\r\n", to); err != nil {
		return true, err
	}
	return true, s.showMineOutcome(out)
}
