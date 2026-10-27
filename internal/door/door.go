package door

import (
	"errors"
	"fmt"
	gd "github.com/robbiew/godoors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"github.com/robbiew/yankeetrader/internal/version"
	"io"
	"strconv"
	"strings"
	"time"
)

type Terminal interface {
	ReadLine(time.Time) (string, error)
	Printf(string, ...any) error
}
type inputKey struct {
	r rune
	k gd.Key
}
type GoDoors struct {
	escaped     bool
	commandMode bool
	savedLine   string
	onIdle      func() error
	pending     []inputKey
	readKey     func(time.Duration) (rune, gd.Key, error)
}

func (g *GoDoors) read(timeout time.Duration) (rune, gd.Key, error) {
	if g.readKey != nil {
		return g.readKey(timeout)
	}
	return gd.ReadKeyTimeout(timeout)
}

// Interrupted consumes Ctrl-X while retaining other keys for the next prompt.
func (g *GoDoors) Interrupted() (bool, error) {
	for i := 0; i < 160; i++ {
		r, k, err := g.read(time.Millisecond)
		if errors.Is(err, gd.ErrInputTimeout) {
			return false, nil
		}
		if err != nil {
			return false, err
		}
		if r == 24 {
			return true, nil
		}
		if len(g.pending) < 4096 {
			g.pending = append(g.pending, inputKey{r, k})
		}
	}
	return false, nil
}

func (*GoDoors) Printf(f string, args ...any) error {
	_, e := fmt.Fprintf(gd.Output(), f, args...)
	return e
}
func (g *GoDoors) ReadLine(deadline time.Time) (string, error)   { return g.readLine(deadline, false) }
func (g *GoDoors) ReadSecret(deadline time.Time) (string, error) { return g.readLine(deadline, true) }
func (g *GoDoors) readLine(deadline time.Time, secret bool) (string, error) {
	g.escaped = false
	var b []rune
	for {
		left := time.Until(deadline)
		if left <= 0 {
			return "", errors.New("session time expired")
		}
		var r rune
		var k gd.Key
		var e error
		if len(g.pending) > 0 {
			r, k = g.pending[0].r, g.pending[0].k
			g.pending = g.pending[1:]
		} else {
			timeout := left
			if g.onIdle != nil && timeout > time.Second {
				timeout = time.Second
			}
			r, k, e = g.read(timeout)
		}
		if errors.Is(e, gd.ErrInputTimeout) && g.onIdle != nil {
			if err := g.onIdle(); err != nil {
				return "", err
			}
			continue
		}
		if e != nil {
			return "", e
		}
		if k == gd.KeyEnter {
			line := string(b)
			if !secret && g.commandMode && strings.HasSuffix(line, "/") {
				line = strings.TrimSuffix(line, "/")
				g.savedLine = line
			}
			return line, g.Printf("\r\n")
		}
		if !secret && g.commandMode && r == 18 && g.savedLine != "" {
			return g.savedLine, g.Printf("%s\r\n", g.savedLine)
		}
		if k == gd.KeyEsc {
			g.escaped = true
			return "quit", nil
		}
		if r == 8 || r == 127 {
			if len(b) > 0 {
				b = b[:len(b)-1]
				if e = g.Printf("\b \b"); e != nil {
					return "", e
				}
			}
			continue
		}
		if k == gd.KeyNone && r >= 32 && r <= 126 && len(b) < 160 {
			b = append(b, r)
			echo := r
			if secret {
				echo = '*'
			}
			if e = g.Printf("%c", echo); e != nil {
				return "", e
			}
		}
	}
}

type Session struct {
	RealName             string
	Store                store.Store
	Terminal             Terminal
	Identity, Alias      string
	Deadline             time.Time
	Now                  func() time.Time
	Classic, ANSI, Local bool
	Music                bool // positively identified CTerm-compatible terminal
}

