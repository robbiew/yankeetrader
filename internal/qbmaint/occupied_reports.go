package qbmaint

import (
	"bytes"
	"fmt"
	"strings"
)

// OccupiedReportStats distinguishes physical inventories, casualties and scored
// factions. Columns are Xannor, Mercenary, neutral; rows are before and after.
// PercentHundredths is exact two-decimal display rounding, not a native witness.
type OccupiedReportStats struct {
	Physical                          [2][3]int
	Losses, Scores, PercentHundredths [2]int
	PublicEvents                      int
}

// ReplayOccupiedAux emits the five auxiliary files from original before files,
// a modeled finalized world and calculated source-ordered combat receipts. It
// does not run a tail, finalize metadata or accept native target corrections.
// Unsupported contexts fail atomically; all returned bytes are owned.
func ReplayOccupiedAux(before map[string][]byte, world []byte, in AuxInputs, events []OccupiedCombatEvent) (map[string][]byte, OccupiedReportStats, error) {
	fail := func(s string) (map[string][]byte, OccupiedReportStats, error) {
		return nil, OccupiedReportStats{}, fmt.Errorf("occupied reports: %s", s)
	}
	if len(before) != 3 {
		return fail("exact three before files")
	}
	for _, n := range []string{"YTDATA.DAT", "YTNAME.DAT", "YTNEWS.DAT"} {
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
			if number(old, r, o) != 0 || get(world, r, o) != want {
				return fail("inactive human assets and published ranks required")
			}
		}
	}
	for slot := 1; slot <= 100; slot++ {
		r := 4051 + slot
		if number(old, r, 85) != 0 {
			title := ""
			for _, name := range []string{"Occupied Haven", "Second Haven", "Route Haven"} {
				if named(old, r, name) {
					title = name
				}
			}
			if (slot != 2 && slot != 3) || title == "" || (get(old, r, 73) != -1 && get(old, r, 73) != 0) || get(old, r, 41) != 305 || get(old, r, 77) != 500000 {
				return fail("clean ordinary before planet")
			}
			for _, o := range []int{45, 49, 53} {
				if get(old, r, o) != 1000 {
					return fail("ordinary before rates")
				}
			}
			for o := 41; o < 137; o += 4 {
				if o == 41 || o == 45 || o == 49 || o == 53 || o == 73 || o == 77 || o == 85 {
					continue
				}
				if number(old, r, o) != 0 {
					return fail("ordinary before assets")
				}
			}
			if !named(world, r, title) || get(world, r, 73) != get(old, r, 73) {
				return fail("retained ordinary name/owner")
			}
		} else if slot != 1 && slot != 99 && slot != 100 && number(world, r, 85) != 0 {
			return fail("additional ordinary planet")
		}
	}
	for slot, name := range map[int]string{1: "The Wanderer", 99: "Mercenary Base", 100: "Xannoron"} {
		if number(old, 4051+slot, 85) != 0 || !named(world, 4051+slot, name) {
			return fail("missing-home bootstrap news context")
		}
	}
	for r := 3052; r <= 4051; r++ {
		if number(old, r, 89) != 0 {
			return fail("tax-funded hiring")
		}
	}
	stats := OccupiedReportStats{PublicEvents: len(events)}
	dead := map[int]bool{}
	previous := 1
	extra := []string{}
	for _, event := range events {
		if event.Group < 2 || event.Group > 20 || event.Group < previous || dead[event.Group] || event.Sector != 854 {
			return fail("source-ordered bounded events")
		}
		previous = event.Group
		initial, remaining := 0, 0
		switch event.Kind {
		case "planet":
			if event.Ground == nil || event.Defense != nil {
				return fail("ground event payload")
			}
			v := event.Ground
			initial, remaining = v.InitialForce, v.Force
			if remaining != 0 || get(old, 905, 93) != 2 || !named(old, 4053, "Route Haven") || get(old, 4053, 73) != 0 {
				return fail("neutral Route Haven event context")
			}
			extra = append(extra, fmt.Sprintf(" *** %d Xannor attacked the planet \"Route Haven\"", initial), " *** Xannor fighters destroyed!")
		case "defense":
			if event.Defense == nil || event.Ground != nil {
				return fail("defense event payload")
			}
			v := event.Defense
			initial, remaining = v.InitialForce, v.Force
			if get(old, 905, 85) != -2 || v.InitialDefenders < 1 || v.InitialDefenders > 100000 || v.Defenders < 0 || v.Defenders > v.InitialDefenders || (remaining == 0) == (v.Defenders == 0) {
				return fail("Mercenary before context/survivors")
			}
			if v.XDamage < initial-remaining || v.XDamage > initial+5000 || v.XDamage > initial-remaining+5000 || v.DefenderDamage < v.InitialDefenders-v.Defenders || v.DefenderDamage > v.InitialDefenders+5000 || v.DefenderDamage > v.InitialDefenders-v.Defenders+5000 {
				return fail("raw damage counters")
			}
			stats.Losses[1] += v.InitialDefenders - v.Defenders
			suffix := "Xannor ftrs dstrd)"
			if v.Defenders == 0 {
				suffix = "Plyr ftrs dstrd)"
			}
			extra = append(extra, fmt.Sprintf(" *** Mercenaries: lost %d, dstrd %d (%s", v.XDamage, v.DefenderDamage, suffix))
		default:
			return fail("unknown public event")
		}
		if initial < 1 || initial > 10000 || remaining < 0 || remaining > initial {
			return fail("bounded moving force")
		}
		stats.Losses[0] += initial - remaining
		if remaining == 0 {
			dead[event.Group] = true
		}
	}
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
	if a[0] != 10000 || (a[1] != 0 && a[1] != 37 && a[1] != 100000) || (a[2] != 0 && a[2] != 37) {
		return fail("retained initial faction inventory")
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
	news, board, e := formatAuxReports(in, stats.Scores[0], [3]bool{true, true, true}, nil)
	if e != nil {
		return fail(e.Error())
	}
	marker := "  -  Mercenary Report:\r\n"
	at := strings.Index(string(news), marker)
	if at < 0 {
		return fail("bootstrap news framing")
	}
	if len(extra) > 0 {
		news = []byte(string(news[:at]) + strings.Join(extra, "\r\n") + "\r\n" + string(news[at:]))
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
