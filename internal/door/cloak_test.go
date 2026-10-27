package door

import (
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"strings"
	"testing"
	"time"
)

func TestSensorsRespectCloakAndDisplayPersistedEnergy(t *testing.T) {
	now := time.Now()
	w, _ := game.New(now, 36, 8)
	p, _ := w.Join("observer", "Observer")
	p.Cloak = .37
	hidden, _ := w.Join("hidden", "HiddenPilot")
	hidden.Sector = 2
	hidden.Cloak = 1
	visible, _ := w.Join("visible", "VisiblePilot")
	visible.Sector = 2
	visible.Cloak = 0
	w.Sectors[1].Warps = []int{2}
	st := store.Store{Dir: t.TempDir()}
	if err := st.Create(w); err != nil {
		t.Fatal(err)
	}
	term := &scripted{lines: []string{"s;s;i;q"}}
	session := Session{Store: st, Terminal: term, Identity: "observer", Alias: "Observer", Deadline: now.Add(time.Minute)}
	if err := session.Run(); err != nil {
		t.Fatal(err)
	}
	output := term.output.String()
	if strings.Contains(output, "HiddenPilot") || strings.Count(output, "VisiblePilot") != 2 || !strings.Contains(output, "Cloak energy: 37%") {
		t.Fatal(output)
	}
	current, err := st.View()
	if err != nil || current.Players[hidden.ID].Cloak != 1 || current.Players[p.ID].Cloak != .37 {
		t.Fatal("scan changed persisted energy", err)
	}
}

func TestClassicInfoUsesCloakFieldAndKeepsScannerUnavailable(t *testing.T) {
	w, _ := game.New(time.Now(), 36, 8)
	p, _ := w.Join("observer", "Observer")
	p.Cloak = .37
	term := &scripted{}
	s := Session{Terminal: term, Deadline: time.Now().Add(time.Minute)}
	if err := s.classicInfo(w, p.ID, false); err != nil {
		t.Fatal(err)
	}
	output := term.output.String()
	if !strings.Contains(output, "Scanner.. : N/A") || !strings.Contains(output, "Cloak Energy. : 37%") {
		t.Fatal(output)
	}
}
