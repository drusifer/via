## Language conventions

### Python

| Concern | Convention |
|---|---|
| Manifest | `pyproject.toml` with a PEP 621 `[project]` table. Tool config (`[tool.pytest.ini_options]`, `[tool.ruff]`, ...) goes in the same file. |
| Environment | `.venv/` at the repo root. |
| Package manager | `uv` for new Python projects. Preserve an existing project's chosen manager unless migration is explicitly requested; keep `poetry`/`pdm`/`hatch` when already established. |
| Dev dependencies | `[dependency-groups].dev` for new uv projects; preserve the existing project's dependency layout. |
| Install | `uv sync` (creates `.venv` and installs locked dependencies). |
| CLI entry points | `[project.scripts]`, so `make install` puts the command in `.venv/bin/`. |
| Version pin | `requires-python` in the manifest; `.python-version` if a version manager is in use. |
| Lockfile | Commit `uv.lock`; refresh it with `uv lock` when dependencies change. |

Notes:
- Use `uv run <command>` for project commands so they run in the managed environment.
- A Debian/Ubuntu/Raspberry Pi OS system Python may reject global `pip install` (PEP 668).
  Use the project environment; do not override the system guard.
- Create the venv with `--system-site-packages` only when a dependency is realistically available
  only from the OS package manager (hardware bindings, some GUI/GPU stacks). Record which
  packages depend on that, because the project is then not reproducible from the manifest alone.
- `sudo` drops the environment: a target that needs root must call the venv interpreter by path
  (`sudo .venv/bin/python ...`), never `sudo python3`.

```make
UV := uv

install: ## Sync the project environment from pyproject.toml and uv.lock
	$(UV) sync

test: ## Run the test suite
	$(UV) run pytest $(ARGS)

distclean: clean ## Also remove the virtualenv
	rm -rf .venv
```

### JavaScript / TypeScript

| Concern | Convention |
|---|---|
| Manifest | `package.json`. Tasks live in its `scripts`; the Makefile calls those scripts rather than duplicating their commands. |
| Environment | `node_modules/` at the repo root. |
| Package manager | Whichever lockfile is present: `package-lock.json` → npm, `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `bun.lock`/`bun.lockb` → bun. If none, npm. Honour a `packageManager` field if set. |
| Dev dependencies | `devDependencies`. |
| Install | The lockfile-exact form: `npm ci`, `pnpm install --frozen-lockfile`, `yarn install --immutable`. Use plain `install` only to create the first lockfile. |
| CLI entry points | `bin` in `package.json`; run local tools with `npx`/`pnpm exec`, never a global install. |
| Version pin | `engines.node` in the manifest and `.nvmrc` (or `.node-version`). |
| Lockfile | Always committed. |

```make
install: ## Install dependencies exactly as locked
	npm ci

test: ## Run the test suite
	npm run test -- $(ARGS)

lint: ## Static checks
	npm run lint
```

### Go

| Concern | Convention |
|---|---|
| Manifest / lockfile | `go.mod` / `go.sum`, both committed. |
| Environment | The module cache is managed by the toolchain; nothing project-local to create. |
| Install | `go mod download` (and `go mod tidy` when the manifest is first written). |
| Tasks | `go test ./...`, `go vet ./...`, `gofmt -l .`, `go build ./...`. |
| Version pin | The `go` (and `toolchain`) directive in `go.mod`. |

### Rust

| Concern | Convention |
|---|---|
| Manifest / lockfile | `Cargo.toml` / `Cargo.lock` (commit the lockfile for binaries; for libraries follow the repo's existing choice). |
| Environment | `target/`, gitignored. |
| Install | `cargo fetch`. |
| Tasks | `cargo test`, `cargo clippy -- -D warnings`, `cargo fmt`, `cargo build --release`. |
| Version pin | `rust-toolchain.toml`. |

### Anything else

Answer five questions from the language's official documentation, then fill in the same table:
what is the manifest, is there a lockfile, where does a project-local environment live, what is
the canonical install command, and where is the runtime version pinned. If the ecosystem has
competing tools and the repo gives no hint, choose the one the language's own docs present first
and state that in the handoff.

