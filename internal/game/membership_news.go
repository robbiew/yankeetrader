package game

import "time"

// JoinWithNews records registration only when a new identity is allocated.
// Authenticated login/replacement remains the caller's transaction; reconnects
// and replacement ships never create a second registration event.
func (w *World) JoinWithNews(identity, alias string, now time.Time) (*Player, error) {
	for _, p := range w.Players {
		if p.Identity == identity {
			return w.Join(identity, alias)
		}
	}
	if err := w.prepareNews(now); err != nil {
		return nil, err
	}
	p, err := w.Join(identity, alias)
	if err != nil {
		return nil, err
	}
	w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsRegistration, Alias: p.Alias})
	p.LastActivity = day(now)
	return p, nil
}

// JoinTeamWithNews publishes only a successful new membership. The event
// snapshots the public alias and team number, never the invitation or team hash.
func (w *World) JoinTeamWithNews(id, teamID int, password string, now time.Time) error {
	if err := w.prepareNews(now); err != nil {
		return err
	}
	if err := w.JoinTeam(id, teamID, password); err != nil {
		return err
	}
	w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsTeamJoined, Alias: w.Players[id].Alias, Team: teamID})
	return nil
}
