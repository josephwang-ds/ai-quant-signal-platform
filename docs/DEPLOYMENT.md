# Scheduled deployment

The public HTML bundle is deployed at <https://lens.josephjwang.com>. Production
deployments now run non-interactively from the Vultr worker with an explicitly
project-scoped Vercel token.

A low-cost Vultr worker is provisioned in Tokyo with Ubuntu 24.04, 1 vCPU, 1 GB RAM,
25 GB SSD, and the image-provided 2.3 GiB swap. The code, core build artifacts, and
roughly 336 MB accession/price caches are installed under `/opt/company-lens`. A live
Finnhub AAPL smoke build produced two company headlines plus one market headline; a
full 193-page build and production deploy also completed from the worker. SSH listens
on port 443 as a fallback. The root-only server secret file and weekday systemd timer
are installed and active.

## Recommended shape

The planned target uses a prepaid Vultr instance as the stateful refresh worker and
Vercel as the public static frontend. No browser request would need to reach Vultr.

```text
systemd timer on Vultr
        │
        ├── refresh mutable SEC submission heads
        ├── download only unseen accession documents
        ├── refresh configured SEC Company Facts fundamentals
        ├── refresh daily market histories
        ├── rebuild 193 static company pages
        ├── package public HTML only (no snapshot JSON/cache)
        └── Vercel CLI deploys prebuilt output → Vercel CDN/domain
```

The full local page directory is about 97 MB because it includes 58 MB of JSON build
artifacts. The Vercel bundle publishes only the 195 HTML files, currently about
42.4 MB. The low-cost worker runs one task at a time and now has the roughly 336 MB
accession and price caches needed for incremental refreshes. The first full page build
took about five minutes, peaked near 560 MB resident memory, and briefly used about
330 MB of swap. That is acceptable for an overnight bonus project; upgrade only if
future runtimes become operationally inconvenient.

## One-time Vultr setup

The paths below match the checked-in service templates.

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin company-lens
sudo mkdir -p /opt/company-lens
sudo chown company-lens:company-lens /opt/company-lens
sudo -u company-lens git clone YOUR_REPOSITORY_URL /opt/company-lens
cd /opt/company-lens
sudo -u company-lens python3.12 -m venv .venv
sudo -u company-lens .venv/bin/pip install -e '.[dev]'
sudo npm install --global vercel
```

Copy the existing local caches for the first deployment. This avoids replaying the
entire SEC history on the server:

```bash
rsync -av data/build data/cache USER@SERVER:/tmp/company-lens-data/
sudo rsync -av /tmp/company-lens-data/ /opt/company-lens/data/
sudo chown -R company-lens:company-lens /opt/company-lens/data
```

Create the worker secret file. `EDGAR_USER_AGENT` must contain the real name and
email that the SEC fair-access policy asks clients to send. Leave Vercel deployment
disabled until the first manual preview succeeds:

```bash
sudo cp ops/company-lens.env.example /etc/company-lens.env
sudo chmod 600 /etc/company-lens.env
sudoedit /etc/company-lens.env
```

Add a Finnhub key only if live headline context is enabled:

```dotenv
FINNHUB_API_KEY="replace-with-finnhub-key"
COMPANY_LENS_HEADLINE_INDEX="/opt/company-lens/data/build/headlines.json"
COMPANY_LENS_FUNDAMENTALS_TICKERS="AAPL"
```

The scheduled worker queries the current local universe rather than a hard-coded
three-ticker list. It requests company-news metadata once per ticker, waits between
requests, adds a bounded global-market set, keeps at most five cached rows per ticker
for fourteen days, and sends the API key in a request header. The public company page
still shows at most three exact-ticker/global-market rows. Review the vendor terms for
the final hosting context before enabling a public production refresh.

## Create and test the Vercel frontend

Build the public bundle on Vultr:

```bash
cd /opt/company-lens
sudo -u company-lens env PYTHONPATH=src .venv/bin/python scripts/build_vercel_output.py
du -sh data/build/vercel_frontend/.vercel/output/static
```

Create a Vercel access token in the Vercel dashboard. For the first interactive
setup, log in and link the generated bundle to a new or existing `company-lens`
project:

```bash
sudo -u company-lens vercel login
sudo -u company-lens vercel link --cwd data/build/vercel_frontend
sudo -u company-lens vercel deploy \
  --cwd data/build/vercel_frontend --prebuilt --archive=tgz
```

Open the preview URL and verify `index.html`, one normal ticker, one single-letter
ticker, and the 404 page. Then deploy production:

```bash
sudo -u company-lens vercel deploy \
  --cwd data/build/vercel_frontend --prebuilt --archive=tgz --prod
```

In Vercel **Project → Settings → General**, note the Project ID; note the Team/User
ID for the owning scope. Put those values and the token into `/etc/company-lens.env`:

```dotenv
VERCEL_DEPLOY_ENABLED="1"
VERCEL_TOKEN="replace-with-server-token"
VERCEL_ORG_ID="team_or_user_id"
VERCEL_PROJECT_ID="prj_project_id"
```

The environment file is mode `600`; do not commit these values. The checked-in
deploy script requires all three variables and uses a compressed prebuilt deployment.
It lets the Vercel CLI read `VERCEL_TOKEN` from the environment instead of placing the
credential in the process command line. The hardened service directs CLI home and
cache writes into private paths under `/opt/company-lens/data` and disables telemetry.
For non-interactive CLI runs, Vercel recommends `VERCEL_ORG_ID` and
`VERCEL_PROJECT_ID` so project linking is not required.
The service stores any Vercel CLI state under `/opt/company-lens/data/vercel-cli`,
because the hardened systemd unit does not expose the worker user's home directory.

`VERCEL_PROJECT_ID` must be the project that serves the public site. That is
**`company-lens-josephjwang`**, carrying `https://lens.josephjwang.com` and
`https://company-lens-josephjwang.vercel.app`. It is the only one; a second
project, `company-lens-demo`, existed until 2026-08-27 and was retired precisely
because two of them is an unstable arrangement — deploying to one leaves the
other serving whatever it last received, and both report success while the two
public URLs drift apart. A stale ID reintroduces that failure, which is why the
ID is worth re-checking rather than copied forward.

