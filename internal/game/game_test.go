package game

import (
	"encoding/json"
	"os"
	"testing"
	"time"
)

var clock = time.Date(2026, 10, 24, 0, 0, 0, 0, time.UTC)

func setup(t *testing.T) (*World, *Player) {
	t.Helper()
	w, e := New(clock, 36, 8)
	if e != nil {
		t.Fatal(e)
	}
	p, e := w.Join("local:q", "Q")
	if e != nil {
		t.Fatal(e)
	}
	return w, p
}
func TestDOSCargoExamples(t *testing.T) {
	var cases []struct {
		Name, Source, Owner string
		CreditsBefore       int64 `json:"credits_before"`
		CargoBefore         int64 `json:"cargo_before"`
		Supply, Coefficient float64
		CreditsAfter        int64 `json:"credits_after"`
		CargoAfter          int64 `json:"cargo_after"`
		TreasuryAfter       int64 `json:"treasury_after"`
	}
	b, e := os.ReadFile("testdata/dos-trading.json")
	if e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(b, &cases); e != nil {
		t.Fatal(e)
	}
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			w, p := setup(t)
			p.Sector = 2
			p.Credits = c.CreditsBefore
			p.Cargo[0] = c.CargoBefore
			p.Holds = 1000
			port := w.Ports[2]
			port.Supply[0] = c.Supply
			port.Coefficient[0] = c.Coefficient
			if c.Owner == "self" {
				port.Owner = p.ID
			}
			if c.Owner == "other" {
				other, _ := w.Join("local:other", "Other")
				port.Owner = other.ID
			}
			if e = w.Dock(p.ID, clock); e != nil {
				t.Fatal(e)
			}
			if e = w.Trade(p.ID, p.DockToken, c.Coefficient > 0, 0, 10, clock); e != nil {
				t.Fatal(e)
			}
			if p.Credits != c.CreditsAfter || p.Cargo[0] != c.CargoAfter || port.Treasury != c.TreasuryAfter {
				t.Fatalf("DOS mismatch from %s: cash=%d cargo=%d treasury=%d", c.Source, p.Credits, p.Cargo[0], port.Treasury)
			}
			if p.Turns != 499 || port.Supply[0] != c.Supply-10 {
				t.Fatal("turn/supply accounting")
			}
			if e = w.Validate(); e != nil {
				t.Fatal(e)
			}
		})
	}
}
func TestEquipmentMoneyIsExactAndEarthIsSink(t *testing.T) {
	w, p := setup(t)
	p.Credits = 100000000
	if e := w.Dock(p.ID, clock); e != nil {
		t.Fatal(e)
	}
	if e := w.Equip(p.ID, p.DockToken, "fighters", 1, clock); e != nil {
		t.Fatal(e)
	}
	if p.Credits != 99999900 || p.Fighters != 26 || w.Ports[1].Treasury != 0 {
		t.Fatal("equipment accounting")
	}
	w.Ports[1].Owner = p.ID
	if w.Validate() == nil {
		t.Fatal("owned Earth accepted")
	}
}
func TestInvalidActionsLeaveAssetsUnchanged(t *testing.T) {
	for _, q := range []int64{-1, 0, 11, MaxQuantity + 1, 9223372036854775807} {
		t.Run(time.Duration(q).String(), func(t *testing.T) {
			w, p := setup(t)
			p.Sector = 2
			_ = w.Dock(p.ID, clock)
			before, _ := json.Marshal(w)
			if w.Trade(p.ID, p.DockToken, true, 0, q, clock) == nil {
				t.Fatal("invalid trade accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("rejected trade mutated state")
			}
		})
	}
	w, p := setup(t)
	_ = w.Dock(p.ID, clock)
	before := p.Credits
	if w.Equip(p.ID, p.DockToken, "holds", 1000, clock) == nil || p.Credits != before {
		t.Fatal("holds limit")
	}
	if w.Move(p.ID, 999) == nil || p.Turns != 499 {
		t.Fatal("invalid move")
	}
}
func TestDockTokensInvalidateStaleSessions(t *testing.T) {
	w, p := setup(t)
	p.Sector = 2
	_ = w.Dock(p.ID, clock)
	old := p.DockToken
	_ = w.Dock(p.ID, clock)
	if w.Trade(p.ID, old, true, 0, 1, clock) == nil {
		t.Fatal("old quote accepted")
	}
	fresh := p.DockToken
	if w.Trade(p.ID, fresh, true, 0, 1, clock.Add(5*time.Minute)) == nil {
		t.Fatal("expired quote accepted")
	}
	_ = w.Move(p.ID, 3)
	if w.Trade(p.ID, fresh, true, 0, 1, clock) == nil {
		t.Fatal("quote survives movement")
	}
}
func TestMaintenanceIdempotentAndClockRollback(t *testing.T) {
	w, p := setup(t)
	p.Turns = 1
	w.Ports[2].Treasury = 1005
	next := clock.Add(24 * time.Hour)
	if !w.Maintain(next) || p.Turns != 500 || w.Ports[2].Treasury != 905 {
		t.Fatal("daily phases")
	}
	b, _ := json.Marshal(w)
	if w.Maintain(next) || w.Maintain(clock) {
		t.Fatal("repeated maintenance")
	}
	a, _ := json.Marshal(w)
	if string(a) != string(b) {
		t.Fatal("repeat/rollback changed economy")
	}
	port := w.Ports[2]
	stock, stamp := port.Supply, port.Updated
	update(port, clock)
	if port.Supply != stock || port.Updated != stamp {
		t.Fatal("rollback production")
	}
}
func TestUniverseAndStableIdentity(t *testing.T) {
	w, p := setup(t)
	same, e := w.Join("local:q", "Renamed")
	if e != nil || same.ID != p.ID || len(w.Players) != 1 {
		t.Fatal("identity tied to alias")
	}
	visited := map[int]bool{1: true}
	queue := []int{1}
	for len(queue) > 0 {
		n := queue[0]
		queue = queue[1:]
		for _, to := range w.Sectors[n].Warps {
			if !visited[to] {
				visited[to] = true
				queue = append(queue, to)
			}
		}
	}
	if len(visited) != len(w.Sectors) {
		t.Fatal("unreachable sector")
	}
}

func TestMalformedWorldRejectedBeforeActions(t *testing.T) {
	cases := []func(*World){func(w *World) { w.Players = nil }, func(w *World) { w.Sectors[1] = nil }, func(w *World) { w.Ports[1] = nil }, func(w *World) { w.Ports[2].Production[0] = 0 }, func(w *World) { w.Ports[2].Supply[0] = 1e12 }, func(w *World) { w.Players[1].Credits = -1 }, func(w *World) { w.NextPlayer = 0 }}
	for i, corrupt := range cases {
		w, _ := setup(t)
		corrupt(w)
		if w.Validate() == nil {
			t.Fatalf("corruption %d accepted", i)
		}
	}
}
