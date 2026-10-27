package game

import (
	"errors"
	"sort"
	"strings"

	"golang.org/x/crypto/bcrypt"
)

// Player.Team is the sole membership relation; rosters are derived, never cached.
type Team struct {
	ID           int
	Name         string
	Captain      int // Zero means the next visiting member succeeds the departed captain.
	PasswordHash string
}

type TeamSummary struct {
	ID      int
	Name    string
	Captain int
	Members []int
}

func teamPassword(password string) (string, error) {
	if len(password) != 4 || !clean(password) {
		return "", errors.New("team passwords must contain exactly four printable characters")
	}
	return strings.ToUpper(password), nil
}
func hashTeamPassword(password string) (string, error) {
	password, err := teamPassword(password)
	if err != nil {
		return "", err
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(hash), err
}
func (w *World) teamMembers(team int) []int {
	members := []int{}
	for id, p := range w.Players {
		if p.Team == team {
			members = append(members, id)
		}
	}
	sort.Ints(members)
	return members
}
func (w *World) validateTeams() error {
	if w.Teams == nil || len(w.Teams) > 50 {
		return errors.New("invalid team table")
	}
	for _, p := range w.Players {
		if p.Team != 0 && w.Teams[p.Team] == nil {
			return errors.New("player references a missing team")
		}
	}
	for id, team := range w.Teams {
		if team == nil || id < 1 || id > 50 || team.ID != id || !clean(team.Name) || len(team.Name) < 3 {
			return errors.New("invalid team")
		}
		members := w.teamMembers(id)
		if len(members) < 1 || len(members) > 4 {
			return errors.New("invalid team capacity")
		}
		if team.Captain != 0 && (w.Players[team.Captain] == nil || w.Players[team.Captain].Team != id) {
			return errors.New("captain is not a member")
		}
		cost, err := bcrypt.Cost([]byte(team.PasswordHash))
		if err != nil || cost != bcrypt.DefaultCost {
			return errors.New("invalid team password hash")
		}
	}
	return nil
}
func (w *World) ListTeams() []TeamSummary {
	teams := []TeamSummary{}
	for id, team := range w.Teams {
		teams = append(teams, TeamSummary{id, team.Name, team.Captain, w.teamMembers(id)})
	}
	sort.Slice(teams, func(i, j int) bool { return teams[i].ID < teams[j].ID })
	return teams
}

// VisitTeam performs DOS's visiting-member succession rule under the world lock.
func (w *World) VisitTeam(id int) (TeamSummary, error) {
	p, err := w.player(id)
	if err != nil {
		return TeamSummary{}, err
	}
	team := w.Teams[p.Team]
	if team == nil {
		return TeamSummary{}, errors.New("you don't belong to a team")
	}
	if team.Captain == 0 {
		team.Captain = id
	}
	return TeamSummary{team.ID, team.Name, team.Captain, w.teamMembers(team.ID)}, nil
}
func (w *World) CreateTeam(id int, name, password string) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	if p.Team != 0 {
		return errors.New("leave your current team first")
	}
	name = teamName(name)
	if !clean(name) || len(name) < 3 {
		return errors.New("use a team name of 3 to 41 printable characters")
	}
	slot := 1
	for slot <= 50 && w.Teams[slot] != nil {
		slot++
	}
	if slot > 50 {
		return errors.New("all team slots are occupied")
	}
	hash, err := hashTeamPassword(password)
	if err != nil {
		return err
	}
	w.Teams[slot] = &Team{ID: slot, Name: name, Captain: id, PasswordHash: hash}
	p.Team = slot
	return nil
}
func (w *World) JoinTeam(id, teamID int, password string) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	if p.Team != 0 {
		return errors.New("leave your current team first")
	}
	team := w.Teams[teamID]
	if team == nil {
		return errors.New("team no longer exists")
	}
	if len(w.teamMembers(teamID)) >= 4 {
		return errors.New("team is full")
	}
	password, err = teamPassword(password)
	if err != nil {
		return err
	}
	if bcrypt.CompareHashAndPassword([]byte(team.PasswordHash), []byte(password)) != nil {
		return errors.New("incorrect team password")
	}
	p.Team = teamID
	return nil
}
func (w *World) teamCaptain(id, teamID int) (*Team, error) {
	p, err := w.player(id)
	if err != nil {
		return nil, err
	}
	team := w.Teams[teamID]
	if team == nil || p.Team != teamID || team.Captain != id {
		return nil, errors.New("only the current team captain may do that")
	}
	return team, nil
}
func (w *World) revokeTeamAccess() {
	for _, p := range w.Players {
		if p.PlanetToken != "" {
			planet := w.Planets[p.LandedPlanet]
			if planet == nil || !w.allowed(p, planet) {
				p.PlanetToken = ""
				p.LandedPlanet = 0
			}
		}
	}
}
func (w *World) LeaveTeam(id, teamID int) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	team := w.Teams[teamID]
	if team == nil || p.Team != teamID {
		return errors.New("team membership changed")
	}
	p.Team = 0
	if len(w.teamMembers(teamID)) == 0 {
		delete(w.Teams, teamID)
	} else if team.Captain == id {
		team.Captain = 0
	}
	w.revokeTeamAccess()
	return nil
}

// BanishTeamMember is a removal, not a permanent ban. Rotate the password to
// prevent rejoining with the same invitation, matching DOS's explicit reminder.
func (w *World) BanishTeamMember(id, teamID, target int) error {
	if _, err := w.teamCaptain(id, teamID); err != nil {
		return err
	}
	p, err := w.player(target)
	if err != nil {
		return err
	}
	if target == id || p.Team != teamID {
		return errors.New("select another current team member")
	}
	p.Team = 0
	w.revokeTeamAccess()
	return nil
}
func (w *World) RenameTeam(id, teamID int, name string) error {
	team, err := w.teamCaptain(id, teamID)
	if err != nil {
		return err
	}
	name = teamName(name)
	if !clean(name) || len(name) < 3 {
		return errors.New("use a team name of 3 to 41 printable characters")
	}
	team.Name = name
	return nil
}
func (w *World) ChangeTeamPassword(id, teamID int, password string) error {
	team, err := w.teamCaptain(id, teamID)
	if err != nil {
		return err
	}
	hash, err := hashTeamPassword(password)
	if err != nil {
		return err
	}
	team.PasswordHash = hash
	return nil
}

// TeamPlanetResources never changes individual ownership or reveals private
// port accounts. Planet quantities are reported through the landing interface.
func (w *World) TeamPlanetResources(id int) ([]Planet, error) {
	p, err := w.player(id)
	if err != nil {
		return nil, err
	}
	if p.Team == 0 {
		return nil, errors.New("you don't belong to a team")
	}
	result := []Planet{}
	for _, planet := range w.Planets {
		owner := w.Players[planet.Owner]
		if owner != nil && owner.ID != id && owner.Team == p.Team {
			result = append(result, *planet)
		}
	}
	sort.Slice(result, func(i, j int) bool { return result[i].Sector < result[j].Sector })
	return result, nil
}

func teamName(name string) string {
	for _, r := range name {
		if r < 32 || r > 126 {
			return ""
		}
	}
	name = strings.Join(strings.Fields(name), " ")
	b := []byte(strings.ToLower(name))
	word := false
	for i, c := range b {
		letter := c >= 'a' && c <= 'z'
		if !word && letter {
			b[i] = c - 32
		}
		word = letter || c == '\''
	}
	if len(b) > 41 {
		b = b[:41]
	}
	return string(b)
}
