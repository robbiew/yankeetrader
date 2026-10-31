package door

import (
	"embed"
	"errors"
	"fmt"
	"io"
	prng "math/rand"
	"strconv"
	"strings"
	"time"

	gd "github.com/robbiew/godoors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/version"
)

// Captured DOS character/attribute templates and original opening/manual files.
//
//go:embed assets/*
var classicAssets embed.FS

func (g *GoDoors) ReadKey(deadline time.Time) (rune, gd.Key, error) {
	if !time.Now().Before(deadline) {
		return 0, gd.KeyNone, errors.New("session time expired")
	}
	if len(g.pending) > 0 {
		key := g.pending[0]
		g.pending = g.pending[1:]
		return key.r, key.k, nil
	}
	return g.read(time.Until(deadline))
}

func (s Session) waitClassicKey() error {
	if terminal, ok := s.Terminal.(interface {
		ReadKey(time.Time) (rune, gd.Key, error)
	}); ok {
		_, key, err := terminal.ReadKey(s.Deadline)
		if err == nil && key == gd.KeyEsc {
			return io.EOF
		}
		return err
	}
	_, err := s.readClassicLine()
	return err
}

func (s Session) classicText(text string) error {
	if !s.ANSI {
		text = plainCP437(text)
	} else if s.Local {
		text = decodeCP437(text)
	}
	return s.Terminal.Printf("%s", text)
}

func plainCP437(text string) string {
	var b strings.Builder
	for _, c := range []byte(text) {
		if c < 128 {
			b.WriteByte(c)
			continue
		}
		switch c {
		case 0xba, 0xb3:
			b.WriteByte('|')
		case 0xcd, 0xc4:
			b.WriteByte('-')
		default:
			b.WriteByte('+')
		}
	}
	return b.String()
}

func decodeCP437(text string) string {
	var b strings.Builder
	for _, c := range []byte(text) {
		if c < 128 {
			b.WriteByte(c)
		} else {
			b.WriteRune(cp437[c-128])
		}
	}
	return b.String()
}

func (s Session) timeLeft() string {
	seconds := int(time.Until(s.Deadline).Seconds())
	if seconds < 0 {
		seconds = 0
	}
	return fmt.Sprintf("%d:%02d", seconds/60, seconds%60)
}

// VT100 DECSC/DECRC also work in terminals that ignore CSI s/u. Preserve
// the input cursor and attributes while updating both clock fields together.
func (s Session) refreshClassicClock(width int) error {
	left := s.timeLeft()
	if s.Local {
		return s.Terminal.Printf("\x1b7\x1b[25;70H\x1b[0;96;44m%-10s\x1b[24;7H\x1b[0;32m%-*s\x1b8", left, width, left)
	}
	return s.Terminal.Printf("\x1b7\x1b[24;7H\x1b[0;32m%-*s\x1b8", width, left)
}

func template(name string) []byte {
	data, err := classicAssets.ReadFile("assets/" + name + ".bin")
	if err != nil {
		panic(err)
	}
	return data
}
func cellText(cells []byte, row, col, width int, text string) {
	for i := 0; i < width; i++ {
		ch := byte(' ')
		if i < len(text) {
			ch = text[i]
		}
		cells[((row-1)*80+col-1+i)*2] = ch
	}
}
func (s Session) status(cells []byte, alias string) {
	cellText(cells, 25, 1, 80, "")
	for x := 0; x < 80; x++ {
		attr := byte(0x1b)
		if x < 15 {
			attr = 0x3e
		}
		if x == 79 {
			attr = 7
		}
		cells[(24*80+x)*2+1] = attr
	}
	cellText(cells, 25, 1, 68, " Yankee Trader   | "+s.Alias+" | "+alias)
	cellText(cells, 25, 70, 10, s.timeLeft())
}

