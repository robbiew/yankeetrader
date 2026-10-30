package game

import (
	"encoding/json"
	"math/rand"
	"reflect"
	"testing"
	"time"
)

func mobileWorld(t *testing.T, count int) *World {
	t.Helper()
	w, err := New(clock, 36, count)
	if err != nil {
		t.Fatal(err)
	}
	w.Xannor = &XannorState{HQ: 8}
	for id := 8; id <= count; id++ {
		w.Sectors[id].Warps = nil
		if id < count {
			w.Sectors[id].Warps = []int{id + 1}
		}
	}
	return w
}
func mobileGroup(w *World, sector int, force int64) *SectorDefense {
	d := &SectorDefense{Owner: XannorOwner, Fighters: force}
	w.Sectors[sector].Defense = d
	return d
}
func mobileRNG(t *testing.T, values ...float64) func() float64 {
	t.Helper()
	at := 0
	return func() float64 {
		if at >= len(values) {
			t.Fatal("unexpected RNG draw")
			return 0
		}
		v := values[at]
		at++
		return v
	}
}
func validMobile(t *testing.T, w *World) {
	t.Helper()
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestXannorSplitThresholdAndReturningForceCannotReactivate(t *testing.T) {
	for _, score := range []int64{1999, 2000, 2001} {
		w := mobileWorld(t, 12)
		p, _ := w.Join("captain", "Captain")
		p.StoredScore = score
		mobileGroup(w, 8, 1)
		mobileGroup(w, 9, 100)
		draws := 0
		w.xannorActions(clock, func() float64 { draws++; return .99 })
		want := 12
		if score == 2001 {
			want = 5
		}
		if draws != want || xannorForce(w) != 101 {
			t.Fatal("wrong fractional threshold or force accounting", score, draws, xannorForce(w))
		}
		validMobile(t, w)
	}
	w := mobileWorld(t, 12)
	p, _ := w.Join("captain", "Captain")
	p.StoredScore = 4000
	mobileGroup(w, 8, 1)
	mobileGroup(w, 9, 100)
	mobileGroup(w, 10, 1)
	w.Sectors[9].Warps = []int{8}
	w.Sectors[10].Warps = []int{8}
	draws := 0
	w.xannorActions(clock, func() float64 { draws++; return .99 })
	if draws != 8 || w.Sectors[8].Defense.Fighters != 102 || w.Sectors[9].Defense != nil || w.Sectors[10].Defense != nil {
		t.Fatal("returned force funded extra splits/activations", draws)
	}
	validMobile(t, w)
}

func TestXannorSplittingConservationBoundsAndFailedPathRefund(t *testing.T) {
	w := mobileWorld(t, 12)
	p, _ := w.Join("captain", "Captain")
	p.StoredScore = 1000000
	mobileGroup(w, 8, 2000)
	draws := 0
	w.xannorActions(clock, func() float64 { draws++; return .5 })
	if xannorForce(w) != 2000 || draws > 135 || w.Sectors[11].Defense == nil || w.Sectors[11].Defense.Fighters < 1 {
		t.Fatal("split force lost, duplicated or failed to deploy", draws)
	}
	validMobile(t, w)
	w = mobileWorld(t, 12)
	mobileGroup(w, 8, 1)
	w.Sectors[8].Warps = nil
	before, _ := json.Marshal(w)
	draws = 0
	w.xannorActions(clock, func() float64 { draws++; return .99 })
	after, _ := json.Marshal(w)
	if draws != 7 || string(before) != string(after) {
		t.Fatal("failed split path lost force or reused refund", draws)
	}
	w = mobileWorld(t, 12)
	w.xannorActions(clock, func() float64 { t.Fatal("zero-force phase must not draw"); return 0 })
	if xannorForce(w) != 0 {
		t.Fatal("zero-bound helper invented force")
	}
	w.Xannor.Reserve = 100
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 10}
	w.xannorActions(clock, func() float64 { t.Fatal("undeployed contested reserve funded a split"); return 0 })
	if w.Xannor.Reserve != 100 {
		t.Fatal("reserve force changed")
	}
	validMobile(t, w)
}

