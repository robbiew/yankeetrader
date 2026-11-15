// Package qbreplay adapts qualified research recipes to qbmaint. It does not
// import modern saves or select playable maintenance policy.
package qbreplay

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"reflect"
	"strings"

	"github.com/robbiew/yankeetrader/internal/qbmaint"
)

const Format = "qbmaint-replay-v1"
const OriginalMaintSHA = "8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6"
const MaxRecipeBytes = 2 << 20

var beforeNames = [...]string{"YTDATA.DAT", "YTNAME.DAT", "YTNEWS.DAT"}
var outputNames = [...]string{"YTDATA.DAT", "YTNAME.DAT", "YTNEWS.DAT", "YTYNEWS.DAT", "YTRMSG.DAT", "YTSCORE.ASC"}

type PortRecipe struct {
	Days         []int    `json:"days"`
	TimerMinutes []string `json:"timer_minutes"`
	Capped       *bool    `json:"capped"`
}
type AuxRecipe struct {
	NewsDate   string `json:"news_date"`
	NewsClock  string `json:"news_clock"`
	ScoreDate  string `json:"score_date"`
	ScoreClock string `json:"score_clock"`
}
type PhaseRecipe struct {
	Ports         PortRecipe `json:"ports"`
	WandererDay   int        `json:"wanderer_day"`
	XannoronDay   int        `json:"xannoron_day"`
	BaseDay       int        `json:"base_day"`
	FinalDay      int        `json:"final_day"`
	InitialState  *uint32    `json:"initial_state"`
	HelperOne     []string   `json:"helper_one"`
	HelperTwo     []string   `json:"helper_two"`
	XannoronTimer string     `json:"xannoron_timer"`
	Aux           AuxRecipe  `json:"aux"`
}
type Document struct {
	Format       string            `json:"format"`
	Profile      string            `json:"profile"`
	Name         string            `json:"name"`
	BeforeSHA256 map[string]string `json:"before_sha256"`
	SourceSHA256 map[string]string `json:"source_sha256"`
	Recipe       PhaseRecipe       `json:"recipe"`
}

// Decode rejects unknown, duplicate (including case aliases), missing and
// malformed fields. Raw SINGLEs are exactly eight lowercase hex digits.
func Decode(data []byte) (Document, qbmaint.InitialRecipe, error) {
	fail := func(e error) (Document, qbmaint.InitialRecipe, error) { return Document{}, qbmaint.InitialRecipe{}, e }
	if len(data) > MaxRecipeBytes {
		return fail(fmt.Errorf("recipe exceeds size limit"))
	}
	// encoding/json otherwise accepts duplicate object keys, silently replacing
	// hash/clock/profile values. Detect these before typed decoding.
	scan := json.NewDecoder(bytes.NewReader(data))
	if e := uniqueJSON(scan); e != nil {
		return fail(e)
	}
	if _, e := scan.Token(); e != io.EOF {
		return fail(fmt.Errorf("one JSON document required"))
	}
	if e := exactFields(data, reflect.TypeOf(Document{})); e != nil {
		return fail(e)
	}
	var d Document
	dec := json.NewDecoder(bytes.NewReader(data))
	dec.DisallowUnknownFields()
	if e := dec.Decode(&d); e != nil {
		return fail(e)
	}
	if d.Format != Format || (d.Profile != "initial" && d.Profile != "initial-wanderer") || !validName(d.Name) {
		return fail(fmt.Errorf("explicit supported format/profile/name required"))
	}
	if len(d.BeforeSHA256) != 3 {
		return fail(fmt.Errorf("exact three before hashes required"))
	}
	for _, n := range beforeNames {
		if !validHash(d.BeforeSHA256[n]) {
			return fail(fmt.Errorf("missing/invalid before hash: %s", n))
		}
	}
	if len(d.SourceSHA256) < 1 || len(d.SourceSHA256) > 256 || d.SourceSHA256["archive/dos-original/YTMAINT.EXE"] != OriginalMaintSHA {
		return fail(fmt.Errorf("immutable original maintenance source identity required"))
	}
	for n, h := range d.SourceSHA256 {
		if !sourceReference(n) || !validHash(h) {
			return fail(fmt.Errorf("invalid relative source path/hash: %s", n))
		}
	}
	p := d.Recipe
	if p.InitialState == nil || *p.InitialState > 0xffffff || p.Ports.Capped == nil || len(p.Ports.Days) != 1000 || len(p.Ports.TimerMinutes) != 1000 || len(p.HelperOne) < 41 || len(p.HelperOne) > 42 || len(p.HelperTwo) != 19 {
		return fail(fmt.Errorf("complete source day/state/helper inventory required"))
	}
	for _, v := range []int{p.WandererDay, p.XannoronDay, p.BaseDay, p.FinalDay} {
		if v < 1 || v > 732 {
			return fail(fmt.Errorf("phase day outside 1..732"))
		}
	}
	for _, v := range p.Ports.Days {
		if v < 1 || v > 732 {
			return fail(fmt.Errorf("port day outside 1..732"))
		}
	}
	if p.Aux.NewsDate == "" || p.Aux.ScoreDate == "" || p.Aux.NewsClock == "" || p.Aux.ScoreClock == "" {
		return fail(fmt.Errorf("separate sampled auxiliary clocks required"))
	}
	r := qbmaint.InitialRecipe{Ports: qbmaint.PortSchedule{Days: append([]int(nil), p.Ports.Days...), Capped: *p.Ports.Capped}, WandererDay: p.WandererDay, XannoronDay: p.XannoronDay, BaseDay: p.BaseDay, FinalDay: p.FinalDay, InitialState: *p.InitialState, Aux: qbmaint.AuxInputs{NewsDate: p.Aux.NewsDate, NewsClock: p.Aux.NewsClock, ScoreDate: p.Aux.ScoreDate, ScoreClock: p.Aux.ScoreClock}}
	for _, entry := range []struct {
		in  []string
		out *[][4]byte
	}{{p.Ports.TimerMinutes, &r.Ports.TimerMinutes}, {p.HelperOne, &r.HelperOne}, {p.HelperTwo, &r.HelperTwo}} {
		for _, s := range entry.in {
			v, e := rawSingle(s)
			if e != nil {
				return fail(e)
			}
			*entry.out = append(*entry.out, v)
		}
	}
	timer, e := rawSingle(p.XannoronTimer)
	if e != nil {
		return fail(e)
	}
	r.XannoronTimer = timer
	return d, r, nil
}
func validHash(s string) bool {
	if len(s) != 64 || s != strings.ToLower(s) {
		return false
	}
	_, e := hex.DecodeString(s)
	return e == nil
}
func safeRelative(s string) bool {
	if len(s) > 512 || !fs.ValidPath(s) || s == "." || strings.ContainsAny(s, "\\:") {
		return false
	}
	for _, c := range s {
		if c < 32 || c == 127 {
			return false
		}
	}
	return true
}
func rawSingle(s string) ([4]byte, error) {
	if len(s) != 8 || s != strings.ToLower(s) {
		return [4]byte{}, fmt.Errorf("raw SINGLE must be eight lowercase hex digits")
	}
	v, e := hex.DecodeString(s)
	if e != nil {
		return [4]byte{}, e
	}
	return [4]byte(v), nil
}
func uniqueJSON(d *json.Decoder) error { return uniqueJSONAt(d, 0) }
func uniqueJSONAt(d *json.Decoder, depth int) error {
	if depth > 16 {
		return fmt.Errorf("recipe JSON nesting exceeds schema limit")
	}
	t, e := d.Token()
	if e != nil {
		return e
	}
	delim, ok := t.(json.Delim)
	if !ok {
		return nil
	}
	switch delim {
	case '{':
		seen := map[string]bool{}
		for d.More() {
			k, e := d.Token()
			if e != nil {
				return e
			}
			s, ok := k.(string)
			if !ok {
				return fmt.Errorf("object key required")
			}
			key := strings.ToLower(s)
			if seen[key] {
				return fmt.Errorf("duplicate JSON field: %s", s)
			}
			seen[key] = true
			if e = uniqueJSONAt(d, depth+1); e != nil {
				return e
			}
		}
	case '[':
		for d.More() {
			if e = uniqueJSONAt(d, depth+1); e != nil {
				return e
			}
		}
	default:
		return fmt.Errorf("unexpected JSON delimiter")
	}
	_, e = d.Token()
	return e
}