func (s Session) drawClassic(cells []byte) error {
	if len(cells) != 4000 {
		return errors.New("invalid DOS screen template")
	}
	var b strings.Builder
	if s.ANSI {
		b.WriteString("\x1b[0m\x1b[2J\x1b[H\x1b[?25l\x1b[?7l")
		previous := -1
		colors := []int{30, 34, 32, 36, 31, 35, 33, 37}
		rows := 24
		if s.Local {
			rows = 25
		}
		for y := 0; y < rows; y++ {
			fmt.Fprintf(&b, "\x1b[%d;1H", y+1)
			for x := 0; x < 80; x++ {
				i := (y*80 + x) * 2
				attr := int(cells[i+1])
				if attr != previous {
					fg := colors[attr&7]
					if attr&8 != 0 {
						fg += 60
					}
					bg := colors[(attr>>4)&7] + 10
					fmt.Fprintf(&b, "\x1b[0;%d;%dm", fg, bg)
					previous = attr
				}
				c := cells[i]
				if c < 32 {
					c = ' '
				}
				b.WriteByte(c)
			}
		}
		b.WriteString("\x1b[0m\x1b[?7h\x1b[?25h\x1b[1;24r\x1b[24;1H")
	} else {
		for y := 0; y < 24; y++ {
			var row strings.Builder
			for x := 0; x < 80; x++ {
				c := cells[(y*80+x)*2]
				if c < 32 {
					c = ' '
				}
				row.WriteByte(c)
			}
			b.WriteString(strings.TrimRight(row.String(), " "))
			b.WriteString("\r\n")
		}
	}
	return s.classicText(b.String())
}

func resurrectionTitle() []byte {
	cells := template("title")
	for row, text := range map[int]string{
		6:  version.Name,
		7:  version.OriginalCredit,
		10: version.Repository,
		12: "Version " + version.Version,
		14: version.BasedOn,
		16: "[ Press any Key ]",
	} {
		attr := cells[((row-1)*80+39)*2+1]
		cellText(cells, row, 1, 80, "")
		for x := 0; x < 80; x++ {
			cells[((row-1)*80+x)*2+1] = attr
		}
		cellText(cells, row, (80-len(text))/2+1, len(text), text)
	}
	return cells
}

