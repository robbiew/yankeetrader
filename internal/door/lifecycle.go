package door

func (s Session) replacementNotice(id int) error {
	w, err := s.Store.View()
	if err != nil {
		return err
	}
	return s.Terminal.Printf("Your replacement ship has been built. Remaining turns: %d.\r\n", w.Players[id].Turns)
}
