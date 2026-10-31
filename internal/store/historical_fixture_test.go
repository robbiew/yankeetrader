package store

import "encoding/json"

// Historical fixtures omit fields introduced after their declared save version.
// This leaves the in-memory expected current world unchanged for comparisons.
func marshalHistoricalWorld(v any) ([]byte, error) {
	raw, err := json.Marshal(v)
	if err != nil {
		return nil, err
	}
	var world map[string]json.RawMessage
	if err = json.Unmarshal(raw, &world); err != nil {
		return nil, err
	}
	var version int
	_ = json.Unmarshal(world["Version"], &version)
	if version >= 24 {
		return raw, nil
	}
	delete(world, "NextPlanetGeneration")
	var planets map[string]map[string]json.RawMessage
	if err = json.Unmarshal(world["Planets"], &planets); err != nil {
		return nil, err
	}
	for _, p := range planets {
		delete(p, "Generation")
	}
	world["Planets"], err = json.Marshal(planets)
	if err != nil {
		return nil, err
	}
	return json.Marshal(world)
}