func (s *Session) classicStartup() (int, error) {
	cells := resurrectionTitle()
	if !s.Local {
		cellText(cells, 1, 1, 80, "")
	}
	if err := s.drawClassic(cells); err != nil {
		return 0, err
	}
	if err := s.waitClassicKey(); err != nil {
		return 0, err
	}
	asset := "assets/ytopen.asc"
	if s.ANSI {
		asset = "assets/ytopen.ans"
	}
	opening, _ := classicAssets.ReadFile(asset)
	art := string(opening)
	if s.ANSI {
		// Preserve the asset while using the same portable save/restore as
		// the clock; some terminals ignore the original CSI s/u sequences.
		art = strings.NewReplacer("\x1b[s", "\x1b7", "\x1b[u", "\x1b8").Replace(art)
		// Brand the live page without changing the preserved DOS source art.
		subtitle := "Resurrection - " + version.Version
		art += "\x1b[7;1H\x1b[2K\x1b[0;96m" + strings.Repeat(" ", (80-len(subtitle))/2) + subtitle +
			"\x1b[15;1H\x1b[2K\x1b[0;37m" + strings.Repeat(" ", (80-len(version.BasedOn))/2) + version.BasedOn +
			"\x1b[16;1H\x1b[2K\x1b[0;31m" + strings.Repeat(" ", (80-len(version.OriginalCredit))/2) + version.OriginalCredit +
			"\x1b[17;1H\x1b[2K\x1b[0;37m                     " + version.Repository +
			"\x1b[18;1H\x1b[2K\x1b[19;1H"
	} else {
		art = strings.Replace(art, "Y A N K E E   T R A D E R ! ! !", version.Name+"\r\nVersion "+version.Version+"\r\n"+version.Repository, 1)
		art = strings.Replace(art, "By Alan Davenport", version.OriginalCredit+"\r\n"+version.BasedOn, 1)
	}
	if err := s.classicText("\r\nCntl-X to Stop\r\n" + art); err != nil {
		return 0, err
	}
	if err := s.Terminal.Printf("\r\n[ Press any Key ]"); err != nil {
		return 0, err
	}
	if err := s.waitClassicKey(); err != nil {
		return 0, err
	}
	if err := s.classicText("\r\nInitializing...\r\n\r\nWelcome " + s.Alias + "!\r\nSearching my records for your name.\r\n"); err != nil {
		return 0, err
	}
	w, err := s.Store.View()
	if err != nil {
		return 0, err
	}
	id := 0
	defaultAlias := s.RealName
	if defaultAlias == "" {
		defaultAlias = s.Alias
	}
	alias := defaultAlias
	for _, p := range w.Players {
		if p.Identity == s.Identity {
			id = p.ID
			alias = p.Alias
			break
		}
	}
	isNew := id == 0
	if isNew {
		for {
			if err = s.classicText("\r\nYou are a new player.\r\n\r\nEnter the FULL alias you wish to use in the game.\r\n\r\nPress [ENTER] to use your real name.\r\n-+> "); err != nil {
				return 0, err
			}
			alias, err = s.readClassicLine()
			if err != nil {
				return 0, err
			}
			alias = strings.Join(strings.Fields(strings.ReplaceAll(alias, ",", " ")), " ")
			if alias == "" {
				alias = defaultAlias
			}
			if err = game.ClassicAlias(w, alias); err != nil {
				if err = s.Terminal.Printf("%s\r\n", err); err != nil {
					return 0, err
				}
				continue
			}
			if err = s.Terminal.Printf("\r\n%s a.k.a. %s\r\n\r\nIs this OK (Y/[N])? ", s.Alias, alias); err != nil {
				return 0, err
			}
			answer, readErr := s.readClassicLine()
			if readErr != nil {
				return 0, readErr
			}
			if strings.EqualFold(strings.TrimSpace(answer), "y") {
				break
			}
		}
	}
	previousDay := ""
	var generation, season uint64
	replaced := false
	reactivated := false
	err = s.Store.Update(func(live *game.World) error {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		if _, e := live.RunMaintenance(s.Now(), prng.Float64); e != nil {
			return e
		}
		// The screen lookup may describe an ended season. Resolve identity again
		// under this lock; never retain its old numeric ID when no match exists.
		p, joinErr := classicLoginPlayer(live, s.Identity, alias)
		if joinErr != nil {
			return joinErr
		}
		id, previousDay = p.ID, p.LastLogin
		replaced = p.Death != nil
		reactivated = !p.RetiredAt.IsZero()
		if err := live.LoginShip(id, s.Now()); err != nil {
			return err
		}
		generation = p.ShipGeneration
		season = live.Season
		p.LastLogin = s.Now().UTC().Format("2006-01-02")
		p.DockToken, p.PlanetToken, p.LandedPlanet = "", "", 0
		if err := live.RecordLogin(id, s.Now()); err != nil {
			return err
		}
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		return nil
	})
	if err != nil {
		return 0, err
	}
	s.Store = s.Store.ForShip(id, generation, season)
	if reactivated {
		if err = s.retirementNotice(); err != nil {
			return 0, err
		}
	}
	if replaced {
		if err := s.replacementNotice(id); err != nil {
			return 0, err
		}
	}
	if isNew {
		if err = s.classicText("\r\nYour Alias has been recorded. Have fun!\r\n\r\nEntering a new player...\r\n\r\nYour ship has been built.\r\nDo you want instructions (Y/N) [N]? "); err != nil {
			return 0, err
		}
		answer, readErr := s.readClassicLine()
		if readErr != nil {
			return 0, readErr
		}
		if strings.EqualFold(strings.TrimSpace(answer), "y") {
			if err = s.classicInstructions(); err != nil {
				return 0, err
			}
		}
	} else if previousDay == s.Now().UTC().Format("2006-01-02") {
		if err = s.classicText("\r\nYou have been on today.\r\n"); err != nil {
			return 0, err
		}
	}
	w, err = s.Store.View()
	if err != nil {
		return 0, err
	}
	if err = s.classicInfo(w, id, true); err != nil {
		return 0, err
	}
	if err = s.waitClassicKey(); err != nil {
		return 0, err
	}
	if err = s.classicText("\r\nChecking for Radio Messages.\r\n"); err != nil {
		return 0, err
	}
	if err = s.deliverRadio(id); err != nil {
		return 0, err
	}
	return id, s.classicSector(w, id)
}

