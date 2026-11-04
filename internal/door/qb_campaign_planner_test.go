package door

import (
	"github.com/robbiew/yankeetrader/internal/game"
	"testing"
	"time"
)

func TestQBCampaignBoundaryChoosesWeakNonHQWithoutMines(t *testing.T) {
	w, err := game.New(time.Date(2032, 6, 13, 12, 0, 0, 0, time.UTC), 36, 8)
	if err != nil {
		t.Fatal(err)
	}
	w.Xannor = &game.XannorState{HQ: 7}
	w.Sectors[1].Warps = []int{2, 3, 7}
	w.Sectors[2].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 100}
	w.Sectors[3].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 2}
	w.Sectors[7].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 1}
	if from, to := qbBoundary(w, 1); from != 1 || to != 3 {
		t.Fatal("wrong frontier", from, to)
	}
	w.Sectors[3].Minefield = []game.MineLayer{{Owner: 1, Count: 1}}
	if from, to := qbBoundary(w, 1); from != 1 || to != 2 {
		t.Fatal("mined/HQ frontier chosen", from, to)
	}
	w.Sectors[2].Minefield = []game.MineLayer{{Owner: 1, Count: 1}}
	if from, to := qbBoundary(w, 1); from != 0 || to != 0 {
		t.Fatal("unsafe fallback", from, to)
	}
}
