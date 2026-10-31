package door

import (
	"errors"
	"fmt"
	"math"
	"strconv"
	"strings"

	"github.com/robbiew/yankeetrader/internal/game"
)

// Read-only previews use the same permission/token/update rules as committed
// actions. Each mutation repeats those checks against the locked current world.
func (s Session) planetView(id int, token string) (*game.World, *game.Player, game.Planet, error) {
	w, err := s.Store.View()
	if err != nil {
		return nil, nil, game.Planet{}, err
	}
	planet, err := w.PlanetStatus(id, token, s.Now())
	if err != nil {
		return nil, nil, game.Planet{}, err
	}
	return w, w.Players[id], planet, nil
}

func (s Session) planetColor(attr int) error {
	if !s.ANSI {
		return nil
	}
	codes := []int{30, 34, 32, 36, 31, 35, 33, 37}
	style := ""
	if attr&8 != 0 {
		style += "1;"
	}
	if attr&128 != 0 {
		style += "5;"
	}
	return s.Terminal.Printf("\x1b[0;%s%d;40m", style, codes[attr&7])
}

func (s Session) planetAnswer(prompt string, pending *[]string, attr int) (string, error) {
	if err := s.planetColor(attr); err != nil {
		return "", err
	}
	if err := s.Terminal.Printf("%s", prompt); err != nil {
		return "", err
	}
	if err := s.planetColor(7); err != nil {
		return "", err
	}
	queued := len(*pending) > 0
	answer, err := s.classicArgument("", pending)
	if err == nil && queued {
		err = s.Terminal.Printf("%s\r\n", answer)
	}
	colorErr := s.planetColor(attr)
	if err != nil {
		return "", err
	}
	return answer, colorErr
}