// All v1 schema fields are mandatory and canonically spelled. In particular,
// null/missing zero-valued clocks or state cannot become implicit defaults.
func exactFields(data []byte, t reflect.Type) error {
	if bytes.Equal(bytes.TrimSpace(data), []byte("null")) {
		return fmt.Errorf("null recipe values are not supported")
	}
	for t.Kind() == reflect.Ptr {
		t = t.Elem()
	}
	switch t.Kind() {
	case reflect.Struct:
		var fields map[string]json.RawMessage
		if e := json.Unmarshal(data, &fields); e != nil {
			return e
		}
		if len(fields) != t.NumField() {
			return fmt.Errorf("complete exact recipe fields required")
		}
		for i := 0; i < t.NumField(); i++ {
			f := t.Field(i)
			name := f.Tag.Get("json")
			value, ok := fields[name]
			if !ok {
				return fmt.Errorf("missing/case-mismatched field: %s", name)
			}
			if e := exactFields(value, f.Type); e != nil {
				return fmt.Errorf("%s: %w", name, e)
			}
		}
	case reflect.Slice:
		var values []json.RawMessage
		if e := json.Unmarshal(data, &values); e != nil {
			return e
		}
		for _, v := range values {
			if e := exactFields(v, t.Elem()); e != nil {
				return e
			}
		}
	case reflect.Map:
		var values map[string]json.RawMessage
		if e := json.Unmarshal(data, &values); e != nil {
			return e
		}
		for _, v := range values {
			if e := exactFields(v, t.Elem()); e != nil {
				return e
			}
		}
	}
	return nil
}

func validName(s string) bool {
	if len(s) < 1 || len(s) > 128 {
		return false
	}
	for _, c := range s {
		if !(c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9' || strings.ContainsRune("._/-", c)) {
			return false
		}
	}
	return true
}

// v1 binds model/acquisition source references, never native after files or
// expected-output oracles disguised as additional file inputs.
func sourceReference(s string) bool {
	if !safeRelative(s) {
		return false
	}
	return s == "archive/dos-original/YTMAINT.EXE" || s == "research/yt-maint/calendar-pins.json" || s == "research/yt-maint/clock-matrix-pins.json" || (strings.HasPrefix(s, "scripts/") && strings.HasSuffix(s, ".py"))
}