func TestXannorGroupLimitAndFriendlySnapshotActivations(t *testing.T) {
	w := mobileWorld(t, 30)
	for id := 9; id <= 28; id++ {
		mobileGroup(w, id, 100)
		w.Sectors[id].Warps = nil
	}
	draws := 0
	w.xannorActions(clock, func() float64 { draws++; return .99 })
	if draws != 39 || xannorForce(w) != 2000 || w.Sectors[28].Defense.Fighters != 100 {
		t.Fatal("group limit or snapshot identity failed", draws)
	}
	for _, passing := range []bool{false, true} {
		w = mobileWorld(t, 12)
		mobileGroup(w, 9, 10)
		receiver := 12
		if passing {
			receiver = 10
		}
		mobileGroup(w, receiver, 20)
		draws = 0
		w.xannorActions(clock, func() float64 { draws++; return .99 })
		want := 3
		if passing {
			want = 5
		}
		if draws != want || w.Sectors[12].Defense == nil || w.Sectors[12].Defense.Fighters != 30 || xannorForce(w) != 30 {
			t.Fatal("receiver repeated activation or passing cancelled it", passing, draws)
		}
		validMobile(t, w)
	}
	w = mobileWorld(t, 12)
	for id := 8; id <= 12; id++ {
		mobileGroup(w, id, MaxQuantity)
	}
	before, _ := json.Marshal(w)
	draws = 0
	w.xannorActions(clock, func() float64 { draws++; return .99 })
	after, _ := json.Marshal(w)
	if draws > 135 || string(before) != string(after) {
		t.Fatal("saturated sectors lost force or retried without a bound", draws)
	}
	validMobile(t, w)
}

func TestXannorPreferredTopAndHQTargetOrdering(t *testing.T) {
	w := mobileWorld(t, 12)
	p, _ := w.Join("captain", "Captain")
	p.Sector, p.Cloak = 10, .5
	ids := []int{8, 9, 10, 11, 12}
	preferred := 11
	target := w.xannorTarget(2, 9, ids, 12, 0, 0, &preferred, false, mobileRNG(t, .99, .5, .5))
	if target != 11 || preferred != 11 {
		t.Fatal("ordinary cloak tie or shared target lost")
	}
	preferred = 0
	target = w.xannorTarget(2, 9, ids, 12, 0, 0, &preferred, false, mobileRNG(t, .99, .5, .50001))
	if target != 10 || preferred != 10 {
		t.Fatal("visible player not selected")
	}
	p.Sector = 1
	for _, strength := range []int64{1, 2} {
		w.Sectors[10].Defense = &SectorDefense{Owner: 1, Fighters: strength}
		preferred = 11
		target = w.xannorTarget(2, 9, ids, 12, 0, 0, &preferred, false, mobileRNG(t, .99, .5))
		want := 11
		if strength == 2 {
			want = 10
		}
		if target != want {
			t.Fatal("foreign preferred-defense threshold", strength, target)
		}
	}
	preferred = 11
	target = w.xannorTarget(20, 9, ids, 12, 2000, 1, &preferred, false, mobileRNG(t, .99, .5))
	if target != 12 {
		t.Fatal("group20 top override was not last normal preference")
	}
	target = w.xannorTarget(20, 9, ids, 12, 2001, 1, &preferred, false, mobileRNG(t, .99, .5))
	if target != 8 {
		t.Fatal("fractional low-HQ override did not beat top target")
	}
	for _, tc := range []struct {
		score        int64
		cloak        float64
		sector, want int
		rolls        []float64
	}{
		{2499999, 0, 10, 12, []float64{.99, .99}},
		{2500000, 0, 10, 10, []float64{0}},
		{2500000, 1, 10, 12, []float64{.66, .99}},
		{2500000, 1, 10, 10, []float64{.67}},
		{2500000, 0, 7, 12, []float64{.99, .99}},
	} {
		p.StoredScore, p.Cloak, p.Sector = tc.score, tc.cloak, tc.sector
		if got := w.xannorHuntSector(ids, p, mobileRNG(t, tc.rolls...)); got != tc.want {
			t.Fatal("wrong hunt threshold/cloak/Union gate", tc, got)
		}
	}
	other, _ := w.Join("other", "Other")
	p.StoredScore, other.StoredScore = 4000, 4000
	if w.xannorTopPlayer() != p {
		t.Fatal("score tie did not select first real player")
	}
	p.Death = &Death{}
	if w.xannorTopPlayer() != other {
		t.Fatal("dead retained alias selected as top player")
	}
}

