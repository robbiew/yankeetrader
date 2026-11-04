package door

// This opt-in acceptance driver uses production Session/Store actions with an
// injected UTC clock. It grants no assets or ownership and never edits a save.
import (
	"compress/gzip"
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"os"
	"path/filepath"
	"reflect"
	"runtime"
	"sort"
	"strings"
	"testing"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
)

//go:embed qb_campaign_test.go
var qbCampaignSource []byte

type qbCampaign struct {
	transcript                                           strings.Builder
	t                                                    *testing.T
	st                                                   store.Store
	at                                                   time.Time
	out                                                  string
	sessions, commands, trades, purchases, days, battles int
	actions                                              []string
	maintenance                                          []map[string]any
	recipe                                               *game.QBRecipe
}

func (c *qbCampaign) retainLogs() {
	c.t.Helper()
	raw, err := json.MarshalIndent(c.actions, "", "  ")
	if err != nil {
		c.t.Error(err)
		return
	}
	if err = os.WriteFile(filepath.Join(c.out, "actions.json"), append(raw, '\n'), 0600); err != nil {
		c.t.Error(err)
	}
	f, err := os.Create(filepath.Join(c.out, "transcript.txt.gz"))
	if err != nil {
		c.t.Error(err)
		return
	}
	z := gzip.NewWriter(f)
	if _, err = z.Write([]byte(c.transcript.String())); err != nil {
		c.t.Error(err)
	}
	if err = z.Close(); err != nil {
		c.t.Error(err)
	}
	if err = f.Close(); err != nil {
		c.t.Error(err)
	}
}

