package game

import "time"

const XannorHQBonus int64 = 1_000_000

// XannorHQReward is a private command result, not a redeemable saved token.
// Credits is the actual bounded addition before later combat/mine aftermath.
type XannorHQReward struct {
	Player, Sector int
	Credits        int64
}

func (w *World) hqRewardEligible(player, sector int, prior SectorDefense) bool {
	p := w.Players[player]
	return w.Xannor != nil && w.Xannor.HQ == sector && sector > 7 &&
		prior.Owner == XannorOwner && prior.Fighters > 0 && p != nil && p.Death == nil && p.RetiredAt.IsZero()
}

// Only called by the two supported battle paths after clearing a live, validated
// force. No public action redeems a pointer or receipt for payment. The store
// transaction includes force removal, credits, news, revenge and later aftermath.
func (w *World) awardXannorHQ(player, sector int, prior SectorDefense, now time.Time) (*XannorHQReward, error) {
	if !w.hqRewardEligible(player, sector, prior) || w.Sectors[sector].Defense != nil {
		return nil, nil
	}
	if err := w.prepareNews(now); err != nil {
		return nil, err
	}
	p := w.Players[player]
	credited := min(XannorHQBonus, MaxMoney-p.Credits)
	p.Credits += credited
	w.queueXannorRevenge(player, sector, prior.Owner)
	w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsXannorHQ, Alias: p.Alias})
	return &XannorHQReward{Player: player, Sector: sector, Credits: credited}, nil
}