func TestXannorMinesFIFOUniformDamageAndWorkBudget(t *testing.T) {
	w := mobileWorld(t, 12)
	p, _ := w.Join("one", "One")
	other, _ := w.Join("two", "Two")
	group := mobileGroup(w, 9, 100000)
	w.Sectors[10].Minefield = []MineLayer{{Owner: p.ID, Count: 1}, {Owner: other.ID, Count: 2}}
	preferred := 0
	draws := 0
	w.walkXannor(group, []int{9, 10, 11}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { draws++; return .5 })
	if draws != 3 || len(w.Sectors[10].Minefield) != 0 || w.Sectors[11].Defense.Fighters != 100000-3*501 {
		t.Fatal("Xannor mine damage used wrong bound/distribution or repeated mine", draws)
	}
	group = mobileGroup(w, 9, 2)
	w.Sectors[11].Defense = nil
	w.Sectors[10].Minefield = []MineLayer{{Owner: p.ID, Count: 1}, {Owner: other.ID, Count: 2}}
	draws = 0
	w.walkXannor(group, []int{9, 10, 11}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { draws++; return 0 })
	if draws != 2 || xannorForce(w) != 0 || !reflect.DeepEqual(w.Sectors[10].Minefield, []MineLayer{{Owner: other.ID, Count: 1}}) || p.Death != nil || other.Death != nil {
		t.Fatal("mine death dropped attribution, consumed excess mines or created a ship death")
	}
	group = mobileGroup(w, 9, MaxQuantity)
	w.Sectors[10].Minefield = []MineLayer{{Owner: p.ID, Count: 20000}}
	draws = 0
	w.walkXannor(group, []int{9, 10, 11}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { draws++; return 0 })
	if draws != xannorWorkLimit-1 || w.Sectors[9].Defense.Fighters != MaxQuantity-int64(draws) || w.Sectors[10].Minefield[0].Count != 20000-int64(draws) {
		t.Fatal("mine work was unbounded or unfinished survivors were misplaced", draws)
	}
	validMobile(t, w)
}

func TestXannorDefenseBatchesTieAndBoundedSurvivors(t *testing.T) {
	for _, tc := range []struct {
		force, defense int64
		roll           float64
		rounds         int
		win            bool
	}{
		{499, 500, .5, 500, true}, {500, 500, .5, 1, true}, {5000, 5000, .5, 10, true}, {5001, 5001, .5, 2, true}, {5001, 5001, .50001, 2, false},
	} {
		w := mobileWorld(t, 12)
		_, _ = w.Join("captain", "Captain")
		group := mobileGroup(w, 9, tc.force)
		w.Sectors[10].Defense = &SectorDefense{Owner: 1, Fighters: tc.defense}
		preferred := 12
		draws := 0
		w.walkXannor(group, []int{9, 10, 11}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { draws++; return tc.roll })
		if draws != tc.rounds {
			t.Fatal("wrong 5000/500/1 casualty boundary", tc, draws)
		}
		if tc.win {
			if w.Sectors[10].Defense != nil || w.Sectors[11].Defense.Fighters != tc.force || preferred != 0 {
				t.Fatal("won battle did not continue or clear preferred target")
			}
		} else {
			if xannorForce(w) != 0 || w.Sectors[10].Defense.Fighters != tc.defense || preferred != 10 {
				t.Fatal("lost battle cleared defenders or failed to retain pursuit sector")
			}
		}
		validMobile(t, w)
	}
	for _, roll := range []float64{0, .99} {
		w := mobileWorld(t, 12)
		_, _ = w.Join("captain", "Captain")
		group := mobileGroup(w, 9, MaxQuantity)
		w.Sectors[10].Defense = &SectorDefense{Owner: 1, Fighters: MaxQuantity}
		preferred := 12
		draws := 0
		w.walkXannor(group, []int{9, 10, 11}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { draws++; return roll })
		if draws != xannorWorkLimit-1 || w.Sectors[9].Defense == nil || w.Sectors[10].Defense == nil || preferred != 12 {
			t.Fatal("unfinished battle did not retain both sides", draws)
		}
		lost := int64(draws) * 5000
		if w.Sectors[9].Defense.Fighters+w.Sectors[10].Defense.Fighters != 2*MaxQuantity-lost {
			t.Fatal("unfinished battle duplicated/lost casualties")
		}
		validMobile(t, w)
	}
}

