package door

import (
	"errors"
	"math/rand"
	"strconv"
	"strings"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func (s Session) launchPlasma(args []string, pending *[]string) error {
	return s.launchPlasmaWithRandom(args, pending, rand.Float64)
}
func (s Session) launchPlasmaWithRandom(args []string, pending *[]string, rng func() float64) error {
	if len(args) != 0 && len(args) != 2 {
		return errors.New("use PLASMA [<sector> <quantity>]")
	}
	if len(args) == 0 {
		to, err := s.classicArgument("Send plasma into which sector (blank cancels)? ", pending)
		if err != nil {
			return err
		}
		if strings.TrimSpace(to) == "" {
			return s.Terminal.Printf("Plasma launch cancelled.\r\n")
		}
		n, err := s.classicArgument("How many plasma bolts (1-64)? ", pending)
		if err != nil {
			return err
		}
		args = []string{to, n}
	}
	to, err := strconv.Atoi(args[0])
	if err != nil {
		return errors.New("choose a sector number")
	}
	count, err := strconv.ParseInt(args[1], 10, 64)
	if err != nil {
		return errors.New("choose a whole number of plasma bolts")
	}
	intent, err := s.Store.PreparePlasma(to, count, s.Now, s.Deadline)
	if err != nil {
		return err
	}
	defer s.Store.CancelPlasma(intent)
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err = terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("Launch %d plasma bolts toward sector %d for one turn? Plasma can hit ANYTHING: friendly, cloaked and your own ships or planets. Black holes may redirect it; an unreachable course still spends the launch. Confirm? [y/N] ", count, to); err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Plasma launch cancelled.\r\n")
	}
	out, err := s.Store.LaunchPlasma(intent, rng, s.Now, s.Deadline)
	return s.plasmaReceipt(out, err)
}
func (s Session) plasmaReceipt(out game.PlasmaResult, err error) error {
	var committed *store.DurabilityError
	if err != nil && !errors.As(err, &committed) {
		return err
	}
	savedErr := err
	if out.Destroyed {
		savedErr = errors.Join(savedErr, game.ErrShipDestroyed)
	}
	// Only aggregate impact totals and the launcher's own assets are disclosed.
	// No target names, hidden bank/inventory, hole pair or redirected coordinates.
	if e := s.Terminal.Printf("Plasma launch saved: %d bolts, %d turn. Bolts remaining: %d; turns remaining: %d. Sector fighters destroyed: %d; mines destroyed: %d. Ships struck/destroyed: %d/%d; planets struck/destroyed: %d/%d.\r\n", out.Launched, out.TurnsSpent, out.BoltsRemaining, out.TurnsRemaining, out.SectorFighters, out.MinesDestroyed, out.ShipsHit, out.ShipsDestroyed, out.PlanetsHit, out.PlanetsDestroyed); e != nil {
		return errors.Join(savedErr, e)
	}
	if e := s.Terminal.Printf("Your losses: %d fighters and %d shields. Salvage credited before any later losses: %d credits, %d holds, %d missiles, %d plasma, %d ground forces; cargo %d/%d/%d. Wreck mines dropped/disarmed: %d/%d.\r\n", out.OwnFightersLost, out.OwnShieldsLost, out.Salvage.Credits, out.Salvage.Holds, out.Salvage.Missiles, out.Salvage.Plasma, out.Salvage.Ground, out.Salvage.Cargo[0], out.Salvage.Cargo[1], out.Salvage.Cargo[2], out.Dropped, out.Disarmed); e != nil {
		return errors.Join(savedErr, e)
	}
	if out.Aftermath.Spent > 0 {
		if e := s.Terminal.Printf("Local wreck-mine aftermath saved: %d mines spent; escape %t.\r\n", out.Aftermath.Spent, out.Aftermath.Escaped); e != nil {
			return errors.Join(savedErr, e)
		}
	}
	if out.RouteUnavailable {
		if e := s.Terminal.Printf("No course reached the requested destination; the accepted launch was spent.\r\n"); e != nil {
			return errors.Join(savedErr, e)
		}
	}
	for _, reward := range out.HQRewards {
		if e := s.Terminal.Printf("Xannor HQ victory reward saved: %d credits actually added.\r\n", reward.Credits); e != nil {
			return errors.Join(savedErr, e)
		}
	}
	if out.SelfDestroyed {
		if e := s.Terminal.Printf("Self-inflicted plasma death: replacement is available after the next UTC midnight.\r\n"); e != nil {
			return errors.Join(savedErr, e)
		}
	}
	if out.Destroyed {
		if e := s.Terminal.Printf("Your ship was destroyed during the launch aftermath; this login has ended.\r\n"); e != nil {
			return errors.Join(savedErr, e)
		}
	}
	return savedErr
}
