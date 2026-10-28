package door

import (
	"errors"
	"strconv"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) placeMines(id int, args []string, pending *[]string) error {
	if len(args) > 1 {
		return errors.New("use D [mine quantity]")
	}
	if len(args) == 0 {
		value, err := s.classicArgument("Drop how many mines in this sector? [0] ", pending)
		if err != nil {
			return err
		}
		if strings.TrimSpace(value) == "" {
			return s.Terminal.Printf("Mine placement cancelled.\r\n")
		}
		args = []string{value}
	}
	count, err := strconv.ParseInt(args[0], 10, 64)
	if err != nil {
		return errors.New("choose a whole mine quantity")
	}
	if count == 0 {
		return s.Terminal.Printf("Mine placement cancelled.\r\n")
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	placement, err := w.PrepareMinePlacement(id, count)
	if err != nil {
		return err
	}
	field := int64(0)
	for _, layer := range placement.Layers {
		field += layer.Count
	}
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("Place %d mines in sector %d (currently %d)? Ships entering can be damaged. [y/N] ", count, placement.Sector, field); err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Mine placement cancelled.\r\n")
	}
	var total int64
	err = s.Store.Update(func(w *game.World) error {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired; mine placement cancelled")
		}
		var err error
		total, err = w.CommitMinePlacement(placement)
		if err == nil && !time.Now().Before(s.Deadline) {
			return errors.New("session time expired; mine placement cancelled")
		}
		return err
	})
	if err != nil {
		return err
	}
	return s.Terminal.Printf("Dropped %d mines in sector %d; the sector now contains %d mines. No turn was spent.\r\n", count, placement.Sector, total)
}
