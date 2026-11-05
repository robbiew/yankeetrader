package door

import (
	gd "github.com/robbiew/godoors"
	"strings"
	"testing"
	"time"
)

func TestDoorInputDeadlineReportsExpiryAndRejectsLateInput(t *testing.T) {
	for _, mode := range []string{"timeout", "late-enter", "secret", "idle-clock"} {
		t.Run(mode, func(t *testing.T) {
			deadline := time.Now().Add(50 * time.Millisecond)
			ticks := 0
			typed := []rune("COLLECT/")
			index := 0
			g := &GoDoors{commandMode: true, savedLine: "PREVIOUS", readKey: func(time.Duration) (rune, gd.Key, error) {
				if mode == "late-enter" && index < len(typed) {
					r := typed[index]
					index++
					return r, gd.KeyNone, nil
				}
				time.Sleep(time.Until(deadline) + time.Millisecond)
				if mode == "late-enter" {
					return 13, gd.KeyEnter, nil
				}
				return 0, gd.KeyNone, gd.ErrInputTimeout
			}}
			if mode == "idle-clock" {
				g.onIdle = func(int) error { ticks++; return nil }
			}
			var line string
			var err error
			if mode == "secret" {
				line, err = g.ReadSecret(deadline)
			} else {
				line, err = g.ReadLine(deadline)
			}
			if err == nil || !strings.Contains(err.Error(), "session time expired") || line != "" || g.savedLine != "PREVIOUS" || ticks != 0 {
				t.Fatal(line, err, g.savedLine, ticks)
			}
		})
	}
}