func (s Session) Run() (runErr error) {
	defer func() {
		if errors.Is(runErr, io.EOF) {
			runErr = nil
		}
	}()

	if s.Classic && s.ANSI {
		defer s.Terminal.Printf("\x1b[r\x1b[25;1H\x1b[0m\r\n")
	}
	if s.Classic {
		s.Alias = terminalLabel(s.Alias)
		s.RealName = terminalLabel(s.RealName)
		if strings.TrimSpace(s.Alias) == "" {
			return errors.New("caller name is missing")
		}
	}
	if s.Now == nil {
		s.Now = time.Now
	}
	var id int
	if s.Classic {
		var err error
		id, err = s.classicStartup()
		if errors.Is(err, io.EOF) {
			return nil
		}
		if err != nil {
			return err
		}
	} else {
		if e := s.Store.Update(func(w *game.World) error {
			w.Maintain(s.Now())
			alias := s.Alias
			for _, existing := range w.Players {
				if existing.Identity == s.Identity && existing.LastLogin != "" {
					alias = existing.Alias
					break
				}
			}
			p, e := w.Join(s.Identity, alias)
			if e == nil {
				id = p.ID
				p.DockToken = ""
				p.PlanetToken = ""
				p.LandedPlanet = 0
			}
			return e
		}); e != nil {
			return e
		}
		if e := s.Terminal.Printf("\r\n%s\r\nWelcome, %s. Actions save automatically. Type ? for help.\r\n", version.String(), s.Alias); e != nil {
			return e
		}
	}
	if terminal, ok := s.Terminal.(*GoDoors); ok {
		terminal.commandMode = true
	}
	pending := []string{}
	token := ""
	planetToken := ""
	if err := s.Store.Update(func(w *game.World) error {
		if w.Players[id].Team != 0 {
			_, err := w.VisitTeam(id)
			return err
		}
		return nil
	}); err != nil {
		return err
	}
	computer := false
	for {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		w, e := s.Store.View()
		if e != nil {
			return e
		}
		p := w.Players[id]
		if p == nil {
			return errors.New("player no longer exists")
		}
		if len(pending) == 0 {
			clockWidth := 0
			if s.Classic {
				label := "Main Command (?=Help)?"
				if computer {
					label = "Computer command (?=help)?"
				}
				if s.ANSI {
					if e = s.Terminal.Printf("\x1b[0;32m"); e != nil {
						return e
					}
				}
				left := s.timeLeft()
				clockWidth = len(left)
				e = s.Terminal.Printf("\r\nTime: %s  %s ", left, label)
			} else {
				e = s.Terminal.Printf("\r\nSector %d | %d credits | %d turns > ", p.Sector, p.Credits, p.Turns)
			}
			if e != nil {
				return e
			}
			if terminal, ok := s.Terminal.(*GoDoors); ok && s.Classic && s.ANSI {
				terminal.onIdle = func() error {
					return s.refreshClassicClock(clockWidth)
				}
			}
			line, e := s.Terminal.ReadLine(s.Deadline)
			if terminal, ok := s.Terminal.(*GoDoors); ok {
				terminal.onIdle = nil
			}
			if errors.Is(e, io.EOF) {
				return nil
			}
			if e != nil {
				return e
			}
			pending = splitCommands(line)
		}
		command := strings.Fields(pending[0])
		pending = pending[1:]
		if len(command) == 0 {
			if s.Classic {
				if computer {
					menu, _ := classicAssets.ReadFile("assets/computer.txt")
					e = s.classicText(string(menu))
				} else {
					e = s.classicSector(w, id)
				}
				if e != nil {
					return e
				}
			}
			continue
		}
		cmd := strings.ToLower(command[0])
		args := command[1:]
		if s.Classic && computer {
			switch cmd {
			case "1":
				computer = false
				if e = s.classicText("\r\n<Computer deactivated>\r\n"); e != nil {
					return e
				}
				if e = s.classicSector(w, id); e != nil {
					return e
				}
				continue
			case "3":
				value, err := s.classicArgument("What sector do you want to go to? ", &pending)
				if err != nil {
					return err
				}
				cmd, args = "auto", []string{value}
			case "10":
				from, err := s.classicArgument("Enter start for path search? ", &pending)
				if err != nil {
					return err
				}
				to, err := s.classicArgument("What sector do you want to go to? ", &pending)
				if err != nil {
					return err
				}
				cmd, args = "path", []string{from, to}
			case "7":
				slot, err := s.classicArgument("Enter the number of the slot to change [1 - 30]: ", &pending)
				if err != nil {
					return err
				}
				n, err := strconv.Atoi(slot)
				if err != nil || n < 1 || n > 30 {
					continue
				}
				sector, err := s.classicArgument("Enter the sector you wish to avoid (0 to clear): ", &pending)
				if err != nil {
					return err
				}
				cmd, args = "avoid", []string{slot, sector}
			case "12", "treasury":
				cmd = "treasury"
			case "$", "collect":
				cmd = "collect"
			default:
				if cmd != "?" && cmd != "help" {
					if err := s.Terminal.Printf("That computer function is not available yet.\r\n"); err != nil {
						return err
					}
					continue
				}
			}
		}
		if s.Classic && cmd == "a" && planetToken == "" {
			cmd = "attack"
		}
		if s.Classic && cmd == "l" {
			cmd = "land"
		}
		if s.Classic && (cmd == "m" || cmd == "move") && len(args) == 0 {
			value, err := s.classicArgument("Move to which sector? ", &pending)
			if err != nil {
				return err
			}
			args = []string{value}
		}
		switch cmd {
		case "q", "quit":
			if s.Classic {
				answer, err := s.classicArgument("\r\n<Quit>\r\nAre you sure (Y/N)? ", &pending)
				if errors.Is(err, io.EOF) {
					return nil
				}
				if err != nil {
					return err
				}
				if !strings.EqualFold(answer, "y") {
					continue
				}
			}
			if err := s.Terminal.Printf("Saved. Safe travels, %s.\r\n", p.Alias); err != nil {
				return err
			}
			return s.exitMusic()
		case "?", "help":
			if s.Classic {
				if computer {
					menu, _ := classicAssets.ReadFile("assets/computer.txt")
					e = s.classicText(string(menu))
				} else {
					e = s.classicHelp(p.Alias)
				}
				break
			}
			e = s.Terminal.Printf("I info | L look | S sensors (free) | M <sector> move\r\nPATH <from> <to> (free) | AUTO <sector> (confirm Y/N)\r\nAVOID [<slot 1-30> <sector, or 0 to clear>] (free)\r\nP dock (1 turn)\r\nBUY/SELL <ore|organics|equipment> <quantity>\r\nT/TEAM team menu (free)\r\nACQUIRE port (confirm Y/N) | TREASURY report | COLLECT personal treasuries\r\nEQUIP <holds|fighters|shields|forces> <quantity> (Earth)\r\nLAND | CREATE <name> (25000) | PLANET status\r\nTAKE <item> <qty> | A take all | TRANSFER <item> [qty]\r\nBANK <target balance> | INVEST <credits> | GARRISON <target>\r\nLEAVE port/planet | Q quit. Stack commands with semicolons.\r\n")
		case "c":
			if s.Classic {
				computer = true
				e = s.classicText("\r\n<Computer activated>\r\n")
			} else {
				e = errors.New("use PATH, AUTO or AVOID")
			}
		case "v":
			if s.Classic {
				e = s.drawClassic(template("title"))
			} else {
				e = errors.New("unknown command; type ? for help")
			}
		case "z":
			if s.Classic {
				e = s.classicInstructions()
			} else {
				e = errors.New("unknown command; type ? for help")
			}
		case "i", "info":
			if s.Classic {
				e = s.classicInfo(w, id, false)
				break
			}
			e = s.Terminal.Printf("%s: holds %d; ore %d; organics %d; equipment %d\r\nFighters %d; shields %d; ground forces %d\r\nMissiles %d; mines %d; plasma %d\r\n", p.Alias, p.Holds, p.Cargo[0], p.Cargo[1], p.Cargo[2], p.Fighters, p.Shields, p.Ground, p.Missiles, p.Mines, p.Plasma)
		case "l", "look":
			if s.Classic {
				e = s.classicSector(w, id)
				break
			}
			sector := w.Sectors[p.Sector]
			e = s.Terminal.Printf("Warps: %v\r\n", sector.Warps)
			if e == nil && sector.Port != 0 {
				e = s.Terminal.Printf("Port: %s\r\n", w.Ports[sector.Port].Name)
			}
			if e == nil && sector.Planet != 0 {
				e = s.Terminal.Printf("Planet: %s\r\n", w.Planets[sector.Planet].Name)
			}
		case "s", "scan", "sensors":
			if len(args) != 0 {
				e = errors.New("use S to scan adjacent sectors")
			} else {
				var reports []game.SensorReport
				reports, e = w.Scan(id)
				if e == nil {
					e = showSensors(s.Terminal, reports)
				}
			}
		case "avoid":
			if len(args) == 0 {
				e = s.Terminal.Printf("Sectors to avoid (30 slots; 0 clears a slot):\r\n")
				for slot, sector := range p.AvoidSectors {
					if e != nil {
						break
					}
					if sector != 0 {
						e = s.Terminal.Printf("Slot %d: sector %d\r\n", slot+1, sector)
					}
				}
				if e == nil && allClear(p.AvoidSectors) {
					e = s.Terminal.Printf("None. Use AVOID <slot> <sector>, or AVOID <slot> 0 to clear.\r\n")
				}
			} else if len(args) != 2 {
				e = errors.New("use AVOID [<slot 1-30> <sector, or 0 to clear>]")
			} else {
				var slot, sector int
				slot, e = strconv.Atoi(args[0])
				if e == nil {
					sector, e = strconv.Atoi(args[1])
				}
				if e == nil {
					e = s.Store.Update(func(w *game.World) error { return w.SetAvoid(id, slot, sector) })
				}
				if e == nil {
					e = s.Terminal.Printf("Avoid slot %d saved: %d. Routing preferences persist across logins.\r\n", slot, sector)
				}
			}
		case "path":
			if len(args) != 2 {
				e = errors.New("use PATH <start sector> <destination sector>")
			} else {
				var from, to int
				from, e = strconv.Atoi(args[0])
				if e == nil {
					to, e = strconv.Atoi(args[1])
				}
				if e == nil {
					var path []int
					path, e = w.PlayerPath(id, from, to)
					if e == nil {
						e = s.Terminal.Printf("Shortest path: %v | %d turns.\r\n", path, len(path)-1)
					}
				}
			}
		case "auto", "autopilot":
			if len(args) != 1 {
				e = errors.New("use AUTO <destination sector>")
			} else {
				var to int
				var path []int
				to, e = strconv.Atoi(args[0])
				if e == nil {
					path, e = w.Course(id, to)
				}
				if e == nil {
					if e = s.Terminal.Printf("Course: %v | %d turns (Ctrl-X stops between hops). Engage autopilot? [y/N] ", path, len(path)-1); e != nil {
						return e
					}
					var answer string
					if len(pending) == 0 {
						answer, e = s.Terminal.ReadLine(s.Deadline)
						if errors.Is(e, io.EOF) {
							return nil
						}
						if e != nil {
							return e
						}
						pending = strings.Split(answer, ";")
					}
					answer, pending = strings.TrimSpace(pending[0]), pending[1:]
					if !strings.EqualFold(answer, "y") {
						e = s.Terminal.Printf("Autopilot cancelled.\r\n")
					} else {
						if s.Classic {
							computer = false
						}
						for hop := 1; hop < len(path); hop++ {
							if terminal, ok := s.Terminal.(interface{ Interrupted() (bool, error) }); ok {
								stopped, err := terminal.Interrupted()
								if err != nil {
									return err
								}
								if stopped {
									if err := s.Terminal.Printf("Autopilot stopped. Completed moves remain saved.\r\n"); err != nil {
										return err
									}
									break
								}
							}
							if !time.Now().Before(s.Deadline) {
								return errors.New("session time expired")
							}
							e = s.Store.Update(func(w *game.World) error { return w.FollowCourse(id, path[hop-1:]) })
							if e != nil {
								break
							}
							token, planetToken = "", ""
							if e = s.Terminal.Printf("Moved to sector %d.\r\n", path[hop]); e != nil {
								return e
							}
						}
					}
				}
			}
		case "create":
			if len(args) == 0 {
				e = errors.New("CREATE <name> costs 25000 credits")
			} else {
				e = s.Store.Update(func(w *game.World) error { return w.CreatePlanet(id, strings.Join(args, " "), s.Now()) })
				if e == nil {
					token = ""
					planetToken = ""
					e = s.Terminal.Printf("Planet created for 25000 credits. Use LAND to visit.\r\n")
				}
			}
		case "land":
			if s.Classic {
				e = s.classicLand(id, &pending)
				if errors.Is(e, io.EOF) {
					return nil
				}
				token, planetToken = "", ""
				break
			}
			var status game.Planet
			e = s.Store.Update(func(w *game.World) error {
				if e := w.Land(id, s.Now()); e != nil {
					return e
				}
				planetToken = w.Players[id].PlanetToken
				status = *w.Planets[w.Players[id].LandedPlanet]
				return nil
			})
			if e == nil {
				token = ""
				e = showPlanet(s.Terminal, status)
			}
		case "planet":
			var status game.Planet
			e = s.Store.Update(func(w *game.World) error {
				var err error
				status, err = w.PlanetStatus(id, planetToken, s.Now())
				return err
			})
			if e == nil {
				e = showPlanet(s.Terminal, status)
			}
		case "bank", "invest", "garrison":
			var q int64
			if len(args) != 1 {
				e = errors.New("use " + strings.ToUpper(cmd) + " <whole target/expenditure>")
			} else {
				q, e = strconv.ParseInt(args[0], 10, 64)
				if e == nil {
					e = s.Store.Update(func(w *game.World) error {
						switch cmd {
						case "bank":
							return w.Bank(id, planetToken, q, s.Now())
						case "invest":
							return w.Invest(id, planetToken, q, s.Now())
						default:
							return w.Garrison(id, planetToken, q, s.Now())
						}
					})
				}
				if e == nil {
					e = s.Terminal.Printf("Planet account/production/garrison saved.\r\n")
				}
			}
		case "a", "takeall":
			e = s.Store.Update(func(w *game.World) error { return w.TakeAll(id, planetToken, s.Now()) })
			if e == nil {
				e = s.Terminal.Printf("Available goods loaded; equipment gets cargo priority.\r\n")
			}
		case "take", "transfer":
			var q int64
			if len(args) < 1 || len(args) > 2 || (cmd == "take" && len(args) != 2) {
				e = errors.New("use TAKE <item> <qty> or TRANSFER <item> [qty]")
			} else {
				if len(args) == 2 {
					q, e = strconv.ParseInt(args[1], 10, 64)
					if e == nil && q <= 0 {
						e = errors.New("enter a positive whole quantity")
					}
				}
				if e == nil {
					e = s.Store.Update(func(w *game.World) error {
						if cmd == "take" {
							return w.Take(id, planetToken, strings.ToLower(args[0]), q, s.Now())
						}
						if strings.ToLower(args[0]) == "cargo" && len(args) != 1 {
							return errors.New("TRANSFER cargo moves all three cargo types; omit quantity")
						}
						return w.Transfer(id, planetToken, strings.ToLower(args[0]), q, s.Now())
					})
				}
				if e == nil {
					e = s.Terminal.Printf("Planet transfer saved.\r\n")
				}
			}
		case "m", "move":
			var to int
			if len(args) != 1 {
				e = errors.New("use M <adjacent sector>")
			} else {
				to, e = strconv.Atoi(args[0])
				if e == nil {
					e = s.Store.Update(func(w *game.World) error { return w.Move(id, to) })
				}
				if e == nil {
					token = ""
					planetToken = ""
					e = s.Terminal.Printf("Moved to sector %d.\r\n", to)
				}
			}
		case "p", "dock":
			var port game.Port
			var prices [3]int64
			e = s.Store.Update(func(w *game.World) error {
				if err := w.Dock(id, s.Now()); err != nil {
					return err
				}
				p := w.Players[id]
				token = p.DockToken
				port = *w.Ports[w.Sectors[p.Sector].Port]
				prices = p.DockPrices
				return nil
			})
			if e == nil {
				planetToken = ""
				if s.Classic {
					e = s.classicPort(id, token, &pending)
					token = ""
				} else if port.ID == 1 {
					e = s.Terminal.Printf("Earth: holds 500, fighters 100, shields 50, forces 750 credits each.\r\n")
				} else {
					for i, name := range game.Goods {
						direction := "buys"
						if port.Coefficient[i] > 0 {
							direction = "sells"
						}
						e = s.Terminal.Printf("Port %s %s at %d credits; available %d.\r\n", direction, name, prices[i], int64(port.Supply[i]))
						if e != nil {
							break
						}
					}
				}
			}
		case "t", "team":
			if len(args) != 0 {
				e = errors.New("use TEAM, then enter choices at the prompts")
			} else {
				e = s.teamMenu(id, &pending)
			}
		case "b", "buyport", "acquire":
			if len(args) != 0 {
				e = errors.New("use ACQUIRE at the port you want to buy")
			} else {
				e = s.buyPort(id, &pending)
			}
		case "treasury":
			if len(args) != 0 {
				e = errors.New("use TREASURY")
			} else {
				e = s.portTreasuryReport(id)
			}
		case "$", "collect":
			if len(args) != 0 {
				e = errors.New("use COLLECT")
			} else {
				e = s.collectPortTreasury(id)
			}
		case "buy", "sell":
			var q int64
			if len(args) != 2 {
				e = errors.New("use BUY/SELL <commodity> <whole quantity>")
			} else {
				i := -1
				for j, name := range game.Goods {
					if strings.ToLower(args[0]) == name {
						i = j
					}
				}
				q, e = strconv.ParseInt(args[1], 10, 64)
				if e == nil {
					e = s.Store.Update(func(w *game.World) error { return w.Trade(id, token, cmd == "buy", i, q, s.Now()) })
				}
				if e == nil {
					e = s.Terminal.Printf("Trade saved.\r\n")
				}
			}
		case "equip":
			var q int64
			if len(args) != 2 {
				e = errors.New("use EQUIP <item> <whole quantity>")
			} else {
				q, e = strconv.ParseInt(args[1], 10, 64)
				if e == nil {
					e = s.Store.Update(func(w *game.World) error { return w.Equip(id, token, strings.ToLower(args[0]), q, s.Now()) })
				}
				if e == nil {
					e = s.Terminal.Printf("Equipment purchased and saved.\r\n")
				}
			}
		case "leave":
			e = s.Store.Update(func(w *game.World) error {
				p := w.Players[id]
				if p == nil {
					return errors.New("player no longer exists")
				}
				if p.DockToken == token {
					p.DockToken = ""
				}
				if p.PlanetToken == planetToken {
					p.PlanetToken = ""
					p.LandedPlanet = 0
				}
				return nil
			})
			token = ""
			planetToken = ""
		default:
			if s.Classic {
				e = errors.New("That command is not available in this edition yet.")
			} else {
				e = errors.New("unknown command; type ? for help")
			}
		}
		if e != nil {
			if outErr := s.Terminal.Printf("%s\r\n", e); outErr != nil {
				return outErr
			}
		}
	}
}

