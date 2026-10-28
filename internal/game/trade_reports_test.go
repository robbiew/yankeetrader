package game

import (
	"encoding/json"
	"reflect"
	"strings"
	"testing"
	"time"
)

func commerceReportWorld(t *testing.T) (*World, *Player) {
	t.Helper()
	w, p := navigationWorld(t)
	for id := range w.Ports {
		if id != 1 {
			w.Sectors[w.Ports[id].Sector].Port = 0
			delete(w.Ports, id)
		}
	}
	// Recreate the captured 10/44 and 30/15 quotes using current Go prices.
	// This is a controlled quote fixture, not a DOS-save import or pricing port.
	w.Ports[2] = &Port{ID: 2, Sector: 101, Name: "Test Port", Updated: w.Created, Supply: [3]float64{1000, 1000, 1000}, Production: [3]float64{100, 100, 100}, Coefficient: [3]float64{50, -45, -55}}
	w.Ports[3] = &Port{ID: 3, Sector: 107, Name: "Servoa", Updated: w.Created, Supply: [3]float64{1000, 1000, 1000}, Production: [3]float64{100, 100, 100}, Coefficient: [3]float64{-50, 50, -55}}
	w.Sectors[101].Port, w.Sectors[107].Port = 2, 3
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	return w, p
}

func TestNearestPortDistancesAndPlayerActionFromDOSCases(t *testing.T) {
	w, p := commerceReportWorld(t)
	p.Turns = 0
	before, _ := json.Marshal(w)
	all, err := w.NearestPorts(p.ID, PortFilter{}, w.Created)
	if err != nil || len(all) != 2 || all[0].Sector != 101 || all[0].Distance != 1 || all[1].Sector != 107 || all[1].Distance != 2 {
		t.Fatalf("nearest-all geometry: %+v, %v", all, err)
	}
	for _, action := range []string{"buy", "sell"} {
		got, err := w.NearestPorts(p.ID, PortFilter{Good: "ore", Action: action}, w.Created)
		want := 101
		if action == "sell" {
			want = 107
		}
		if err != nil || len(got) != 1 || got[0].Sector != want {
			t.Fatalf("player %s filter reversed: %+v, %v", action, got, err)
		}
	}
	all[0].Supply[0] = 0
	_, _ = w.NearestPorts(p.ID, PortFilter{}, w.Created.Add(24*time.Hour))
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("forecast or returned data changed live economy/account")
	}
}

func TestTradeSpreadAndDirectedReturnFromDOSCases(t *testing.T) {
	for _, direct := range []bool{false, true} {
		for _, holds := range []int64{10, 100} {
			w, p := commerceReportWorld(t)
			p.Holds, p.Turns = holds, 0
			if direct {
				w.Sectors[107].Warps = append(w.Sectors[107].Warps, 101)
			}
			before, _ := json.Marshal(w)
			routes, err := w.TradeRoutes(p.ID, false, w.Created)
			if err != nil || len(routes) != 1 {
				t.Fatal(routes, err)
			}
			wantReturn := 4
			if direct {
				wantReturn = 1
			}
			r := routes[0]
			if r.From != 101 || r.To != 107 || r.ApproachHops != 1 || r.ReturnHops != wantReturn || r.Spread != 49 || r.OutboundGood != 0 || r.ReturnGood != 1 || r.OutboundBuy != 10 || r.OutboundSell != 30 || r.ReturnBuy != 15 || r.ReturnSell != 44 || r.OutboundUnits != 1000 || r.ReturnUnits != 1000 {
				t.Fatalf("wrong quote forecast (direct=%t, holds=%d): %+v", direct, holds, r)
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("free route report mutated world")
			}
			if _, err := w.TradeRoutes(p.ID, true, w.Created); err == nil {
				t.Fatal("adjacent profits accepted a sector without a trading port")
			}
			p.Sector = 101
			local, err := w.TradeRoutes(p.ID, true, w.Created)
			if err != nil || len(local) != 1 || local[0].Spread != 49 || local[0].ApproachHops != 0 {
				t.Fatal("current-port report differs", local, err)
			}
		}
	}
}

