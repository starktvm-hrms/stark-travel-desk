#!/usr/bin/env bash
# One-time setup of travel.starkpeople.in (Stark Travel Desk) on the existing nginx VPS.
#
# Run as root in hPanel → VPS → Browser terminal:
#   curl -fsSL https://raw.githubusercontent.com/starktvm-hrms/stark-travel-desk/main/deploy/vps-setup.sh -o /tmp/travel-setup.sh && sudo bash /tmp/travel-setup.sh
#
# Non-interactive: TRAVEL_USER=admin TRAVEL_PASS='...' bash vps-setup.sh
#
# What it ADDS (nothing existing is edited or removed):
#   /var/www/travel.starkpeople.in/          a checkout of the repo's main branch (web/ is served, server/ runs the API)
#   /opt/stark-travel-venv/                   Python virtualenv with the Anthropic SDK (for Stark Decoder)
#   /etc/systemd/system/stark-travel.service  the API on 127.0.0.1:${TRAVEL_PORT:-8795}, run as user `stark-travel`
#   /var/lib/stark-travel/                    the SQLite database (trips, travellers, settings) + daily backups
#   nginx site file for travel.starkpeople.in sites-available + symlink, or conf.d
#   /etc/cron.d/stark-travel                  pulls new code every 5 minutes, nightly database backup
#   a Let's Encrypt certificate for this subdomain only (if certbot is installed)
#
# Safe to re-run: it only rewrites its own files. If nginx rejects the new config,
# the new site file is removed again and nginx is left untouched.
set -euo pipefail

DOMAIN="travel.starkpeople.in"
REPO="${REPO:-https://github.com/starktvm-hrms/stark-travel-desk.git}"
BRANCH="${BRANCH:-main}"
WEBROOT="/var/www/${DOMAIN}"
VENV="/opt/stark-travel-venv"
SERVICE="stark-travel"
SERVICE_FILE="/etc/systemd/system/${SERVICE}.service"
DATA_DIR="/var/lib/stark-travel"
CRON_FILE="/etc/cron.d/stark-travel"
API_PORT="${TRAVEL_PORT:-8795}"

say()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || fail "run as root (use sudo)."
command -v nginx >/dev/null || fail "nginx is not installed on this server."
command -v systemctl >/dev/null || fail "systemd is required."
for pkg in git python3 curl; do command -v "$pkg" >/dev/null || { say "Installing $pkg"; apt-get install -y -q "$pkg" >/dev/null; }; done
python3 -c 'import venv, ensurepip' 2>/dev/null || { say "Installing python3-venv"; apt-get update -q >/dev/null; apt-get install -y -q python3-venv >/dev/null; }

if [ -d /etc/nginx/sites-enabled ] && grep -Rqs "sites-enabled" /etc/nginx/nginx.conf; then
  SITE_FILE="/etc/nginx/sites-available/${DOMAIN}"; SITE_LINK="/etc/nginx/sites-enabled/${DOMAIN}"
else
  SITE_FILE="/etc/nginx/conf.d/${DOMAIN}.conf"; SITE_LINK=""
fi
OTHER=$(grep -RlsE "server_name[^;]*\b${DOMAIN//./\\.}\b" /etc/nginx 2>/dev/null | grep -vxF "$SITE_FILE" | grep -vxF "${SITE_LINK:-/nonexistent}" || true)
[ -z "$OTHER" ] || fail "${DOMAIN} is already configured in: ${OTHER}. Nothing was changed."

# 1. Code
say "Fetching the app into ${WEBROOT}"
if [ -d "${WEBROOT}/.git" ]; then
  git -C "$WEBROOT" fetch -q --depth 1 origin "$BRANCH"
  git -C "$WEBROOT" reset -q --hard "origin/${BRANCH}"
else
  [ ! -e "$WEBROOT" ] || fail "${WEBROOT} exists and is not ours. Nothing was changed."
  git clone -q --depth 1 --branch "$BRANCH" "$REPO" "$WEBROOT" || fail "could not clone ${REPO}."
