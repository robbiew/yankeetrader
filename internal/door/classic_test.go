package door

import (
	gd "github.com/robbiew/godoors"
	"github.com/robbiew/yankeetrader/internal/version"
	"regexp"
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func TestClassicNewPlayerAndReturningAlias(t *testing.T) {
	term := &scripted{lines: []string{"", "", "Pilot", "y", "n", "", "?;c;?;1;q;y"}}
	s, st := navigationSession(t, term)
	s.Classic = true
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	text := term.output.String()
	cursor := 0
	for _, part := range []string{"Yankee Trader", version.OriginalCredit, version.BasedOn, "Initializing...", "You are a new player.", "Enter the FULL alias", "Is this OK (Y/[N])?", "Your Alias has been recorded.", "Your ship has been built.", "Do you want instructions", "[ Info ]", "[ Press any Key ]", "Sector: 1", "Main Command (?=Help)?", "<Help>", "<Computer activated>", "Computer commands:", "<Computer deactivated>"} {
		at := strings.Index(text[cursor:], part)
		if at < 0 {
			t.Fatalf("missing or out-of-order %q in %s", part, text)
		}
		cursor += at + len(part)
	}
	if strings.Contains(text, "Orion") || strings.Contains(text, "100000") {
		t.Fatal("fixture state leaked")
	}
	w, err := st.View()
	if err != nil {
		t.Fatal(err)
	}
	p := w.Players[1]
	if p.Alias != "Pilot" || p.Credits != 1005 || p.Turns != 500 || p.LastLogin == "" {
		t.Fatalf("onboarding state: %+v", p)
	}
	term = &scripted{lines: []string{"", "", "", "q;y"}}
	s.Terminal = term
	s.Alias = "Changed BBS handle"
	if err = s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ = st.View()
	if len(w.Players) != 1 || w.Players[1].Alias != "Pilot" || strings.Contains(term.output.String(), "You are a new player") || !strings.Contains(term.output.String(), "You have been on today.") {
		t.Fatal("returning login lost alias or repeated registration")
	}
}

func TestResurrectionTitle(t *testing.T) {
	for _, tc := range []struct{ ansi, local bool }{{false, true}, {true, true}, {true, false}} {
		term := &scripted{}
		s := Session{Terminal: term, ANSI: tc.ansi, Local: tc.local}
		if err := s.drawClassic(resurrectionTitle()); err != nil {
			t.Fatal(err)
		}
		text := regexp.MustCompile(`\x1b\[[0-9;?]*[@-~]`).ReplaceAllString(term.output.String(), "")
		for _, want := range []string{version.Name, version.OriginalCredit, "Version " + version.Version, version.Repository, version.BasedOn, "[ Press any Key ]"} {
			if !strings.Contains(text, want) {
				t.Fatalf("missing %q", want)
			}
		}
		for _, obsolete := range []string{"UNREGISTERED", "REGISTER THIS GAME", "Fidonet", "1-717", "Compiled", "By Alan Davenport", "original YT Version"} {
			if strings.Contains(text, obsolete) {
				t.Fatalf("obsolete splash text %q", obsolete)
			}
		}
	}
}

func TestClassicDefaultsReservedAliasesAndCancellation(t *testing.T) {
	term := &scripted{lines: []string{"", "", "Sysop", "Xannor", "Mercenaries", "Rejected", "n", "", "y", "n", "", "q;y"}}
	s, st := navigationSession(t, term)
	s.Classic = true
	s.RealName = "Real Trader"
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Alias != "Real Trader" {
		t.Fatal("blank alias did not choose real name")
	}
	if strings.Count(term.output.String(), "That ALIAS is NOT allowed") != 3 {
		t.Fatal("reserved aliases accepted")
	}
	for _, lines := range [][]string{{}, {""}, {"", ""}, {"", "", "Proposed"}, {"", "", "Proposed", "n"}} {
		term := &scripted{lines: lines}
		s, st := navigationSession(t, term)
		s.Classic = true
		if err := s.Run(); err != nil {
			t.Fatal(err)
		}
		w, _ := st.View()
		if len(w.Players) != 0 {
			t.Fatal("disconnected or rejected alias created a player")
		}
	}
}

func TestClassicAliasCollisionDoesNotCreateAnotherPlayer(t *testing.T) {
	term := &scripted{lines: []string{"", "", "Pilot", "Other", "y", "n", "", "q;y"}}
	s, st := navigationSession(t, term)
	s.Classic = true
	if err := st.Update(func(w *game.World) error { _, err := w.Join("existing", "Pilot"); return err }); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if len(w.Players) != 2 || w.Players[2].Alias != "Other" || !strings.Contains(term.output.String(), "already in use") {
		t.Fatal("duplicate alias accepted")
	}
}

func TestClassicEncodingAndOriginalTitleCells(t *testing.T) {
	for _, tc := range []struct {
		name        string
		ansi, local bool
	}{{"ascii", false, true}, {"local", true, true}, {"remote", true, false}} {
		t.Run(tc.name, func(t *testing.T) {
			term := &scripted{}
			s := Session{Terminal: term, ANSI: tc.ansi, Local: tc.local}
			if err := s.drawClassic(template("title")); err != nil {
				t.Fatal(err)
			}
			text := term.output.String()
			if strings.Contains(text, "\x1b[") != tc.ansi {
				t.Fatal("ANSI controls leaked or missing")
			}
			if !strings.Contains(text, "By Alan Davenport") {
				t.Fatal("title missing")
			}
			term.output.Reset()
			if err := s.classicText(string([]byte{0xc9, 0xcd, 0xbb})); err != nil {
				t.Fatal(err)
			}
			want := "+-+"
			if tc.ansi && tc.local {
				want = "╔═╗"
			} else if tc.ansi {
				want = string([]byte{0xc9, 0xcd, 0xbb})
			}
			if term.output.String() != want {
				t.Fatalf("encoding %q != %q", term.output.String(), want)
			}
		})
	}
}

func TestClassicExpiredLoginAndDateValidation(t *testing.T) {
	term := &courseTerminal{scripted: &scripted{lines: []string{"", "", "Pilot", "y", "n", ""}}}
	s, st := navigationSession(t, term)
	s.Classic = true
	s.Deadline = time.Now().Add(-time.Second)
	if err := s.Run(); err == nil {
		t.Fatal("expired startup accepted")
	}
	w, _ := st.View()
	if len(w.Players) != 0 {
		t.Fatal("expired startup creates player")
	}
	_, err := w.Join("date", "Date")
	if err != nil {
		t.Fatal(err)
	}
	w.Players[1].LastLogin = "not-a-date"
	if err = w.Validate(); err == nil {
		t.Fatal("invalid login date accepted")
	}
}

func TestDOSCommandRepeat(t *testing.T) {
	commands := splitCommands("I/R3;;M 2;Q")
	if strings.Join(commands, ";") != "I;I;I;;M 2;Q" {
		t.Fatal(commands)
	}
	if len(splitCommands("I/R21")) != 1 {
		t.Fatal("unbounded command repeat")
	}
}

func TestCompactReconnectPreservesChosenClassicAlias(t *testing.T) {
	term := &scripted{lines: []string{"", "", "Pilot", "y", "n", "", "q;y"}}
	s, st := navigationSession(t, term)
	s.Classic = true
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	s.Classic = false
	s.Alias = "ChangedCaller"
	s.Terminal = &scripted{lines: []string{"q"}}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if w.Players[1].Alias != "Pilot" {
		t.Fatal("compact login overwrote chosen in-game alias")
	}
}

func TestSavedCommandReplayDoesNotRequireEnter(t *testing.T) {
	keys := []rune{'I', '/', 13, 18}
	g := &GoDoors{commandMode: true, readKey: func(time.Duration) (rune, gd.Key, error) {
		r := keys[0]
		keys = keys[1:]
		if r == 13 {
			return r, gd.KeyEnter, nil
		}
		return r, gd.KeyNone, nil
	}}
	line, err := g.ReadLine(time.Now().Add(time.Minute))
	if err != nil || line != "I" || g.savedLine != "I" {
		t.Fatal(line, err)
	}
	line, err = g.ReadLine(time.Now().Add(time.Minute))
	if err != nil || line != "I" || len(keys) != 0 {
		t.Fatal("Ctrl-R did not replay", line, err)
	}
}

func TestClassicPromptClockTimeoutPreservesInput(t *testing.T) {
	reads, ticks := 0, 0
	g := &GoDoors{onIdle: func() error { ticks++; return nil }, readKey: func(time.Duration) (rune, gd.Key, error) {
		reads++
		switch reads {
		case 1:
			return 0, gd.KeyNone, gd.ErrInputTimeout
		case 2:
			return 'I', gd.KeyNone, nil
		default:
			return 13, gd.KeyEnter, nil
		}
	}}
	line, err := g.ReadLine(time.Now().Add(time.Minute))
	if err != nil || line != "I" || ticks != 1 {
		t.Fatal("clock refresh lost input", line, ticks, err)
	}
}

func TestInstructionPagingControls(t *testing.T) {
	const prompt = "[ENTER] for more, [E] to end, or [NS] for Non-stop "
	for _, tc := range []struct {
		name     string
		input    []string
		prompts  int
		complete bool
	}{
		{"end", []string{"e"}, 1, false},
		{"next then end", []string{"", "E"}, 2, false},
		{"nonstop", []string{"ns"}, 1, true},
		{"invalid then nonstop", []string{"bad", "NS"}, 2, true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			term := &scripted{lines: tc.input}
			s := Session{Terminal: term, Deadline: time.Now().Add(time.Minute)}
			if err := s.classicInstructions(); err != nil {
				t.Fatal(err)
			}
			text := term.output.String()
			if strings.Count(text, prompt) != tc.prompts {
				t.Fatalf("wrong prompt count: %d", strings.Count(text, prompt))
			}
			if strings.Contains(text, "That's it for the instructions.") != tc.complete {
				t.Fatal("wrong manual completion state")
			}
			if len(term.lines) != 0 {
				t.Fatal("did not consume navigation input")
			}
		})
	}
}

