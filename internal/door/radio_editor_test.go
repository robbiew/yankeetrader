package door

import (
	"github.com/robbiew/yankeetrader/internal/game"
	"reflect"
	"strings"
	"testing"
)

func TestRadioEditorListContinueAndConfirmedFirstReplacement(t *testing.T) {
	term := &scripted{lines: []string{"FIRST", "alpha alpha", "", "L", "E", "2", "alpha", "BETA", "n", "E", "2", "alpha", "BETA", "y", "C", " plus", "", "S"}}
	s, _ := radioSession(t, term)
	lines, err := s.radioEditor()
	if err != nil || !reflect.DeepEqual(lines, []string{"FIRST", "BETA alpha plus"}) {
		t.Fatal(lines, err)
	}
	if !strings.Contains(term.output.String(), " 2: alpha alpha") || !strings.Contains(term.output.String(), "Change Saved!") {
		t.Fatal(term.output.String())
	}
}
func TestRadioEditorLimitsAbortAndInvalidCommands(t *testing.T) {
	term := &scripted{lines: []string{strings.Repeat("x", 75), "valid", "", "E", "0", "E", "1", "missing", "A", "n", "S"}}
	s, _ := radioSession(t, term)
	lines, err := s.radioEditor()
	if err != nil || !reflect.DeepEqual(lines, []string{"valid"}) {
		t.Fatal(lines, err)
	}
	term = &scripted{lines: []string{"valid", "", "A", "y"}}
	s, _ = radioSession(t, term)
	lines, err = s.radioEditor()
	if err != nil || len(lines) != 0 {
		t.Fatal(lines, err)
	}
}
func TestMultilineComposerDoesNotSendBeforeFreshFinalConfirmation(t *testing.T) {
	for _, action := range []string{"s", "a", "s;q"} {
		term := &scripted{lines: []string{"radio EDIT Enemy;y;discarded", "FIRST; literal/", "SECOND", "", "S", action, "q"}}
		s, st := radioSession(t, term)
		if err := s.Run(); err != nil {
			t.Fatal(err)
		}
		w, _ := st.View()
		want := 0
		if action == "s" {
			want = 2
		}
		if len(w.Radio) != want {
			t.Fatal(action, w.Radio)
		}
	}
}

func TestRadioEditorTwentyLineCapAndResume(t *testing.T) {
	input := make([]string, 20)
	for i := range input {
		input[i] = "line"
	}
	input = append(input, "C", "X", "S")
	term := &scripted{lines: input}
	s, _ := radioSession(t, term)
	lines, err := s.radioEditor()
	if err != nil || len(lines) != 20 || lines[19] != "lineX" || !strings.Contains(term.output.String(), "Message full!") {
		t.Fatal(lines, err)
	}
}
func TestInterruptedEditorDoesNotPublishDraft(t *testing.T) {
	term := &scripted{lines: []string{"radio EDIT ALL;y", "FIRST"}}
	s, st := radioSession(t, term)
	_ = s.Run()
	w, _ := st.View()
	if !strings.Contains(term.output.String(), " 2: ") || len(w.Radio) != 0 {
		t.Fatal("interrupted draft published", term.output.String())
	}
	for _, n := range w.News {
		if string(n.Kind) == "radio-broadcast" {
			t.Fatal("interrupted draft published news")
		}
	}
}
func TestEditAliasStillUsesSingleLineComposer(t *testing.T) {
	term := &scripted{lines: []string{"radio Edit;y", "one line", "s", "q"}}
	s, st := radioSession(t, term)
	if err := st.Update(func(w *game.World) error { w.Players[2].Alias = "Edit"; return nil }); err != nil {
		t.Fatal(err)
	}
	if err := s.Run(); err != nil {
		t.Fatal(err)
	}
	w, _ := st.View()
	if len(w.Radio) != 1 || w.Radio[0].Text != "one line" {
		t.Fatal(w.Radio)
	}
}