fi
[ -f "${WEBROOT}/server/app.py" ] && [ -f "${WEBROOT}/web/index.html" ] || fail "app files missing in ${WEBROOT}."

# 2. Python environment
say "Preparing Python environment in ${VENV}"
[ -x "${VENV}/bin/python" ] || python3 -m venv "$VENV"
"${VENV}/bin/pip" install -q --upgrade pip >/dev/null
"${VENV}/bin/pip" install -q -r "${WEBROOT}/requirements.txt"

# 3. Service user, data, first sign-in
if ss -ltnH "sport = :${API_PORT}" 2>/dev/null | grep -q . && ! systemctl is-active -q "$SERVICE"; then
  fail "port ${API_PORT} is already used by another program. Re-run with TRAVEL_PORT=<free port>."
fi
id -u "$SERVICE" >/dev/null 2>&1 || useradd --system --no-create-home --home-dir "$DATA_DIR" --shell /usr/sbin/nologin "$SERVICE"
install -d -m 750 -o "$SERVICE" -g "$SERVICE" "$DATA_DIR" "${DATA_DIR}/backups"
api_cli() { runuser -u "$SERVICE" -- env STARK_DATA_DIR="$DATA_DIR" "${VENV}/bin/python" "${WEBROOT}/server/app.py" "$@"; }
if [ -n "$(api_cli list-users 2>/dev/null)" ]; then
  say "Keeping existing sign-in users: $(api_cli list-users | paste -sd ' ')"
else
  AUTH_USER="${TRAVEL_USER:-}"; AUTH_PASS="${TRAVEL_PASS:-}"
  if [ -z "$AUTH_USER" ] || [ -z "$AUTH_PASS" ]; then
    if [ -t 0 ]; then TTY=/dev/stdin
    elif ( : </dev/tty ) 2>/dev/null && [ -t 1 ]; then TTY=/dev/tty
    else fail "no terminal to ask for a login. Download and run the script instead (see the top of this file)."; fi
    say "Create the first admin sign-in for ${DOMAIN}"
    read -rp "  Username: " AUTH_USER <"$TTY" || fail "could not read input."
    while :; do
      read -rsp "  Password (min 10 chars): " AUTH_PASS <"$TTY" || fail "could not read input."; echo
      [ "${#AUTH_PASS}" -ge 10 ] && break; echo "  Too short, try again."
    done
  fi
  [ -n "$AUTH_USER" ] || fail "username must not be empty."
  STARK_PASSWORD="$AUTH_PASS" api_cli add-user "$AUTH_USER" >/dev/null || fail "could not create the user."
  unset AUTH_PASS
  say "Created admin ${AUTH_USER}"
fi

# 4. systemd unit
say "Writing ${SERVICE_FILE}"
cat > "$SERVICE_FILE" <<UNIT
# Stark Travel Desk API, added by deploy/vps-setup.sh
[Unit]
Description=Stark Travel Desk API (${DOMAIN})
After=network-online.target
Wants=network-online.target

[Service]
User=${SERVICE}
Group=${SERVICE}
Environment=STARK_DATA_DIR=${DATA_DIR}
Environment=STARK_PORT=${API_PORT}
Environment=STARK_BASE_URL=https://${DOMAIN}
Environment=STARK_TZ=Asia/Kolkata
Environment=PYTHONUNBUFFERED=1
ExecStart=${VENV}/bin/python ${WEBROOT}/server/app.py
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ReadWritePaths=${DATA_DIR}

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable -q "$SERVICE"
systemctl restart "$SERVICE"
for _ in $(seq 1 15); do curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1 && break; sleep 1; done
curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1 || fail "the API did not start. See: journalctl -u ${SERVICE} -n 50"
say "API running (data in ${DATA_DIR})"