func TestStatusBarIsLocalOnly(t *testing.T) {
	for _, local := range []bool{false, true} {
		term := &scripted{}
		s := Session{Terminal: term, ANSI: true, Local: local, Alias: "BBS Caller", Deadline: time.Now().Add(time.Minute)}
		cells := template("info")
		s.status(cells, "Pilot")
		if err := s.drawClassic(cells); err != nil {
			t.Fatal(err)
		}
		text := term.output.String()
		if strings.Contains(text, "\x1b[25;1H") != local || strings.Contains(text, "BBS Caller") != local {
			t.Fatalf("local=%v: unexpected status visibility", local)
		}
	}
}

type instructionInterruptTerminal struct {
	scripted
	checks int
}

func (t *instructionInterruptTerminal) Interrupted() (bool, error) {
	t.checks++
	return true, nil
}

func TestInstructionNonstopCanBeInterrupted(t *testing.T) {
	term := &instructionInterruptTerminal{scripted: scripted{lines: []string{"NS"}}}
	s := Session{Terminal: term, Deadline: time.Now().Add(time.Minute)}
	if err := s.classicInstructions(); err != nil {
		t.Fatal(err)
	}
	if term.checks != 1 || !strings.Contains(term.output.String(), "Ctrl-X to Stop") || strings.Contains(term.output.String(), "That's it for the instructions.") {
		t.Fatal("nonstop did not stop at interruption")
	}
}

func TestExitMusicRequiresDetectedSupport(t *testing.T) {
	for _, tc := range []struct{ ansi, music bool }{{true, true}, {true, false}, {false, true}, {false, false}} {
		term := &scripted{lines: []string{"q"}}
		s, _ := navigationSession(t, term)
		s.ANSI, s.Music = tc.ansi, tc.music
		if err := s.Run(); err != nil {
			t.Fatal(err)
		}
		text := term.output.String()
		if !strings.Contains(text, "Safe travels") {
			t.Fatal("missing goodbye")
		}
		if tc.ansi && tc.music {
			if !strings.HasSuffix(text, gd.MusicSequence(exitTune)) {
				t.Fatalf("missing safe music sequence: %q", text)
			}
		} else if strings.Contains(text, "FBEAP") || strings.Contains(text, "\x0e") {
			t.Fatalf("music leaked to unsupported terminal: %q", text)
		}
	}
}
