package door

import (
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/robbiew/yankeetrader/internal/game"
)

func (s Session) editorRead(prompt string) (string, error) {
	if !time.Now().Before(s.Deadline) {
		return "", errors.New("session time expired")
	}
	if _, err := s.Store.View(); err != nil {
		return "", err
	}
	if err := s.Terminal.Printf("%s", prompt); err != nil {
		return "", err
	}
	return s.readLiteralLine()
}
func editorLineValid(text string) bool {
	if len(text) > game.MaxRadioText || strings.TrimSpace(text) == "" {
		return false
	}
	for _, b := range []byte(text) {
		if b < 32 || b > 126 {
			return false
		}
	}
	return true
}
func (s Session) radioEditor() ([]string, error) {
	var lines []string
	entering := true
	resume := false
	if err := s.Terminal.Printf("Messages are limited to 20 lines of 74 ASCII characters. Blank ends entry.\r\n"); err != nil {
		return nil, err
	}
	for {
		if entering {
			if resume {
				suffix, err := s.editorRead(fmt.Sprintf("%2d: %s", len(lines), lines[len(lines)-1]))
				if err != nil {
					return nil, err
				}
				changed := lines[len(lines)-1] + suffix
				if !editorLineValid(changed) {
					if err := s.Terminal.Printf("Use 1-74 printable ASCII characters.\r\n"); err != nil {
						return nil, err
					}
					continue
				}
				lines[len(lines)-1] = changed
				resume = false
			}
			for len(lines) < game.MaxRadioLines {
				line, err := s.editorRead(fmt.Sprintf("%2d: ", len(lines)+1))
				if err != nil {
					return nil, err
				}
				if strings.TrimSpace(line) == "" {
					break
				}
				if !editorLineValid(line) {
					if err := s.Terminal.Printf("Use 1-74 printable ASCII characters.\r\n"); err != nil {
						return nil, err
					}
					continue
				}
				lines = append(lines, line)
			}
			if len(lines) == game.MaxRadioLines {
				if err := s.Terminal.Printf("Message full!\r\n"); err != nil {
					return nil, err
				}
			}
			if len(lines) == 0 {
				return nil, nil
			}
			entering = false
		}
		action, err := s.editorRead("[L] List [S] Send [A] Abort [C] Continue [E] Edit -=> ")
		if err != nil {
			return nil, err
		}
		switch strings.ToUpper(strings.TrimSpace(action)) {
		case "L":
			for i, line := range lines {
				if err := s.Terminal.Printf("%2d: %s\r\n", i+1, line); err != nil {
					return nil, err
				}
			}
		case "C":
			entering = true
			resume = true
		case "E":
			answer, err := s.editorRead(fmt.Sprintf("Edit Which line? (1 - %d) -=> ", len(lines)))
			if err != nil {
				return nil, err
			}
			n, err := strconv.Atoi(strings.TrimSpace(answer))
			if err != nil || n < 1 || n > len(lines) {
				if err := s.Terminal.Printf("INVALID LINE NUMBER!\r\n"); err != nil {
					return nil, err
				}
				continue
			}
			if err := s.Terminal.Printf("Line %d reads: %s\r\n", n, lines[n-1]); err != nil {
				return nil, err
			}
			old, err := s.editorRead("Replace what section? -=> ")
			if err != nil {
				return nil, err
			}
			if old == "" {
				continue
			}
			if !strings.Contains(lines[n-1], old) {
				if err := s.Terminal.Printf("Section NOT FOUND in line %d!\r\n", n); err != nil {
					return nil, err
				}
				continue
			}
			replacement, err := s.editorRead("Replace it with what? -=> ")
			if err != nil {
				return nil, err
			}
			changed := strings.Replace(lines[n-1], old, replacement, 1)
			if !editorLineValid(changed) {
				if err := s.Terminal.Printf("Edited line must contain 1-74 printable ASCII characters.\r\n"); err != nil {
					return nil, err
				}
				continue
			}
			if err := s.Terminal.Printf("Line %d now reads: %s\r\n", n, changed); err != nil {
				return nil, err
			}
			answer, err = s.editorRead("Is this OK? [Y/N]? -=> ")
			if err != nil {
				return nil, err
			}
			if strings.EqualFold(strings.TrimSpace(answer), "Y") {
				lines[n-1] = changed
				if err := s.Terminal.Printf("Change Saved!\r\n"); err != nil {
					return nil, err
				}
			}
		case "S":
			return lines, nil
		case "A":
			answer, err := s.editorRead("Are you sure? [y/N] ")
			if err != nil {
				return nil, err
			}
			if strings.EqualFold(strings.TrimSpace(answer), "Y") {
				return nil, nil
			}
		}
	}
}
