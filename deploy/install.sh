#!/usr/bin/env bash
set -euo pipefail
# Run from an extracted release as the SSH owner. No existing service is overwritten outside this project.
src=$(cd "$(dirname "$0")/.." && pwd)
root=/opt/flugel-cyberlab
owner=$(id -un)
test "$owner" != root
command -v docker >/dev/null
docker compose version >/dev/null
test -f "$src/apps/web/dist/index.html"
sudo -n true
if ss -ltnH '( sport = :8317 )' | grep -q . && ! systemctl is-active --quiet cyberlab-api; then
  echo 'Port 8317 is occupied by another service'; exit 1
fi
if ! id cyberlab >/dev/null 2>&1; then sudo useradd --system --home /var/lib/cyberlab --shell /usr/sbin/nologin cyberlab; fi
sudo install -d -m 755 "$root/releases"
release="$root/releases/$(date -u +%Y%m%dT%H%M%SZ)"
sudo install -d -m 755 "$release"
sudo cp -a "$src/." "$release/"
sudo chmod -R a+rX "$release"
sudo python3 -m venv "$release/.venv"
sudo "$release/.venv/bin/pip" install --disable-pip-version-check -r "$release/requirements-dev.txt"
sudo install -d -o cyberlab -g cyberlab -m 700 /var/lib/cyberlab
sudo install -d -o "$owner" -g cyberlab -m 770 /var/lib/cyberlab-runner
sudo install -d -o "$owner" -g cyberlab -m 770 /run/cyberlab
cd "$release"
# Build the shared target before switching the active version. It publishes no ports.
docker build --tag flugel-cyberlab/exercises:1.0 labs/shared
sudo ln -sfn "$release" "$root/current"
cat <<EOF | sudo tee /etc/tmpfiles.d/cyberlab.conf >/dev/null
d /run/cyberlab 0770 $owner cyberlab -
EOF
cat <<EOF | sudo tee /etc/systemd/system/cyberlab-runner.service >/dev/null
[Unit]
Description=FLUGEL Cyber Range private lab broker
After=docker.service
Requires=docker.service
[Service]
User=$owner
Group=cyberlab
SupplementaryGroups=docker
WorkingDirectory=$root/current
Environment=PYTHONPATH=$root/current
Environment=CYBERLAB_RUNNER_DATA=/var/lib/cyberlab-runner
ExecStart=$root/current/.venv/bin/uvicorn runner.service:app --uds /run/cyberlab/runner.sock --workers 1 --no-access-log
Restart=on-failure
UMask=0007
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/run/cyberlab /var/lib/cyberlab-runner
PrivateTmp=true
MemoryMax=512M
TasksMax=128
[Install]
WantedBy=multi-user.target
EOF
cat <<EOF | sudo tee /etc/systemd/system/cyberlab-api.service >/dev/null
[Unit]
Description=FLUGEL Cyber Range dashboard and API
After=network.target cyberlab-runner.service
Wants=cyberlab-runner.service
[Service]
User=cyberlab
Group=cyberlab
WorkingDirectory=$root/current
Environment=PYTHONPATH=$root/current/apps/api
Environment=CYBERLAB_DATA=/var/lib/cyberlab
Environment=CYBERLAB_RUNNER_SOCKET=/run/cyberlab/runner.sock
Environment=CYBERLAB_HOSTS=127.0.0.1,localhost
ExecStart=$root/current/.venv/bin/uvicorn cyberlab.main:create_app --factory --host 127.0.0.1 --port 8317 --workers 1 --no-access-log
Restart=on-failure
UMask=0077
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/cyberlab
PrivateTmp=true
MemoryMax=512M
TasksMax=128
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable cyberlab-runner cyberlab-api
sudo systemctl restart cyberlab-runner cyberlab-api
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8317/api/health; then break; fi
  sleep 1
done
curl -fsS http://127.0.0.1:8317/api/health/capacity
echo
echo "Release: $release"
echo 'Dashboard: http://127.0.0.1:8317 (SSH tunnel required for remote access)'
