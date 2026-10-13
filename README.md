# Long-Term Episodic Vector Memory

A small, local vector-memory tool for storing user-supplied numeric embeddings and retrieving episodes by **exact cosine similarity**. The repository also retains an independent, illustrative three-worker audit pipeline.

**Repository:** https://github.com/abusuraihsakhri/long-term-episodic-vector-db

## What works

- **Browser app:** add, replace, search, delete, import, and export episodes. Data persists between browser sessions in local storage.
- **Python store:** persist vectors in a versioned JSON file, search them using exact cosine similarity, and manage episodes with CLI commands.
- **Legacy audit demonstrator:** run threshold-based three-worker evaluations in Python, CLI, CSV batches, or the development FastAPI server.
- **Tests:** Python unit tests across 3.10–3.12, browser logic tests with Node.js, and an installable Python wheel.

The user supplies embeddings as numeric arrays. No embedding model, HNSW index, approximate nearest-neighbor graph, cloud database, model-provider integration, temporal decay, or clustering algorithm is implemented. Legacy enrichment modules are threshold-reporting examples rather than production implementations of the named algorithms.

## Browser application

Serve this repository locally (ES modules may not load via `file://`):

```bash
python -m http.server 8080
```

Open **http://localhost:8080/** (redirects to `web/`). GitHub Pages can serve the same static files from the `master` branch's repository root if Pages is configured for that source.

Enter a unique ID, descriptive text, and an embedding such as `[1, 0, 0]`. Add more episodes with the same vector dimension and search with another vector. Results are sorted by cosine similarity, highest first. Use **Export JSON** for a backup before clearing browser storage or importing another collection.

The browser implementation is plain JavaScript; Pyodide/PyScript is **not required**. It does not communicate with the Python service.

## Python CLI

Python **3.10+** is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[api,test]'

long-term-episodic-vector-db memory-put --id episode-1 --vector '[1,0,0]' --text "Example episode"
long-term-episodic-vector-db memory-put --id episode-2 --vector '[0,1,0]' --text "Another episode"
long-term-episodic-vector-db memory-search --vector '[0.9,0.1,0]' --top-k 2
long-term-episodic-vector-db memory-list
long-term-episodic-vector-db memory-delete --id episode-1
```

By default, Python stores the collection in `episodes.json` in the current directory. Set `EPISODIC_STORE_PATH` or use `--db PATH` on each command to choose another location. Metadata can be supplied with `memory-put --metadata '{"session":"sample"}'`. Duplicate IDs are replaced. Vectors must be nonzero, finite, and all have the same dimensionality (1–4096). Results support `--min-similarity` between -1 and 1.

### Legacy audit demonstrator

```bash
python cli.py audit --task-id T1 --target SAMPLE-1 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
python cli.py batch -i sample.csv -o results.csv
python cli.py verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

The development service has `/health`, `/metrics`, `/api/audit`, `/api/chat`, and `/api/audit/logs` endpoints. `/metrics` returns JSON rather than Prometheus text. The `chat` endpoint uses a deterministic mock; it does not perform model inference.

The numerical thresholds used in the audit demonstration are **illustrative, not clinically validated**. Do not use this pipeline to make clinical decisions.

### Docker

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

The Compose server binds to `127.0.0.1:8000` by default. The API is not authenticated; do not expose it to the public internet without implementing access controls. Docker storage and in-memory audit history are not durable across container replacement unless separate persistent storage is configured.

## Privacy and security limitations

The static application makes no network requests for vector data, but stores it **unencrypted in browser local storage** under the current site origin. Python stores vectors in a local JSON file; treat exported JSON and local files as sensitive if their contents are sensitive. **Do not enter PHI, secrets, or patient identifiers** into the demo.

The legacy audit pipeline uses simple regular expressions to flag *some* identifier patterns; this is **not** comprehensive PHI detection, HIPAA Safe Harbor de-identification, or an assurance that protected data cannot leave the system. Its HMAC-SHA256 chain detects modification of retained in-memory entries when the key is retained, but is not a durable or externally anchored audit log. The mock LLM provider performs no real verification.

For production use, add authentication, authorization, storage security, retention policies, logging controls, and task-specific validation.

## Tests

```bash
python -m pytest -q
node --check web/app.mjs
node --test web/test-app.mjs
python -m pip check
```

Browser support: current Chromium, Firefox, and Safari versions supporting ES modules and local storage. The static app has no build step or external JavaScript dependencies. For large collections, a linear scan may become slow; concurrent processes should not share the same Python JSON file.

## License

MIT. See [LICENSE](LICENSE).
