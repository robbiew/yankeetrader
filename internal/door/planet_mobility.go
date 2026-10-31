package door

import (
	"errors"
	"fmt"
	"math/rand"
	"strconv"
	"strings"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

func (s Session) thrusters(token string, args []string, pending *[]string) error {
	return s.thrustersWithRandom(token, args, pending, rand.Float64)
}
func (s Session) thrustersWithRandom(token string, args []string, pending *[]string, rng func() float64) error {
	if len(args) > 1 {
		return errors.New("use THRUST <destination> while landed")
	}
	value := ""
	var err error
	if len(args) == 1 {
		value = args[0]
	} else {
		value, err = s.classicArgument("Planet thrusters destination (blank cancels): ", pending)
	}
	if err != nil {
		return err
	}
	if value == "" {
		return s.Terminal.Printf("Planet thrusters cancelled.\r\n")
	}
	to, err := strconv.Atoi(value)
	if err != nil {
		return errors.New("enter a whole destination sector")
	}
	entry, err := s.Store.PreparePlanetAction("thrusters", token, to, 0, s.Now, s.Deadline)
	if err != nil {
		return err
	}
	defer s.Store.CancelPlanetAction(entry)
	if err = s.freshPlanetPrompt(pending, fmt.Sprintf("Planet route %v; quote %d turns (10 per hop). Collision or stress can destroy the planet and fighters. Reached mines stop travel and can damage, warp or destroy your ship; hostile fighters stop the route for an encounter. Completed hops remain spent. Engage? [y/N] ", entry.Path, 10*(len(entry.Path)-1))); err != nil {
		return err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return s.Terminal.Printf("Planet thrusters cancelled; no movement or turns spent.\r\n")
	}
	out, err := s.Store.CommitPlanetAction(entry, rng, s.Now, s.Deadline)
	return s.planetActionReceipt(out, err)
}
func (s Session) freshPlanetPrompt(pending *[]string, prompt string) error {
	*pending = nil
	if terminal, ok := s.Terminal.(interface{ DiscardTypeahead() error }); ok {
		if err := terminal.DiscardTypeahead(); err != nil {
			return err
		}
	}
	return s.Terminal.Printf("%s", prompt)
}

// forceLanding is shared by compact LAND and classic denied landing. Successful
// capture returns the fresh grant, allowing each interface to resume normally.
func (s Session) forceLanding(id int, pending *[]string) (string, error) {
	return s.forceLandingWithRandom(id, pending, rand.Float64)
}
func (s Session) forceLandingWithRandom(id int, pending *[]string, rng func() float64) (string, error) {
	w, err := s.Store.View()
	if err != nil {
		return "", err
	}
	target, adopt, err := w.LandingTarget(id, s.Now())
	if err != nil {
		return "", err
	}
	quantity := int64(0)
	if !adopt {
		if w.Players[id].Ground == 0 {
			return "", errors.New("permission to land is denied by ground defenses; no carried ground forces for an assault")
		}
		if err = s.freshPlanetPrompt(pending, fmt.Sprintf("\r\n\r\nSensors report ground forces of %d units. You have %d.\r\nDo you wish to try to force a landing? [y/N] ", target.Ground, w.Players[id].Ground)); err != nil {
			return "", err
		}
		if s.Classic {
			if err = s.planetColor(7); err != nil {
				return "", err
			}
		}
		consent, err := s.readAttackConfirmation()
		if s.Classic {
			if colorErr := s.planetColor(3); err == nil {
				err = colorErr
			}
		}
		if err != nil {
			return "", err
		}
		if !strings.EqualFold(strings.TrimSpace(consent), "y") {
			if s.Classic {
				return "", nil
			}
			return "", s.Terminal.Printf("Forced landing cancelled.\r\n")
		}
		answer, err := s.classicArgument(fmt.Sprintf("Ground defenses: %d; carried: %d. Commit how many ground forces? (0/blank cancels): ", target.Ground, w.Players[id].Ground), pending)
		if err != nil {
			return "", err
		}
		if answer == "" || answer == "0" {
			return "", s.Terminal.Printf("Forced landing cancelled.\r\n")
		}
		quantity, err = strconv.ParseInt(answer, 10, 64)
		if err != nil || quantity < 1 {
			return "", errors.New("enter a positive whole ground force quantity")
		}
	}
	entry, err := s.Store.PreparePlanetAction("assault", "", 0, quantity, s.Now, s.Deadline)
	if err != nil {
		return "", err
	}
	defer s.Store.CancelPlanetAction(entry)
	prompt := fmt.Sprintf("Force landing on %s with %d ground forces? Committed troops are spent; captured survivors become its garrison. Combat is bounded to %d rounds; unfinished survivors retreat without refund. No turn fee. [y/N] ", terminalLabel(target.Name), quantity, game.MaxGroundRounds)
	if adopt {
		prompt = fmt.Sprintf("Adopt the vacant government on %s? Unrest reduces its garrison; no carried troops or turns are spent. [y/N] ", terminalLabel(target.Name))
	}
	if err = s.freshPlanetPrompt(pending, prompt); err != nil {
		return "", err
	}
	answer, err := s.readAttackConfirmation()
	if err != nil {
		return "", err
	}
	if !strings.EqualFold(strings.TrimSpace(answer), "y") {
		return "", s.Terminal.Printf("Forced landing cancelled; no troops spent.\r\n")
	}
	out, err := s.Store.CommitPlanetAction(entry, rng, s.Now, s.Deadline)
	if err = s.planetActionReceipt(out, err); err != nil {
		return "", err
	}
	if !out.Captured {
		return "", nil
	}
	return out.LandingToken, nil
}
func (s Session) planetActionReceipt(out game.PlanetReceipt, err error) error {
	var committed *store.DurabilityError
	if err != nil && !errors.As(err, &committed) {
		return err
	}
	var output error
	if out.Kind == "thrusters" {
		output = s.Terminal.Printf("Planet thrusters saved: %s; completed %d hops, sector %d -> %d (destination %d). Transport %d turns; aftermath %d; total %d; remaining %d. Planet destroyed: %t; planet sector %d; stop: %s. Fighters lost %d; remaining %d. All landing grants revoked.\r\n", terminalLabel(out.Name), out.Hops, out.From, out.FinalSector, out.Destination, out.TransportTurns, out.AftermathTurns, out.TurnsSpent, out.TurnsRemaining, out.Destroyed, out.PlanetSector, out.Stop, out.FightersLost, out.FightersRemaining)
		if output == nil {
			output = s.showMineOutcome(out.Mines)
		}
		if output == nil && out.HostileDefense {
			output = s.Terminal.Printf("Hostile fighters remain here; resolve their encounter before acting.\r\n")
		}
	} else {
		output = s.Terminal.Printf("Ground action saved on %s: captured %t; adopted %t; unfinished %t; %d rounds. Committed %d; attackers lost %d; retreated without refund %d; defenders lost %d; garrison %d; carried ground remaining %d. Turns spent %d; remaining %d.\r\n", terminalLabel(out.Name), out.Captured, out.Adopted, out.Interrupted, out.Rounds, out.Committed, out.AttackersLost, out.Retreated, out.DefendersLost, out.Garrison, out.GroundRemaining, out.TurnsSpent, out.TurnsRemaining)
	}
	return errors.Join(err, output)
}
