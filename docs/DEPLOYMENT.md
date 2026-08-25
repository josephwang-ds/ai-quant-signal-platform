# Scheduled deployment

The public HTML bundle is deployed at <https://company-lens-demo.vercel.app>. Vercel
automatically assigned the first deployment to production even though the CLI command
did not pass `--prod`; later non-`--prod` deployments remain previews. The Vultr worker,
server secret file, and systemd timer are still unapplied.

## Recommended shape

The planned target uses a prepaid Vultr instance as the stateful refresh worker and
Vercel as the public static frontend. No browser request would need to reach Vultr.

```text
systemd timer on Vultr
        │
        ├── refresh mutable SEC submission heads
        ├── download only unseen accession documents
        ├── refresh daily market histories
        ├── rebuild 193 static company pages
        ├── package public HTML only (no snapshot JSON/cache)
        └── Vercel CLI deploys prebuilt output → Vercel CDN/domain
```

The full local page directory is about 97 MB because it includes 58 MB of JSON build
artifacts. The Vercel bundle publishes only the 195 HTML files, currently about
41.6 MB. Vultr keeps the roughly 335 MB accession and price caches. Start with Ubuntu,
2 vCPU, 4 GB RAM, and at least 40 GB disk; resize only if the journal shows memory
pressure or refresh time becomes uncomfortable.

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
For non-interactive CLI runs, Vercel recommends `VERCEL_ORG_ID` and
`VERCEL_PROJECT_ID` so project linking is not required.
The service stores any Vercel CLI state under `/opt/company-lens/data/vercel-cli`,
because the hardened systemd unit does not expose the worker user's home directory.

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

The timer runs Monday through Friday at 23:30 UTC, with up to ten minutes of jitter.
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
The normal Vercel path publishes only 38.5 MB of HTML and therefore remains well under
the current 100 MB Hobby static CLI upload limit.

## Failure behavior

- Accessions are unique keys, so running the job twice does not duplicate filings.
- A failed issuer retains its last good filing and price history.
- Pages are rebuilt from the merged last-good artifacts even when a source is partial.
- A future Vercel deployment should run only after the HTML build and public bundle
  both succeed.
- Snapshot JSON, accession text, Parquet files, and SEC identity never enter the
  Vercel bundle.
- A partial refresh exits non-zero after rebuilding, so systemd records a visible
  failure while the last usable site remains online.
- Each page separately displays the latest filing date and the last SEC check time.
