# Honey_Pot_SPY

## Overview

Honey_Pot_SPY is an open-source Python project for setting up an interactive honeypot data collector and behavioral analysis engine. It collects network and user interaction signals, constructs session state machines, computes alert features, and exposes local analysis/visualization APIs for research and SOC proof-of-concept deployments.

## Goals

- Detect, log, and classify suspicious activity using honeypot interactions.
- Model attacker behavior as state transitions with timing and event context.
- Provide modular pipelines for ingestion, sessionization, anomaly scoring, and alert publication.
- Enable local evaluation and extendability for advanced ML/graph-based threat detection.

## Repository Structure

- `app.py` - Entry point and main API orchestration.
- `graph.py` - Graph construction and graph traversal utilities.
- `state_struct.py` - Finite-state machine definitions and transitions for attack session state modeling.
- `utils.py` - Utilities for logging, configuration, parsing, and helper abstractions.
- `requirements.txt` - Python dependencies for the project.

## Technical Explanation

### Input data and sources

Honey_Pot_SPY can ingest: 
- Raw connection metadata (IP, port, protocol, timestamps)
- Payload and command input sequences from compromised endpoints/honeypots
- Pre-labeled attack vectors (optional) for supervised evaluation

### State machine model

`state_struct.py` defines a deterministic state machine with:
- States representing high-level behavior phases (e.g., `INITIAL`, `AUTH_FAILED`, `SHELL`, `DATA_EXFILTRATION`, `TEARDOWN`).
- Transition rules triggered by event patterns.
- Timeouts and gap handling to split sessions on inactivity.

This FSM enables sequence-based classification and anomaly score weighting by state path.

### Graph model

`graph.py` builds a directed graph where:
- Nodes represent IP addresses, users, sessions, and resources accessed.
- Edges are events (connection attempt, command exec, file transfer) with weights such as frequency, byte volume, or similarity.
- Graph analytics can detect lateral movement and repeated C2 fingerprints.

### Processing flow (`app.py`)

1. Load config from environment or constants.
2. Ingest event stream (file, stdin, or network capture).
3. Normalize events via `utils` parsing.
4. Apply state_struct FSM on per-source session segments.
5. Compute metrics for edge weights in `graph` module.
6. Generate alerts and write structured output.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Run the main module:

```bash
python app.py --input data/events.json --output results/alerts.json
```

Supported options (likely code-driven; validate by inspecting `app.py`):
- `--input` (path to event dataset)
- `--output` (path to JSON/CSV alert output)
- `--mode` (`simulation`, `realtime`, `batch`)
- `--debug` (enable verbose logging)

## Extending functionality

1. Add additional event types in `utils.py` normalization (attack-specific protocols, new telemetry sources).
2. Expand case states in `state_struct.py` with domain-specific states and conditions.
3. Enhance `graph.py` with community detection, PageRank scoring, and time-aware weighting.
4. Add ML inference layer that uses path features and graph embeddings for predictive classification.

## Testing

- Use unit tests for each module (add test suite under `tests/` if absent).
- Validate transitions with synthetic session traces.
- Profile memory/latency for large event streams.

## Security Note

This project handles adversarial input and should not be exposed to production data without sanitization. Keep dependency versions updated and audit imported packages.

## License

MIT / Open-source-friendly (update as needed).
