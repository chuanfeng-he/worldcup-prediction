.PHONY: test generate serve run docker clean

test:
	python3 -m pytest -q tests

generate:
	python3 -m wcmodel.cli generate --sims 5000 --seed 2026

serve:
	python3 -m wcmodel.cli serve --host 127.0.0.1 --port 8080

run: generate serve

docker:
	docker compose up --build

clean:
	rm -rf public/data public/index.html public/assets .pytest_cache
