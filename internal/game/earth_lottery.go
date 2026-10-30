package game

import (
	"errors"
	"math"
	"time"
)

const LotteryPrice int64 = 5
const DefaultLotteryLimit = 5

// LotteryLimit is optional in a save: omission uses five, explicit zero disables.
func (w *World) LotteryLimit() int {
	if w.LotteryDailyLimit == nil {
		return DefaultLotteryLimit
	}
	return *w.LotteryDailyLimit
}
func LotteryPrize(matches int) int64 {
	switch matches {
	case 1:
		return 100
	case 2:
		return 1000
	case 3:
		return 10000
	case 4:
		return 100000
	case 5:
		return 1000000
	case 6:
		return 100000000
	}
	return 0
}
func ValidLotteryTicket(ticket string) bool {
	if len(ticket) != 6 {
		return false
	}
	for i := range ticket {
		if ticket[i] < '0' || ticket[i] > '9' {
			return false
		}
	}
	return true
}
func lotteryMatches(ticket, draw string) int {
	var available [10]int
	for i := range draw {
		available[draw[i]-'0']++
	}
	matches := 0
	for i := range ticket {
		digit := ticket[i] - '0'
		if available[digit] > 0 {
			matches++
			available[digit]--
		}
	}
	return matches
}
func (w *World) validateLottery() error {
	if w.LotteryLimit() < 0 || w.LotteryLimit() > 9 {
		return errors.New("invalid paid lottery daily limit")
	}
	for _, p := range w.Players {
		if p == nil {
			continue
		} // Identity validation reports nil players.
		if p.LotteryDay == "" {
			if p.LotteryPlays != 0 || p.LotterySequence != 0 {
				return errors.New("lottery count has no date")
			}
			continue
		}
		d, err := time.Parse("2006-01-02", p.LotteryDay)
		if err != nil || day(d) != p.LotteryDay || p.LotteryDay < day(w.Created) || p.LotteryPlays < 1 || p.LotteryPlays > 9 || p.LotterySequence < uint64(p.LotteryPlays) {
			return errors.New("invalid paid lottery history")
		}
	}
	return nil
}

// LotteryRemaining is a read-only UTC projection. Only a saved ticket resets the
// date/count, so reconnects, ship replacement and clock rollback grant no plays.
func (w *World) LotteryRemaining(id int, now time.Time) (int, error) {
	p, err := w.player(id)
	if err != nil {
		return 0, err
	}
	if err = w.newsTime(now); err != nil {
		return 0, err
	}
	if w.LotteryLimit() < 0 || w.LotteryLimit() > 9 || day(now) < p.LotteryDay {
		return 0, errors.New("invalid lottery date or limit")
	}
	used := 0
	if p.LotteryDay == day(now) {
		used = p.LotteryPlays
	}
	return max(0, w.LotteryLimit()-used), nil
}

type LotteryIntent struct {
	Ship                            TravelShip
	DockUntil                       time.Time
	Maintenance, Day, Ticket, Nonce string
	Sequence                        uint64
	Used, Limit                     int
}
type LotteryReceipt struct {
	Ticket, Draw                       string
	Matches, Remaining                 int
	Fee, Gross, Award, Capped, Balance int64
}

func (w *World) PrepareLottery(id int, token, ticket string, now time.Time) (LotteryIntent, error) {
	if !ValidLotteryTicket(ticket) {
		return LotteryIntent{}, errors.New("enter exactly six digits (including leading zeroes)")
	}
	p, port, err := w.docked(id, token, now)
	if err != nil {
		return LotteryIntent{}, err
	}
	if port.ID != 1 || !p.RetiredAt.IsZero() {
		return LotteryIntent{}, errors.New("paid lottery tickets are sold at Earth")
	}
	left, err := w.LotteryRemaining(id, now)
	if err != nil {
		return LotteryIntent{}, err
	}
	if left == 0 {
		return LotteryIntent{}, errors.New("no paid lottery plays remaining for this UTC date")
	}
	if p.Credits < LotteryPrice {
		return LotteryIntent{}, errors.New("not enough credits for a lottery ticket")
	}
	if p.LotterySequence == math.MaxUint64 {
		return LotteryIntent{}, errors.New("paid lottery sequence exhausted")
	}
	used := 0
	if p.LotteryDay == day(now) {
		used = p.LotteryPlays
	}
	return LotteryIntent{Ship: w.travelShip(p), DockUntil: p.DockUntil, Maintenance: w.LastMaintenance, Day: day(now), Ticket: ticket, Sequence: p.LotterySequence, Used: used, Limit: w.LotteryLimit()}, nil
}

// CommitLottery draws exactly six digits and validates every fallible input before
// mutating resources. Store saves fee, actual award, quota, replay sequence and
// optional public news together. It deliberately avoids original MBF arithmetic.
func (w *World) CommitLottery(entry LotteryIntent, draw func() (int, error), now time.Time) (LotteryReceipt, error) {
	fresh, err := w.PrepareLottery(entry.Ship.Player, entry.Ship.DockToken, entry.Ticket, now)
	if err != nil {
		return LotteryReceipt{}, err
	}
	fresh.Nonce = entry.Nonce
	if fresh != entry {
		return LotteryReceipt{}, errors.New("lottery quote, date or ship changed; confirm again")
	}
	if draw == nil {
		return LotteryReceipt{}, errors.New("missing lottery random source")
	}
	var digits [6]byte
	for i := range digits {
		digit, e := draw()
		if e != nil {
			return LotteryReceipt{}, e
		}
		if digit < 0 || digit > 9 {
			return LotteryReceipt{}, errors.New("invalid lottery random digit")
		}
		digits[i] = byte('0' + digit)
	}
	matches := lotteryMatches(entry.Ticket, string(digits[:]))
	if matches >= 4 {
		if err = w.prepareNews(now); err != nil {
			return LotteryReceipt{}, err
		}
	}
	p := w.Players[entry.Ship.Player]
	balance := p.Credits - LotteryPrice
	gross := LotteryPrize(matches)
	award := min(gross, MaxMoney-balance)
	p.Credits = balance + award
	p.LotteryDay, p.LotteryPlays = entry.Day, entry.Used+1
	p.LotterySequence++
	if matches >= 4 {
		w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsLottery, Alias: p.Alias, LotteryMatches: matches, LotteryPrize: award})
	}
	return LotteryReceipt{Ticket: entry.Ticket, Draw: string(digits[:]), Matches: matches, Remaining: entry.Limit - p.LotteryPlays, Fee: LotteryPrice, Gross: gross, Award: award, Capped: gross - award, Balance: p.Credits}, nil
}
