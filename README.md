# Magic-Mirror-UNRAID

**For GitHub/Unraid publishing, read START_HERE.md first.**

# Magic Mirror — start here

Requires Python 3.10+ and a modern browser.

1. Extract this folder.
2. Open a terminal here and install dependencies: `python -m pip install -r requirements.txt` (use `python3` on macOS/Linux).
3. Run `python run.py`, or use Start_Windows.bat / `sh start.sh`.
4. Python prints two private links: one for this computer and one with its actual local network IP. Open the network link on your TV/phone connected to the same home network. Keep Python running.

This launcher enables LAN access by default. For computer-only access: `python run.py --local`. Other options: `--port 8765`, `--no-browser`, `--demo`, `--data-dir PATH`.

If another device cannot connect: allow Python/inbound TCP 8765 in the host firewall on the private network; avoid guest Wi-Fi/client isolation. Confirm the host and TV are on the same network. A DHCP reservation for the host keeps its address stable. The link token changes at each launch, so use the newly printed link. Connection Status also shows the detected IP. A computer with multiple adapters may require choosing the correct LAN address manually.

The server uses HTTP and a pairing token. Use trusted home networking; do not port-forward it. Stop it with Ctrl+C. Settings and readable credentials stay in your existing user-profile `~/.python_magic_mirror/settings.csv`; updating this program folder does not erase them.

Read PROGRAM.md for architecture/components, docs/SETUP_GUIDE.md for accounts, and docs/API_SETUP.md for live ETA. Tests are optional for running the app.

## Docker / Unraid

Docker packaging is included. Run `docker compose up -d --build`, or follow **docs/DOCKER_UNRAID.md** for the supplied Unraid template and persistent appdata setup. No registry image has been published; build it locally once.

## Thursday weekend Red Alert

On Thursday in the configured dashboard timezone, unfinished assignments due Friday, Saturday or Sunday trigger Red Alert and a pulsing TNG-style count popup. Acknowledge dismisses the popup for the current date/count in that browser session; a changed count shows it again. The automatic theme clears when the condition ends. Disable under Settings → Display if desired. Reduced-motion browser preferences suppress pulsing. Calendar fetching includes at least seven upcoming days while enabled. This uses local completion state; it does not query Canvas submission status.

## GitHub publishing

This ZIP extracts directly to repository-root contents. Include .github/workflows/publish.yml when uploading. Follow docs/GITHUB_SETUP.md to publish a tested GHCR image and switch Unraid to registry-based updates.

## Repeating Thursday warning

The Thursday assignment popup pulses five times over 12 seconds and closes automatically. It repeats every eight minutes while the condition remains active. Acknowledge closes the current popup; it does not disable the next reminder. Reduced-motion preferences disable animation while preserving the timeout.