func (s Session) classicInstructions() error {
	raw, _ := classicAssets.ReadFile("assets/ytinstr.doc")
	lines := strings.Split(strings.ReplaceAll(string(raw), "\r\n", "\n"), "\n")
	for i, line := range lines {
		if strings.EqualFold(strings.TrimSpace(line), "by "+version.OriginalCreator) {
			lines = append(lines[:i], append([]string{version.OriginalCredit, version.BasedOn}, lines[i+1:]...)...)
			break
		}
	}
	nonstop := false
	for i, line := range lines {
		if !time.Now().Before(s.Deadline) {
			return errors.New("session time expired")
		}
		if nonstop {
			if terminal, ok := s.Terminal.(interface{ Interrupted() (bool, error) }); ok {
				stop, err := terminal.Interrupted()
				if err != nil {
					return err
				}
				if stop {
					return nil
				}
			}
		}
		if err := s.classicText(line + "\r\n"); err != nil {
			return err
		}
		if !nonstop && (i+1)%22 == 0 && i+1 < len(lines) {
			for {
				if err := s.classicText("[ENTER] for more, [E] to end, or [NS] for Non-stop "); err != nil {
					return err
				}
				answer, err := s.readClassicLine()
				if err != nil {
					return err
				}
				switch strings.ToUpper(strings.TrimSpace(answer)) {
				case "E":
					return nil
				case "NS":
					nonstop = true
					if err := s.classicText("Ctrl-X to Stop\r\n"); err != nil {
						return err
					}
				case "":
				default:
					continue
				}
				break
			}
		}
	}
	return nil
}

func numberCell(n int64, width int) string {
	value := strconv.FormatInt(n, 10)
	if len(value) > width {
		value = fmt.Sprintf("%.3g", float64(n))
	}
	return value
}
func (s Session) classicInfo(w *game.World, id int, pause bool) error {
	p := w.Players[id]
	cells := template("info")
	for row := 1; row <= 12; row++ {
		cellText(cells, row, 1, 80, "")
	}
	cellText(cells, 5, 1, 80, "                    [ Info ]")
	cellText(cells, 7, 1, 80, "Name  : "+p.Alias)
	cellText(cells, 8, 1, 80, "Time  : "+s.timeLeft())
	team := "None"
	if p.Team != 0 {
		team = strconv.Itoa(p.Team)
	}
	cellText(cells, 9, 1, 80, "Team  : "+team)
	if s.visibility.AntiCloakActivations() > 0 {
		cellText(cells, 10, 1, 80, "Anti-cloak active for this login; normal cloak consumption applies.")
	}
	if w.HasXannorRevenge(id) {
		cellText(cells, 11, 1, 80, "Xannor revenge pending for this ship.")
	}
	owned := int64(0)
	for _, port := range w.Ports {
		if port.Owner == id {
			owned++
		}
	}
	left := []int64{p.Credits, p.Turns, p.Fighters, p.Mines, p.Missiles, 0, p.Shields, p.Ground}
	right := []int64{int64(p.Sector), p.Holds, p.Cargo[0], p.Cargo[1], p.Cargo[2], owned, 0, p.Plasma}
	for row := 14; row <= 21; row++ {
		cellText(cells, row, 15, 12, numberCell(left[row-14], 12))
		cellText(cells, row, 45, 5, numberCell(right[row-14], 5))
	}
	scanner := "NONE"
	if p.DangerScanner {
		scanner = "Installed"
	}
	cellText(cells, 19, 15, 12, scanner)
	cellText(cells, 20, 45, 5, fmt.Sprintf("%.0f%%", p.Cloak*100))
	if !pause {
		cellText(cells, 24, 1, 80, "")
	}
	s.status(cells, p.Alias)
	return s.drawClassic(cells)
}
func (s Session) classicSector(w *game.World, id int) error {
	p := w.Players[id]
	sector := w.Sectors[p.Sector]
	if s.ANSI {
		if err := s.Terminal.Printf("\x1b[0;31m"); err != nil {
			return err
		}
	}
	if err := s.Terminal.Printf("\r\nSector: %d\r\n", p.Sector); err != nil {
		return err
	}
	if w.Disrupted(id, p.Sector) {
		if err := s.Terminal.Printf("** Space-time disruption detected! **\r\n"); err != nil {
			return err
		}
	}
	if port := w.Ports[sector.Port]; port != nil {
		selling := []string{}
		for i, c := range port.Coefficient {
			if c > 0 {
				selling = append(selling, []string{"Ore", "Org", "Equ"}[i])
			}
		}
		if port.ID == 1 {
			selling = []string{"Ship equipment"}
		}
		if err := s.Terminal.Printf("Port: %s, Selling: %s\r\n", port.Name, strings.Join(selling, ", ")); err != nil {
			return err
		}
	}
	if planet := w.Planets[sector.Planet]; planet != nil {
		if err := s.planetColor(14); err != nil {
			return err
		}
		if err := s.Terminal.Printf("Planet: %s * Forces: %d\r\n", planet.Name, planet.Ground); err != nil {
			return err
		}
		if err := s.planetColor(4); err != nil {
			return err
		}
	}
	warps := []string{}
	for _, to := range sector.Warps {
		warps = append(warps, strconv.Itoa(to))
	}
	return s.Terminal.Printf("Warps lead to: %s\r\n", strings.Join(warps, ", "))
}
func (s Session) classicHelp(alias string) error {
	cells := template("main-help")
	cellText(cells, 24, 1, 80, "")
	s.status(cells, alias)
	if err := s.drawClassic(cells); err != nil {
		return err
	}
	if s.ANSI {
		return s.Terminal.Printf("\x1b[23;1H")
	}
	return nil
}

