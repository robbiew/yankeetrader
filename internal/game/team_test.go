package game

import (
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"strings"
	"testing"
)

func TestDOSTeamGoldenActions(t *testing.T) {
	type snapshot struct {
		Members        map[int]int
		Captain        int
		Roster         []int
		Name           string
		Credits, Turns int64
	}
	var cases []struct {
		Name          string
		Actor         int
		Before, After snapshot
	}
	b, err := os.ReadFile("testdata/dos-teams.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(b, &cases); err != nil {
		t.Fatal(err)
	}
	hash, _ := hashTeamPassword("ABCD")
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			w, _ := New(clock, 36, 8)
			// Preserve the DOS player numbers without importing unrelated DOS inventories.
			for i := 1; i <= 6; i++ {
				p, e := w.Join(fmt.Sprint(i), fmt.Sprint("Pilot", i))
				if e != nil {
					t.Fatal(e)
				}
				p.Team = c.Before.Members[i]
			}
			p := w.Players[c.Actor]
			p.Credits, p.Turns = c.Before.Credits, c.Before.Turns
			if len(w.teamMembers(1)) > 0 {
				captain := c.Before.Captain
				if w.Players[captain] == nil || w.Players[captain].Team != 1 {
					captain = 0
				}
				w.Teams[1] = &Team{ID: 1, Name: c.Before.Name, Captain: captain, PasswordHash: hash}
			}
			switch c.Name {
			case "team-create-confirm":
				err = w.CreateTeam(c.Actor, "Orion", "ABCD")
			case "team-short-name":
				err = w.CreateTeam(c.Actor, "AB", "ABCD")
			case "team-join", "team-rejoin":
				err = w.JoinTeam(c.Actor, 1, "ABCD")
			case "team-lowercase":
				err = w.JoinTeam(c.Actor, 1, "abcd")
			case "team-wrong":
				err = w.JoinTeam(c.Actor, 1, "WXYZ")
			case "team-full":
				err = w.JoinTeam(c.Actor, 1, "ABCD")
			case "team-quit", "team-last":
				err = w.LeaveTeam(c.Actor, 1)
			case "team-banish":
				err = w.BanishTeamMember(c.Actor, 1, 3)
			case "team-member-privilege":
				err = w.ChangeTeamPassword(c.Actor, 1, "WXYZ")
			case "team-password":
				err = w.ChangeTeamPassword(c.Actor, 1, "WXYZ")
			case "team-successor", "team-promote":
				_, err = w.VisitTeam(c.Actor)
			default:
				t.Fatal("unhandled golden case")
			}
			rejected := c.Name == "team-wrong" || c.Name == "team-full" || c.Name == "team-short-name" || c.Name == "team-member-privilege"
			if (err != nil) != rejected {
				t.Fatalf("error=%v rejected=%v", err, rejected)
			}
			for id, want := range c.After.Members {
				if w.Players[id].Team != want {
					t.Fatalf("player %d membership %d != DOS %d", id, w.Players[id].Team, want)
				}
			}
			captain := 0
			if w.Teams[1] != nil {
				captain = w.Teams[1].Captain
				if w.Teams[1].Name != c.After.Name {
					t.Fatal("DOS team name mismatch", w.Teams[1].Name, c.After.Name)
				}
			}
			// DOS keeps a stale departed captain until the next visit. Go stores vacancy.
			want := c.After.Captain
			if w.Players[want] == nil || w.Players[want].Team != 1 {
				want = 0
			}
			if captain != want || p.Credits != c.After.Credits || p.Turns != c.After.Turns {
				t.Fatal("DOS captain/cost mismatch", captain, want, p)
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestTeamPasswordsRolesAndRejoin(t *testing.T) {
	w, p := setup(t)
	other, _ := w.Join("other", "Other")
	if err := w.CreateTeam(p.ID, "  ORION   traders  ", "aBcD"); err != nil {
		t.Fatal(err)
	}
	if w.Teams[1].Name != "Orion Traders" {
		t.Fatal(w.Teams[1].Name)
	}
	b, _ := json.Marshal(w)
	if strings.Contains(strings.ToUpper(string(b)), "ABCD") {
		t.Fatal("invitation saved as plaintext")
	}
	if err := w.JoinTeam(other.ID, 1, "abcd"); err != nil {
		t.Fatal(err)
	}
	for _, action := range []func() error{
		func() error { return w.CreateTeam(other.ID, "Another", "WXYZ") },
		func() error { return w.RenameTeam(other.ID, 1, "Hijacked") },
		func() error { return w.ChangeTeamPassword(other.ID, 1, "WXYZ") },
		func() error { return w.BanishTeamMember(other.ID, 1, p.ID) },
		func() error { return w.BanishTeamMember(p.ID, 1, p.ID) },
	} {
		before, _ := json.Marshal(w)
		if action() == nil {
			t.Fatal("unauthorized team action accepted")
		}
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("rejected action changed world")
		}
	}
	if err := w.BanishTeamMember(p.ID, 1, other.ID); err != nil {
		t.Fatal(err)
	}
	if err := w.JoinTeam(other.ID, 1, "ABCD"); err != nil {
		t.Fatal("removal was made into a permanent ban", err)
	}
	if err := w.BanishTeamMember(p.ID, 1, other.ID); err != nil {
		t.Fatal(err)
	}
	if err := w.ChangeTeamPassword(p.ID, 1, "WXYZ"); err != nil {
		t.Fatal(err)
	}
	if w.JoinTeam(other.ID, 1, "ABCD") == nil {
		t.Fatal("old invitation survived rotation")
	}
	if err := w.JoinTeam(other.ID, 1, "wxyz"); err != nil {
		t.Fatal(err)
	}
	if err := w.LeaveTeam(p.ID, 1); err != nil {
		t.Fatal(err)
	}
	if w.Teams[1].Captain != 0 {
		t.Fatal("premature captain election")
	}
	if _, err := w.VisitTeam(other.ID); err != nil || w.Teams[1].Captain != other.ID {
		t.Fatal("visiting member did not succeed", err)
	}
	if w.RenameTeam(p.ID, 1, "Hijacked") == nil {
		t.Fatal("departed captain retained role")
	}
	if err := w.LeaveTeam(other.ID, 1); err != nil {
		t.Fatal(err)
	}
	if len(w.Teams) != 0 {
		t.Fatal("empty team retained")
	}
	if err := w.CreateTeam(other.ID, "Reused", "EFGH"); err != nil || other.Team != 1 {
		t.Fatal("free slot not reusable", err)
	}
}

func TestTeamRemovalRevokesActivePlanetAccessAndKeepsAssets(t *testing.T) {
	for _, removeOwner := range []bool{false, true} {
		t.Run(fmt.Sprint(removeOwner), func(t *testing.T) {
			w, p := setup(t)
			p.Credits = 100000
			other, _ := w.Join("other", "Other")
			if err := w.CreateTeam(p.ID, "Orion", "ABCD"); err != nil {
				t.Fatal(err)
			}
			if err := w.JoinTeam(other.ID, 1, "ABCD"); err != nil {
				t.Fatal(err)
			}
			if err := w.CreatePlanet(p.ID, "Home", clock); err != nil {
				t.Fatal(err)
			}
			planet := w.Planets[2]
			planet.Bank = 1000
			w.Ports[2].Owner, w.Ports[2].Treasury = p.ID, 777
			if err := w.Land(other.ID, clock); err != nil {
				t.Fatal(err)
			}
			token := other.PlanetToken
			if err := w.Bank(other.ID, token, 1000, clock); err != nil {
				t.Fatal(err)
			}
			resources, err := w.TeamPlanetResources(other.ID)
			if err != nil || len(resources) != 1 {
				t.Fatal(resources, err)
			}
			if removeOwner {
				err = w.LeaveTeam(p.ID, 1)
			} else {
				err = w.BanishTeamMember(p.ID, 1, other.ID)
			}
			if err != nil {
				t.Fatal(err)
			}
			if other.PlanetToken != "" || other.LandedPlanet != 0 {
				t.Fatal("active landing not revoked")
			}
			if w.Bank(other.ID, token, 0, clock) == nil || w.RenamePlanet(other.ID, token, "Stolen", clock) == nil {
				t.Fatal("former teammate retained access")
			}
			if planet.Bank != 1000 || planet.Owner != p.ID || w.Ports[2].Owner != p.ID || w.Ports[2].Treasury != 777 {
				t.Fatal("removal confiscated personal assets")
			}
			if amount, err := w.CollectPortTreasury(p.ID); err != nil || amount != 777 {
				t.Fatal("owner could not collect after departure", err)
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestTeamValidationAndPasswordFailures(t *testing.T) {
	for _, password := range []string{"", "abc", "abcde", "ab\x1bc"} {
		w, p := setup(t)
		before, _ := json.Marshal(w)
		if w.CreateTeam(p.ID, "Orion", password) == nil {
			t.Fatal("invalid password accepted")
		}
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("failed creation mutated world")
		}
	}
	w, p := setup(t)
	p.Team = 1
	if w.Validate() == nil {
		t.Fatal("missing team accepted")
	}
	p.Team = 0
	if err := w.CreateTeam(p.ID, "Orion", "ABCD"); err != nil {
		t.Fatal(err)
	}
	for _, mode := range []string{"captain", "password", "empty", "capacity"} {
		t.Run(mode, func(t *testing.T) {
			b, _ := json.Marshal(w)
			var v World
			_ = json.Unmarshal(b, &v)
			switch mode {
			case "captain":
				v.Teams[1].Captain = 50
			case "password":
				v.Teams[1].PasswordHash = "plaintext"
			case "empty":
				v.Players[p.ID].Team = 0
			case "capacity":
				for i := 0; i < 4; i++ {
					other, _ := v.Join(fmt.Sprint(i), fmt.Sprint("Other", i))
					other.Team = 1
				}
			}
			if v.Validate() == nil {
				t.Fatal("invalid team state accepted")
			}
		})
	}
}

func TestCaptainCanRemoveDestroyedMemberAndReuseRosterSlot(t *testing.T) {
	w, captain := setup(t)
	if err := w.CreateTeam(captain.ID, "Orion", "ABCD"); err != nil {
		t.Fatal(err)
	}
	var members []*Player
	for i := 0; i < 3; i++ {
		member, err := w.Join(fmt.Sprintf("member:%d", i), fmt.Sprintf("Member%d", i))
		if err != nil {
			t.Fatal(err)
		}
		if err = w.JoinTeam(member.ID, 1, "ABCD"); err != nil {
			t.Fatal(err)
		}
		members = append(members, member)
	}
	victim := members[0]
	w.Ports[2].Owner, w.Ports[2].Treasury = victim.ID, 777
	enemy, err := w.Join("enemy", "Enemy")
	if err != nil {
		t.Fatal(err)
	}
	applicant, err := w.Join("applicant", "Applicant")
	if err != nil {
		t.Fatal(err)
	}
	if err = w.RecordDeath(DeathContext{Victim: victim.ID, Generation: victim.ShipGeneration, Sector: victim.Sector, Killer: enemy.ID, Cause: "combat"}, clock); err != nil {
		t.Fatal(err)
	}
	// Legacy version-4 dead accounts could retain membership. Keep that
	// compatibility regression even though new deaths remove it immediately.
	victim.Team = 1
	if err = w.JoinTeam(applicant.ID, 1, "ABCD"); err == nil {
		t.Fatal("full team accepted another member")
	}
	frozen := *victim
	frozenDeath := *victim.Death
	frozen.Death = &frozenDeath
	if err = w.BanishTeamMember(members[1].ID, 1, victim.ID); err == nil {
		t.Fatal("ordinary member removed destroyed teammate")
	}
	if err = w.BanishTeamMember(captain.ID, 1, 99); err == nil {
		t.Fatal("missing target accepted")
	}
	if err = w.BanishTeamMember(captain.ID, 1, enemy.ID); err == nil {
		t.Fatal("nonmember target accepted")
	}
	if err = w.BanishTeamMember(captain.ID, 1, victim.ID); err != nil {
		t.Fatal("captain could not remove destroyed member", err)
	}
	frozen.Team = 0
	if !reflect.DeepEqual(*victim, frozen) {
		t.Fatal("removal changed frozen ship or death attribution")
	}
	if w.Ports[2].Owner != enemy.ID || w.Ports[2].Treasury != 777 {
		t.Fatal("membership removal changed the already settled estate")
	}
	if err = w.JoinTeam(applicant.ID, 1, "ABCD"); err != nil {
		t.Fatal("removed member still occupied roster slot", err)
	}
	if len(w.ListTeams()[0].Members) != 4 {
		t.Fatal("incorrect roster capacity")
	}
	if err = w.ReplaceShip(victim.ID, clock); err != nil {
		t.Fatal(err)
	}
	if victim.Team != 0 {
		t.Fatal("replacement restored removed membership")
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}
