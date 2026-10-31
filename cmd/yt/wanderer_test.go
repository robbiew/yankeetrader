package main

import (
	"bytes"
	"errors"
	"github.com/robbiew/yankeetrader/internal/game"
	"github.com/robbiew/yankeetrader/internal/store"
	"io"
	"strings"
	"testing"
)

type receiptWriter struct{ failure error }

func (w receiptWriter) Write(p []byte) (int, error) { return 0, w.failure }
func TestMaintenanceReceiptCommittedWarningAndPrivacy(t *testing.T) {
	receipt := game.MaintenanceReceipt{Ran: true, Wanderer: game.WandererResult{Status: "relocated", From: 1234, To: 2345, Generation: 3456, Destroyed: true}}
	var b bytes.Buffer
	warning := &store.DurabilityError{Err: errors.New("sync")}
	if err := printMaintenanceReceipt(&b, receipt, warning); !errors.Is(err, warning) || !strings.Contains(b.String(), "destroyed by later daily actions") || strings.Contains(b.String(), "1234") || strings.Contains(b.String(), "2345") || strings.Contains(b.String(), "3456") {
		t.Fatal(b.String(), err)
	}
	for _, failure := range []error{io.EOF, io.ErrClosedPipe, errors.New("write failure")} {
		if err := printMaintenanceReceipt(receiptWriter{failure}, receipt, warning); !errors.Is(err, warning) || !errors.Is(err, failure) {
			t.Fatal(err)
		}
	}
	b.Reset()
	abort := errors.New("aborted")
	if err := printMaintenanceReceipt(&b, receipt, abort); err != abort || b.Len() != 0 {
		t.Fatal("false saved receipt", b.String(), err)
	}
	b.Reset()
	if err := printMaintenanceReceipt(&b, game.MaintenanceReceipt{}, nil); err != nil || !strings.Contains(b.String(), "already current") {
		t.Fatal(b.String(), err)
	}
}
