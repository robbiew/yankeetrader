package qbmaint

import (
	"fmt"
	"strings"
	"time"
)

// AuxInputs keeps independently sampled native news and scoreboard clocks apart.
// Dates are exact ISO calendar dates. Exact native 24:00:00 is admitted without
// carrying the date, as in the qualified clock matrix.
type AuxInputs struct{ NewsDate, NewsClock, ScoreDate, ScoreClock string }

// ReplayInitialAux emits five DOS auxiliary files from original before files,
// an independently modeled final world and explicit clock inputs. Only the
// all-inactive, missing-NPC bootstrap scoreboard/news is admitted. No target,
// filesystem, host clock or general PRINT USING formatter is used.
func ReplayInitialAux(before map[string][]byte, world []byte, in AuxInputs) (map[string][]byte, error) {
	return replayInitialAux(before, world, in, nil)
}
func replayInitialAux(before map[string][]byte, world []byte, in AuxInputs, events []WandererEncounter) (map[string][]byte, error) {
	fail := func(s string) (map[string][]byte, error) { return nil, fmt.Errorf("initial auxiliary replay: %s", s) }
	if len(before) != 3 {
		return fail("exact three-file before inventory")
	}
	for _, n := range []string{"YTDATA.DAT", "YTNAME.DAT", "YTNEWS.DAT"} {
		if _, ok := before[n]; !ok {
			return fail("missing before file")
		}
	}
	old := before["YTDATA.DAT"]
	if len(old) != WorldRecords*RecordSize || len(world) != len(old) {
		return fail("default world extent")
	}
	read := func(b []byte, r, o int) [4]byte { a := (r-1)*RecordSize + o; return [4]byte(b[a : a+4]) }
	get := func(b []byte, r, o int) int {
		n, ok := integer(read(b, r, o))
		if !ok {
			return -999999
		}
		return n
	}
	for _, b := range [][]byte{old, world} {
		for o, n := range map[int]int{53: 51, 57: 3051, 61: 4051, 93: 4151} {
			if get(b, 1, o) != n {
				return fail("geometry")
			}
		}
		if get(b, 1, 41) != 11 || string(b[:11]) != "YTSCORE.ASC" {
			return fail("default scoreboard path")
		}
	}
	for r := 2; r <= 51; r++ {
		for o := 41; o < 137; o += 4 {
			if read(old, r, o)[3] != 0 {
				return fail("populated inactive before player")
			}
			want := 0
			if o == 109 {
				want = -1
			}
			if get(world, r, o) != want {
				return fail("modeled inactive rank/assets required")
			}
		}
	}
	for slot := 1; slot <= 100; slot++ {
		r := 4051 + slot
		if read(old, r, 85)[3] != 0 {
			return fail("existing before planet")
		}
		want := 0
		name := ""
		switch slot {
		case 1:
			want = 12
			name = "The Wanderer"
		case 99:
			want = 14
			name = "Mercenary Base"
		case 100:
			want = 8
			name = "Xannoron"
		}
		if get(world, r, 85) != want {
			return fail("initial planet activity")
		}
		if name != "" && string(world[(r-1)*137:(r-1)*137+len(name)]) != name {
			return fail("modeled NPC name")
		}
	}
	lost, err := retainedWandererLosses(world, events)
	if err != nil {
		return fail(err.Error())
	}
	for index, b := range [][]byte{old, world} {
		total := 0
		for s := 1; s <= 3000; s++ {
			force := get(b, 51+s, 81)
			if force < 0 || force > 10000 {
				return fail("bounded initial force")
			}
			if force > 0 && get(b, 51+s, 85) != -1 {
				return fail("non-Xannor deployment")
			}
			total += force
		}
		want := 10000
		if index == 1 {
			want -= lost
		}
		if total != want {
			return fail("initial NPC score total")
		}
	}
	news, board, e := formatAuxReports(in, 100*(10000-lost), [3]bool{true, true, true}, events)
	if e != nil {
		return fail(e.Error())
	}
	return map[string][]byte{"YTNAME.DAT": append([]byte{}, before["YTNAME.DAT"]...), "YTYNEWS.DAT": append([]byte{}, before["YTNEWS.DAT"]...), "YTRMSG.DAT": {}, "YTNEWS.DAT": news, "YTSCORE.ASC": board}, nil
}

// formatAuxReports is shared by the strict bootstrap and bounded evolved
// admissions. It owns no admission policy, filesystem, clock or oracle reads.
func formatAuxReports(in AuxInputs, score int, created [3]bool, events []WandererEncounter) ([]byte, []byte, error) {
	date := func(value string) (string, error) {
		d, e := time.Parse("2006-01-02", value)
		if e != nil || d.Year() < 2026 || d.Year() > 2028 {
			return "", fmt.Errorf("bounded source date")
		}
		return d.Format("01-02-2006"), nil
	}
	newsDate, e := date(in.NewsDate)
	if e != nil {
		return nil, nil, fmt.Errorf("news date")
	}
	scoreDate, e := date(in.ScoreDate)
	if e != nil {
		return nil, nil, fmt.Errorf("score date")
	}
	clock := func(s string) bool {
		if s == "24:00:00" {
			return true
		}
		if len(s) != 8 {
			return false
		}
		t, e := time.Parse("15:04:05", s)
		return e == nil && t.Format("15:04:05") == s
	}
	if !clock(in.NewsClock) || !clock(in.ScoreClock) {
		return nil, nil, fmt.Errorf("exact native clock")
	}
	// These literals and the fixed bootstrap PRINT USING row are source-qualified
	// against the immutable original executable by the portable exporter.
	news := []string{in.NewsClock + " " + newsDate + ": Maintenance Program Ran (Revision 03/14/94)"}
	if created[0] {
		news = append(news, "  -  The Wanderer is missing or has been destroyed!", "  -  The Wanderer regenerated with P.H.O.E.N.I.X. device!")
	}
	if created[1] {
		news = append(news, "  -  The Xannor have made a Planet!", "The Xannor home base now has a planet!")
	}
	news = append(news, "  -  Xannor report:", "Calculated Dynamic Xannor Regeneration is 0 fighters.")
	for _, event := range events {
		news = append(news, fmt.Sprintf(" *** %d Xannor attacked the planet \"The Wanderer\"", event.Inputs.Force), " *** Xannor fighters destroyed!")
	}
	news = append(news, "  -  Mercenary Report:")
	if created[2] {
		news = append(news, "  -  The Mercenaries have built a home base using a captured Genesis Device!")
	}
	text := fmt.Sprintf("%d", score)
	for i := len(text) - 3; i > 0; i -= 3 {
		text = text[:i] + "," + text[i:]
	}
	row := fmt.Sprintf("  %15s  %7s%%    %15s  %6s%%", text, "100.00", "0", "0.00")
	board := []string{"", "Y a n k e e   T r a d e r   S c o r e b o a r d", "", "Last updated at: " + scoreDate + " " + in.ScoreClock, "",
		"Rank  Rank%        Score        Team   Ports   Player", "==== ======= ================= ====== ======= ================================", "",
		"T e a m   R a n k i n g s", "", "Rank  Rank%        Score        Team   Team Name", "==== ======= ================= ====== ========================================", "",
		"N o n  -  H u m a n   P l a y e r s", "", "    The Xannor       Rank%     The Mercenaries   Rank%", "================== =========  ================= =======",
		row, ""}
	dos := func(lines []string) []byte { return []byte(strings.Join(lines, "\r\n") + "\r\n\x1a") }
	return dos(news), dos(board), nil
}