func TestTradeReportsHonorAvoidsDefensesReturnReachabilityAndStock(t *testing.T) {
	for _, mode := range []string{"avoid-target", "avoid-return", "no-return", "guarded", "empty-stock", "no-complement", "zero-spread"} {
		t.Run(mode, func(t *testing.T) {
			w, p := commerceReportWorld(t)
			switch mode {
			case "avoid-target":
				p.AvoidSectors = []int{107}
			case "avoid-return":
				p.AvoidSectors = []int{109}
			case "no-return":
				w.Sectors[107].Warps = nil
			case "guarded":
				w.Sectors[107].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 50}
			case "empty-stock":
				w.Ports[3].Supply[1] = .5
			case "no-complement":
				w.Ports[3].Coefficient = w.Ports[2].Coefficient
			case "zero-spread":
				w.Ports[2].Coefficient = [3]float64{1, -1, -1}
				w.Ports[3].Coefficient = [3]float64{-1, 1, -1}
			}
			routes, err := w.TradeRoutes(p.ID, false, w.Created)
			if err != nil || len(routes) != 0 {
				t.Fatal("invalid round trip advertised", routes, err)
			}
			ports, err := w.NearestPorts(p.ID, PortFilter{}, w.Created)
			if err != nil {
				t.Fatal(err)
			}
			if mode == "guarded" || mode == "avoid-target" {
				if len(ports) != 1 || ports[0].Sector != 101 {
					t.Fatal("hidden/avoided target disclosed", ports)
				}
			} else if len(ports) != 2 {
				t.Fatal("nearest report incorrectly required a round trip", ports)
			}
		})
	}
}

func TestNearestOwnershipFiltersAndLiveMembership(t *testing.T) {
	w, p := commerceReportWorld(t)
	member, _ := w.Join("member-secret", "Member")
	enemy, _ := w.Join("enemy-secret", "Enemy")
	if err := w.CreateTeam(p.ID, "Orion", "ABCD"); err != nil {
		t.Fatal(err)
	}
	if err := w.JoinTeam(member.ID, p.Team, "ABCD"); err != nil {
		t.Fatal(err)
	}
	w.Ports[2].Owner, w.Ports[3].Owner = p.ID, member.ID
	for i, sector := range []int{103, 104} {
		port := *w.Ports[2]
		port.ID, port.Sector, port.Owner = 4+i, sector, 0
		if i == 0 {
			port.Owner = enemy.ID
		}
		w.Ports[port.ID] = &port
		w.Sectors[sector].Port = port.ID
	}
	for filter, want := range map[string][]int{"all": {101, 103, 104, 107}, "own": {101}, "team": {101, 107}, "enemy": {103}, "unowned": {104}} {
		ports, err := w.NearestPorts(p.ID, PortFilter{Ownership: filter}, w.Created)
		var got []int
		for _, port := range ports {
			got = append(got, port.Sector)
		}
		if err != nil || !reflect.DeepEqual(got, want) {
			t.Fatalf("%s filter: %v, %v", filter, got, err)
		}
		data, _ := json.Marshal(ports)
		if strings.Contains(string(data), "secret") || strings.Contains(string(data), "Treasury") {
			t.Fatal("private account data exposed")
		}
	}
	if err := w.LeaveTeam(member.ID, p.Team); err != nil {
		t.Fatal(err)
	}
	ports, err := w.NearestPorts(p.ID, PortFilter{Ownership: "team"}, w.Created)
	if err != nil || len(ports) != 1 || ports[0].Sector != 101 {
		t.Fatal("former teammate remained in team filter", ports, err)
	}
}

func TestTradeReportsRejectBadFiltersAndCurrentAvoid(t *testing.T) {
	w, p := commerceReportWorld(t)
	for _, filter := range []PortFilter{{Ownership: "bad"}, {Ownership: "team"}, {Good: "ore"}, {Good: "bad", Action: "buy"}, {Action: "buy"}} {
		if _, err := w.NearestPorts(p.ID, filter, w.Created); err == nil {
			t.Fatal("bad/unavailable filter accepted", filter)
		}
	}
	if _, err := w.NearestPorts(999, PortFilter{}, w.Created); err == nil {
		t.Fatal("missing player accepted")
	}
	if _, err := w.TradeRoutes(p.ID, false, time.Time{}); err == nil {
		t.Fatal("invalid report time accepted")
	}
	p.AvoidSectors = []int{100}
	if _, err := w.NearestPorts(p.ID, PortFilter{}, w.Created); err == nil {
		t.Fatal("current-sector avoid ignored")
	}
}

func TestTradeReportsMaximumUniverse(t *testing.T) {
	w, err := New(time.Now(), 36, 3000)
	if err != nil {
		t.Fatal(err)
	}
	p, _ := w.Join("route-scale", "Navigator")
	p.Turns = 0
	before, _ := json.Marshal(w)
	routes, err := w.TradeRoutes(p.ID, false, w.Created)
	if err != nil || len(routes) == 0 {
		t.Fatal("maximum universe did not produce reports", err)
	}
	seen := map[[2]int]bool{}
	for i, route := range routes {
		key := [2]int{min(route.From, route.To), max(route.From, route.To)}
		if seen[key] || !contains(w.Sectors[route.From].Warps, route.To) || route.ReturnHops < 1 || route.Spread <= 0 {
			t.Fatal("duplicate or invalid round trip at scale", route)
		}
		seen[key] = true
		if i < 5 {
			path, err := w.PlayerPath(p.ID, route.To, route.From)
			if err != nil || len(path)-1 != route.ReturnHops {
				t.Fatal("report disagrees with authoritative path finder", route, path, err)
			}
		}
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("large report changed the saved world")
	}
}
