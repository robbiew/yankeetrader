package door

import (
	"regexp"
	"strconv"
	"strings"
	"testing"
	"time"
)

// promptLine replays one terminal row: printable text, CR, CUF and SGR. Any
// other escape (save/restore, absolute moves) fails the test, because the
// remote clock must not depend on sequences that terminals or BBS stdio
// bridges drop.
func promptLine(t *testing.T, text string) (string, int) {
	t.Helper()
	row, col := []rune(strings.Repeat(" ", 80)), 0
	csi := regexp.MustCompile(`^\x1b\[([0-9;]*)([A-Za-z])`)
	for len(text) > 0 {
		switch {
		case text[0] == '\r':
			col, text = 0, text[1:]
		case text[0] == '\x1b':
			m := csi.FindStringSubmatch(text)
			if m == nil || (m[2] != "C" && m[2] != "m") {
				t.Fatalf("unsupported sequence in remote clock output: %q", text)
			}
			if m[2] == "C" {
				n, _ := strconv.Atoi(m[1])
				if n < 1 {
					n = 1
				}
				col += n
			}
			text = text[len(m[0]):]
		default:
			row[col] = rune(text[0])
			col, text = col+1, text[1:]
		}
	}
	return strings.TrimRight(string(row), " "), col
}

// Reproduces the SyncTerm report: typing after a tick must continue at the
// input position, not after the clock.
func TestRemoteClockRefreshReturnsToInputColumn(t *testing.T) {
	const label = "Main Command (?=Help)?"
	for _, typed := range []string{"", "c;3;", "c;3;3000;y"} {
		term := &scripted{}
		s := Session{Terminal: term, Deadline: time.Now().Add(100 * time.Second)}
		start := "1:40"
		prompt := "Time: " + start + "  " + label + " " + typed
		if err := s.refreshClassicClock(len(start), len(label), len(typed)); err != nil {
			t.Fatal(err)
		}
		line, col := promptLine(t, prompt+term.output.String())
		if col != len(prompt) {
			t.Fatalf("typed %q: cursor at column %d, want %d (%q)", typed, col, len(prompt), line)
		}
		if !strings.HasSuffix(line, strings.TrimRight("  "+label+" "+typed, " ")) || !regexp.MustCompile(`^Time: 1:[34][0-9] `).MatchString(line) {
			t.Fatalf("typed %q: prompt line corrupted: %q", typed, line)
		}
	}
}

func TestRemoteClockPadsShrinkingTime(t *testing.T) {
	term := &scripted{}
	s := Session{Terminal: term, Deadline: time.Now().Add(9 * time.Second)}
	prompt := "Time: 10:00  X "
	if err := s.refreshClassicClock(5, 1, 0); err != nil {
		t.Fatal(err)
	}
	line, col := promptLine(t, prompt+term.output.String())
	if !regexp.MustCompile(`^Time: 0:0[0-9]   X$`).MatchString(line) || col != len(prompt) {
		t.Fatalf("shrinking clock left old digits or moved input: %q col %d", line, col)
	}
}

func TestRemoteClockSkipsWrappedInput(t *testing.T) {
	term := &scripted{}
	s := Session{Terminal: term, Deadline: time.Now().Add(time.Minute)}
	if err := s.refreshClassicClock(4, 22, 80-6-4-25); err != nil {
		t.Fatal(err)
	}
	if term.output.Len() != 0 {
		t.Fatalf("clock redrawn after input reached the margin: %q", term.output.String())
	}
}

func TestLocalClockAlsoUpdatesStatusRow(t *testing.T) {
	term := &scripted{}
	s := Session{Terminal: term, Local: true, Deadline: time.Now().Add(100 * time.Second)}
	if err := s.refreshClassicClock(4, 22, 0); err != nil {
		t.Fatal(err)
	}
	text := term.output.String()
	status := regexp.MustCompile("^\x1b7\x1b\\[25;70H\x1b\\[0;96;44m(.{10})\x1b8")
	m := status.FindStringSubmatch(text)
	if m == nil {
		t.Fatalf("local status row not updated: %q", text)
	}
	line, col := promptLine(t, "Time: 1:40  Main Command (?=Help)? "+text[len(m[0]):])
	if col != 35 || !strings.HasPrefix(line, "Time: "+strings.TrimSpace(m[1])) {
		t.Fatalf("local prompt clock disagrees with status row: %q col %d", line, col)
	}
}