func (s Session) classicLand(id int, pending *[]string) error {
	if err := s.planetColor(2); err != nil {
		return err
	}
	if err := s.Terminal.Printf("\r\n<Land/Create planet>\r\n"); err != nil {
		return err
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	p := w.Players[id]
	if p == nil {
		return errors.New("player no longer exists")
	}
	planet := w.Planets[w.Sectors[p.Sector].Planet]
	if planet == nil {
		return s.classicCreate(id, pending, p.Credits, p.Sector)
	}
	if err = s.planetColor(3); err != nil {
		return err
	}
	if err = s.Terminal.Printf("\r\nLanding...\r\n"); err != nil {
		return err
	}
	var token string
	err = s.Store.Update(func(w *game.World) error {
		if err := w.Land(id, s.Now()); err != nil {
			return err
		}
		token = w.Players[id].PlanetToken
		return nil
	})
	if err != nil {
		if err.Error() != "permission to land is denied by ground defenses" {
			return err
		}
		if err = s.Terminal.Printf("\r\nThis is space traffic control at planet %s\r\nPermission to land is ", planet.Name); err != nil {
			return err
		}
		if err = s.planetColor(0x8e); err != nil {
			return err
		}
		if err = s.Terminal.Printf("DENIED!"); err != nil {
			return err
		}
		if err = s.planetColor(3); err != nil {
			return err
		}
		token, err = s.forceLanding(id, pending)
		if err != nil {
			return err
		}
		if token != "" {
			return s.finishClassicLanding(id, token, pending)
		}

		w, err = s.Store.View()
		if err != nil {
			return err
		}
		return s.classicSector(w, id)
	}
	return s.finishClassicLanding(id, token, pending)
}

func (s Session) finishClassicLanding(id int, token string, pending *[]string) error {
	var err error

	if err = s.classicPlanet(id, token, pending); err != nil {
		return err
	}
	// A newer landing from a different connection must retain its token.
	if err = s.Store.Update(func(w *game.World) error {
		if p := w.Players[id]; p != nil && p.PlanetToken == token {
			p.PlanetToken = ""
			p.LandedPlanet = 0
		}
		return nil
	}); err != nil {
		return err
	}
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	return s.classicSector(w, id)
}

func (s Session) classicCreate(id int, pending *[]string, credits int64, sector int) error {
	if err := s.Terminal.Printf("\r\nThere is no planet in this sector.\r\nPlanets cost 25000 credits.\r\nYou have %d credits.\r\n", credits); err != nil {
		return err
	}
	if credits < 25000 {
		return s.Terminal.Printf("You do not have enough credits.\r\n")
	}
	answer, err := s.planetAnswer("Do you wish to buy a planet(Y/N) [N]? ", pending, 2)
	if err != nil {
		return err
	}
	if !strings.EqualFold(answer, "y") {
		return nil
	}
	for {
		name, err := s.planetAnswer("\r\nWhat do you want to name this planet? -=>", pending, 2)
		if err != nil {
			return err
		}
		if len(name) < 1 || len(name) > 41 {
			if err = s.Terminal.Printf("Use a printable planet name of 1 to 41 characters.\r\n"); err != nil {
				return err
			}
			continue
		}
		answer, err = s.planetAnswer(fmt.Sprintf("\r\n\"%s\" Is this OK? (Y/n) [Y] ?", name), pending, 2)
		if err != nil {
			return err
		}
		if answer != "" && !strings.EqualFold(answer, "y") {
			continue
		}
		if err = s.Store.Update(func(w *game.World) error {
			if w.Players[id] == nil || w.Players[id].Sector != sector {
				return errors.New("sector changed; start planet creation again")
			}
			return w.CreatePlanet(id, name, s.Now())
		}); err != nil {
			return err
		}
		if err = s.Terminal.Printf("\r\nPlanet \"%s\" created with Genesis Device!\r\n\r\nTo increase productivity on your new planet, spend credits [$] on it.\r\n", name); err != nil {
			return err
		}
		w, err := s.Store.View()
		if err != nil {
			return err
		}
		return s.classicSector(w, id)
	}
}

const planetHelp = "\r\n<Help>\r\n\r\n1 - Take Ore\r\n2 - Take Organics\r\n3 - Take Equipment\r\n4 - Take Fighters\r\n5 - Take Missiles\r\n6 - Take Mines\r\n9 - Take Plasma Bolts\r\nA - Take <A>ll (Default)\r\nB - Planet's <B>ank\r\nD - <D>isplay Planet\r\nF - Take/Leave Ground <F>orces\r\nL - <L>eave Planet\r\nN - Re-<N>ame Planet\r\nT - <T>ransfer Cargo to Planet\r\n! - Use Planet Thrusters\r\n$ - Raise Productivity\r\n"

func planetRates(p game.Planet) [9]int64 {
	total := p.Production[0] + p.Production[1] + p.Production[2]
	bank := float64(p.Bank)
	// The original report uses the MBF single-precision 1% constant. This
	// display rounding does not change the game's exact integer interest rules.
	percent := float64(float32(.01))
	return [9]int64{int64(p.Production[0] + bank/10000), int64(p.Production[1] + bank/20000), int64(p.Production[2] + bank/30000), int64(math.Floor(total) + bank/500), int64(math.Floor(total/2500) + bank/100000), int64(math.Floor(total/25000) + bank/250000), int64(bank * percent), int64(float64(p.Ground)*percent + bank/10000), int64(math.Floor(total/100000) + bank/25000000)}
}
func (s Session) planetDisplay(p *game.Player, planet game.Planet) error {
	if err := s.Terminal.Printf("\r\nPlanet: %s\r\n\r\n Item           Production     Amount    In Holds\r\n=============  ============   ========  ==========\r\n", planet.Name); err != nil {
		return err
	}
	labels := []string{"Ore..........", "Organics.....", "Equipment....", "Fighters.....", "Missiles.....", "Mines........", "Credits......", "Forces.......", "Plasma bolts."}
	amounts := []int64{int64(planet.Cargo[0]), int64(planet.Cargo[1]), int64(planet.Cargo[2]), int64(planet.Fighters), int64(planet.Missiles), int64(planet.Mines), planet.Bank, planet.Ground, int64(planet.Plasma)}
	holds := []int64{p.Cargo[0], p.Cargo[1], p.Cargo[2], p.Fighters, p.Missiles, p.Mines, p.Credits, p.Ground, p.Plasma}
	rates := planetRates(planet)
	for i, label := range labels {
		if err := s.Terminal.Printf("%s %12d   %8d  %10d\r\n", label, rates[i], amounts[i], holds[i]); err != nil {
			return err
		}
	}
	return nil
}

func (s Session) classicPlanet(id int, token string, pending *[]string) error {
	_, p, planet, err := s.planetView(id, token)
	if err != nil {
		return err
	}
	if err = s.planetColor(3); err != nil {
		return err
	}
	if err = s.planetDisplay(p, planet); err != nil {
		return err
	}
	for {
		_, p, planet, err = s.planetView(id, token)
		if err != nil {
			return err
		}
		if err = s.planetColor(3); err != nil {
			return err
		}
		if err = s.Terminal.Printf("\r\nYou have %d free cargo holds.\r\n", p.Holds-p.Cargo[0]-p.Cargo[1]-p.Cargo[2]); err != nil {
			return err
		}
		choice, err := s.planetAnswer(fmt.Sprintf("\r\nTime: %s  Planet command (?=help) [A]? ", s.timeLeft()), pending, 3)
		if err != nil {
			return err
		}
		switch strings.ToLower(choice) {
		case "l", "leave":
			return nil
		case "?", "help":
			err = s.Terminal.Printf("%s", planetHelp)
		case "d", "planet":
			err = s.planetDisplay(p, planet)
		case "a", "":
			err = s.planetTakeAll(id, token)
		case "!", "thrust", "thrusters":
			err = s.thrusters(token, nil, pending)
			return err
		case "n":
			err = s.planetRename(id, token, pending)
		case "t":
			err = s.planetTransfer(id, token, pending)
		case "b", "f", "$":
			err = s.planetAccount(id, token, choice, pending)
		case "1", "2", "3", "4", "5", "6", "9":
			err = s.planetTake(id, token, choice, pending)
		default:
			err = s.Terminal.Printf("That planet function is not available in this edition yet.\r\n")
		}
		if err != nil {
			// A rejected action leaves the menu usable; a replaced landing,
			// lost permission or unreadable store ends this landing session.
			if _, _, _, viewErr := s.planetView(id, token); viewErr != nil {
				return err
			}
			if outErr := s.Terminal.Printf("%s\r\n", err); outErr != nil {
				return outErr
			}
		}
	}
}

func (s Session) planetTakeAll(id int, token string) error {
	var before, after game.Player
	err := s.Store.Update(func(w *game.World) error {
		if w.Players[id] == nil {
			return errors.New("player no longer exists")
		}
		before = *w.Players[id]
		if err := w.TakeAll(id, token, s.Now()); err != nil {
			return err
		}
		after = *w.Players[id]
		return nil
	})
	if err != nil {
		return err
	}
	return s.Terminal.Printf("\r\n<Take all>\r\n\r\nTaking:\r\n\r\nFighters..... %d\r\nMissiles..... %d\r\nMines........ %d\r\nPlasma bolts. %d\r\nEquipment.... %d\r\nOrganics..... %d\r\nOre.......... %d\r\n", after.Fighters-before.Fighters, after.Missiles-before.Missiles, after.Mines-before.Mines, after.Plasma-before.Plasma, after.Cargo[2]-before.Cargo[2], after.Cargo[1]-before.Cargo[1], after.Cargo[0]-before.Cargo[0])
}

func (s Session) planetTake(id int, token, choice string, pending *[]string) error {
	_, p, planet, err := s.planetView(id, token)
	if err != nil {
		return err
	}
	index := map[string]int{"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "9": 6}[choice]
	kinds := []string{"ore", "organics", "equipment", "fighters", "missiles", "mines", "plasma"}
	titles := []string{"Ore>", "Organics)", "Equipment)", "Fighters)", "Missiles)", "Mines)", "Plasma Bolts>"}
	stocks := []float64{planet.Cargo[0], planet.Cargo[1], planet.Cargo[2], planet.Fighters, planet.Missiles, planet.Mines, planet.Plasma}
	max := int64(math.Floor(stocks[index]))
	if index < 3 {
		max = min(max, p.Holds-p.Cargo[0]-p.Cargo[1]-p.Cargo[2])
	} else {
		ship := []int64{p.Fighters, p.Missiles, p.Mines, p.Plasma}
		max = min(max, game.MaxQuantity-ship[index-3])
	}
	answer, err := s.planetAnswer(fmt.Sprintf("\r\n<Take %s\r\n\r\nHow much [ %d ]? ", titles[index], max), pending, 3)
	if err != nil {
		return err
	}
	q := max
	if answer != "" {
		q, err = strconv.ParseInt(answer, 10, 64)
	}
	if err == nil && q == 0 {
		return nil
	}
	if err != nil || q < 1 || q > max {
		return s.Terminal.Printf("Enter a whole quantity from 0 to %d.\r\n", max)
	}
	return s.Store.Update(func(w *game.World) error { return w.Take(id, token, kinds[index], q, s.Now()) })
}

func (s Session) planetTransfer(id int, token string, pending *[]string) error {
	answer, err := s.planetAnswer("\r\n<Transfer items to planet>\r\n\r\nTransfer which item?\r\n\r\n[B] Plasma Bolts\r\n[C] Cargo\r\n[F] Fighters\r\n[S] Missiles\r\n[M] Mines\r\n\r\n-=>", pending, 3)
	if err != nil {
		return err
	}
	kind, label := "", ""
	switch strings.ToLower(answer) {
	case "b":
		kind, label = "plasma", "Plasma Bolts"
	case "c":
		kind, label = "cargo", "Cargo"
	case "f":
		kind, label = "fighters", "Fighters"
	case "s":
		kind, label = "missiles", "Missiles"
	case "m":
		kind, label = "mines", "Mines"
	default:
		return nil
	}
	var q int64
	if kind == "fighters" {
		_, p, _, err := s.planetView(id, token)
		if err != nil {
			return err
		}
		answer, err = s.planetAnswer(fmt.Sprintf("\r\nYou have %d fighters. Transfer how many -=>", p.Fighters), pending, 3)
		if err != nil {
			return err
		}
		if answer == "" || answer == "0" {
			return nil
		}
		q, err = strconv.ParseInt(answer, 10, 64)
		if err != nil || q < 1 {
			return s.Terminal.Printf("Enter a positive whole quantity.\r\n")
		}
	}
	if err = s.Store.Update(func(w *game.World) error { return w.Transfer(id, token, kind, q, s.Now()) }); err != nil {
		return err
	}
	if kind == "cargo" {
		return s.Terminal.Printf("\r\nCargo transferred!!\r\n")
	}
	if err = s.Terminal.Printf("\r\n"); err != nil {
		return err
	}
	if err = s.planetColor(0x83); err != nil {
		return err
	}
	if err = s.Terminal.Printf("%s Transferred!", label); err != nil {
		return err
	}
	if err = s.planetColor(3); err != nil {
		return err
	}
	return s.Terminal.Printf("\r\n")
}

func (s Session) planetAccount(id int, token, choice string, pending *[]string) error {
	_, p, planet, err := s.planetView(id, token)
	if err != nil {
		return err
	}
	prompt := ""
	switch strings.ToLower(choice) {
	case "b":
		prompt = fmt.Sprintf("\r\nWelcome to the intergalactic bank of %s!\r\n\r\nHow many credits do you want in the account? %d Available ->", planet.Name, p.Credits+planet.Bank)
	case "f":
		prompt = fmt.Sprintf("\r\nDrop how many ground force units on the planet? %d Available ->", p.Ground+planet.Ground)
	case "$":
		prompt = fmt.Sprintf("\r\nProductivity is increased by 1 Unit of EQU, ORG  & ORE for each 250 credits.\r\n\r\nYou have %d Credits.\r\n\r\nSpend how much to raise productivity? -+> ", p.Credits)
	}
	answer, err := s.planetAnswer(prompt, pending, 3)
	if err != nil {
		return err
	}
	if answer == "" {
		return nil
	}
	q, err := strconv.ParseInt(answer, 10, 64)
	if err != nil || q < 0 {
		return s.Terminal.Printf("Enter a nonnegative whole quantity.\r\n")
	}
	var current game.Planet
	var added int64
	err = s.Store.Update(func(w *game.World) error {
		before, err := w.PlanetStatus(id, token, s.Now())
		if err != nil {
			return err
		}
		switch strings.ToLower(choice) {
		case "b":
			err = w.Bank(id, token, q, s.Now())
		case "f":
			err = w.Garrison(id, token, q, s.Now())
		case "$":
			err = w.Invest(id, token, q, s.Now())
		}
		if err != nil {
			return err
		}
		current = *w.Planets[w.Players[id].LandedPlanet]
		added = planetRates(current)[3] - planetRates(before)[3]
		return nil
	})
	if err != nil {
		return err
	}
	switch strings.ToLower(choice) {
	case "b":
		return s.Terminal.Printf("\r\nYou have %d credits on deposit at 1%% interest. Have a nice day!\r\n", current.Bank)
	case "f":
		if err = s.Terminal.Printf("\r\n"); err != nil {
			return err
		}
		if err = s.planetColor(0x8b); err != nil {
			return err
		}
		if err = s.Terminal.Printf("Ground force strength now at %d units!", current.Ground); err != nil {
			return err
		}
		if err = s.planetColor(3); err != nil {
			return err
		}
		return s.Terminal.Printf("\r\n")
	default:
		delta := strconv.FormatFloat(float64(q)/250, 'f', -1, 64)
		delta = strings.TrimPrefix(delta, "0.")
		if q < 250 {
			delta = "." + delta
		}
		if err = s.Terminal.Printf("\r\nProductivity increased by %s units of ORE, ORG & EQU!\r\n", delta); err != nil {
			return err
		}
		if added > 0 {
			return s.Terminal.Printf("Also increased: Fighters: %d\r\n", added)
		}
		return nil
	}
}

func (s Session) planetRename(id int, token string, pending *[]string) error {
	for {
		w, _, _, err := s.planetView(id, token)
		if err != nil {
			return err
		}
		if err = w.CanRenamePlanet(id, token, s.Now()); err != nil {
			if errors.Is(err, game.ErrProtectedPlanetRename) {
				return s.planetRenameWarning(err)
			}
			return err
		}
		name, err := s.planetAnswer("\r\nWhat do you want to name this planet? -=>", pending, 3)
		if err != nil {
			return err
		}
		if name == "" {
			return nil
		}
		inputName := name
		name, err = game.PlanetRenameName(name)
		if errors.Is(err, game.ErrReservedPlanetName) {
			return s.planetRenameWarning(err)
		}
		if err != nil {
			return err
		}
		answer, err := s.planetAnswer(fmt.Sprintf("\r\n\"%s\" Is this OK? (Y/n) [Y] ?", name), pending, 3)
		if err != nil {
			return err
		}
		if strings.EqualFold(answer, "n") {
			continue
		}
		return s.Store.Update(func(w *game.World) error { return w.RenamePlanet(id, token, inputName, s.Now()) })
	}
}

func (s Session) planetRenameWarning(err error) error {
	if outErr := s.Terminal.Printf("\r\n"); outErr != nil {
		return outErr
	}
	if outErr := s.planetColor(0x8b); outErr != nil {
		return outErr
	}
	if outErr := s.Terminal.Printf("%s", err); outErr != nil {
		return outErr
	}
	if outErr := s.planetColor(3); outErr != nil {
		return outErr
	}
	return s.Terminal.Printf("\r\n")
}