# 5. nginx
HAD_SITE_FILE=0; [ -f "$SITE_FILE" ] && HAD_SITE_FILE=1
SITE_BACKUP=""; [ "$HAD_SITE_FILE" -eq 1 ] && { SITE_BACKUP=$(mktemp); cp "$SITE_FILE" "$SITE_BACKUP"; }
if [ "$HAD_SITE_FILE" -eq 1 ] && grep -q "managed by Certbot" "$SITE_FILE"; then
  say "Site file already has HTTPS from certbot; leaving it as is"
else
  say "Writing ${SITE_FILE}"
  cat > "$SITE_FILE" <<NGINX
# Stark Travel Desk — added by deploy/vps-setup.sh (github.com/starktvm-hrms/stark-travel-desk)
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    root ${WEBROOT}/web;
    index index.html;

    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "same-origin" always;
    add_header X-Robots-Tag "noindex, nofollow" always;

    location ^~ /.well-known/acme-challenge/ { root ${WEBROOT}/web; try_files \$uri =404; }
    location ~ /\\. { return 404; }

    # stark-travel-api
    location /api/ {
        proxy_pass http://127.0.0.1:${API_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        client_max_body_size 2m;
    }

    location / {
        expires -1;
        try_files \$uri \$uri/ /index.html;
    }
}
NGINX
fi
[ -n "$SITE_LINK" ] && ln -sfn "$SITE_FILE" "$SITE_LINK"
if ! nginx -t 2>/tmp/travel-nginx-test.log; then
  cat /tmp/travel-nginx-test.log >&2
  if [ "$HAD_SITE_FILE" -eq 0 ]; then rm -f "$SITE_FILE"; [ -n "$SITE_LINK" ] && rm -f "$SITE_LINK"; else cp "$SITE_BACKUP" "$SITE_FILE"; fi
  fail "nginx rejected the configuration; the new site file was removed and nginx was not reloaded."
fi
systemctl reload nginx
say "nginx reloaded"

# 6. HTTPS
command -v certbot >/dev/null || { say "Installing certbot"; apt-get install -y -q certbot python3-certbot-nginx >/dev/null || true; }
if command -v certbot >/dev/null; then
  say "Requesting an SSL certificate for ${DOMAIN}"
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --redirect --keep-until-expiring --register-unsafely-without-email \
    || echo "  certbot failed (DNS may still be propagating). Re-run this script in a few minutes."
else
  echo "  certbot is not available, so the site is HTTP only for now. Gmail sign-in needs HTTPS."
fi

# 7. Auto-update + nightly backup
cat > "$CRON_FILE" <<CRON
# Stark Travel Desk (added by deploy/vps-setup.sh)
# Pull new code every 5 minutes; reinstall packages / restart the API only when needed.
*/5 * * * * root cd ${WEBROOT} && old=\$(git rev-parse HEAD) && git fetch -q --depth 1 origin ${BRANCH} && git reset -q --hard origin/${BRANCH} && new=\$(git rev-parse HEAD) && if [ "\$old" != "\$new" ]; then git diff --quiet "\$old" "\$new" -- requirements.txt || ${VENV}/bin/pip install -q -r requirements.txt; git diff --quiet "\$old" "\$new" -- server requirements.txt || systemctl restart ${SERVICE}; fi
# Nightly database backup, 30 days kept.
17 2 * * * ${SERVICE} sqlite3 ${DATA_DIR}/travel.db ".backup ${DATA_DIR}/backups/travel-\$(date +\\%F).db" 2>/dev/null || cp ${DATA_DIR}/travel.db ${DATA_DIR}/backups/travel-\$(date +\\%F).db; find ${DATA_DIR}/backups -name 'travel-*.db' -mtime +30 -delete
CRON
chmod 644 "$CRON_FILE"

say "Done. Open https://${DOMAIN} and sign in. Then: Settings → Gmail, Claude API key, WhatsApp function."