func (c *qbCampaign) world() *game.World {
	c.t.Helper()
	w, e := c.st.View()
	if e != nil {
		c.t.Fatal(e)
	}
	if !reflect.DeepEqual(w.QBRecipe, c.recipe) {
		c.t.Fatal("recipe changed")
	}
	return w
}
func (c *qbCampaign) play(lines ...string) string {
	c.t.Helper()
	term := &scripted{lines: lines}
	c.sessions++
	c.commands += len(lines)
	c.actions = append(c.actions, lines...)
	// Fixed known disruption locations isolate economy/maintenance/endgame.
	// Live random disruption and TCP/PTTY behavior remain the separate Door32 campaign.
	s := Session{Store: c.st, Terminal: term, Identity: "acceptance:atlas", Alias: "Atlas", Now: func() time.Time { return c.at }, Deadline: time.Now().Add(time.Minute), disruptionRandom: func() float64 { return .999999 }}
	if e := s.Run(); e != nil {
		c.t.Fatal(e, term.output.String())
	}
	text := term.output.String()
	fmt.Fprintf(&c.transcript, "SESSION %d UTC %s INPUT %q\n%s\n", c.sessions, c.at.Format(time.RFC3339), lines, text)
	if strings.Contains(text, "Error:") {
		c.t.Fatal(text)
	}
	if len(term.lines) != 0 {
		c.t.Fatal("unconsumed input", term.lines, text)
	}
	c.world()
	return text
}
func (c *qbCampaign) snapshot(name string) {
	c.t.Helper()
	raw, e := os.ReadFile(filepath.Join(c.st.Dir, "world.json"))
	if e != nil {
		c.t.Fatal(e)
	}
	f, e := os.Create(filepath.Join(c.out, name+".json.gz"))
	if e != nil {
		c.t.Fatal(e)
	}
	z := gzip.NewWriter(f)
	if _, e = z.Write(raw); e != nil {
		c.t.Fatal(e)
	}
	if e = z.Close(); e != nil {
		c.t.Fatal(e)
	}
	if e = f.Close(); e != nil {
		c.t.Fatal(e)
	}
}
func (c *qbCampaign) nextDay() {
	c.t.Helper()
	w := c.world()
	if w.Players[1].Sector != 1 {
		path := qbSafePath(w, w.Players[1].Sector, 1)
		if len(path) == 0 || int64(len(path)) > w.Players[1].Turns {
			c.t.Fatal("cannot legally park at Earth before maintenance")
		}
		lines := []string{}
		for _, to := range path {
			lines = append(lines, fmt.Sprintf("m %d", to))
		}
		lines = append(lines, "q")
		c.play(lines...)
	}
	c.days++
	if c.days > 24 {
		c.t.Fatal("campaign exceeded 24 UTC days")
	}
	c.at = c.at.Add(24 * time.Hour)
	before := c.world()
	c.snapshot(fmt.Sprintf("day-%02d-before", c.days))
	var receipt game.MaintenanceReceipt
	rng := rand.New(rand.NewSource(int64(700 + c.days)))
	if e := c.st.Update(func(w *game.World) error { var e error; receipt, e = w.RunMaintenance(c.at, rng.Float64); return e }); e != nil {
		c.t.Fatal(e)
	}
	after := c.world()
	if !receipt.Ran || after.LastMaintenance != c.at.Format("2006-01-02") || after.Players[1].Turns != 500 {
		c.t.Fatal("daily maintenance did not replenish turns")
	}
	c.snapshot(fmt.Sprintf("day-%02d-after", c.days))
	raw, _ := json.Marshal(after)
	if e := c.st.Update(func(w *game.World) error {
		r, e := w.RunMaintenance(c.at, func() float64 { c.t.Fatal("same-day RNG consumed"); return 0 })
		if r.Ran {
			c.t.Fatal("maintenance repeated")
		}
		return e
	}); e != nil {
		c.t.Fatal(e)
	}
	c.snapshot(fmt.Sprintf("day-%02d-repeat", c.days))
	repeated, _ := json.Marshal(c.world())
	if string(raw) != string(repeated) {
		c.t.Fatal("same-day maintenance changed world")
	}
	// Production/counters are observed from all ports, not just the traded pair.
	grew := 0
	for id, p := range after.Ports {
		if p.Supply != before.Ports[id].Supply {
			grew++
		}
	}
	if grew == 0 {
		c.t.Fatal("no port economy advanced")
	}
	c.maintenance = append(c.maintenance, map[string]any{"date": after.LastMaintenance, "ran": receipt.Ran, "same_day_noop": true, "turns_before": before.Players[1].Turns, "turns_after": after.Players[1].Turns, "ports_changed": grew, "wanderer": receipt.Wanderer.Status, "hq": after.Xannor.HQ})
	c.play("i", "q") // Reconnect at the new game date through production login.
	c.t.Logf("day %d: credits %d, owned %d", c.days, after.Players[1].Credits, qbOwned(after))
}
func qbOwned(w *game.World) int {
	n := 0
	for id, p := range w.Ports {
		if id != 1 && p.Owner == 1 {
			n++
		}
	}
	return n
}
func qbSafePath(w *game.World, from, to int) []int {
	queue := []int{from}
	parent := map[int]int{from: 0}
	for len(queue) > 0 {
		at := queue[0]
		queue = queue[1:]
		if at == to {
			path := []int{}
			for x := to; x != from; x = parent[x] {
				path = append([]int{x}, path...)
			}
			return path
		}
		for _, next := range w.Sectors[at].Warps {
			if _, ok := parent[next]; ok || next == 2999 || w.Sectors[next].Defense != nil || len(w.Sectors[next].Minefield) > 0 {
				continue
			}
			parent[next] = at
			queue = append(queue, next)
		}
	}
	return nil
}
func (c *qbCampaign) travel(to int) {
	c.t.Helper()
	w := c.world()
	if w.Players[1].Sector == to {
		return
	}
	path := qbSafePath(w, w.Players[1].Sector, to)
	if len(path) == 0 {
		c.t.Fatalf("no safe path to %d", to)
	}
	returnPath := qbSafePath(w, to, 1)
	if to != 1 && len(returnPath) == 0 {
		c.t.Fatal("no safe return to Earth")
	}
	if int64(len(path)+len(returnPath)+8) > w.Players[1].Turns {
		c.nextDay()
		w = c.world()
		path = qbSafePath(w, w.Players[1].Sector, to)
		if len(path) == 0 {
			c.t.Fatal("maintenance blocked route")
		}
	}
	lines := []string{}
	for _, sector := range path {
		lines = append(lines, fmt.Sprintf("m %d", sector))
	}
	lines = append(lines, "q")
	c.play(lines...)
	if c.world().Players[1].Sector != to {
		c.t.Fatal("travel did not reach target")
	}
}
func (c *qbCampaign) trade(seller, buyer, good int) {
	c.t.Helper()
	w := c.world()
	reserve := len(qbSafePath(w, w.Players[1].Sector, seller)) + len(qbSafePath(w, seller, buyer)) + len(qbSafePath(w, buyer, 1)) + 12
	if int64(reserve) > w.Players[1].Turns {
		c.nextDay()
		seller, buyer, good = qbTradeRoute(c.world())
	}
	name := game.Goods[good]
	c.travel(seller)
	w = c.world()
	p := w.Players[1]
	port := w.Ports[w.Sectors[seller].Port]
	refs := [3]float64{20.051570892333984, 29.302257537841797, 41.20359420776367}
	price := int64(math.Max(1, math.Floor(refs[good]*(1-port.Coefficient[good]*port.Supply[good]/(port.Production[good]*1000))+.5)))
	quantity := p.Holds
	if p.Credits/price < quantity {
		quantity = p.Credits / price
	}
	if quantity < 1 {
		c.t.Fatal("cannot afford trade")
	}
	buyReceipt := c.play("p", fmt.Sprintf("buy %s %d", name, quantity), "q")
	if c.world().Players[1].Cargo[good] != quantity {
		c.t.Fatal("buy failed", buyReceipt)
	}
	c.travel(buyer)
	c.play("p", fmt.Sprintf("sell %s %d", name, quantity), "q")
	c.trades++
	if c.world().Players[1].Cargo[good] != 0 {
		c.t.Fatal("sale failed")
	}
}
func qbDistances(w *game.World, from int) map[int]int {
	distance := map[int]int{from: 0}
	queue := []int{from}
	for head := 0; head < len(queue); head++ {
		at := queue[head]
		for _, next := range w.Sectors[at].Warps {
			if _, ok := distance[next]; ok || next == 2999 || w.Sectors[next].Defense != nil || len(w.Sectors[next].Minefield) > 0 {
				continue
			}
			distance[next] = distance[at] + 1
			queue = append(queue, next)
		}
	}
	return distance
}

