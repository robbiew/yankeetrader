package door

import (
	"errors"
	"fmt"
	"strconv"
	"strings"

	"github.com/robbiew/yankeetrader/internal/game"
)

// portView rejects expired or superseded docking sessions before presenting a quote.
// The game rules repeat this check under the store lock when committing a purchase.
func (s Session) portView(id int, token string) (*game.World, *game.Player, *game.Port, error) {
	w, err := s.Store.View()
	if err != nil {
		return nil, nil, nil, err
	}
	p := w.Players[id]
	if p == nil || token == "" || p.DockToken != token || !s.Now().Before(p.DockUntil) {
		return nil, nil, nil, errors.New("dock again; this docking session is no longer current")
	}
	sector := w.Sectors[p.Sector]
	if sector == nil || w.Ports[sector.Port] == nil {
		return nil, nil, nil, errors.New("no port here")
	}
	return w, p, w.Ports[sector.Port], nil
}

func (s Session) classicPort(id int, token string, pending *[]string) error {
	_, p, port, err := s.portView(id, token)
	if err != nil {
		return err
	}
	if err = s.portColor(2); err != nil {
		return err
	}
	if err = s.Terminal.Printf("<Port>\r\n\r\n"); err != nil {
		return err
	}
	if err = s.portColor(6); err != nil {
		return err
	}
	if err = s.Terminal.Printf("Docking, One Turn Deducted, %d left.\r\n", p.Turns); err != nil {
		return err
	}
	if port.ID == 1 {
		err = s.earthShop(id, token, pending)
	} else {
		err = s.cargoShop(id, token, pending)
	}
	if err != nil {
		return err
	}
	// Do not clear a new docking session established by another connection.
	if err = s.Store.Update(func(w *game.World) error {
		if p := w.Players[id]; p != nil && p.DockToken == token {
			p.DockToken = ""
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

func (s Session) earthShop(id int, token string, pending *[]string) error {
	for {
		w, p, _, err := s.portView(id, token)
		if err != nil {
			return err
		}
		if err = s.portColor(6); err != nil {
			return err
		}
		if err = s.Terminal.Printf("\r\nCommerce report for Earth: %s\r\n\r\n", s.Now().Format("01-02-2006 15:04:05")); err != nil {
			return err
		}
		if err = s.Terminal.Printf("----------------------*--------*------------\r\n         ITEM         *  COST  * CAN AFFORD\r\n----------------------*--------*------------\r\n"); err != nil {
			return err
		}
		labels := []string{"[1] Cloak Energy", "[2] Cargo Holds", "[3] Fighters", "[4] Play Lottery", "[5] Danger Scanner", "[6] Anti-Cloak Device", "[7] Ground Forces", "[8] Shield Power", "[9] Hire Spies (Each)"}
		costs := []int64{1000, 500, 100, 5, 250000, 500000, 750, 50, 333000}
		for i, label := range labels {
			afford := "N/A"
			if i == 1 || i == 2 || i == 6 || i == 7 {
				afford = strconv.FormatInt(p.Credits/costs[i], 10)
			}
			if err = s.Terminal.Printf("%-22s* %-7d* %s\r\n", label, costs[i], afford); err != nil {
				return err
			}
		}
		if err = s.Terminal.Printf("----------------------*--------*------------\r\n\r\n[I] Ship Info -=*=- [0] Leave Port\r\n\r\n"); err != nil {
			return err
		}
		choice, err := s.portArgument(fmt.Sprintf("Credits: %d -=*=- Buy Which Item? -=>", p.Credits), pending)
		if err != nil {
			return err
		}
		if choice == "0" {
			return nil
		}
		if strings.EqualFold(choice, "i") {
			if err = s.classicInfo(w, id, true); err != nil {
				return err
			}
			continue
		}
		item, label := "", ""
		switch choice {
		case "2":
			item, label = "holds", "holds"
		case "3":
			item, label = "fighters", "fighters"
		case "7":
			item, label = "forces", "ground force units"
		case "8":
			item, label = "shields", "shield power"
		}
		if item == "" {
			if err = s.Terminal.Printf("That item is unavailable.\r\n"); err != nil {
				return err
			}
			continue
		}
		if item == "holds" {
			if p.Holds >= 1000 {
				if err = s.portColor(14); err != nil {
					return err
				}
				if err = s.Terminal.Printf("\r\n\r\nYou dont need any holds.\r\n"); err != nil {
					return err
				}
				continue
			}
			if err = s.Terminal.Printf("\r\n\r\nYou need %d holds.\r\n", 1000-p.Holds); err != nil {
				return err
			}
		}
		prompt := "\r\nBuy how many " + label + "? [0]? "
		if item == "holds" {
			prompt = "Buy how many holds? [0]? "
		}
		if item == "shields" {
			prompt = "\r\nBuy how much shield power? [0]? "
		}
		answer, err := s.portArgument(prompt, pending)
		if err != nil {
			return err
		}
		if answer == "" || answer == "0" {
			continue
		}
		q, err := strconv.ParseInt(answer, 10, 64)
		if err == nil {
			err = s.Store.Update(func(w *game.World) error { return w.Equip(id, token, item, q, s.Now()) })
		}
		if err != nil {
			if err = s.Terminal.Printf("Purchase rejected: %s\r\n", err); err != nil {
				return err
			}
			continue
		}
	}
}

func (s Session) cargoShop(id int, token string, pending *[]string) error {
	w, p, port, err := s.portView(id, token)
	if err != nil {
		return err
	}
	if err = s.portColor(6); err != nil {
		return err
	}
	if port.Owner != 0 {
		owner := ""
		if port.Owner == id {
			owner = fmt.Sprintf("YOU, Credits: %d", port.Treasury)
		} else if player := w.Players[port.Owner]; player != nil {
			owner = player.Alias + " "
		}
		if err = s.Terminal.Printf("\r\nThis port is owned by: %s\r\n", owner); err != nil {
			return err
		}
	}
	if err = s.Terminal.Printf("\r\nCommerce report for %s: %s\r\n\r\n Items         Status      # units    in holds   Cost\r\n", port.Name, s.Now().Format("01-02-2006 15:04:05")); err != nil {
		return err
	}
	if err = s.portColor(14); err != nil {
		return err
	}
	if err = s.Terminal.Printf("=======       =========   =========   ========   ====\r\n"); err != nil {
		return err
	}
	for i, name := range game.Goods {
		status := "Buying"
		if port.Coefficient[i] > 0 {
			status = "Selling"
		}
		color := 6
		if port.Coefficient[i] > 0 {
			color = 2
		}
		if err = s.portColor(color); err != nil {
			return err
		}
		label := strings.ToUpper(name[:1]) + name[1:] + strings.Repeat(".", 13-len(name))
		if err = s.Terminal.Printf("%s  %-7s   %9d   %8d   %4d\r\n", label, status, int64(port.Supply[i]), p.Cargo[i], p.DockPrices[i]); err != nil {
			return err
		}
	}
	if err = s.portColor(6); err != nil {
		return err
	}
	for i, name := range game.Goods {
		// Refresh after each completed transaction and every user-input boundary.
		_, p, port, err = s.portView(id, token)
		if err != nil {
			return err
		}
		buy := port.Coefficient[i] > 0
		empty := p.Holds - p.Cargo[0] - p.Cargo[1] - p.Cargo[2]
		max := min(int64(port.Supply[i]), game.MaxQuantity)
		action, direction := "sell", "buying"
		if buy {
			if p.DockPrices[i] < 1 {
				return errors.New("invalid price; dock again")
			}
			max = min(max, empty, p.Credits/p.DockPrices[i])
			action, direction = "buy", "selling"
		} else {
			max = min(max, p.Cargo[i])
		}
		if max <= 0 {
			continue
		}
		if err = s.Terminal.Printf("\r\nYou have %d credits and %d empty cargo holds.\r\n\r\nWe are %s up to %d.  You have %d in your holds.\r\n", p.Credits, empty, direction, int64(port.Supply[i]), p.Cargo[i]); err != nil {
			return err
		}
		answer, err := s.portArgument(fmt.Sprintf("How many holds of %s do you want to %s [ %d ]? ", strings.ToUpper(name[:1])+name[1:], action, max), pending)
		if err != nil {
			return err
		}
		q := max
		if answer != "" {
			q, err = strconv.ParseInt(answer, 10, 64)
		}
		if answer == "0" {
			continue
		}
		if err != nil || q < 1 || q > max {
			if err = s.Terminal.Printf("Enter a whole quantity from 0 to %d.\r\n", max); err != nil {
				return err
			}
			// Invalid input ends this commodity without changing cargo.
			continue
		}
		// Validate on a fresh, disposable world before offering agreement; only the
		// confirmed transaction below writes the authoritative world.
		quote, err := s.Store.View()
		if err != nil {
			return err
		}
		if err = quote.Trade(id, token, buy, i, q, s.Now()); err != nil {
			return err
		}
		bill := q * p.DockPrices[i]
		phrase := "We'll buy them for"
		if buy {
			phrase = "We'll sell them for"
		}
		answer, err = s.portArgument(fmt.Sprintf("Agreed, %d units.\r\n\r\n%s %d credits.\r\nDo you agree? [Y/n] ", q, phrase, bill), pending)
		if err != nil {
			return err
		}
		if answer != "" && !strings.EqualFold(answer, "y") {
			if err = s.Terminal.Printf("Never mind!\r\n"); err != nil {
				return err
			}
			continue
		}
		if err = s.Store.Update(func(w *game.World) error { return w.Trade(id, token, buy, i, q, s.Now()) }); err != nil {
			return err
		}
		message := "We'll take them!"
		if buy {
			message = "It's Yours!"
		}
		if err = s.Terminal.Printf("%s\r\n", message); err != nil {
			return err
		}
	}
	_, p, _, err = s.portView(id, token)
	if err != nil {
		return err
	}
	return s.Terminal.Printf("\r\nYou have %d credits and %d empty cargo holds.\r\n", p.Credits, p.Holds-p.Cargo[0]-p.Cargo[1]-p.Cargo[2])
}

// DOS uses brown (6) for commerce, green (2) for selling rows, bright
// yellow (14) for the cargo separator, and gray (7) for entered answers.
func (s Session) portColor(color int) error {
	if !s.ANSI {
		return nil
	}
	// Bold + base yellow also works with traditional BBS ANSI interpreters.
	if color == 14 {
		return s.Terminal.Printf("\x1b[0;1;33;40m")
	}
	codes := map[int]int{2: 32, 6: 33, 7: 37}
	return s.Terminal.Printf("\x1b[0;%d;40m", codes[color])
}

func (s Session) portArgument(prompt string, pending *[]string) (answer string, err error) {
	if err = s.Terminal.Printf("%s", prompt); err != nil {
		return "", err
	}
	if err = s.portColor(7); err != nil {
		return "", err
	}
	answer, err = s.classicArgument("", pending)
	colorErr := s.portColor(6)
	if err != nil {
		return "", err
	}
	return answer, colorErr
}
