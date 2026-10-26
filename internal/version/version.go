// Package version contains the application identity and release version.
package version

const (
	Name            = "Yankee Trader: The Resurrection"
	OriginalVersion = "3.6"
	Repository      = "https://github.com/robbiew/yankeetrader"
)

// Version is the current project's semantic version. Release builds may
// override it with -ldflags -X github.com/robbiew/yankeetrader/internal/version.Version=...
var Version = "0.1.0"

// String returns the concise application name and version for UI and CLI use.
func String() string {
	return Name + " " + Version
}
