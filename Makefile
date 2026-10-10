# Recall Radar task runner. Owner: D. Targets call owner modules; owners request target
# changes via docs/handoffs. Every recipe line is what CI or a gate runs — keep them honest.
SHELL := /bin/bash
.DEFAULT_GOAL := help
export RR_DATA_DIR ?= data
export RR_RAW_DIR ?= $(RR_DATA_DIR)/raw
RR_API_PORT ?= 8000
PY := uv run python
DB := $(RR_DATA_DIR)/recall_radar.duckdb
SCOPE ?= full
PERIOD ?= development

.PHONY: help setup whoami contracts contracts-check fetch verify-snapshot ingest investigations \
        detect match evaluate tune export gate1 pipeline lint test test-real check claims serve \
        serve-fixture web-build e2e e2e-install integration repro submission deploy vm-setup \
        sync-data rollback outage-check

help: ## list targets
	@grep -E '^[a-z0-9-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-16s %s\n",$$1,$$2}'

setup: ## install locked Python deps (+ web deps once web/ exists)
	uv sync --locked
	@if [ -f web/package-lock.json ]; then npm --prefix web ci; else echo "web/ not scaffolded yet (C0)"; fi

whoami: ## branch, HEAD, contract version, config hash (paste into handoffs)
	@echo "branch=$$(git branch --show-current) head=$$(git rev-parse --short HEAD) contract=$$($(PY) -c 'from recall_radar.contracts import CONTRACT_VERSION as v; print(v)') config=$$($(PY) -m recall_radar.method.config hash)"

contracts: ## regenerate JSON schema + TS types from recall_radar/contracts.py
	$(PY) scripts/export_contracts.py
	@if [ -d web/node_modules ]; then npm --prefix web run gen:contracts; else echo "skipped TS types: run 'npm --prefix web ci' first"; fi

contracts-check: contracts ## fail if generated contract files are stale
	git diff --exit-code -- contracts/schema web/src/contracts.gen.ts

fetch: ## download NHTSA sources into $RR_RAW_DIR (SET=gate1|all)
	bash scripts/fetch_sources.sh $(or $(SET),all)

verify-snapshot: ## A: compare $RR_RAW_DIR with snapshots/SNAPSHOT.lock.json
	$(PY) -m recall_radar.data.snapshot verify --raw "$(RR_RAW_DIR)"

ingest: ## A: parse, clean, dedupe, redact complaints (SCOPE=gate1|full)
	$(PY) -m recall_radar.data.ingest --config config.yaml --db "$(DB)" --scope $(SCOPE)

investigations: ## A: INV + RCL parsing and investigation families
	$(PY) -m recall_radar.data.investigations --config config.yaml --db "$(DB)"

detect: ## B: group_month, scores, alert episodes (SCOPE=gate1|full)
	$(PY) -m recall_radar.method.detect --config config.yaml --db "$(DB)" --scope $(SCOPE)

match: ## B: tier 1-2 matching (+ tier-3 labels from review/)
	$(PY) -m recall_radar.method.match --config config.yaml --db "$(DB)" --scope $(SCOPE)

evaluate: ## B: metrics for PERIOD=development|held_out (held_out refuses without freeze-v1)
	$(PY) -m recall_radar.method.evaluate --config config.yaml --db "$(DB)" --period $(PERIOD) --scope $(SCOPE)

tune: ## B: development-only threshold grid (SCOPE=gate1|full); writes exports/tuning_development*.csv
	$(PY) -m recall_radar.method.tune --config config.yaml --db "$(DB)" --scope $(SCOPE)

export: ## B: write exports/ and exports/demo/ from the evaluated DB
	$(PY) -m recall_radar.method.export --config config.yaml --db "$(DB)"

gate1: ## bounded feasibility run: 2015-2019 complaints + INV + RCL, families 2017-2019
	$(MAKE) ingest SCOPE=gate1
	$(MAKE) investigations
	$(MAKE) detect SCOPE=gate1
	$(MAKE) match SCOPE=gate1
	$(MAKE) evaluate SCOPE=gate1 PERIOD=development

pipeline: ## full run; held_out only if tag freeze-v1 exists
	$(MAKE) ingest investigations detect match SCOPE=full
	$(MAKE) evaluate SCOPE=full PERIOD=development
	@if git rev-parse -q --verify refs/tags/freeze-v1 >/dev/null; then $(MAKE) evaluate SCOPE=full PERIOD=held_out; else echo "held_out sealed: no freeze-v1 tag"; fi
	$(MAKE) export

lint: ## ruff
	uv run ruff check .

test: lint ## CI-equivalent: python tests (no real data), web tests, secrets + claims checks
	uv run pytest
	@if [ -f web/package-lock.json ]; then npm --prefix web run typecheck && npm --prefix web run test; fi
	$(PY) scripts/check_secrets.py
	$(MAKE) --no-print-directory claims

test-real: ## tests that need the local snapshot (marker real_data)
	uv run pytest -m real_data

claims: ## D: banned words + placeholder grammar + no hand-typed numbers in submission/ and README
	$(PY) scripts/check_claims.py
	$(PY) scripts/fill_numbers.py --check

check: contracts-check test ## everything CI runs, plus the ownership check for this branch
	$(PY) scripts/check_ownership.py

web-build: ## C: production build into web/dist
	npm --prefix web run build

serve: ## offline demo: API + built web on localhost, cached data, no outbound calls
	@test -d web/dist || npm --prefix web run build
	RR_MODE=cached $(PY) -m uvicorn recall_radar.api.main:app --host 127.0.0.1 --port $(RR_API_PORT)

serve-fixture: ## same server, but every endpoint returns contracts/fixtures/api/*
	RR_MODE=fixture $(PY) -m uvicorn recall_radar.api.main:app --host 127.0.0.1 --port $(RR_API_PORT)

e2e: ## D: Playwright smoke against BASE_URL (default local serve)
	BASE_URL=$(or $(BASE_URL),http://127.0.0.1:$(RR_API_PORT)) npm --prefix web run e2e

e2e-install: ## D: one-time Playwright Chromium download for make e2e
	npm --prefix web exec -- playwright install chromium

integration: ## D: live API conformance + displayed=exported vs RR_BASE_URL (RR_RELEASE=1 at gates)
	RR_BASE_URL=$(or $(RR_BASE_URL),http://127.0.0.1:$(RR_API_PORT)) uv run pytest tests/integration -m real_data

repro: ## B/D: clean-clone rerun of HEAD; compares exports with committed exports/demo
	bash scripts/repro.sh

submission: ## D: fill placeholders in submission/*.md from exports/demo/results.csv -> submission/out/
	$(PY) scripts/fill_numbers.py $(if $(CUT),--cut-unmeasured)

deploy: ## D: release REF (default HEAD) to the VM, MODE=cached|fixture; asks before running
	bash deploy/deploy.sh $(or $(REF),HEAD) --mode $(or $(MODE),cached)

vm-setup: ## D: one-time VM preparation (Caddy, uv, user rr, systemd unit, ufw); asks first
	bash deploy/vm_setup.sh

sync-data: ## D: upload the DuckDB file (default $RR_DATA_DIR/recall_radar.duckdb) to the VM (D5, <= 500 MB); asks first
	bash deploy/sync_data.sh "$(DB)"

rollback: ## D: VM back to the previous release (or REF=<sha prefix>); asks first
	bash deploy/rollback.sh $(REF)

outage-check: ## D: VM serves every screen with outbound traffic blocked (RELEASE=1 at gates)
	bash deploy/outage_check.sh $(if $(RELEASE),--release)
