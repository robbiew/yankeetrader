package door

import (
	"regexp"
	"strings"
	"testing"
	"time"
)

func TestClockRefreshRestoresCursorAndPadsShrinkingTime(t *testing.T) {
	term := &scripted{}
	s := Session{Terminal: term, Deadline: time.Now().Add(100 * time.Second)}
	if err := s.refreshClassicClock(6); err != nil {
		t.Fatal(err)
	}
	pattern := regexp.MustCompile("^\x1b7\x1b\\[25;70H\x1b\\[0;96;44m(.{10})\x1b\\[24;7H\x1b\\[0;32m(.{6})\x1b8$")
	fields := pattern.FindStringSubmatch(term.output.String())
	if fields == nil {
		t.Fatalf("refresh did not bracket updates with VT100 save/restore: %q", term.output.String())
	}
	if strings.TrimSpace(fields[1]) != strings.TrimSpace(fields[2]) || !strings.HasSuffix(fields[2], "  ") {
		t.Fatalf("clock fields disagree or retain old digits: %q", fields)
	}
}