// Find the weakest non-HQ hostile boundary of the currently safe component.
func qbBoundary(w *game.World, from int) (int, int) {
	reachable := qbDistances(w, from)
	ids := []int{}
	for id := range reachable {
		ids = append(ids, id)
	}
	sort.Ints(ids)
	origin, target := 0, 0
	weakest := int64(game.MaxQuantity)
	for _, id := range ids {
		for _, to := range w.Sectors[id].Warps {
			d := w.Sectors[to].Defense
			if to == 2999 || to == w.Xannor.HQ || d == nil || len(w.Sectors[to].Minefield) > 0 {
				continue
			}
			if d.Fighters < weakest {
				origin, target, weakest = id, to, d.Fighters
			}
		}
	}
	return origin, target
}
func (c *qbCampaign) clearBoundary() {
	c.t.Helper()
	w := c.world()
	from, to := qbBoundary(w, w.Players[1].Sector)
	if to == 0 {
		c.t.Fatal("no legal non-HQ boundary to breach")
	}
	force := w.Sectors[to].Defense.Fighters*30 + 200
	if force > 5000 {
		c.t.Fatal("boundary exceeds campaign combat budget")
	}
	if w.Players[1].Fighters < force {
		c.travel(1)
		p := c.world().Players[1]
		c.play("p", fmt.Sprintf("equip fighters %d", force-p.Fighters), "q")
	}
	c.travel(from)
	receipt := c.play(fmt.Sprintf("breach %d %d", to, force), "y", "y", "q")
	after := c.world()
	if after.Sectors[to].Defense != nil || after.Players[1].Sector != to || !strings.Contains(receipt, "Defense encounter saved:") {
		c.t.Fatal("confirmed breach failed", receipt)
	}
	c.battles++
}

