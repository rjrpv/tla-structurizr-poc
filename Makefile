# Convenience targets for the RJR-267 workflow. The rules live in AGENTS.md.

PYTHON  ?= python3
TLC_JAR ?= tla2tools.jar
TLC_URL ?= https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar

.PHONY: install-hooks check test observe tla examples examples-py

## Install the pre-commit hook (keeps code/baseline.json in sync on commit).
install-hooks:
	git config core.hooksPath .githooks
	@echo "installed: git hooks now point at .githooks"

## Gate: fail if the committed baseline is out of sync with the code.
check:
	$(PYTHON) code/observe.py --check

## Run the test suite (invariants + state-space mirror + architecture).
test:
	cd code && $(PYTHON) -m pytest -q

## Print the structural observation (vs the committed baseline).
observe:
	$(PYTHON) code/observe.py

## Model-check the TLA+ spec (downloads TLC if the jar is missing).
tla: $(TLC_JAR)
	java -jar $(TLC_JAR) -workers auto tla/ReservationSystem

## Model-check all the canonical examples in examples/ (RJR-275).
examples: $(TLC_JAR)
	@for m in TrafficLight Counter Queue LeaderElection TokenRing Inventory KeyValueStore Consensus; do \
		echo "=== $$m ==="; \
		java -jar $(TLC_JAR) -workers auto -nowarning examples/$$m \
			| grep -E "Model checking completed|Error|Semantic errors|distinct states found"; \
	done

## Run the Python state-space mirror for the canonical examples (RJR-275).
## Anchors the code to the TLA+ models: invariant holds everywhere and the
## reachable state count matches TLC.
examples-py:
	$(PYTHON) -m pytest -q examples/tests

$(TLC_JAR):
	curl -fsSL -o $(TLC_JAR) $(TLC_URL)
