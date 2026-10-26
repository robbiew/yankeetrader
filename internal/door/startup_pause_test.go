package door

import (
	"strings"
	"testing"
	"time"

	gd "github.com/robbiew/godoors"
	"github.com/robbiew/yankeetrader/internal/game"
)

type startupPauseTerminal struct {
	scripted
	t    *testing.T
	keys int
	ansi bool
}

func (p *startupPauseTerminal) ReadKey(time.Time) (rune, gd.Key, error) {
	p.keys++
	text := p.output.String()
	switch p.keys {
	case 1:
		return 0, gd.KeyEnter, nil
	case 2:
		artPresent := strings.Contains(text, "RE-USE THEM WITH ONE")
		if p.ansi {
			artPresent = strings.Contains(text, "\x1b7") && strings.Contains(text, "\x1b8") && !strings.Contains(text, "\x1b[s") && !strings.Contains(text, "\x1b[u")
		}
		if !artPresent || strings.Contains(text, "[ Info ]") || strings.Contains(text, "Initializing...") {
			p.t.Fatal("opening page was replaced before receiving its own keypress")
		}
	case 3:
		if !strings.Contains(text, "[ Info ]") || strings.Count(text, "[ Press any Key ]") != 3 {
			p.t.Fatal("ship info lacks its separate key pause")
		}
	default:
		p.t.Fatal("unexpected extra startup key pause")
	}
	return ' ', gd.KeyNone, nil
}

func TestOpeningAndShipInfoRequireSeparateKeys(t *testing.T) {
	for _, ansi := range []bool{false, true} {
		t.Run(map[bool]string{false: "ascii", true: "ansi"}[ansi], func(t *testing.T) {
			term := &startupPauseTerminal{scripted: scripted{lines: []string{"q;y"}}, t: t, ansi: ansi}
			s, st := navigationSession(t, term)
			s.Classic = true
			s.ANSI = ansi
			s.Local = true
			if err := st.Update(func(w *game.World) error { _, err := w.Join(s.Identity, s.Alias); return err }); err != nil {
				t.Fatal(err)
			}
			if err := s.Run(); err != nil {
				t.Fatal(err)
			}
			if term.keys != 3 {
				t.Fatal("title, opening and info did not each wait for a key", term.keys)
			}
		})
	}
}
