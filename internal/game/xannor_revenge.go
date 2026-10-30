package game

// One committed HQ victory replaces the previous pending target. Binding to
// this incarnation prevents death/replacement from reviving an old vendetta.
type XannorRevengeTarget struct {
	Player     int
	Generation uint64
}

// Called only after a player destroys the entire deployed hostile garrison.
// Sector identity alone cannot turn a Mercenary/human defeat into Xannor revenge.
func (w *World) queueXannorRevenge(player, sector, priorOwner int) {
	if w.Xannor == nil || w.Xannor.HQ != sector || sector <= 7 || priorOwner != XannorOwner {
		return
	}
	p := w.Players[player]
	if p == nil || p.Death != nil {
		return
	}
	w.Xannor.Revenge = &XannorRevengeTarget{Player: p.ID, Generation: p.ShipGeneration}
}

func (w *World) HasXannorRevenge(player int) bool {
	if w.Xannor == nil || w.Xannor.Revenge == nil {
		return false
	}
	target := w.Xannor.Revenge
	p := w.Players[player]
	return target.Player == player && p != nil && p.Death == nil && p.ShipGeneration == target.Generation
}

// Consume even when no mobile force/route is available, or the target is in the
// protected Union. The daily marker makes this a once-only attempt, not a retry
// on each login. Current state replaces the legacy live/cache discrepancy.
func (w *World) consumeXannorRevenge() (bool, int) {
	target := w.Xannor.Revenge
	if target == nil {
		return false, 0
	}
	valid := w.HasXannorRevenge(target.Player)
	w.Xannor.Revenge = nil
	p := w.Players[target.Player]
	if !valid || p.Sector <= 7 || w.Sectors[p.Sector] == nil {
		return false, 0
	}
	return true, p.Sector
}
