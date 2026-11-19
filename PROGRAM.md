# Program components

## Purpose

A Python-hosted browser dashboard for a TV, desktop or phone, styled with LCARS and other themes. One Python process serves every device; settings, checkmarks and integrations are shared.

## Delivery structure

| Path | Responsibility |
|---|---|
| run.py | Main entry point; trusted LAN enabled by default; --local restricts access |
| Start_Windows.bat / start.sh | Launch from the correct folder |
| requirements.txt | Python dependencies |
| app/mirror.py | HTTP server, pairing/authentication, configuration validation/persistence, refresh orchestration, assignments, schedules, ETA, radar/alerts adapters and runtime error log |
| app/services.py | iCal fetching/recurrence, ZIP weather, IMAP read-only scanning and shipment extraction |
| app/portable.py | CSV import/export with typed JSON cell values |
| app/aerospace.py | NASA feed parsing, cacheable headlines and daily trivia selection |
| app/demo.py | Isolated sample data, without external account access |
| app/static/index.html | Browser shell and settings/editor dialogs |
| app/static/app.js | Tiles, settings, API calls, themes/layouts, grid dragging, TV scaling and overflow loops |
| app/static/style.css | Theme geometry, palettes, typography, TV canvas and responsive styles |
| templates/Settings_Template.csv | Blank/default portable settings; never contains real credentials |
| docs/ | Account setup, Routes setup and validation history |
| examples/send_sensors.py | Optional authenticated sensor update example |
| tests/ | Python fixture/HTTP regressions and Node frontend checks |

## Startup and network access

`python run.py` binds port 8765 on all IPv4 interfaces. The terminal prints the localhost pairing URL and detected LAN IP URL. Use the LAN URL from other devices. `--local` binds only loopback. The token is eight random URL-safe characters and changes every launch. Requests to API endpoints require it. There is no external cloud hosting requirement. LAN firewall/Wi-Fi configuration must permit the connection. Local IP detection selects the default outbound interface with hostname fallback.

The server serves `/`, `/app.js`, `/style.css`; its paired endpoints include `/api/state`, `/api/action`, `/api/refresh`, `/api/backup` and `/api/credentials`. Credentials are retrieved on demand for settings rather than included in normal state responses. The browser polls state; background refresh runs at the configured interval. Sources publish results as they finish.

## Tiles and features

Clock with timezone/year progress; shared Work/School travel estimates; weather, sunrise/sunset and daylight/nighttime hours; Schedule; assignment checklist with completion cleanup; Class Times selected per calendar; Cargo Manifest; countdowns; NASA trivia; radar; connection status/local IP; workshop; optional sensor telemetry. Standalone progress and school-ETA variants remain available in Show / hide panels.

Calendar sources support HTTPS/secret webcal links, Basic authentication and bearer tokens. Schedule visibility, assignment classification and Class Times selection are independent. No completion state is sent back to Canvas/Google. Assignments more than seven days overdue become locally complete.

IMAP accounts are read-only. Shipment settings control age, candidate cap, detection strictness, blocked senders, inferred delivery and retention. Stages are inferred from messages, not verified with a carrier. Manual orders are separate.

Weather/radar/alerts/daylight share one ZIP code. Weather uses Open-Meteo and Zippopotam.us; radar uses RainViewer and OpenStreetMap tiles with attribution; alerts use NWS. These require internet although no weather API key is configured. Routes ETA requires an enabled Google Routes API key/billing and two addresses per destination. NASA trivia requires its feed. Provider availability and account authentication are external dependencies.

TV view fits a reference canvas to the viewport. Saved rows fit vertically while preserving relative positions; Arrange offers grid snapping and added rows. Overflow content loops; clock and radar remain stationary. LCARS/Red Alert share geometry; other themes have structural variants.

## Persistent data

Default data directory: `~/.python_magic_mirror` (Windows: `%USERPROFILE%\.python_magic_mirror`). `settings.csv` stores preferences, layouts, calendar URLs, credentials, addresses and local checklist data. `settings.before-import.csv` retains the setup before the latest import. Legacy settings.json migrates when no CSV exists. `aerospace_news.json` stores headline cache. Demo data uses a separate demo subfolder. Most fetched integration data is session memory. --data-dir overrides this location.

CSV files contain readable secrets. Keep pairing links and backups private. HTTP is intended for trusted LAN use, not public deployment. Runtime errors are shown in System Log with sensitive values redacted. Restart/re-pair after updating.

## Validation and maintenance

From this folder: `python -m unittest discover -s tests -v`; frontend checks: `node tests/test_frontend.js` (Node is needed only for those development checks). Tests use fixtures/mocks plus local HTTP requests. See docs/TEST_REPORT.md for limits and history. Do not interpret passing fixture tests as confirmation of private accounts or remote provider availability.

