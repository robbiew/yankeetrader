package door

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/store"
)

// finishArrival prints only committed outcomes. Receipt errors retain a committed
// durability warning, and forced travel discards any queued command/course.
func (s Session) finishArrival(actionErr error, pending *[]string) (bool, error) {
	var warning *store.DurabilityError
	if actionErr != nil && !errors.As(actionErr, &warning) {
		// A previous successful write may already have produced a terminal error.
		// Still discard its receipt rather than printing success for a later action.
		_ = s.Store.TakeArrival()
		return false, actionErr
	}
	out := s.Store.TakeArrival()
	if len(out.Warps) == 0 && len(out.Mines) == 0 {
		return false, actionErr
	}
	var output error
	if len(out.Warps) > 0 {
		if pending != nil {
			*pending = nil
		}
		if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
			output = terminal.DiscardTypeahead()
		}
	}
	for _, step := range out.Warps {
		if output == nil {
			output = s.Terminal.Printf("A *-BLACK HOLE-* grabs you! Forced warp saved: sector %d -> %d; heat %d/31; recharge %d turns; meltdown %t.\r\n", step.From, step.Destination, step.Heat, step.RechargeTurns, step.Meltdown)
		}
	}
	if output == nil && len(out.Warps) > 0 {
		output = s.Terminal.Printf("Disruption arrival saved: final sector %d; total action turns spent %d; remaining %d. Queued travel stopped.\r\n", out.FinalSector, out.TurnsSpent, out.TurnsRemaining)
	}
	for _, mines := range out.Mines {
		if output == nil {
			escaped := mines.Escaped
			mines.Escaped = false // Its historical landing need not be the final arrival.
			output = s.showMineOutcome(mines)
			if output == nil && escaped {
				output = s.Terminal.Printf("Mine escape initially reached sector %d before subsequent arrival checks; final ship sector is %d.\r\n", mines.Sector, out.FinalSector)
			}
		}
	}
	if output == nil && out.HostileDefense {
		output = s.Terminal.Printf("Hostile fighters guard sector %d; resolve their encounter before normal actions.\r\n", out.FinalSector)
	}
	return true, errors.Join(actionErr, output)
}

// sessionInputEnd preserves committed storage warnings even through EOF paths.
func sessionInputEnd(err error) error {
	var committed *store.DurabilityError
	if errors.As(err, &committed) {
		return err
	}
	return nil
}
