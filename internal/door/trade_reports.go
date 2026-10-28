package door

import (
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func parsePortFilter(args []string) (game.PortFilter, error) {
	filter := game.PortFilter{Ownership: "all"}
	if len(args) == 0 {
		return filter, nil
	}
	choice := strings.ToLower(strings.TrimSpace(args[0]))
	owners := map[string]string{"a": "all", "all": "all", "y": "own", "own": "own", "t": "team", "team": "team", "e": "enemy", "enemy": "enemy", "u": "unowned", "unowned": "unowned"}
	if owner, ok := owners[choice]; ok && len(args) == 1 {
		filter.Ownership = owner
		return filter, nil
	}
	goods := map[string]string{"1": "equipment", "2": "organics", "3": "ore", "equipment": "equipment", "organics": "organics", "ore": "ore"}
	if good, ok := goods[choice]; ok && len(args) == 2 {
		action := strings.ToLower(strings.TrimSpace(args[1]))
		if action == "b" {
			action = "buy"
		}
		if action == "s" {
			action = "sell"
		}
		if action == "buy" || action == "sell" {
			filter.Good, filter.Action = good, action
			return filter, nil
		}
	}
	return filter, errors.New("use NEAREST [all|own|team|enemy|unowned] or NEAREST <ore|organics|equipment> <buy|sell>")
}

func (s Session) nearestFilterInput(pending *[]string) ([]string, error) {
	choice, err := s.classicArgument("Show buying/selling [1] Equ, [2] Org, [3] Ore,\r\n[Y] Your Ports, [T] Team's Ports, [E] Enemy Ports\r\n[U] Un-owned Ports OR [A] All Ports ? -=> [A] ", pending)
	if err != nil {
		return nil, err
	}
	choice = strings.ToLower(strings.TrimSpace(choice))
	if choice == "" {
		choice = "a"
	}
	args := []string{choice}
	for _, good := range []string{"1", "2", "3", "ore", "organics", "equipment"} {
		if choice == good {
			action, err := s.classicArgument("Your action: [B] Buy or [S] Sell? ", pending)
			return append(args, action), err
		}
	}
	return args, nil
}

func (s Session) tradeReport(id int, command string, args []string, pending *[]string) error {
	filter := game.PortFilter{}
	if command == "nearest" {
		if s.Classic && len(args) == 0 {
			var err error
			args, err = s.nearestFilterInput(pending)
			if err != nil {
				return err
			}
		}
		var err error
		filter, err = parsePortFilter(args)
		if err != nil {
			return err
		}
	} else if len(args) != 0 {
		return errors.New("use PAIRS or PROFITS without arguments")
	}
	for offset := 0; ; {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		// Every page follows a fresh bound read. A teammate leaving or a new
		// target defense must not disclose stale quotes after the paging prompt.
		w, err := s.Store.View()
		if err != nil {
			return err
		}
		now := s.Now()
		var blocks []string
		pageSize := 4
		if command == "nearest" {
			ports, err := w.NearestPorts(id, filter, now)
			if err != nil {
				return err
			}
			for _, port := range ports {
				actions := [3]string{"S", "S", "S"}
				for i := range actions {
					if port.Selling[i] {
						actions[i] = "B"
					}
				}
				blocks = append(blocks, fmt.Sprintf("Distance: %d | Sector: %d | %s\r\n%s ore @ %d  %s organics @ %d  %s equipment @ %d\r\nStock/demand ore/org/equ: %d/%d/%d\r\nOwner: %s\r\n", port.Distance, port.Sector, port.Name,
					actions[0], port.Prices[0], actions[1], port.Prices[1], actions[2], port.Prices[2], int64(port.Supply[0]), int64(port.Supply[1]), int64(port.Supply[2]), port.OwnerAlias))
			}
		} else {
			routes, err := w.TradeRoutes(id, command == "profits", now)
			if err != nil {
				return err
			}
			for _, route := range routes {
				blocks = append(blocks, fmt.Sprintf("%d -> %d | Approach: %d warps | Out: 1 | Return: %d\r\nBuy %s @ %d in %d; sell @ %d in %d\r\nReturn: buy %s @ %d in %d; sell @ %d in %d\r\nSpread: %d credits/unit of each | Stock/demand: %d/%d\r\n", route.From, route.To, route.ApproachHops, route.ReturnHops,
					game.Goods[route.OutboundGood], route.OutboundBuy, route.From, route.OutboundSell, route.To,
					game.Goods[route.ReturnGood], route.ReturnBuy, route.To, route.ReturnSell, route.From,
					route.Spread, route.OutboundUnits, route.ReturnUnits))
			}
		}
		if offset == 0 {
			legend := "B/S is your buy/sell action. Prices and stock/demand are forecasts.\r\n"
			if command != "nearest" {
				legend = "Price spreads are per unit of each commodity, not ship earnings.\r\nCash, holds, docking turns and later price/stock changes are excluded.\r\n"
			}
			if err = s.Terminal.Printf("\r\n%sRoutes honor AVOID; mines/defenses can still interrupt travel.\r\n", legend); err != nil {
				return err
			}
		}
		if len(blocks) == 0 {
			return s.Terminal.Printf("No matching accessible ports or trade routes found.\r\n")
		}
		if err = s.Terminal.Printf("\r\nReport from sector %d (free):\r\n", w.Players[id].Sector); err != nil {
			return err
		}
		end := min(offset+pageSize, len(blocks))
		for _, block := range blocks[min(offset, len(blocks)):end] {
			if err = s.Terminal.Printf("%s", block); err != nil {
				return err
			}
		}
		if end == len(blocks) {
			return s.Terminal.Printf("End of report.\r\n")
		}
		if err = s.Terminal.Printf("More results? [Enter=more, Q=stop] "); err != nil {
			return err
		}
		// Paging responses do not consume queued main/computer commands.
		answer, err := s.Terminal.ReadLine(s.Deadline)
		if err != nil {
			return err
		}
		if answer = strings.TrimSpace(answer); answer != "" && !strings.EqualFold(answer, "y") {
			return nil
		}
		offset = end
	}
}