## Container delivery

Dockerfile builds a Python 3.12 image with a non-root runtime, /config persistence and port 8765. compose.yaml supports build-and-start with a named settings volume. unraid/my-magic-mirror.xml supplies Bridge networking and appdata mapping for a locally built image. docs/DOCKER_UNRAID.md covers setup, migration, permissions and manual updates.

## Thursday weekend Red Alert

On Thursday in the configured dashboard timezone, unfinished assignments due Friday, Saturday or Sunday trigger Red Alert and a pulsing TNG-style count popup. The popup pulses five times, closes after 12 seconds and repeats every eight minutes while active. Acknowledge closes the current popup only. The automatic theme clears when the condition ends. Disable under Settings → Display if desired. Reduced-motion browser preferences suppress pulsing. Calendar fetching includes at least seven upcoming days while enabled. This uses local completion state; it does not query Canvas submission status.

GitHub delivery includes .github/workflows/publish.yml: tests on pull requests, tests plus GHCR publishing for published releases/manual dispatch. See docs/GITHUB_SETUP.md. The archive now contains repository-root files without a wrapper directory.


## iDRAC hardware telemetry

Settings → iDRAC configures the management IP, username, password and enable switch. Connection Status includes an iDRAC row. The footer immediately before Sources / Day Mode / Blank Screen shows only cumulative kWh, actual fan readings and CPU temperatures. Unavailable readings display a dash; previous readings are dimmed on connection failure.

app/idrac.py uses read-only `ipmitool -I lanplus` commands: `sdr type temperature`, `sdr type fan`, and `delloem powermonitor`. Commands use argument arrays, no shell interpolation, password via IPMI_PASSWORD/-E, and 12-second timeouts. The Docker image installs ipmitool; non-Docker hosts must install it separately. IPMI-over-LAN must be enabled and UDP 623 reachable from the container. No privileged container or host device mount is needed for network IPMI.

The uploaded script's raw manual fan-control commands and hardcoded credentials are intentionally not included. The dashboard does not set fan speed or disable automatic cooling. A speed percentage calculated by another controller cannot be inferred from RPM; when the hardware exposes RPM only, the footer shows actual RPM. CPU sensors are restricted to processor/CPU names or processor entity 3.x, excluding inlet/exhaust temperatures. Credentials are saved in CSV and revealed only by the authenticated credentials endpoint for Settings. Monitoring follows the existing dashboard refresh interval. Hardware and a real Docker rebuild have not been tested here.


## Temperature-based fan controller update

The dashboard now includes optional Dell OEM manual fan control; enable it explicitly in Settings → iDRAC after disabling any other fan-control script. No hardcoded host or credentials are included. The monitor/control loop runs every 15 seconds independently of web/calendar refresh. Formula: minimum percent plus (maximum CPU temperature minus target, floored at zero) × gain; capped at 100%. Minimum, target, gain and automatic-cooling temperature threshold are configurable. Defaults are 20%, 46°C, 2.5%/°C and 75°C. These defaults are not a hardware-specific cooling guarantee; configure for the server's requirements.

The footer shows cumulative kWh, successfully commanded fan percentage, average measured fan RPM, and CPU temperatures. Automatic mode shows Auto instead of guessing a percentage. The parser reads pipe-separated sensor values after the label, so Fan1 RPM cannot be interpreted as 1 RPM. RPM averaging uses actual RPM sensors only.

On missing CPU/fan readings, a stopped fan or threshold breach, the controller requests 100% emergency cooling while retaining manual mode. Command failures attempt the same recovery. Updates, shutdowns, disabling monitoring and changing the target host do not send an automatic-mode command; the previous controller retains its hardware setting. While the app is stopped it cannot adjust fans to changing temperatures. IPMI/network failures may prevent any command from reaching the server. No commands have been tested against physical hardware.

## Approval for manual fan increases above 50%

Manual targets above 50% create a latched Red Alert and an Approve/Deny popup. Until approved, manual commands are capped at 50%. Approval permits up to the requested percent; a higher target needs another approval. Deny keeps a 50% manual ceiling during the current high-demand episode. Once the calculated target falls to 50% or below, a future high-demand episode can ask again. Pending alerts remain until decided; host/control-setting changes reset approval state. Decisions are session memory and reset after restart.

Sensor faults, stopped fans and the configured temperature safety threshold override approval with 100% emergency manual cooling. No automatic-mode handoff is sent. Repeated identical mode/speed commands are skipped; a new controller process reasserts manual mode and its freshly calculated target.


## Static styling integrity

The dashboard and pairing screen share app/static/style.css. Regression tests check its format and required selectors. The stylesheet URL revision forces browsers to reload the corrected asset.