func TestXannorFriendlyTransitPartialMergeAndHQReserveCapacity(t *testing.T) {
	w := mobileWorld(t, 12)
	_, _ = w.Join("captain", "Captain")
	group := mobileGroup(w, 9, 100)
	receiver := mobileGroup(w, 12, MaxQuantity-50)
	w.Sectors[12].Minefield = []MineLayer{{Owner: 1, Count: 1}}
	acted := map[*SectorDefense]bool{}
	preferred := 0
	w.walkXannor(group, []int{9, 10, 11, 12}, acted, &preferred, clock, func() float64 { return 0 })
	if w.Sectors[12].Defense.Fighters != MaxQuantity || w.Sectors[11].Defense.Fighters != 49 || len(w.Sectors[12].Minefield) != 0 || !acted[receiver] {
		t.Fatal("partial merge bypassed mines or lost overflow/receiver activation")
	}
	validMobile(t, w)
	w = mobileWorld(t, 12)
	_, _ = w.Join("captain", "Captain")
	group = mobileGroup(w, 9, 100)
	receiver = mobileGroup(w, 10, MaxQuantity-50)
	acted = map[*SectorDefense]bool{}
	w.walkXannor(group, []int{9, 10, 11}, acted, &preferred, clock, func() float64 { t.Fatal("capacity hold must not draw"); return 0 })
	if w.Sectors[9].Defense.Fighters != 100 || receiver.Fighters != MaxQuantity-50 || acted[receiver] {
		t.Fatal("overfull friendly transit changed either participant")
	}
	w = mobileWorld(t, 12)
	_, _ = w.Join("captain", "Captain")
	group = mobileGroup(w, 9, 100)
	w.Xannor.Reserve = MaxQuantity - 50
	w.Sectors[8].Defense = &SectorDefense{Owner: 1, Fighters: 1}
	w.walkXannor(group, []int{9, 8}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { return 0 })
	if w.Sectors[8].Defense.Fighters != 50 || w.Sectors[9].Defense.Fighters != 50 || w.Xannor.Reserve != MaxQuantity-50 {
		t.Fatal("HQ entry overflowed reserve or discarded survivors")
	}
	validMobile(t, w)
}

func TestXannorFriendlyPlanetStocksUntouched(t *testing.T) {
	w := mobileWorld(t, 12)
	group := mobileGroup(w, 9, 100)
	home := &Planet{ID: 100, Sector: 10, Owner: XannorOwner, FactionHome: XannorHome, Name: "Xannoron", Updated: clock, Fighters: 37.5, Ground: 10}
	w.Planets[100], w.Sectors[10].Planet = home, 100
	preferred := 0
	w.walkXannor(group, []int{9, 10, 11}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { t.Fatal("friendly home must not draw"); return 0 })
	if home.Fighters != 37.5 || home.Owner != XannorOwner || home.Ground != 10 || w.Sectors[11].Defense.Fighters != 100 {
		t.Fatal("friendly planet became a Mercenary-style pickup")
	}
	validMobile(t, w)
}

func TestXannorProtectedPathsDailyOrderAndReplay(t *testing.T) {
	w := mobileWorld(t, 12)
	p, _ := w.Join("captain", "Captain")
	p.StoredScore = 2001
	mobileGroup(w, 8, 1)
	mobileGroup(w, 9, 100)
	w.Sectors[9].Warps = []int{7}
	w.Sectors[7].Warps = []int{8}
	before, _ := json.Marshal(w)
	w.xannorActions(clock, func() float64 { return 0 })
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("mobile group used a protected transit shortcut")
	}
	w.Sectors[9].Warps = []int{8}
	now := clock.Add(24 * time.Hour)
	w.maintain(now, func() float64 { return 0 })
	if xannorForce(w) != 101 || w.Sectors[8].Defense.Fighters != 101 || w.Sectors[9].Defense != nil || p.StoredScore == 2001 {
		t.Fatal("maintenance omitted movement or used refreshed score too early")
	}
	before, _ = json.Marshal(w)
	if w.maintain(now, nil) || w.maintain(clock, nil) {
		t.Fatal("daily replay/rollback repeated mobile actions")
	}
	after, _ = json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("replay changed authoritative force")
	}
	validMobile(t, w)
}

func TestXannorSeededFriendlyConservation(t *testing.T) {
	for seed := int64(0); seed < 32; seed++ {
		rng := rand.New(rand.NewSource(seed))
		w := mobileWorld(t, 32)
		p, _ := w.Join("captain", "Captain")
		p.StoredScore = rng.Int63n(3000000)
		for id := 8; id <= 32; id++ {
			w.Sectors[id].Warps = []int{8 + (id-7)%25, 8 + (id+16)%25}
			if rng.Intn(3) != 0 {
				values := []int64{1, 100, MaxQuantity / 2, MaxQuantity - 1, MaxQuantity}
				mobileGroup(w, id, values[rng.Intn(len(values))])
			}
		}
		before := xannorForce(w)
		draws := 0
		w.xannorActions(clock, func() float64 { draws++; return rng.Float64() })
		if xannorForce(w) != before || draws > 136 {
			t.Fatal("friendly force was lost/created or phase retried", seed, before, xannorForce(w), draws)
		}
		validMobile(t, w)
	}
}
