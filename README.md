# device-registry

Central server for scanner devices: the capstone application of the AWS Cloud & Application Deployment
Training. Scanner devices in the public network register here and send a heartbeat, so the server
knows which devices exist and which are online. The same repository is used from Day 2 to Day 7.

| Day | What is added |
|---|---|
| 2 | This starter: health check, device registration, heartbeat, device list, scanner simulator, tests, lint, CI workflow |
| 4 | Dockerfile and Compose file; runs as a container on EC2, device list on an EBS-backed directory |
| 5 | The simulator uploads scan data and logs to the landing S3 bucket |
| 6 | Device list in a database; dashboard VM shows device status |
| 7 | Lambda function that sorts uploads by city into the secure bucket; dashboard data; monitoring, runbook, final demo |

## Requirements

Python 3.11 or newer (FastAPI 0.165 needs at least 3.11). On Amazon Linux 2023:

```bash
sudo dnf install -y python3.11 python3.11-pip git
```

## Run it on Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If activation is blocked, run `Set-ExecutionPolicy -Scope Process RemoteSigned` in that window first.
In a second PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$body = '{"device_id":"scanner-007","city":"pune","owner":"site-team-a"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/devices -ContentType 'application/json' -Body $body
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/devices/scanner-007/heartbeat
Invoke-RestMethod http://127.0.0.1:8000/devices
```

## Run it on Linux (EC2 host, from Day 4)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/devices -H 'Content-Type: application/json' \
  -d '{"device_id":"scanner-007","city":"pune","owner":"site-team-a"}'
curl -s -X POST http://127.0.0.1:8000/devices/scanner-007/heartbeat
curl -s http://127.0.0.1:8000/devices
```

Interactive API documentation: `http://127.0.0.1:8000/docs`.

## The scanner simulator

`simulator/scanner_sim.py` plays one scanner device. It registers, sends a heartbeat before each
scan, and writes one JSON file per scan plus one log file. It uses the standard library only. With
the server running:

```powershell
python simulator/scanner_sim.py --device-id scanner-008 --city mumbai --scans 3
```

The files go to `outbox/`, named exactly as they will be named in the landing bucket from Day 5:

```text
outbox/mumbai/scanner-008/2026-11-24/scan-090507-01.json
outbox/mumbai/scanner-008/2026-11-24/log-090509.log
```

## Endpoints

| Method and path | Purpose | Success | Failure |
|---|---|---|---|
| `GET /health` | Liveness check | 200 `{"status":"ok",...}` | - |
| `POST /devices` | Register a device | 201 with `status` and `upload_prefix` | 422 with the broken rule; 409 if already registered |
| `POST /devices/{device_id}/heartbeat` | Record that the device is alive | 200 with `status: online` | 404 if not registered |
| `GET /devices` | List all devices with their status | 200 with a list | - |

Status of a device: `registered` (no heartbeat yet), `online` (last heartbeat at most
`HEARTBEAT_TIMEOUT_SECONDS` ago), `offline` (older than that).

Registration rules (`app/validation.py`): the device id has 3 to 40 lowercase letters, digits or `-`;
the city is in `ALLOWED_CITIES`; the owner has lowercase letters, digits or `-`. The upload prefix is
`<city>/<device_id>/`.

The starter keeps the device list in memory, so it is empty after a restart. That is fixed on Day 4.

## Checks (the same three that CI runs)

```bash
ruff check .
ruff format --check .
pytest -q
```

`.github/workflows/ci.yml` runs them on every pull request and on every push to `main`.

## Configuration

Environment variables only; see `.env.example`. Never commit `.env`, keys or tokens.

| Variable | Default | Meaning |
|---|---|---|
| `APP_ENV` | `local` | Shown by `/health` |
| `HEARTBEAT_TIMEOUT_SECONDS` | `120` | A device with an older heartbeat is `offline` |
| `ALLOWED_CITIES` | `pune,mumbai,delhi` | Cities a device may register for |

## Layout

```text
app/main.py               routes
app/registry.py           the device list and the status rule
app/validation.py         registration rules and upload-prefix naming
app/config.py             settings from environment variables
simulator/scanner_sim.py  simulated scanner device
tests/                    pytest tests
```