func qbTradeRoute(w *game.World) (int, int, int) {
	earthDistance := qbDistances(w, 1)
	seller, buyer, good := 0, 0, 0
	best := 0.0
	ids := []int{}
	for id := range w.Ports {
		if id != 1 {
			ids = append(ids, id)
		}
	}
	sort.Ints(ids)
	for _, id := range ids {
		a := w.Ports[id]
		if w.Sectors[a.Sector].Defense != nil {
			continue
		}
		distance, reachable := earthDistance[a.Sector]
		if !reachable || distance > 8 {
			continue
		}
		for _, link := range w.Sectors[a.Sector].Warps {
			pid := w.Sectors[link].Port
			if pid < 2 || w.Sectors[link].Defense != nil {
				continue
			}
			b := w.Ports[pid]
			back := qbSafePath(w, link, a.Sector)
			if len(back) == 0 || len(back) > 3 {
				continue
			}
			for g := 0; g < 3; g++ {
				if a.Coefficient[g] <= 0 || b.Coefficient[g] >= 0 {
					continue
				}
				score := (a.Coefficient[g] - b.Coefficient[g]) / float64(1+len(back))
				if score > best {
					best = score
					seller = a.Sector
					buyer = b.Sector
					good = g
				}
			}
		}
	}
	if seller == 0 {
		panic("no bounded trading route")
	}

	return seller, buyer, good
}

