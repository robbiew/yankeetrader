package door

import (
	"errors"
	"github.com/robbiew/yankeetrader/internal/store"
)

func (s Session) planetCreationReceipt(saved error, name string, classic bool) error {
	var committed *store.DurabilityError
	if saved != nil && !errors.As(saved, &committed) {
		return saved
	}
	var output error
	if classic {
		output = s.Terminal.Printf("\r\nPlanet \"%s\" created with Genesis Device!\r\n\r\nTo increase productivity on your new planet, spend credits [$] on it.\r\n", name)
	} else {
		output = s.Terminal.Printf("Planet created for 25000 credits. Use LAND to visit.\r\n")
	}
	// A receipt failure must not hide a committed replacement warning.
	return errors.Join(saved, output)
}
