# Docker and Unraid installation

The package includes a Dockerfile, Compose file and Unraid template. The image is built locally; no prepublished registry image exists yet. Docker is not needed on your TV: it only opens a browser.

## Ordinary Docker — simplest startup

Extract the package and open a terminal in Magic_Mirror:

```sh
docker compose up -d --build
docker compose logs magic-mirror
```

Open `http://YOUR-SERVER-IP:8765/` and enter the eight-character token from the logs, or append `#token=TOKEN`. The log may show the container's internal IP: use the server's LAN IP instead. The token changes after a restart. A named Docker volume retains settings across updates. Import your existing CSV in Settings → Backup.

Stop: `docker compose down`. Update: replace the program files, then run `docker compose up -d --build` again. Do not use `down -v` unless you intend to delete the settings volume.

## Unraid — build once, then manage in Docker tab

1. Extract the Magic_Mirror folder to `/mnt/user/appdata/magic-mirror-build` (its Dockerfile should be directly inside that directory).
2. Open Unraid's terminal and run:

```sh
docker build -t magic-mirror:local /mnt/user/appdata/magic-mirror-build
mkdir -p /mnt/user/appdata/magic-mirror
chown 99:100 /mnt/user/appdata/magic-mirror
chmod 700 /mnt/user/appdata/magic-mirror
```

3. For the provided template, copy `unraid/my-magic-mirror.xml` to `/boot/config/plugins/dockerMan/templates-user/my-magic-mirror.xml`. In Unraid choose Docker → Add Container, then select the magic-mirror user template. UI labels may vary by Unraid version.
4. Check: image `magic-mirror:local`, Bridge networking, TCP host port 8765 → container 8765, `/mnt/user/appdata/magic-mirror` → `/config`, and privileged mode off. Apply. The image must already exist from step 2; it is not downloadable from a registry. Enable Autostart in the Docker tab.
5. Open container logs and copy the token. Visit `http://UNRAID-LAN-IP:8765/#token=TOKEN` on your TV or phone. Unraid's WebUI shortcut opens the page where you can enter the token.
6. Import your old settings CSV. All accounts, theme settings and layouts save into the appdata directory.

### Terminal-only Unraid alternative

After building the image and preparing the settings directory above:

```sh
docker run -d --name magic-mirror \
  --restart unless-stopped \
  --user 99:100 \
  --cap-drop=ALL --security-opt=no-new-privileges:true \
  -p 8765:8765 \
  -v /mnt/user/appdata/magic-mirror:/config \
  magic-mirror:local
```

Update by building the new files under the same tag, then recreating the container with the same mapping. Back up appdata or export a CSV first. Unraid's registry-based Check for Updates cannot detect changes to this locally built image; rebuild/recreate manually.

## Persistence and permissions

Only /config is writable persistent application data. CSV contains readable credentials. The standard Docker image runs as UID/GID 10001; the Unraid template overrides to 99:100 for appdata compatibility. If starting with a copied config directory, ensure that the chosen runtime user can write it. Avoid mounting the Docker socket or unrelated host directories.

## Networking and limitations

The server binds inside the container on all interfaces and publishes only port 8765. No host network, privileged mode, or VM is needed. Use trusted LAN access; do not port-forward this HTTP app. Calendar/email/weather require outbound internet and working DNS. Containers use UTC by default, but the dashboard's configured timezone controls calendar/clock behavior.

The packaged container recipe was inspected and the app/tests verified locally. An actual Docker image build could not be run in the development environment because Docker is unavailable. A fully one-click registry install requires publishing a built image; this package does not claim one has been published.