func TestQBFullWorldAcceptanceCampaign(t *testing.T) {
	out := os.Getenv("YT_QB_CAMPAIGN_OUT")
	if out == "" {
		t.Skip("opt-in acceptance: set YT_QB_CAMPAIGN_OUT to a new output directory")
	}
	if e := os.Mkdir(out, 0700); e != nil {
		t.Fatal(e)
	}
	at := time.Date(2032, 6, 13, 12, 0, 0, 0, time.UTC)
	w, e := game.NewQB36(at, 36, 0xc805, "2027-01-01")
	if e != nil {
		t.Fatal(e)
	}
	if w.GenesisPorts != nil || w.GenesisThreshold() != 300 {
		t.Fatal("default threshold changed")
	}
	c := &qbCampaign{t: t, st: store.Store{Dir: filepath.Join(out, "world")}, at: at, out: out, recipe: w.QBRecipe.Clone()}
	base := w
	defer c.retainLogs()
	if e = c.st.Create(w); e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(out, "driver.go.txt"), qbCampaignSource, 0600); e != nil {
		t.Fatal(e)
	}
	c.snapshot("initial")
	c.play("i", "q")
	ids := []int{}
	for id := range w.Ports {
		if id != 1 {
			ids = append(ids, id)
		}
	}
	sort.Ints(ids)
	// Grow holds using earned credits, then earn the complete acquisition budget.
	routeDay := -1
	seller, buyer, good := 0, 0, 0
	for cycle := 0; c.world().Players[1].Credits < 2_500_000; cycle++ {
		if cycle >= 180 {
			t.Fatal("trade budget exhausted")
		}
		if c.world().Players[1].Turns < 24 {
			c.nextDay()
		}
		if routeDay != c.days {
			seller, buyer, good = qbTradeRoute(c.world())
			routeDay = c.days
		}
		c.trade(seller, buyer, good)
		p := c.world().Players[1]
		if p.Holds < 1000 && p.Credits > 5000 {
			add := (p.Credits - 2000) / 1000
			if add > 1000-p.Holds {
				add = 1000 - p.Holds
			}
			if add > 0 {
				c.travel(1)
				c.play("p", fmt.Sprintf("equip holds %d", add), "q")
			}
		}
	}
	c.snapshot("earned-budget")
	// Buy the nearest safe unowned port with separately confirmed production UI.
	for qbOwned(c.world()) < 300 {
		w = c.world()
		p := w.Players[1]
		target, bestDistance := 0, 100000
		distances := qbDistances(w, p.Sector)
		for _, id := range ids {
			port := w.Ports[id]
			if port.Owner != 0 || w.Sectors[port.Sector].Defense != nil {
				continue
			}
			distance, reachable := distances[port.Sector]
			if port.Sector == p.Sector {
				target = port.Sector
				bestDistance = 0
				break
			}
			if reachable && distance < bestDistance {
				target = port.Sector
				bestDistance = distance
			}
		}
		if target == 0 {
			c.clearBoundary()
			continue
		}
		if int64(bestDistance+len(qbSafePath(w, target, 1))+8) > p.Turns {
			c.nextDay()
			continue
		}
		c.travel(target)
		if qbOwned(c.world()) == 299 {
			text := c.play("genesis", "q")
			if !strings.Contains(text, "1 short") {
				t.Fatal("299 ports allowed Genesis", text)
			}
		}
		purchaseReceipt := c.play("b", "y", "q")
		c.purchases++
		if qbOwned(c.world()) != c.purchases {
			t.Fatal("purchase failed or unexpected ownership", purchaseReceipt)
		}
	}
	// Ensure multiple full maintenance dates even if planner gets faster later.
	for c.days < 3 {
		c.nextDay()
	}
	preReconnect := *c.world().Players[1]
	c.play("i") // EOF disconnect after a committed read, then reconnect.
	c.play("i", "q")
	reconnected := c.world().Players[1]
	if preReconnect.ID != reconnected.ID || preReconnect.Credits != reconnected.Credits || preReconnect.Turns != reconnected.Turns || preReconnect.Holds != reconnected.Holds || preReconnect.Cargo != reconnected.Cargo {
		t.Fatal("same-day reconnect gifted or lost assets")
	}
	c.snapshot("before-genesis")
	before := c.world()
	stale := c.st.ForShip(1, before.Players[1].ShipGeneration, before.Season)
	text := c.play("genesis", "GENESIS")
	if !strings.Contains(text, "300 ports (required 300)") {
		t.Fatal(text)
	}
	after := c.world()
	if after.Season != 2 || len(after.Players) != 0 || len(after.SeasonResults) != 1 || after.SeasonResults[0].Ports != 300 || after.SeasonResults[0].Threshold != 300 {
		t.Fatal("default Genesis result")
	}
	for id, p := range after.Ports {
		old := base.Ports[id]
		if p.Sector != old.Sector || p.Name != old.Name || p.Production != old.Production || p.Coefficient != old.Coefficient || p.Owner != 0 || p.Treasury != 0 {
			t.Fatal("recipe layout/reset changed")
		}
	}
	initial := base
	for id, s := range after.Sectors {
		if !reflect.DeepEqual(s.Warps, initial.Sectors[id].Warps) {
			t.Fatal("warp layout changed")
		}
	}
	if after.Xannor.HQ != initial.Xannor.HQ || after.LastMaintenance != c.at.Format("2006-01-02") {
		t.Fatal("HQ/watermark changed")
	}
	c.snapshot("after-genesis")
	if _, e = stale.View(); e != game.ErrSeasonChanged {
		t.Fatal("old login authorized", e)
	}
	c.play("seasons", "q")
	if len(c.world().Players) != 1 || c.world().Players[1].Credits != 1005 || qbOwned(c.world()) != 0 {
		t.Fatal("new-season reconnect")
	}
	c.snapshot("reconnected")
	sealed, _ := os.ReadFile(filepath.Join(c.st.Dir, "world.json"))
	if e = stale.Update(func(w *game.World) error { w.Players[1].Credits++; return nil }); e != game.ErrSeasonChanged {
		t.Fatal("stale action after ID reuse", e)
	}
	unchanged, _ := os.ReadFile(filepath.Join(c.st.Dir, "world.json"))
	if string(sealed) != string(unchanged) {
		t.Fatal("stale action changed new save")
	}
	report := map[string]any{"go_version": runtime.Version(), "profile": "qb36-v1", "sectors": 3000, "ports": 1000, "threshold": 300, "days": c.days, "sessions": c.sessions, "commands": c.commands, "trade_cycles": c.trades, "purchases": c.purchases, "boundary_battles": c.battles, "source_recipe": c.recipe, "maintenance": c.maintenance, "old_login_rejected": true, "outcome": "passed", "clock": "injected UTC; wall deadlines remain real", "disruptions": "fixed known sector 2999 avoided by planner"}
	for name, data := range map[string]any{"summary": report, "actions": c.actions} {
		raw, e := json.MarshalIndent(data, "", "  ")
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(out, name+".json"), append(raw, '\n'), 0600); e != nil {
			t.Fatal(e)
		}
	}
	c.retainLogs()
	manifest := map[string]string{}
	entries, _ := os.ReadDir(out)
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		raw, e := os.ReadFile(filepath.Join(out, entry.Name()))
		if e != nil {
			t.Fatal(e)
		}
		sum := sha256.Sum256(raw)
		manifest[entry.Name()] = hex.EncodeToString(sum[:])
	}
	raw, _ := json.MarshalIndent(manifest, "", "  ")
	if e = os.WriteFile(filepath.Join(out, "manifest.json"), raw, 0600); e != nil {
		t.Fatal(e)
	}
	t.Logf("passed: %d days, %d sessions, %d trade cycles, %d purchases", c.days, c.sessions, c.trades, c.purchases)
}

