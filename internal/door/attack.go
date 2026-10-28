package door

import (
	"errors"
	gd "github.com/robbiew/godoors"
	"math/rand"
	"strconv"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

// DiscardTypeahead prevents already queued terminal keys approving a destructive
// confirmation. Bounded draining cannot hold a session indefinitely.
func (g *GoDoors) DiscardTypeahead() error {
	g.pending = nil
	g.savedLine = ""
	for i := 0; i < 4096; i++ {
		_, _, err := g.read(time.Millisecond)
		if errors.Is(err, gd.ErrInputTimeout) {
			return nil
		}
		if err != nil {
			return err
		}
	}
	return errors.New("too much queued input; attack cancelled")
}

func (s Session) attackShip(id int, args []string, pending *[]string, visibility *game.Visibility) error {
	if len(args) != 0 && len(args) != 2 {
		return errors.New("use ATTACK [<ship number> <fighters>]")
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	candidates, err := w.VisibleAttackCandidates(id, visibility)
	if err != nil {
		return err
	}
	if len(candidates) == 0 {
		return s.Terminal.Printf("No visible enemy ships here.\r\n")
	}
	if err = s.Terminal.Printf("Visible enemy ships:\r\n"); err != nil {
		return err
	}
	for _, ship := range candidates {
		if err = s.Terminal.Printf("%d: %s | Fighters %d | Shields %d\r\n", ship.ID, ship.Alias, ship.Fighters, ship.Shields); err != nil {
			return err
		}
	}
	if len(args) == 0 {
		target, err := s.classicArgument("Attack which ship number (blank cancels)? ", pending)
		if err != nil {
			return err
		}
		if strings.TrimSpace(target) == "" {
			return s.Terminal.Printf("Attack cancelled.\r\n")
		}
		force, err := s.classicArgument("How many fighters will you commit? ", pending)
		if err != nil {
			return err
		}
		args = []string{target, force}
	}
	target, err := strconv.Atoi(args[0])
	if err != nil {
		return errors.New("choose a visible ship number")
	}
	var alias string
	for _, ship := range candidates {
		if ship.ID == target {
			alias = ship.Alias
		}
	}
	if alias == "" {
		return errors.New("choose a visible enemy ship from this list")
	}
	fighters, err := strconv.ParseInt(args[1], 10, 64)
	if err != nil {
		return errors.New("choose a whole number of available fighters")
	}
	intent, err := w.PrepareVisibleAttack(id, target, fighters, visibility)
	if err != nil {
		return err
	}
	// Throw away command-chain answers and actual terminal typeahead before the
	// prompt. Only a separate, exact Y may authorize this one prepared intent.
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("Attack %s with %d fighters? Damage and losses save immediately. [y/N] ", alias, fighters); err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Attack cancelled.\r\n")
	}
	if !time.Now().Before(s.Deadline) {
		return errors.New("session time expired; attack cancelled")
	}
	var result game.ShipDuelResult
	err = s.Store.Update(func(w *game.World) error {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired; attack cancelled")
		}
		var err error
		result, err = w.CommitVisibleAttack(intent, visibility, rand.Float64, s.Now())
		if err == nil && !time.Now().Before(s.Deadline) {
			return errors.New("session time expired; attack cancelled")
		}
		return err
	})
	if err != nil {
		return err
	}
	if err = s.Terminal.Printf("Attack saved. Lost %d fighters; target has %d fighters and %d shields.\r\n", result.AttackerLosses, result.DefenderFighters, result.DefenderShields); err != nil {
		return err
	}
	if !result.Destroyed {
		return nil
	}
	loot := result.Salvage
	if err = s.Terminal.Printf("%s destroyed. Salvaged %d credits, %d holds, %d missiles, %d plasma, %d ground forces, %d mines; cargo %d ore / %d organics / %d equipment.\r\n", alias, loot.Credits, loot.Holds, loot.Missiles, loot.Plasma, loot.Ground, loot.Mines, loot.Cargo[0], loot.Cargo[1], loot.Cargo[2]); err != nil {
		return err
	}
	if result.DisarmedMines > 0 {
		return s.Terminal.Printf("Earth protection safely disposed of %d unsalvaged mines.\r\n", result.DisarmedMines)
	}
	if result.DroppedMines > 0 {
		if err = s.Terminal.Printf("Wreck dropped %d unsalvaged mines.\r\n", result.DroppedMines); err != nil {
			return err
		}
	}
	return s.showMineOutcome(result.MineAftermath)
}

// Command-repeat syntax must not transform a confirmation into a saved Y.
func (s Session) readAttackConfirmation() (string, error) {
	if g, ok := s.Terminal.(*GoDoors); ok {
		mode := g.commandMode
		g.commandMode = false
		defer func() { g.commandMode = mode; g.savedLine = "" }()
	}
	return s.readClassicLine()
}
