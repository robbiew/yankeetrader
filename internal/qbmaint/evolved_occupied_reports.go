package qbmaint

import (
	"bytes"
	"fmt"
	"slices"
	"strings"
)

// ReplayEvolvedOccupiedAux publishes five child auxiliary files from modeled final
// world and calculated ledgers. It never finalizes world metadata or runs a tail.
// Unsupported contexts return nil/zero statistics and all outputs are owned.
func ReplayEvolvedOccupiedAux(before map[string][]byte, world []byte, in AuxInputs, events []OccupiedCombatEvent, tail EvolvedOccupiedTailStats) (map[string][]byte, OccupiedReportStats, error) {
	fail := func(s string) (map[string][]byte, OccupiedReportStats, error) {
		return nil, OccupiedReportStats{}, fmt.Errorf("evolved occupied reports: %s", s)
	}
	if len(before) != 6 {
		return fail("exact six before files")
	}
	for _, n := range []string{"YTDATA.DAT", "YTNAME.DAT", "YTNEWS.DAT", "YTYNEWS.DAT", "YTRMSG.DAT", "YTSCORE.ASC"} {
		if _, ok := before[n]; !ok {
			return fail("missing before file")
		}
	}
	old := before["YTDATA.DAT"]
	if len(old) != WorldRecords*RecordSize || len(world) != len(old) {
		return fail("default world extents")
	}
	raw := func(b []byte, r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(b[a : a+4]) }
	get := func(b []byte, r, o int) int {
		n, ok := integer(raw(b, r, o))
		if !ok {
			return -999999
		}
		return n
	}
	number := func(b []byte, r, o int) float64 { return portSingleValue(raw(b, r, o)) }
	named := func(b []byte, r int, name string) bool {
		a := (r - 1) * RecordSize
		return get(b, r, 85) == len(name) && bytes.Equal(b[a:a+41], []byte(fmt.Sprintf("%-41s", name)))
	}
	for _, b := range [][]byte{old, world} {
		if get(b, 1, 41) != 11 || string(b[:11]) != "YTSCORE.ASC" || get(b, 1, 45) != 26 {
			return fail("fixed source scoreboard path/year")
		}
		for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
			if get(b, 1, o) != n {
				return fail("geometry")
			}
		}
	}
	if get(old, 1, 41) != 11 || string(old[:11]) != "YTSCORE.ASC" {
		return fail("default scoreboard path")
	}
	for r := 2; r <= 51; r++ {
		for o := 41; o < 137; o += 4 {
			want := 0
			if o == 109 {
				want = -1
			}
			if (number(old, r, o) != 0 && !(o == 109 && number(old, r, o) == -1)) || get(world, r, o) != want {
				return fail("inactive human assets and published ranks required")
			}
		}
	}
	if len(before["YTRMSG.DAT"]) != 0 {
		return fail("private compression excluded")
	}
	day := get(world, 1, 81)
	if (day != 307 && day != 308) || get(old, 1, 81) != day-1 {
		return fail("child date handoff")
	}
	date := fmt.Sprintf("2026-11-%02d", day-304)
	if in.NewsDate != date || in.ScoreDate != date {
		return fail("explicit source report dates")
	}
	for _, w := range [][]byte{old, world} {
		for r, name := range map[int]string{4052: "The Wanderer", 4150: "Mercenary Base", 4151: "Xannoron"} {
			owner := 0
			if r == 4150 {
				owner = -2
			}
			if r == 4151 {
				owner = -1
			}
			if !named(w, r, name) || get(w, r, 73) != owner {
				return fail("named existing homes")
			}
		}
		for slot := 1; slot <= 100; slot++ {
			r := 4051 + slot
			active := number(w, r, 85) != 0
			if slot != 1 && slot != 2 && slot != 99 && slot != 100 && active {
				return fail("unknown active planet")
			}
			links := 0
			sector := 0
			for s := 1; s <= 3000; s++ {
				if get(w, 51+s, 93) == slot {
					links++
					sector = s
				}
			}
			if active && links != 1 || !active && links != 0 {
				return fail("planet link inventory")
			}
			if slot == 2 && active && (!named(w, r, "Route Haven") || get(w, r, 73) != 0 || sector != 854) {
				return fail("neutral Route Haven context")
			}
		}
		for r := 3052; r <= 4051; r++ {
			if number(w, r, 89) != 0 {
				return fail("hiring excluded")
			}
		}
	}
	if (get(old, 4053, 85) != 0) != (get(world, 4053, 85) != 0) {
		return fail("ordinary creation/deletion excluded")
	}
	stats := OccupiedReportStats{PublicEvents: len(events)}
	dead := map[int]bool{}
	previous := 1
	extra := []string{}
	previousGround := -1
	for _, event := range events {
		if event.Group < 2 || event.Group > 20 || event.Group < previous || dead[event.Group] || event.Sector != 854 {
			return fail("source-ordered bounded events")
		}
		previous = event.Group
		initial, remaining := 0, 0
		if event.Kind != "planet" || event.Ground == nil || event.Defense != nil {
			return fail("only fatal Route Haven events")
		}
		v := event.Ground
		initial, remaining = v.InitialForce, v.Force
		if remaining != 0 || get(old, 905, 93) != 2 || !named(old, 4053, "Route Haven") || get(old, 4053, 73) != 0 || v.InitialGround < 1 || v.InitialGround > 600000 || v.Ground < 1 || v.Ground >= v.InitialGround {
			return fail("actual surviving ground context")
		}
		if v.RawForce > 0 || v.Draws < 1 || previousGround >= 0 && v.InitialGround != previousGround {
			return fail("source ground ledger chronology")
		}
		previousGround = v.Ground
		extra = append(extra, fmt.Sprintf(" *** %d Xannor attacked the planet \"Route Haven\"", initial), " *** Xannor fighters destroyed!")
		if initial < 1 || initial > 10000 || remaining < 0 || remaining > initial {
			return fail("bounded moving force")
		}
		stats.Losses[0] += initial - remaining
		if remaining == 0 {
			dead[event.Group] = true
		}
	}
	if previousGround >= 0 && get(world, 4053, 77) != previousGround {
		return fail("ground ledger/world handoff")
	}
	for _, b := range tail.Battles {
		if b.Sector != 109 || b.InitialForce != 97525 || b.InitialDefenders != 182 || b.Force < 1 || b.Force > b.InitialForce || b.Defenders != 0 || b.Losses != b.InitialForce-b.Force || b.DefenderLosses != b.InitialDefenders || b.Rounds != b.Losses+b.DefenderLosses || b.Draws != b.Rounds+1 {
			return fail("selected Mercenary victory ledger")
		}
		stats.Losses[0] += b.DefenderLosses
		stats.Losses[1] += b.Losses
	}
	if len(tail.Battles) > 1 {
		return fail("one qualified battle")
	}
	stats.PublicEvents += len(tail.Battles)
	if stats.Losses[0] > 10000 || stats.Losses[1] > 100000 {
		return fail("casualties exceed inventory")
	}
	for index, b := range [][]byte{old, world} {
		for s := 1; s <= 3000; s++ {
			force, owner := get(b, 51+s, 81), get(b, 51+s, 85)
			if force < 0 || force > 110000 {
				return fail("bounded whole physical force")
			}
			column := 0
			switch owner {
			case -1:
				column = 0
			case -2:
				column = 1
			case 0:
				column = 2
			default:
				return fail("physical owner")
			}
			stats.Physical[index][column] += force
		}
		n := stats.Physical[index]
		if n[0]+n[1]+n[2] > 110000 {
			return fail("physical inventory exceeds bound")
		}
	}
	a, b := stats.Physical[0], stats.Physical[1]
	if a[0] > 10000 || a[1] > 100000 || a[2] > 37 || b[0] > 10000 || b[1] > 100000 || b[2] > 37 {
		return fail("bounded faction inventory")
	}
	if tail.FinalForce != b[1] || tail.MercenaryForce-tail.Losses != tail.FinalForce || tail.Losses != stats.Losses[1] {
		return fail("tail/physical publication mismatch")
	}
	final := []int{}
	for s := 1; s <= 3000; s++ {
		if get(world, 51+s, 81) > 0 && get(world, 51+s, 85) == -2 {
			final = append(final, s)
		}
	}
	if !slices.Equal(final, tail.FinalMercenarySectors) {
		return fail("tail endpoint inventory")
	}
	if b[0]+stats.Losses[0] != a[0] || b[1]+stats.Losses[1] != a[1] || b[2] != a[2] {
		return fail("casualty/physical faction conservation")
	}
	stats.Scores = [2]int{100 * b[0], 100 * b[1]}
	leader := max(stats.Scores[0], stats.Scores[1])
	if leader <= 0 {
		return fail("positive NPC denominator")
	}
	for i, score := range stats.Scores {
		numerator := int64(score) * 10000
		denominator := int64(leader)
		q, r := numerator/denominator, numerator%denominator
		if r*2 == denominator {
			return fail("halfway percentage formatting")
		}
		if r*2 > denominator {
			q++
		}
		stats.PercentHundredths[i] = int(q)
	}
	news, board, e := formatAuxReports(in, stats.Scores[0], [3]bool{}, nil)
	if e != nil {
		return fail(e.Error())
	}
	marker := "  -  Mercenary Report:\r\n"
	at := strings.Index(string(news), marker)
	if at < 0 {
		return fail("source news framing")
	}
	if len(extra) > 0 {
		news = []byte(string(news[:at]) + strings.Join(extra, "\r\n") + "\r\n" + string(news[at:]))
	}
	if len(tail.Battles) > 0 {
		merc := []string{}
		for _, b := range tail.Battles {
			merc = append(merc, fmt.Sprintf(" *** %d Mercenaries attacking %d fighters beloning to The Xannor!", b.InitialForce, b.InitialDefenders), " *** The Mercenaries Won!")
		}
		marker := []byte{0x1a}
		if !bytes.HasSuffix(news, marker) {
			return fail("news EOF framing")
		}
		news = append(bytes.Clone(news[:len(news)-1]), []byte(strings.Join(merc, "\r\n")+"\r\n\x1a")...)
	}
	comma := func(n int) string {
		text := fmt.Sprint(n)
		for i := len(text) - 3; i > 0; i -= 3 {
			text = text[:i] + "," + text[i:]
		}
		return text
	}
	percent := func(n int) string { return fmt.Sprintf("%d.%02d", n/100, n%100) }
	lines := strings.Split(string(board), "\r\n")
	lines[len(lines)-3] = fmt.Sprintf("  %15s  %7s%%    %15s  %6s%%", comma(stats.Scores[0]), percent(stats.PercentHundredths[0]), comma(stats.Scores[1]), percent(stats.PercentHundredths[1]))
	board = []byte(strings.Join(lines, "\r\n"))
	return map[string][]byte{"YTNAME.DAT": bytes.Clone(before["YTNAME.DAT"]), "YTYNEWS.DAT": bytes.Clone(before["YTNEWS.DAT"]), "YTRMSG.DAT": {}, "YTNEWS.DAT": news, "YTSCORE.ASC": board}, stats, nil
}
