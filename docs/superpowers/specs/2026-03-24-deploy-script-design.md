# Deploy Script Design (Docker Compose v2)

Date: 2026-03-24
Owner: Codex (with user approval)

## Goal
Provide a single, repo-local bash script for CentOS 10 that offers one-command start/stop/logs for all services defined in `docker-compose.yml`, using Docker Compose v2 (`docker compose`).

## Scope
- Add `deploy.sh` at repository root.
- Commands:
  - `start`: `docker compose up -d`
  - `stop`: `docker compose down`
  - `logs`: `docker compose logs -f --tail=200`
  - `status`: `docker compose ps`
  - `help` (or no args): print usage
- Auto `cd` to the script directory before running commands.
- Validate `docker` and `docker compose` availability with friendly errors.

## Non-Goals
- No systemd integration.
- No Windows support in this script.
- No environment file management or compose overrides.

## Architecture
A single bash script with small functions per command and a dispatcher on `$1`.

## Data Flow
1. Entry: parse `$1` (or default to `help`).
2. Ensure script runs from repo root (by `cd` to script dir).
3. Check `docker` and `docker compose` commands are available.
4. Execute the selected subcommand.

## Error Handling
- Missing `docker`: exit non-zero with a clear message.
- Missing Compose v2: exit non-zero with a clear message.
- Unsupported subcommand: print help and exit non-zero.
- Runtime command failures: propagate exit code; hint to check logs.

## Testing Plan
- `./deploy.sh` prints usage and exits 0.
- `./deploy.sh start` brings up services (`docker compose ps` shows running).
- `./deploy.sh status` prints current status.
- `./deploy.sh logs` follows all service logs until Ctrl+C.
- `./deploy.sh stop` stops and removes containers.

## Rollout Notes
- Intended for CentOS 10 with Docker + Compose v2 installed.
- Uses the existing `docker-compose.yml` at repo root.