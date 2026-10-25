.PHONY: build test vet smoke
build:
	go build -o bin/yt ./cmd/yt
test:
	go test -race ./...
vet:
	go vet ./...
smoke: build
	python3 scripts/smoke.py
