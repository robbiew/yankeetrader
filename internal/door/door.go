package door

import (
	"errors"
	"fmt"
	gd "github.com/robbiew/godoors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
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
	pending []inputKey
	readKey func(time.Duration) (rune, gd.Key, error)
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

func (GoDoors) Printf(f string, args ...any) error {
	_, e := fmt.Fprintf(gd.Output(), f, args...)
	return e
}
func (g *GoDoors) ReadLine(deadline time.Time) (string, error) {
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
			r, k, e = g.read(left)
		}
		if e != nil {
			return "", e
		}
		if k == gd.KeyEnter {
			return string(b), g.Printf("\r\n")
		}
		if k == gd.KeyEsc {
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
			if e = g.Printf("%c", r); e != nil {
				return "", e
			}
		}
	}
}

type Session struct {
	Store           store.Store
	Terminal        Terminal
	Identity, Alias string
	Deadline        time.Time
	Now             func() time.Time
}

func (s Session) Run() error {
	if s.Now == nil {
		s.Now = time.Now
	}
	var id int
	if e := s.Store.Update(func(w *game.World) error {
		w.Maintain(s.Now())
		p, e := w.Join(s.Identity, s.Alias)
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
	if e := s.Terminal.Printf("\r\nYANKEE TRADER - Go reconstruction\r\nWelcome, %s. Actions save automatically. Type ? for help.\r\n", s.Alias); e != nil {
		return e
	}
	pending := []string{}
	token := ""
	planetToken := ""
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
			if e = s.Terminal.Printf("\r\nSector %d | %d credits | %d turns > ", p.Sector, p.Credits, p.Turns); e != nil {
				return e
			}
			line, e := s.Terminal.ReadLine(s.Deadline)
			if errors.Is(e, io.EOF) {
				return nil
			}
			if e != nil {
				return e
			}
			pending = strings.Split(line, ";")
		}
		command := strings.Fields(pending[0])
		pending = pending[1:]
		if len(command) == 0 {
			continue
		}
		cmd := strings.ToLower(command[0])
		args := command[1:]
		switch cmd {
		case "q", "quit":
			return s.Terminal.Printf("Saved. Safe travels, %s.\r\n", p.Alias)
		case "?", "help":
			e = s.Terminal.Printf("I info | L look | S sensors (free) | M <sector> move\r\nPATH <from> <to> (free) | AUTO <sector> (confirm Y/N)\r\nAVOID [<slot 1-30> <sector, or 0 to clear>] (free)\r\nP dock (1 turn)\r\nBUY/SELL <ore|organics|equipment> <quantity>\r\nEQUIP <holds|fighters|shields|forces> <quantity> (Earth)\r\nLAND | CREATE <name> (25000) | PLANET status\r\nTAKE <item> <qty> | A take all | TRANSFER <item> [qty]\r\nBANK <target balance> | INVEST <credits> | GARRISON <target>\r\nLEAVE port/planet | Q quit. Stack commands with semicolons.\r\n")
		case "i", "info":
			e = s.Terminal.Printf("%s: holds %d; ore %d; organics %d; equipment %d\r\nFighters %d; shields %d; ground forces %d\r\nMissiles %d; mines %d; plasma %d\r\n", p.Alias, p.Holds, p.Cargo[0], p.Cargo[1], p.Cargo[2], p.Fighters, p.Shields, p.Ground, p.Missiles, p.Mines, p.Plasma)
		case "l", "look":
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
				if port.ID == 1 {
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
			e = errors.New("unknown command; type ? for help")
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
