#!/usr/bin/env bash
# Idempotent server setup for tenders.best (Ubuntu 22.04/24.04 or Debian 12).
#
#   DOMAIN=archacrm.twc1.net bash deploy/deploy.sh
#
# What it does: system packages, user `tenders`, code in /opt/tenders, Python venv,
# systemd service (web + collector every 3 h), nginx vhost, Let's Encrypt certificate.
# Re-running it updates the code and restarts the service.
set -euo pipefail

DOMAIN="${DOMAIN:-archacrm.twc1.net}"
APP_DIR="${APP_DIR:-/opt/tenders}"
SRC_DIR="${SRC_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"   # repo checkout to copy from
LE_EMAIL="${LE_EMAIL:-admin@${DOMAIN}}"
PORT=8000

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "run as root"; exit 1; }

log "System packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip nginx certbot python3-certbot-nginx rsync curl >/dev/null

log "Application user and directory"
id -u tenders >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin tenders
mkdir -p "$APP_DIR"
if [ "$SRC_DIR" != "$APP_DIR" ]; then
  rsync -a --delete --exclude data --exclude .venv --exclude .env --exclude .git --exclude __pycache__ "$SRC_DIR"/ "$APP_DIR"/
fi
mkdir -p "$APP_DIR/data"

log "Python environment"
[ -d "$APP_DIR/.venv" ] || python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -q --upgrade pip
"$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

if [ ! -f "$APP_DIR/.env" ]; then
  log "Writing $APP_DIR/.env (edit admin password there if needed)"
  cat > "$APP_DIR/.env" <<EOF
TB_DATA_DIR=$APP_DIR/data
TB_COLLECT_INTERVAL_HOURS=3
TB_SCHEDULER=1
TB_COLLECT_ON_START=1
TB_SECURE_COOKIES=1
EOF
fi
chown -R tenders:tenders "$APP_DIR"
chmod 600 "$APP_DIR/.env"

log "systemd service"
install -m 644 "$APP_DIR/deploy/tenders.service" /etc/systemd/system/tenders.service
systemctl daemon-reload
systemctl enable tenders >/dev/null
systemctl restart tenders
sleep 2
curl -fsS "http://127.0.0.1:$PORT/api/stats" >/dev/null && echo "app answers on :$PORT" || { journalctl -u tenders -n 30 --no-pager; exit 1; }

log "nginx vhost for $DOMAIN"
sed "s/__DOMAIN__/$DOMAIN/g; s#__APP_DIR__#$APP_DIR#g" "$APP_DIR/deploy/nginx.conf" > "/etc/nginx/sites-available/$DOMAIN"
ln -sf "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/$DOMAIN"
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

SERVER_IP=$(curl -fsS https://api.ipify.org || hostname -I | awk '{print $1}')
DOMAIN_IP=$(getent ahostsv4 "$DOMAIN" | awk '{print $1; exit}' || true)
if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
  log "Let's Encrypt certificate"
  certbot --nginx --non-interactive --agree-tos -m "$LE_EMAIL" -d "$DOMAIN" --redirect || echo "certbot failed, site stays on http"
else
  echo "WARNING: $DOMAIN resolves to '${DOMAIN_IP:-nothing}', this server is $SERVER_IP."
  echo "Point the domain to this server in the Timeweb panel, then run: certbot --nginx -d $DOMAIN --redirect"
fi

log "Done: http(s)://$DOMAIN  admin: /admin"
