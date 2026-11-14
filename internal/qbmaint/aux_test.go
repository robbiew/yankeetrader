package qbmaint

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"os"
	"testing"
)

type auxCase struct {
	Name       string
	Before     string            `json:"before_aux"`
	NewsDate   string            `json:"news_date"`
	NewsClock  string            `json:"news_clock"`
	ScoreDate  string            `json:"score_date"`
	ScoreClock string            `json:"score_clock"`
	Native     map[string]string `json:"native_files"`
}
type auxFixtureData struct {
	Format string
	Before map[string]map[string]string `json:"before_aux"`
	Cases  []auxCase
}

func auxFixture(t *testing.T) auxFixtureData {
	t.Helper()
	raw, e := os.ReadFile("testdata/initial_aux.json")
	if e != nil {
		t.Fatal(e)
	}
	var d auxFixtureData
	if e = json.Unmarshal(raw, &d); e != nil || d.Format != "qb-initial-aux-v1" || len(d.Cases) != 29 {
		t.Fatal("aux fixture", e)
	}
	return d
}
func composedWorld(t *testing.T, p fixture, x []xannoronCase, m []mobileCase, b []baseCase, c tailCase) []byte {
	t.Helper()
	world, in := tailPrefix(t, p, x, m, b, c)
	if _, e := ReplayInitialNPCTail(world, in); e != nil {
		t.Fatal(e)
	}
	var pc *fixtureCase
	for i := range p.Cases {
		if p.Cases[i].Name == c.Name {
			pc = &p.Cases[i]
			break
		}
	}
	if pc == nil {
		t.Fatal("port schedule")
	}
	ports, _, e := ReplayCleanPorts(unpack(t, p.Worlds[pc.BeforeSHA]), schedule(t, *pc))
	if e != nil {
		t.Fatal(e)
	}
	copy(world[PortStart:PortStart+len(ports)], ports)
	world, e = ReplayInactiveRanks(world, c.Day)
	if e != nil {
		t.Fatal(e)
	}
	return world
}
func auxPrefix(t *testing.T, d auxFixtureData, c auxCase) (map[string][]byte, []byte, AuxInputs) {
	t.Helper()
	p, x, m, b, tails := tailFixture(t)
	var tc *tailCase
	for i := range tails {
		if tails[i].Name == c.Name {
			tc = &tails[i]
			break
		}
	}
	if tc == nil {
		t.Fatal("tail predecessor")
	}
	world := composedWorld(t, p, x, m, b, *tc)
	var old []byte
	for _, pc := range p.Cases {
		if pc.Name == c.Name {
			old = unpack(t, p.Worlds[pc.BeforeSHA])
			break
		}
	}
	before := map[string][]byte{"YTDATA.DAT": old}
	for n, s := range d.Before[c.Before] {
		v, e := base64.StdEncoding.DecodeString(s)
		if e != nil {
			t.Fatal(e)
		}
		before[n] = v
	}
	return before, world, AuxInputs{NewsDate: c.NewsDate, NewsClock: c.NewsClock, ScoreDate: c.ScoreDate, ScoreClock: c.ScoreClock}
}
func TestInitialAuxSixNativeFiles(t *testing.T) {
	d := auxFixture(t)
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before, world, in := auxPrefix(t, d, c)
			saved := map[string][]byte{}
			for n, v := range before {
				saved[n] = append([]byte(nil), v...)
			}
			oldWorld := append([]byte(nil), world...)
			out, e := ReplayInitialAux(before, world, in)
			if e != nil {
				t.Fatal(e)
			}
			if len(out) != 5 || len(c.Native) != 6 {
				t.Fatal("exact six-file output inventory")
			}
			if digest(world) != c.Native["YTDATA.DAT"] {
				t.Fatal("whole Go world")
			}
			for n, v := range out {
				if digest(v) != c.Native[n] {
					t.Fatal("complete native file", n)
				}
				if n == "YTNEWS.DAT" || n == "YTSCORE.ASC" {
					if !bytes.HasSuffix(v, []byte{'\r', '\n', 26}) || bytes.Contains(bytes.ReplaceAll(v, []byte("\r\n"), nil), []byte{'\n'}) {
						t.Fatal("DOS CRLF/EOF")
					}
				}
			}
			for n, v := range before {
				if !bytes.Equal(v, saved[n]) {
					t.Fatal("mutated before file", n)
				}
			}
			if !bytes.Equal(world, oldWorld) {
				t.Fatal("mutated modeled world")
			}
			for _, n := range []string{"YTNAME.DAT", "YTYNEWS.DAT"} {
				if len(out[n]) > 0 {
					out[n][0] ^= 255
				}
			}
			for n, v := range before {
				if !bytes.Equal(v, saved[n]) {
					t.Fatal("output alias", n)
				}
			}
		})
	}
}
func TestInitialAuxAdmission(t *testing.T) {
	d := auxFixture(t)
	before, world, in := auxPrefix(t, d, d.Cases[0])
	changes := map[string]func(map[string][]byte, []byte, *AuxInputs){"missing": func(b map[string][]byte, _ []byte, _ *AuxInputs) { delete(b, "YTNEWS.DAT") }, "messages": func(b map[string][]byte, _ []byte, _ *AuxInputs) { b["YTRMSG.DAT"] = []byte{1} }, "path": func(b map[string][]byte, _ []byte, _ *AuxInputs) { b["YTDATA.DAT"][0] = 'X' }, "active": func(_ map[string][]byte, w []byte, _ *AuxInputs) { w[137+88] = 129 }, "assets": func(b map[string][]byte, _ []byte, _ *AuxInputs) { b["YTDATA.DAT"][137+44] = 129 }, "human force": func(_ map[string][]byte, w []byte, _ *AuxInputs) {
		hq, _ := integer([4]byte(w[117:121]))
		v := encode(2)
		copy(w[(50+hq)*137+85:], v[:])
	}, "date": func(_ map[string][]byte, _ []byte, i *AuxInputs) { i.NewsDate = "2026-02-30" }, "clock": func(_ map[string][]byte, _ []byte, i *AuxInputs) { i.ScoreClock = "24:00:01" }, "name": func(_ map[string][]byte, w []byte, _ *AuxInputs) { w[4051*137] = 'X' }}
	for n, f := range changes {
		t.Run(n, func(t *testing.T) {
			b := map[string][]byte{}
			for n, v := range before {
				b[n] = append([]byte(nil), v...)
			}
			w := append([]byte(nil), world...)
			i := in
			f(b, w, &i)
			saved := append([]byte(nil), w...)
			out, e := ReplayInitialAux(b, w, i)
			if e == nil || out != nil || !bytes.Equal(w, saved) {
				t.Fatal("invalid auxiliary input admitted/partial output")
			}
		})
	}
	if out, e := ReplayInitialAux(before, world[:2], in); e == nil || out != nil {
		t.Fatal("short world")
	}
}
func TestInitialAuxNative24HourNoDateCarry(t *testing.T) {
	d := auxFixture(t)
	b, w, in := auxPrefix(t, d, d.Cases[0])
	in.NewsDate = "2026-12-31"
	in.ScoreDate = "2027-01-01"
	in.NewsClock = "24:00:00"
	in.ScoreClock = "00:00:01"
	out, e := ReplayInitialAux(b, w, in)
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.HasPrefix(out["YTNEWS.DAT"], []byte("24:00:00 12-31-2026")) || !bytes.Contains(out["YTSCORE.ASC"], []byte("01-01-2027 00:00:01")) {
		t.Fatal("separate native sampled dates/clocks")
	}
}