func showPlanet(t Terminal, p game.Planet) error {
	return t.Printf("Planet %s | governor %d | garrison %d | bank %d credits\r\nProduction: ore %.6g, organics %.6g, equipment %.6g per day\r\nWarehouses: ore %.6g, organics %.6g, equipment %.6g\r\nFighters %.6g | missiles %.6g | mines %.6g | plasma %.6g\r\n", p.Name, p.Owner, p.Ground, p.Bank, p.Production[0], p.Production[1], p.Production[2], p.Cargo[0], p.Cargo[1], p.Cargo[2], p.Fighters, p.Missiles, p.Mines, p.Plasma)
}

func showSensors(t Terminal, reports []game.SensorReport) error {
	if err := t.Printf("[ Sensors Activated ]\r\n"); err != nil {
		return err
	}
	for _, r := range reports {
		if err := t.Printf("Sector: %d | Warps: %v\r\n", r.Sector, r.Warps); err != nil {
			return err
		}
		if r.PortName != "" {
			selling := strings.Join(r.Selling, ", ")
			if r.PortID == 1 {
				selling = "ship equipment"
			} else if selling == "" {
				selling = "no cargo"
			}
			if err := t.Printf("Port: %s | Selling: %s\r\n", r.PortName, selling); err != nil {
				return err
			}
		}
		if r.PlanetName != "" {
			if err := t.Printf("Planet: %s | Forces: %d\r\n", r.PlanetName, r.Ground); err != nil {
				return err
			}
		}
		for _, ship := range r.Ships {
			if err := t.Printf("Ship: %s | Team: %d | Fighters: %d | Shields: %d\r\n", ship.Alias, ship.Team, ship.Fighters, ship.Shields); err != nil {
				return err
			}
		}
	}
	return t.Printf("[ End Sensor Scan ]\r\n")
}

func allClear(sectors []int) bool {
	for _, sector := range sectors {
		if sector != 0 {
			return false
		}
	}
	return true
}

func splitCommands(line string) []string {
	var commands []string
	for _, command := range strings.Split(line, ";") {
		upper := strings.ToUpper(command)
		at := strings.LastIndex(upper, "/R")
		if at >= 0 {
			n, err := strconv.Atoi(strings.TrimSpace(command[at+2:]))
			if err == nil && n >= 2 && n <= 20 {
				for i := 0; i < n; i++ {
					commands = append(commands, strings.TrimSpace(command[:at]))
				}
				continue
			}
		}
		commands = append(commands, command)
	}
	return commands
}