func TestQBCampaignSafePlanning(t *testing.T) {
	w, e := game.New(time.Date(2032, 6, 13, 12, 0, 0, 0, time.UTC), 36, 8)
	if e != nil {
		t.Fatal(e)
	}
	// A shorter hostile route must never beat a longer safe directed route.
	w.Sectors[1].Warps = []int{2, 3}
	w.Sectors[2].Warps = []int{4}
	w.Sectors[3].Warps = []int{5}
	w.Sectors[5].Warps = []int{4}
	w.Sectors[2].Defense = &game.SectorDefense{Owner: game.XannorOwner, Fighters: 1}
	if p := qbSafePath(w, 1, 4); !reflect.DeepEqual(p, []int{3, 5, 4}) {
		t.Fatal("unsafe route", p)
	}
	if distance := qbDistances(w, 1)[4]; distance != 3 {
		t.Fatal("wrong safe distance", distance)
	}
	w.Sectors[3].Minefield = []game.MineLayer{{Owner: 1, Count: 1}}
	if p := qbSafePath(w, 1, 4); p != nil {
		t.Fatal("silently routed through hazards", p)
	}
}
func TestQBCampaignPlannerUsesCurrentTradeClasses(t *testing.T) {
	at := time.Date(2032, 6, 13, 12, 0, 0, 0, time.UTC)
	w, e := game.NewQB36(at, 36, 0xc805, "2027-01-01")
	if e != nil {
		t.Fatal(e)
	}
	for day := 0; day < 3; day++ {
		seller, buyer, good := qbTradeRoute(w)
		if w.Ports[w.Sectors[seller].Port].Coefficient[good] <= 0 || w.Ports[w.Sectors[buyer].Port].Coefficient[good] >= 0 {
			t.Fatal("stale trade classes")
		}
		rng := rand.New(rand.NewSource(int64(701 + day)))
		if _, e = w.RunMaintenance(at.Add(time.Duration(day+1)*24*time.Hour), rng.Float64); e != nil {
			t.Fatal(e)
		}
	}
}
