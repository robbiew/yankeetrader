package door

import (
	"errors"
	"fmt"
	gd "github.com/robbiew/godoors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"github.com/robbiew/yankeetrader/internal/version"
	"io"
	prng "math/rand"
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
	disruptionRandom     func() float64 // Test injection only; production uses independent login draws.
	visibility           *game.Visibility
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
	var visibility *game.Visibility
	defer func() {
		var committed *store.DurabilityError
		if errors.Is(runErr, io.EOF) && !errors.As(runErr, &committed) {
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
	var generation, season uint64
	replaced := false
	reactivated := false
	if s.Classic {
		var err error
		id, err = s.classicStartup()
		if errors.Is(err, io.EOF) {
			return sessionInputEnd(err)
		}
		if err != nil {
			return err
		}
	} else {
		if e := s.Store.Update(func(w *game.World) error {
			if !time.Now().Before(s.Deadline) {
				return errors.New("session time expired")
			}
			if _, e := w.RunMaintenance(s.Now(), prng.Float64); e != nil {
				return e
			}
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
				replaced = p.Death != nil
				reactivated = !p.RetiredAt.IsZero()
				if e = w.LoginShip(id, s.Now()); e != nil {
					return e
				}
				generation = p.ShipGeneration
				season = w.Season
				p.DockToken = ""
				p.PlanetToken = ""
				p.LandedPlanet = 0
			}
			if e == nil {
				e = w.RecordLogin(id, s.Now())
			}
			if e == nil && !time.Now().Before(s.Deadline) {
				e = errors.New("session time expired")
			}
			return e
		}); e != nil {
			return e
		}
		s.Store = s.Store.ForShip(id, generation, season)
		if reactivated {
			if err := s.retirementNotice(); err != nil {
				return err
			}
		}
		if replaced {
			if err := s.replacementNotice(id); err != nil {
				return err
			}
		}
		if e := s.Terminal.Printf("\r\n%s\r\nWelcome, %s. Actions save automatically. Type ? for help.\r\n", version.String(), s.Alias); e != nil {
			return e
		}
	}
	rng := s.disruptionRandom
	if rng == nil {
		rng = prng.Float64
	}
	startErr := s.Store.StartDisruption(rng, s.Now, s.Deadline)
	if _, err := s.finishArrival(startErr, nil); err != nil {
		return err
	}
	if terminal, ok := s.Terminal.(*GoDoors); ok {
		terminal.commandMode = true
	}
	var err error
	visibility, err = s.Store.SessionVisibility()
	if err != nil {
		return err
	}
	s.visibility = visibility
	pending := []string{}
	token := ""
	planetToken := ""
	if _, err := s.resolveCurrentMines(id, &pending); err != nil {
		return err
	}
	if err := s.Store.Update(func(w *game.World) error {
		if w.Players[id].Team != 0 {
			_, err := w.VisitTeam(id)
			return err
		}
		return nil
	}); err != nil && !errors.Is(err, game.ErrDefenseEncounter) {
		return err
	}
	computer := false
	for {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		if interrupted, err := s.resolveCurrentMines(id, &pending); err != nil {
			return err
		} else if interrupted {
			continue
		}
		if err := s.intelligence(true); err != nil {
			return err
		}
		if err := s.battleReports(id, true); err != nil {
			return err
		}
		if err := s.deliverRadio(id); err != nil {
			return err
		}
		w, e := s.Store.View()
		if e != nil {
			return e
		}
		p := w.Players[id]
		if p != nil {
			if p.DockToken != token {
				token = ""
			}
			if p.PlanetToken != planetToken {
				planetToken = ""
			}
		}
		if p == nil {
			return errors.New("player no longer exists")
		}
		if len(pending) == 0 && w.HostileDefense(id, p.Sector) {
			if e = s.Terminal.Printf("Hostile sector fighters block normal actions. Use BRIBE [credits], BREACH %d <fighters> or FLEE.\r\n", p.Sector); e != nil {
				return e
			}
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
				return sessionInputEnd(e)
			}
			if e != nil {
				return e
			}
			pending = splitCommands(line)
		}
		// Input may have waited while another process destroyed/replaced the
		// ship. Refresh before even a read-only dispatch; mutations recheck
		// again under the transaction lock.
		if interrupted, err := s.resolveCurrentMines(id, &pending); err != nil {
			return err
		} else if interrupted {
			continue
		}
		w, e = s.Store.View()
		if e != nil {
			return e
		}
		p = w.Players[id]
		if p.DockToken != token {
			token = ""
		}
		if p.PlanetToken != planetToken {
			planetToken = ""
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
			case "2":
				cmd = "portreport"
			case "8":
				cmd = "news"
			case "9":
				cmd = "planetreport"
			case "13":
				cmd = "myplanets"
			case "4":
				cmd = "rank"
			case "5":
				cmd = "radio"
			case "6":
				cmd = "messages"
			case "14":
				cmd = "nearest"
			case "15":
				cmd = "spies"
			case "16":
				cmd = "pairs"
			case "17":
				cmd = "profits"
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
			case "11":
				groups, err := w.OwnSectorFighters(id)
				if err != nil {
					return err
				}
				if e = s.Terminal.Printf("\r\nSearching;\r\n\r\n Sector   Amount\r\n--------*--------\r\n"); e != nil {
					return e
				}
				if len(groups) == 0 {
					e = s.Terminal.Printf("No sector fighters found.\r\n")
				} else {
					for _, group := range groups {
						if e = s.Terminal.Printf(" %-8d %d\r\n", group.Sector, group.Fighters); e != nil {
							return e
						}
					}
				}
				if e != nil {
					return e
				}
				continue
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
		if s.Classic && cmd == "b" && w.HostileDefense(id, p.Sector) {
			cmd = "bribe"
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
					return sessionInputEnd(err)
				}
				if err != nil {
					return err
				}
				if !strings.EqualFold(answer, "y") {
					continue
				}
			}
			if err := s.Store.RefreshScoresOnLogout(s.Deadline); err != nil {
				return err
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
			e = s.Terminal.Printf("I info | L look | S sensors (free) | M <sector> move\r\nPORTREPORT [sector] | PLANETREPORT [sector] | MYPLANETS\r\nNEAREST [all|own|team|enemy|unowned] or <good> <buy|sell>\r\nPAIRS (reachable port pairs) | PROFITS (current port neighbors)\r\nRANK [OLD] (player/team scores)\r\nBATTLES (private Xannor reports; last 32)\r\nNEWS [TODAY|YESTERDAY] (public journal)\r\nSPIES (active locations) | INTEL (this login's last 30 reports)\r\nHIRE <starting sector> [starting sector ...] (Earth; 333000 each; max 3)\r\nRADIO [alias or player number] | MESSAGES (history) | INBOX (unread)\r\nPATH <from> <to> (free) | AUTO <sector> (confirm Y/N)\r\nG/GENESIS end season (actual owned ports; fresh literal GENESIS)\r\nSEASONS (public winner history)\r\nW/WARP emergency warp (random destination; fresh Y/N)\r\nLOTTERY [six digits] (Earth; 5 credits; fresh Y/N)\r\nANTICLOAK (Earth; 500000 for this login; fresh Y/N)\r\nAVOID [<slot 1-30> <sector, or 0 to clear>] (free)\r\nATTACK [<ship number> <fighters>] (fresh Y/N confirmation)\r\nMISSILE [<sector> <quantity>] (routed; fresh Y/N; may trigger retaliation)\r\n+/PLASMA [<sector> <quantity>] (1-64; indiscriminate; fresh Y/N)\r\nD/DROP [<quantity>] mines in current sector (fresh Y/N)\r\nF/DEFEND <final quantity> | REINFORCE <quantity>\r\nBRIBE [credits] or BRIBE <sector> <credits> | BREACH <sector> <fighters> | FLEE (fresh confirmation)\r\nP dock (1 turn)\r\nBUY/SELL <ore|organics|equipment> <quantity>\r\nT/TEAM team menu (free)\r\nACQUIRE port (confirm Y/N) | TREASURY report | COLLECT personal treasuries\r\nEQUIP <holds|fighters|shields|forces|scanner|cloak> <quantity> (Earth; scanner quantity 1; cloak in whole points)\r\nLAND (denied access offers ground assault) | CREATE <name> (25000) | PLANET status\r\nTHRUST <sector> (landed; 10 turns/hop; fresh confirmation)\r\nTAKE <item> <qty> | A take all | TRANSFER <item> [qty]\r\nBANK <target balance> | INVEST <credits> | GARRISON <target>\r\nLEAVE port/planet | Q quit. Stack commands with semicolons.\r\n")
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
			if e == nil {
				e = s.Terminal.Printf("Cloak energy: %.0f%%\r\n", p.Cloak*100)
			}
			if e == nil {
				e = s.Terminal.Printf("Danger scanner installed: %t\r\n", p.DangerScanner)
			}
			if e == nil && visibility.AntiCloakActivations() > 0 {
				e = s.Terminal.Printf("Anti-cloak active for this login; normal cloak consumption applies.\r\n")
			}
			if e == nil && w.HasXannorRevenge(id) {
				e = s.Terminal.Printf("Xannor revenge pending for this ship.\r\n")
			}
		case "l", "look":
			if s.Classic {
				e = s.classicSector(w, id)
				break
			}
			sector := w.Sectors[p.Sector]
			e = s.Terminal.Printf("Warps: %v\r\n", sector.Warps)
			if e == nil && w.Disrupted(id, p.Sector) {
				e = s.Terminal.Printf("** Space-time disruption detected! **\r\n")
			}
			if e == nil && sector.Port != 0 {
				e = s.Terminal.Printf("Port: %s\r\n", w.Ports[sector.Port].Name)
			}
			if e == nil && sector.Planet != 0 {
				e = s.Terminal.Printf("Planet: %s\r\n", w.Planets[sector.Planet].Name)
			}
		case "+", "plasma":
			e = s.launchPlasma(args, &pending)
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "!", "missile", "missiles":
			if visibility == nil {
				visibility, e = s.Store.SessionVisibility()
			}
			if e == nil {
				e = s.launchMissiles(id, args, &pending, visibility)
				if errors.Is(e, io.EOF) {
					return sessionInputEnd(e)
				}
			}
		case "d", "drop", "lay":
			e = s.placeMines(id, args, &pending)
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "f", "defend":
			e = s.setSectorFighters(id, args, &pending, false)
		case "reinforce":
			e = s.setSectorFighters(id, args, &pending, true)
		case "bribe":
			e = s.bribe(id, args, &pending)
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "breach", "flee":
			e = s.defenseEncounter(id, args, &pending, cmd == "flee")
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "attack":
			if visibility == nil {
				visibility, e = s.Store.SessionVisibility()
			}
			if e == nil {
				e = s.attackShip(id, args, &pending, visibility)
				if errors.Is(e, io.EOF) {
					return sessionInputEnd(e)
				}
			}
		case "s", "scan", "sensors":
			if len(args) != 0 {
				e = errors.New("use S to scan adjacent sectors")
			} else {
				var reports []game.SensorReport
				if visibility == nil {
					visibility, e = s.Store.SessionVisibility()
				}
				if e == nil {
					reports, e = w.ScanVisible(id, visibility, prng.Float64)
				}
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
		case "rank", "rankings":
			e = s.rankings(id, args, &pending)
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "news":
			e = s.newspaper(id, args, &pending)
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "spies":
			if len(args) != 0 {
				e = errors.New("use SPIES without arguments")
			} else {
				e = s.listSpies()
			}
		case "intel":
			if len(args) != 0 {
				e = errors.New("use INTEL without arguments")
			} else {
				e = s.intelligence(false)
			}
		case "hire":
			if len(args) == 0 {
				e = errors.New("use HIRE <starting sector> [starting sector ...] while docked at Earth")
			} else {
				e = s.hireSpies(token, args, &pending)
			}
		case "battles":
			if len(args) != 0 {
				e = errors.New("use BATTLES without arguments")
			} else {
				e = s.battleReports(id, false)
			}
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "radio":
			e = s.sendRadio(id, args, &pending)
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "messages", "inbox":
			e = s.radioHistory(id, args, cmd == "inbox")
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "nearest", "pairs", "profits":
			e = s.tradeReport(id, cmd, args, &pending)
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "portreport", "planetreport", "myplanets":
			e = s.computerReport(id, cmd, args, &pending)
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
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
		case "g", "genesis":
			var done bool
			done, e = s.genesis(args, &pending)
			if done {
				return e
			}
		case "seasons":
			e = s.seasonHistory(args)
		case "lottery":
			e = s.paidLottery(token, args, &pending)
			var committed *store.DurabilityError
			if errors.Is(e, io.EOF) && !errors.As(e, &committed) {
				return nil
			}
		case "anticloak", "anti-cloak":
			e = s.activateAntiCloak(token, args, &pending)
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
			}
		case "w", "warp":
			e = s.manualWarp(id, args, &pending)
			if errors.Is(e, io.EOF) {
				return sessionInputEnd(e)
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
							return sessionInputEnd(e)
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
							handled, scanErr := s.scannedMove(id, path[hop], &pending, path[hop-1:])
							if handled || scanErr != nil {
								if errors.Is(scanErr, io.EOF) {
									return sessionInputEnd(scanErr)
								}
								e = scanErr
								break
							}
							e = s.Store.UpdateWithSpies(func(w *game.World) error { return w.FollowCourse(id, path[hop-1:]) }, s.Now(), s.Deadline)
							interrupted, arrivalErr := s.finishArrival(e, &pending)
							e = arrivalErr
							if e != nil || interrupted {
								break
							}
							token, planetToken = "", ""
							if e = s.intelligence(true); e != nil {
								return e
							}
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
				current, viewErr := s.Store.View()
				if viewErr != nil {
					e = viewErr
					break
				}
				e = s.Store.CreatePlanet(id, strings.Join(args, " "), current.Players[id].Sector, s.Now, s.Deadline)
				if e == nil {
					token, planetToken = "", ""
				}
				e = s.planetCreationReceipt(e, strings.Join(args, " "), false)
			}
		case "land":
			if s.Classic {
				e = s.classicLand(id, &pending)
				if errors.Is(e, io.EOF) {
					var committed *store.DurabilityError
					if errors.As(e, &committed) {
						return e
					}
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
			if e != nil && e.Error() == "permission to land is denied by ground defenses" {
				planetToken, e = s.forceLanding(id, &pending)
				if e == nil && planetToken != "" {
					current, viewErr := s.Store.View()
					e = viewErr
					if e == nil {
						status, e = current.PlanetStatus(id, planetToken, s.Now())
					}
				}
			}
			if e == nil && planetToken != "" {
				token = ""
				e = showPlanet(s.Terminal, status)
			}
		case "thrust", "thrusters":
			e = s.thrusters(planetToken, args, &pending)
			if e == nil {
				current, viewErr := s.Store.View()
				e = viewErr
				if e == nil {
					if current.Players[id].PlanetToken != planetToken {
						planetToken = ""
					}
					if current.Players[id].DockToken != token {
						token = ""
					}
				}
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
					e = s.moveShip(id, to, &pending)
					if errors.Is(e, io.EOF) {
						return sessionInputEnd(e)
					}
				}
				if e == nil {
					token = ""
					planetToken = ""

				}
			}
		case "p", "dock":
			var port game.Port
			var prices [3]int64
			e = s.Store.UpdateWithSpies(func(w *game.World) error {
				if err := w.Dock(id, s.Now()); err != nil {
					return err
				}
				p := w.Players[id]
				token = p.DockToken
				port = *w.Ports[w.Sectors[p.Sector].Port]
				prices = p.DockPrices
				return nil
			}, s.Now(), s.Deadline)
			if e == nil {
				planetToken = ""
				if e = s.intelligence(true); e != nil {
					return e
				}
				if s.Classic {
					e = s.classicPort(id, token, &pending)
					token = ""
				} else if port.ID == 1 {
					e = s.Terminal.Printf("Earth: holds 500, fighters 100, shields 50, forces 750 credits each. Danger scanner: 250000 (one). Cloak: 1000 per point; ANTICLOAK: 500000 per login activation.\r\nLOTTERY [six digits]: 5 credits, finite daily plays, fresh Y/N.\r\nSpies: 333000 each; HIRE <starting sector> [sector ...], max 3 this login.\r\n")
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
					if strings.EqualFold(args[0], "cloak") {
						e = s.buyCloak(token, q)
					} else if strings.EqualFold(args[0], "scanner") {
						e = s.buyScanner(id, token, q)
					} else {
						e = s.Store.Update(func(w *game.World) error { return w.Equip(id, token, strings.ToLower(args[0]), q, s.Now()) })
					}
				}
				if e == nil && !strings.EqualFold(args[0], "scanner") && !strings.EqualFold(args[0], "cloak") {
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
		if _, arrivalErr := s.finishArrival(e, &pending); arrivalErr != nil {
			e = arrivalErr
		}
		if errors.Is(e, game.ErrShipDestroyed) || errors.Is(e, game.ErrShipChanged) || errors.Is(e, game.ErrSeasonChanged) {
			return e
		}
		// A visible committed write with uncertain durability must end the login.
		// Returning to the prompt would invite another payment after its receipt.
		var committed *store.DurabilityError
		if errors.As(e, &committed) {
			return e
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
		if r.Disruption {
			if err := t.Printf("** Space-time disruption detected! **\r\n"); err != nil {
				return err
			}
		}
		if r.Mines > 0 {
			if err := t.Printf("Sector mines: %d\r\n", r.Mines); err != nil {
				return err
			}
		}
		if r.DefenseFighters > 0 {
			if err := t.Printf("Sector fighters: %d | Owner: %s\r\n", r.DefenseFighters, r.DefenseOwner); err != nil {
				return err
			}
		}
		if r.PlanetName != "" {
			if err := t.Printf("Planet: %s | Forces: %d\r\n", r.PlanetName, r.Ground); err != nil {
				return err
			}
		}
		for _, ship := range r.Ships {
			if ship.Revealed {
				if err := t.Printf("A cloaking field shimmers and fades.\r\n"); err != nil {
					return err
				}
			}
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