func (s Session) classicArgument(prompt string, pending *[]string) (string, error) {
	if err := s.Terminal.Printf("%s", prompt); err != nil {
		return "", err
	}
	if len(*pending) == 0 {
		line, err := s.readClassicLine()
		if err != nil {
			return "", err
		}
		*pending = strings.Split(line, ";")
	}
	value := strings.TrimSpace((*pending)[0])
	*pending = (*pending)[1:]
	return value, nil
}

var cp437 = []rune(`ÇüéâäàåçêëèïîìÄÅÉæÆôöòûùÿÖÜ¢£¥₧ƒáíóúñÑªº¿⌐¬½¼¡«»░▒▓│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌█▄▌▐▀αßΓπΣσµτΦΘΩδ∞φε∩≡±≥≤⌠⌡÷≈°∙·√ⁿ²■ `)

func (s Session) readClassicLine() (string, error) {
	if !time.Now().Before(s.Deadline) {
		return "", errors.New("session time expired")
	}
	value, err := s.Terminal.ReadLine(s.Deadline)
	if g, ok := s.Terminal.(*GoDoors); ok && g.escaped {
		return "", io.EOF
	}
	return value, err
}

func terminalLabel(value string) string {
	var b strings.Builder
	for _, c := range []byte(value) {
		if c >= 32 && c != 127 {
			b.WriteByte(c)
		}
	}
	return strings.TrimSpace(b.String())
}

// Original DOS tune from YT.EXE, file offset 0x275ce. Use the portable
// CTerm introducer rather than the legacy CSI M form (delete-line on VT100).
const exitTune = "MBO2T200L64FBEAP8FBEAP8FBEAP4FBEAP8FBEAP8FBEAP4T128"

func (s Session) exitMusic() error {
	if !s.ANSI || !s.Music {
		return nil
	}
	return s.Terminal.Printf("%s", gd.MusicSequence(exitTune))
}

func (s Session) retirementNotice() error {
	return s.Terminal.Printf("Your inactive account has returned from retirement. Released estates are not restored; private history is preserved.\r\n")
}

// classicLoginPlayer is called only inside the authenticated login transaction.
// Its lookup starts fresh; an ID remembered by startup is never authentication.
func classicLoginPlayer(live *game.World, identity, alias string) (*game.Player, error) {
	for _, p := range live.Players {
		if p.Identity == identity {
			return p, nil
		}
	}
	if err := game.ClassicAlias(live, alias); err != nil {
		return nil, err
	}
	return live.Join(identity, alias)
}
