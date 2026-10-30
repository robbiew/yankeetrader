package door

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"math/rand"
	"strings"
	"time"
)

func (s Session) showMineOutcome(out game.MineOutcome) error {
	if out.Bursts == 0 {
		return nil
	}
	if err := s.Terminal.Printf("Mine encounter saved: %d mines exploded in %d bursts.\r\n", out.Spent, out.Bursts); err != nil {
		return err
	}
	if out.ScannerLost {
		if err := s.Terminal.Printf("Danger scanner destroyed by mines.\r\n"); err != nil {
			return err
		}
	}
	if out.Destroyed {
		if out.Killer == 0 {
			if err := s.Terminal.Printf("Your ship was destroyed by unowned mines. Reconnect for a replacement.\r\n"); err != nil {
				return err
			}
			return game.ErrShipDestroyed
		}
		if err := s.Terminal.Printf("Your ship was destroyed by mines from player %d. Reconnect for a replacement.\r\n", out.Killer); err != nil {
			return err
		}
		return game.ErrShipDestroyed
	}
	if out.Escaped {
		return s.Terminal.Printf("Emergency warp escaped to safe sector %d.\r\n", out.Sector)
	}
	return nil
}
func (s Session) resolveCurrentMines(id int) error {
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	if !w.HasMineEncounter(id) {
		return nil
	}
	out, err := s.Store.ResolveMines(s.Now(), rand.Float64)
	if err != nil {
		return err
	}
	return s.showMineOutcome(out)
}
func (s Session) moveShip(id, to int, pending *[]string) error {
	if handled, err := s.scannedMove(id, to, pending, nil); handled || err != nil {
		return err
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	entry, err := w.PrepareMineEntry(id, to)
	if err != nil {
		return err
	}
	if len(entry.Layers) == 0 {
		if err = s.Store.UpdateWithSpies(func(w *game.World) error { return w.Move(id, to) }, s.Now(), s.Deadline); err != nil {
			return err
		}
		return s.Terminal.Printf("Moved to sector %d.\r\n", to)
	}
	total := int64(0)
	for _, l := range entry.Layers {
		total += l.Count
	}
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("Sector %d contains %d mines. Enter this dangerous sector? [y/N] ", to, total); err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Minefield entry cancelled.\r\n")
	}
	var out game.MineOutcome
	err = s.Store.UpdateWithSpies(func(w *game.World) error {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		var err error
		out, err = w.CommitMineEntry(entry, rand.Float64, s.Now())
		if err == nil && !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		return err
	}, s.Now(), s.Deadline)
	if err != nil {
		return err
	}
	if err = s.Terminal.Printf("Moved into sector %d.\r\n", to); err != nil {
		return err
	}
	return s.showMineOutcome(out)
}
