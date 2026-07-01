---
name: render
description: Render CLI usage guide for InvestaCo. All Render operations must be backed by static config (render.yaml) or a repeatable Makefile target — never one-off CLI commands. Covers deploys, logs, blueprint validation, and env var management.
triggers: ["*render", "*devops deploy", "*devops infra", "*devops monitor", "render cli", "render deploy"]
requires: ["make", "bob-tools"]
---

One-line summary: All Render operations go through `make <target>` or `render.yaml` — never raw one-off CLI commands.

TLDR:
    Every `render` CLI invocation must live in a Makefile target or render.yaml — no ad-hoc commands.
    Use `make deploy` to deploy, `make logs` to tail logs, `make validate-infra` to validate render.yaml.
    Env vars have no CLI support in v2.20.0 — use `make dump-render-env` and `make push-key` (Python/requests scripts).
    render.yaml is the source of truth for service config; CLI is for operations (deploys, logs, sessions).

# Render CLI — InvestaCo

## Core Principle

> **All Render operations must be backed by static config (`render.yaml`) and/or a repeatable Makefile target.**

Never run a one-off `render` command that isn't captured somewhere reproducible. If you're about to type `render deploys create srv-xxx` at the shell, stop — add it to the Makefile first, then run `make deploy`.

**Why:** One-off CLI commands are invisible to the team, non-repeatable across environments, and break the declarative model. If it's worth doing once, it's worth automating.

---

## Installed Version

```
render v2.20.0
```

Upgrade: download from https://github.com/render-oss/cli/releases

---

## Make Targets (use these — not raw CLI)

| Target | What it does | Render CLI command underneath |
|--------|-------------|-------------------------------|
| `make deploy` | Run tests → git push → trigger deploy | `render deploys create <service-id>` |
| `make logs` | Tail live production logs | `render logs --resources <id> --tail` |
| `make validate-infra` | Validate render.yaml before applying | `render blueprints validate render.yaml` |
| `make dump-render-env` | Export current env vars to `.render-env-export.json` | Python/requests (CLI has no env-var support) |
| `make diff-env` | Diff local `.env` against last dump — shows CHANGED / LOCAL ONLY / RENDER ONLY | Python (no CLI equivalent) |
| `make push-key` | Push `FIELD_ENCRYPTION_KEY` from `.env` to Render | Python/requests (CLI has no env-var support) |

**Always use `make help` to see the current authoritative target list.**

---

## render.yaml — Static Config (source of truth)

`render.yaml` at the repo root is the declarative source of truth for service configuration. The CLI operates on what's already deployed; `render.yaml` defines what *should* be deployed.

```yaml
services:
  - type: web
    name: InvestaCo
    runtime: python
    plan: starter
    buildCommand: pip install .
    startCommand: gunicorn wsgi:app
    envVars:
      - key: FIELD_ENCRYPTION_KEY
        sync: false          # must be set manually via make push-key
      - key: FLASK_ENV
        value: production    # hardcoded — do not override in dashboard
      ...
```

**Rules:**
- Any service config change (plan, build command, start command) goes in `render.yaml` first, then `make validate-infra`, then `make deploy`
- `sync: false` env vars are managed by `make push-key` / `make dump-render-env`
- Never change service config in the Render dashboard without updating `render.yaml` to match

---

## CLI Command Reference

### Deploys

```bash
# Via make (preferred):
make deploy

# Direct (only if make target doesn't cover the case):
render deploys create <service-id> --output text --confirm
render deploys list <service-id> --output json
render deploys cancel <deploy-id>
```

### Logs

```bash
# Via make (preferred):
make logs

# Direct (for ad-hoc filtering not in a make target):
render logs --resources <service-id> --tail
render logs --resources <service-id> --level error --limit 200
render logs --resources <service-id> --status-code 500
render logs --resources <service-id> --start 2026-06-27T00:00:00Z
```

### Blueprint Validation

```bash
# Via make (preferred):
make validate-infra

# Direct:
render blueprints validate render.yaml
```

### Services

```bash
render services --output json                        # list all services
render services update <id> --plan pro --confirm     # update service plan
render ssh <service-id>                              # SSH into instance
render psql <database-id>                            # psql session
```

### Auth

```bash
render login     # browser OAuth — stores token locally
render whoami    # verify logged-in identity
render logout
```

---

## Environment Variables — CLI Gap

**The Render CLI v2.20.0 has no `env-vars` subcommand.** Use the Makefile targets instead:

```bash
make dump-render-env   # snapshot current Render env vars → .render-env-export.json
make push-key          # push FIELD_ENCRYPTION_KEY from .env to Render
```

Both targets require `RENDER_API_KEY` and `RENDER_SERVICE_ID` in `.env`.

Bootstrap sequence before any key change:
```
make dump-render-env → make diff-env → review output → make push-key → make deploy
```

`make diff-env` classifies every key as:
- `CHANGED` — value differs between local and Render (will be updated by push)
- `LOCAL ONLY` — in `.env` but not yet in Render (will be added)
- `LOCAL ONLY (ops)` — ops credentials (`RENDER_API_KEY`, `RENDER_SERVICE_ID`, `FLASK_ENV`) expected to be local-only
- `RENDER ONLY` — in Render but not in local `.env` (Render-managed, e.g. `DATABASE_URL`)
- `RENDER MANAGED` — injected by platform, never in `.env`
- `UNCHANGED` — matches, no action needed

---

## Adding a New Render Operation

When you need a new Render CLI operation:

1. **Add it to `Makefile.prj`** (real recipe) and `Makefile` `else` block (mkf stub) — see the `make` skill
2. **Use `RENDER_SERVICE_ID`** from `.env` rather than hardcoding service IDs
3. **Run `make validate-infra`** if the operation involves config changes to `render.yaml`
4. **Document it here** in the Make Targets table above

Never add a Render operation as a standalone script that isn't reachable via `make`.

---

## RENDER_SERVICE_ID Convention

Targets that need the service ID read it from `.env`:

```makefile
@SERVICE_ID=$$(grep '^RENDER_SERVICE_ID=' .env 2>/dev/null | cut -d= -f2); \
[ -n "$$SERVICE_ID" ] || { echo "error: RENDER_SERVICE_ID not set in .env"; exit 1; }; \
render <command> $$SERVICE_ID ...
```

`RENDER_SERVICE_ID` is not sensitive (it's a public identifier) but lives in `.env` for consistency with other Render credentials.