## Ask AI provider keys (Vercel, not Vultr)

Live Q&A is a Vercel serverless function. It discovers providers only from API keys
present in that project's environment. An empty environment returns `models: []` and
the company page labels Q&A as not configured; it does not treat that as a network
failure.

Add these as sensitive Production variables on the linked Vercel project. Never put
them in Git, generated HTML, `/etc/company-lens.env` command lines, or browser
JavaScript:

```dotenv
OPENAI_API_KEY="replace-with-openai-key"
COMPANY_LENS_OPENAI_MODEL="replace-with-a-currently-valid-openai-model"
COMPANY_LENS_ASK_ORIGIN="https://lens.josephjwang.com"
COMPANY_LENS_ASK_DAILY_BUDGET="300"
COMPANY_LENS_ASK_KV_REST_URL="replace-with-a-redis-rest-endpoint"
COMPANY_LENS_ASK_KV_REST_TOKEN="replace-with-that-endpoint-s-token"
```

### What actually bounds the spend

The endpoint is unauthenticated and five paid provider keys sit behind it, so it
is worth being precise about which control does what.

`COMPANY_LENS_ASK_ORIGIN` compares the `Origin` header to a string. A browser
sets that header honestly; `curl` sets it to whatever you like. It keeps the
demo from being embedded in someone else's page and it is not a spending control.

`COMPANY_LENS_ASK_DAILY_BUDGET` is the ceiling that matters: a count of paid
calls per UTC day for the whole function, checked before the per-IP window and
before any provider is contacted. Exhausting it returns
`429 daily_budget_exhausted` and the static evidence on the page stays readable.

**Both counters are only global if the KV variables are set.** Without them the
counts live in one serverless instance's memory: they reset on every cold start,
and concurrent instances each keep their own, so the effective allowance is the
configured limit multiplied by however many instances are live. That is a speed
bump for one visitor clicking repeatedly, not a bound on what the endpoint can
spend. Any Redis-compatible REST endpoint works and the function reaches it with
plain `fetch`, so no dependency is added. If the store is unreachable the
function degrades to the per-instance counters rather than failing open -- a bad
minute at the counter store must not become an unmetered spend window.

`GET /api/ask` reports `daily_budget` and `shared_counters`, so the deployed
configuration can be checked without a paid call.

Use an explicit `COMPANY_LENS_OPENAI_MODEL`. Do not rely on the function's default
model name. Environment-variable changes do not repair an already-running
deployment; redeploy production after adding them.

After deploy, `GET https://lens.josephjwang.com/api/ask` should list the configured
OpenAI model. A bounded POST is a paid provider call and needs a separate check.

Add the production domain under Vercel **Project → Domains**, then create the DNS
record Vercel shows. TLS is issued and renewed by Vercel. Do not point the public
domain at Vultr in this architecture.

Install and enable the timer:

```bash
sudo cp ops/systemd/company-lens-refresh.service /etc/systemd/system/
sudo cp ops/systemd/company-lens-refresh.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now company-lens-refresh.timer
sudo systemctl start company-lens-refresh.service
```

The enabled timer runs Monday through Friday at 23:30 UTC, with up to ten minutes of jitter.
That is 07:30 China time the next morning and after the US market close in both EDT
and EST. `Persistent=true` runs a missed job after a reboot. The refresh script also
uses a file lock, so a manual run cannot overlap the scheduled run.

Inspect status and logs with:

```bash
systemctl list-timers company-lens-refresh.timer
systemctl status company-lens-refresh.service
journalctl -u company-lens-refresh.service -n 200 --no-pager
```

## Optional Vultr-only fallback

If Vercel is unavailable, Nginx can serve the same site directly. Replace the
example domain and enable the checked-in configuration:

```bash
sudo apt-get install nginx
sudo cp ops/nginx/company-lens.conf /etc/nginx/sites-available/company-lens
sudo ln -s /etc/nginx/sites-available/company-lens /etc/nginx/sites-enabled/company-lens
sudo nginx -t
sudo systemctl reload nginx
```

The generated HTML is self-contained, so Nginx does not need Python on web requests.
The normal Vercel path publishes only 42.4 MB of HTML and therefore remains well under
the current 100 MB Hobby static CLI upload limit.

## Failure behavior

- Accessions are unique keys, so running the job twice does not duplicate filings.
- A failed issuer retains its last good filing and price history.
- Pages are rebuilt from the merged last-good artifacts even when a source is partial.
- Vercel deployment runs only after the HTML build and public bundle both succeed.
- Snapshot JSON, accession text, Parquet files, and SEC identity never enter the
  Vercel bundle.
- A partial refresh exits non-zero after rebuilding, so systemd records a visible
  failure while the last usable site remains online.
- Each page separately displays the latest filing date and the last SEC check time.
