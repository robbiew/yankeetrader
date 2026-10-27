package game

import (
	"encoding/json"
	"errors"
	"math"
	"testing"
	"time"
)

func TestDeathAttributionAndReplacementBudget(t *testing.T) {
	for _, cause := range []string{"combat", "retaliation", "hazard", "self"} {
		t.Run(cause, func(t *testing.T) {
			w, p := setup(t)
			killer, _ := w.Join("killer", "Killer")
			killer.Sector = 2
			p.Sector, p.Turns, p.Credits, p.Mines = 2, 37, 12345, 5
			p.Cargo = [3]int64{2, 3, 4}
			p.Ground = 42
			w.Ports[2].Owner, w.Ports[2].Treasury = p.ID, 777
			if err := w.CreateTeam(p.ID, "Orion", "ABCD"); err != nil {
				t.Fatal(err)
			}
			member, _ := w.Join("member", "Member")
			if err := w.JoinTeam(member.ID, 1, "ABCD"); err != nil {
				t.Fatal(err)
			}
			actor := killer.ID
			if cause == "self" {
				actor = p.ID
			}
			if cause == "hazard" {
				actor = 0
			}
			ctx := DeathContext{Victim: p.ID, Generation: p.ShipGeneration, Sector: 2, Killer: actor, Cause: cause}
			if err := w.RecordDeath(ctx, clock); err != nil {
				t.Fatal(err)
			}
			if p.Death.Cause != cause || p.Death.Killer != actor || p.Sector != 0 || p.ShipGeneration != 1 || p.Credits != 12345 || p.Mines != 5 || p.Turns != 37 || w.Teams[1].Captain != 0 {
				t.Fatal("death state lost attribution/assets", p)
			}
			if err := w.Validate(); err != nil {
				t.Fatal(err)
			}
			before, _ := json.Marshal(w)
			for _, action := range []func() error{
				func() error { return w.RecordDeath(ctx, clock) }, func() error { return w.Move(p.ID, 3) }, func() error { return w.Dock(p.ID, clock) },
				func() error { _, e := w.CollectPortTreasury(p.ID); return e }, func() error { return w.CreatePlanet(p.ID, "Ghost", clock) },
				func() error { return w.ChangeTeamPassword(p.ID, 1, "WXYZ") },
			} {
				if action() == nil {
					t.Fatal("dead ship acted")
				}
				after, _ := json.Marshal(w)
				if string(before) != string(after) {
					t.Fatal("rejected dead action changed world")
				}
			}
			now := clock
			if cause == "self" {
				if w.ReplaceShip(p.ID, now) == nil {
					t.Fatal("self-death cooldown missing")
				}
				now = clock.Add(24 * time.Hour)
				w.Maintain(now)
			}
			if err := w.ReplaceShip(p.ID, now); err != nil {
				t.Fatal(err)
			}
			wantTurns := int64(37)
			if cause == "self" {
				wantTurns = 500
			}
			if p.Death != nil || p.Sector != 1 || p.ShipGeneration != 2 || p.Credits != 1005 || p.Holds != 10 || p.Fighters != 25 || p.Shields != 100 || p.Missiles != 1 || p.Mines != 0 || p.Plasma != 0 || p.Ground != 0 || p.Cargo != [3]int64{} || p.Turns != wantTurns {
				t.Fatal("incorrect replacement", p)
			}
			treasury := int64(777)
			if cause == "self" {
				treasury = 700
			} // ordinary daily tax, unrelated to replacement
			if w.Ports[2].Owner != p.ID || w.Ports[2].Treasury != treasury || p.Team != 1 {
				t.Fatal("replacement retitled account assets")
			}
			if w.CheckShip(p.ID, 0) == nil || w.CheckShip(p.ID, 1) == nil {
				t.Fatal("old generation accepted after replacement")
			}
			if err := w.CheckShip(p.ID, 2); err != nil {
				t.Fatal(err)
			}
			if w.ReplaceShip(p.ID, now) == nil {
				t.Fatal("replacement replay accepted")
			}
			if err := w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestDeathTargetRevalidationAndNoPartialTransition(t *testing.T) {
	for _, mode := range []string{"moved", "generation", "cause", "killer", "self", "clock", "overflow", "team", "attacker-moved"} {
		t.Run(mode, func(t *testing.T) {
			w, p := setup(t)
			other, _ := w.Join("other", "Other")
			p.Sector = 2
			other.Sector = 2
			ctx := DeathContext{Victim: p.ID, Sector: 2, Killer: other.ID, Cause: "combat"}
			now := clock
			switch mode {
			case "team":
				_ = w.CreateTeam(p.ID, "Orion", "ABCD")
				_ = w.JoinTeam(other.ID, 1, "ABCD")
			case "attacker-moved":
				other.Sector = 3
			case "moved":
				p.Sector = 3
			case "generation":
				p.ShipGeneration = 2
			case "cause":
				ctx.Cause = "unknown"
			case "killer":
				ctx.Killer = 99
			case "self":
				ctx.Killer = p.ID
			case "clock":
				now = clock.Add(-time.Second)
			case "overflow":
				p.ShipGeneration = math.MaxUint64 - 1
				ctx.Generation = p.ShipGeneration
			}
			before, _ := json.Marshal(w)
			if w.RecordDeath(ctx, now) == nil {
				t.Fatal("invalid death accepted")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("failed death mutated state")
			}
		})
	}
}

func TestDeathClearsAgreementsAndScannerHidesDestroyedShip(t *testing.T) {
	w, p := setup(t)
	other, _ := w.Join("other", "Other")
	other.Sector = 2
	p.Sector = 2
	if err := w.Dock(other.ID, clock); err != nil {
		t.Fatal(err)
	}
	token := other.DockToken
	if err := w.RecordDeath(DeathContext{Victim: other.ID, Sector: 2, Killer: p.ID, Cause: "retaliation"}, clock); err != nil {
		t.Fatal(err)
	}
	if other.DockToken != "" || !other.DockUntil.IsZero() {
		t.Fatal("dead dock session retained")
	}
	if !errors.Is(w.Trade(other.ID, token, true, 0, 1, clock), ErrShipDestroyed) {
		t.Fatal("dead trade accepted")
	}
	reports, err := w.Scan(p.ID)
	if err != nil {
		t.Fatal(err)
	}
	for _, r := range reports {
		for _, ship := range r.Ships {
			if ship.ID == other.ID {
				t.Fatal("destroyed ship remains on scanner")
			}
		}
	}
	// Corruption must be rejected, without dereferencing nonexistent sector zero.
	other.DockToken = token
	if w.Validate() == nil {
		t.Fatal("dead docking token accepted")
	}
}
