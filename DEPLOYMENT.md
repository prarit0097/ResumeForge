# Deploying ResumeForge to a VPS (git pull + gunicorn + nginx)

This fits a VPS that already runs several apps behind **nginx**, each as its own
**gunicorn** service on a unique loopback port. ResumeForge is just one more.

Updates are pull-based: you `git push` from your machine, then run
`./deploy/deploy.sh` on the VPS (or it pulls + restarts for you).

---

## 1. First-time setup on the VPS

```bash
# Clone into your apps directory
cd ~/apps
git clone https://github.com/prarit0097/ResumeForge.git
cd ResumeForge

# Python venv + dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Headless Chromium for PDF/PNG export — installs the browser AND its OS libs.
# (--with-deps needs sudo; it apt-installs the shared libraries Chromium needs.)
python -m playwright install --with-deps chromium
```

## 2. Configure `.env` (never committed)

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
nano .env
```

Set, at minimum:

```dotenv
DEBUG=False
SECRET_KEY=<paste the generated key>
ALLOWED_HOSTS=resume.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://resume.yourdomain.com
OPENROUTER_API_KEY=sk-or-...
LLM_MODEL=deepseek/deepseek-v4-flash

# Analytics + SEO (optional but you asked for traffic tracking)
GA_MEASUREMENT_ID=G-XXXXXXXXXX
SITE_URL=https://resume.yourdomain.com
```

> **Pick a free port.** Each app on your VPS uses its own gunicorn port. This one
> defaults to `127.0.0.1:8001` — change `GUNICORN_BIND` in the systemd unit (and
> `proxy_pass` in nginx) if 8001 is taken.

## 3. Migrate + collect static

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy        # sanity check (warnings about CDN are fine)
```

## 4. gunicorn service (systemd)

```bash
sudo cp deploy/resumeforge.service /etc/systemd/system/resumeforge.service
sudo nano /etc/systemd/system/resumeforge.service   # set YOUR_USER + path + port
sudo systemctl daemon-reload
sudo systemctl enable --now resumeforge
sudo systemctl status resumeforge
```

## 5. nginx + HTTPS

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/resumeforge
sudo nano /etc/nginx/sites-available/resumeforge   # set domain + upstream port
sudo ln -s /etc/nginx/sites-available/resumeforge /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d resume.yourdomain.com       # free HTTPS
```

Point a DNS A record for `resume.yourdomain.com` at the VPS first.

---

## 6. Future updates (the everyday loop)

On your machine:

```bash
git add -A && git commit -m "..." && git push
```

On the VPS:

```bash
cd ~/apps/ResumeForge
./deploy/deploy.sh      # pulls, installs, migrates, collectstatic, restarts
```

`deploy.sh` is idempotent and safe to re-run.

---

## Google Analytics (traffic)

1. Create a **GA4** property at <https://analytics.google.com> → get a
   Measurement ID like `G-XXXXXXXXXX`.
2. Put it in `.env` as `GA_MEASUREMENT_ID` and run `./deploy/deploy.sh`.

Privacy: analytics loads on every page, but the gtag snippet **strips the secret
`?t=` token and masks the resume id** before sending anything to Google, so no
private resume data ever leaves the server. Resume/draft pages are also
`noindex`; the landing page is indexable so the site can be found.

## Notes / gotchas

- **SQLite** is the default DB (one file, `db.sqlite3`, git-ignored). Fine for
  this app's load. Back it up with the rest of the VPS.
- **Playwright/Chromium** must be installed on the VPS (`playwright install
  --with-deps chromium`) or PDF/PNG downloads fail. `deploy.sh` re-runs the
  browser install each time (cheap if already present).
- **Rate limiting** uses the in-process cache (fine for a single gunicorn group).
  If you scale to multiple machines, point `django-ratelimit` at a shared Redis.
- Uploads are capped at 5 MB; nginx is set to `client_max_body_size 6M`.
