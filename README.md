# Network & Security Monitor

A live network health dashboard and lightweight security event triage tool
for a UniFi-managed network — built against the network I manage day to day
at my warehouse job.

It does two things:

1. **Network health** — polls the UniFi Network Controller's official
   Integration API for device (switches, APs, gateways) and client status,
   and shows it on a live dashboard.
2. **Security triage** — receives firewall/IDS-IPS log events (via syslog or
   a webhook), scores them with a small set of transparent rules, and
   surfaces anything that looks worth a human's attention.

> Independent personal project. Not affiliated with or endorsed by Ubiquiti
> Inc. "UniFi" is a trademark of Ubiquiti Inc.

## Why

Most "network monitor" side projects ping a few hosts and call it done. This
one is scoped around the controller I actually operate, using Ubiquiti's
documented Integration API rather than reverse-engineered endpoints, so it's
real infrastructure work rather than a toy demo.

## Architecture

```
UniFi Controller (Integration API) --poll--> Flask app --> SQLite --> Dashboard (HTML/JS)
UniFi firewall/IDS syslog          --UDP-->  syslog listener --score--> SQLite --> Dashboard
External tooling                  --POST-->  /api/events/ingest (bearer token) --score--> SQLite
```

- `app/unifi_client.py` — thin client for the UniFi Network **Integration
  API** (API-key auth; no username/password is ever stored).
- `app/poller.py` — background thread that polls devices/clients on an
  interval and mirrors their state into SQLite.
- `app/syslog_listener.py` — a small UDP syslog receiver that parses UniFi's
  netfilter-style firewall log lines (`SRC=`, `DST=`, ...) plus IDS/IPS
  alert lines.
- `app/triage.py` — rule-based scoring for incoming security events. Every
  point added is a named rule (high-risk category, repeat offender within a
  time window, credential/brute-force keywords), so the "why" behind a score
  is always visible — no black-box model to trust blindly.
- `app/routes.py` — the dashboard page plus a small JSON API
  (`/api/status`, `/api/events`, `/api/events/ingest`).

## Setup

1. **Generate a UniFi API key** — in the UniFi OS console, under
   `Settings → Control Plane → Integrations → API Keys` (the exact location
   varies by controller/firmware version — look for "Integrations" or "API"
   under Settings).
2. Clone the repo and install dependencies:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
3. Fill in `.env`:
   - `UNIFI_HOST` — e.g. `https://192.168.1.1`
   - `UNIFI_API_KEY` — the key from step 1
   - `UNIFI_SITE` — your site ID (run `python scripts/list_sites.py` after
     setting the two values above to look it up — most controllers only
     have one site, `default`)
   - `INGEST_WEBHOOK_TOKEN` — a random string; required to use the webhook
     ingest endpoint from outside localhost
   - `UNIFI_VERIFY_SSL` defaults to `false` because most UniFi controllers
     use a self-signed certificate — set it to `true` if yours has a
     trusted one.
4. Run it:
   ```bash
   python run.py
   ```
   Then open `http://localhost:5000`.

### Feeding it security events

Point your UDM/USG's remote syslog target
(`Settings → System → Logging` in the UniFi OS console) at this host on
`SYSLOG_LISTEN_PORT` (default `5514`, UDP). Firewall block events and
IDS/IPS alerts will start showing up in the Security Events panel.

If your controller can't reach this host directly (e.g. it's on a separate
network from where this app runs), forward events to
`POST /api/events/ingest` instead:

```bash
curl -X POST http://localhost:5000/api/events/ingest \
  -H "Authorization: Bearer $INGEST_WEBHOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category": "ips_alert", "src_ip": "203.0.113.4", "message": "test alert"}'
```

## Security notes

- **UDP syslog has no built-in authentication** — anything on the same
  network segment as `SYSLOG_LISTEN_PORT` can send spoofed events. Restrict
  it at the network/firewall level to only the UniFi controller's IP, or
  prefer the `/api/events/ingest` webhook (which is token-authenticated)
  when the source can reach this host over HTTP instead.
- `UNIFI_VERIFY_SSL` defaults to `false` to work out of the box against a
  self-signed controller certificate — this trades away protection against
  a MITM on that connection. Set it to `true` (and give the controller a
  real certificate) for anything beyond a trusted local network.
- Change `FLASK_SECRET_KEY` from its default before using cookies/sessions
  for anything beyond local development.
- Dependencies are checked for known CVEs on every CI run (`pip-audit`) —
  see `.github/workflows/ci.yml`.

## Running tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Roadmap

- [ ] Persistent uptime history / charts per device
- [ ] Email or Slack alerting above a severity threshold
- [ ] Auth on the dashboard itself (currently assumes a trusted network)
- [ ] Multi-site support in one dashboard

## License

MIT — see [LICENSE](LICENSE).
