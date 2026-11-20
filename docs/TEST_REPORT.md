# Validation report — Personal Operations v10

## Private iCal support

102 Python tests and 4 frontend regression checks passed; JavaScript syntax passed. New checks cover webcal-to-HTTPS normalization, private credential CSV persistence and state redaction, no-auth/Basic/Bearer request construction, and invalid credential rejection. Private provider accounts were not connected; authentication is tested with mocked HTTP responses.

## Previous visible settings credentials and System Log

99 Python tests and 4 frontend regression checks passed; JavaScript syntax passed. New tests verify credential endpoint authentication, on-demand primary/additional password access, exclusion from ordinary state responses, and bounded/redacted/deduplicated server logs. The new log styling and settings UI were not independently browser-tested.

## Previous completed assignment cleanup

96 Python tests and 4 frontend regression checks passed. Added checks for immediate hiding across views, persistent automatic completion after seven overdue days, all-day seven/eight-day boundaries, and preservation of ordinary appointments. Updated the demo regression expectation to exclude its already-completed sample.

## Previous polling diagnostics and shipment parsing update

92 Python tests passed, plus 4 JavaScript polling/render regression checks using a minimal DOM adapter. Tests verify rendering errors are not labeled disconnects, expired sessions request re-pairing, failed panels are isolated, and polling recovers. New email fixtures cover multipart HTML tracking links, USPS/DHL links, lookalike-host rejection and promotional link rejection. JavaScript syntax checks passed. The user's exact runtime error and private mailbox messages were not available, so the specific cause on their computer is not confirmed. No new full-browser check was performed.

## Previous independent schedule visibility update

87 tests passed. New tests verify hiding a calendar retains assignments and persists through CSV reload, independent past/future schedule bounds, historical non-assignment event fetching, and invalid range rejection. JavaScript syntax checking passed. Schedule controls live only in Settings → Calendars; the card button is removed. UI changes were not independently browser-tested.

## Previous schedule settings update

All 83 regression tests passed again and JavaScript syntax checking passed. The Schedule panel now opens calendar controls directly; calendar toggles use the existing validated calendar update action. Added persisted agenda display preferences. This UI update was not independently browser-tested.

## Multiple-mailbox and filtering update

**83 automated tests passed**, including the previous 71 checks. Python compilation and JavaScript syntax checks passed. New tests cover multiple-account CSV persistence/redaction, edits, password retention/clearing, deletion, validation, save rollback, independent mailbox jobs, cross-mailbox tracking deduplication, supported shipment acceptance, promotional notices, tracking-only messages, spam headers, blocked senders/domains and relaxed filtering. The new UI was syntax checked; private IMAP accounts and live mailbox filtering were not connected or independently verified here. Trivia now displays its answer automatically.

## Previous CSV and trivia update

**71 automated tests passed**, including all existing regression checks. Python compilation and JavaScript syntax checking passed.

New coverage includes complete CSV round trips with passwords, Unicode, commas and newlines; legacy JSON migration; invalid/duplicate/type-invalid import rejection; saved-password clearing and retention; rollback on save failures; private file permissions; preservation of the previous setup; authenticated HTTP backup/import; and secrets excluded from normal dashboard responses.

A live NASA feed smoke check retrieved and parsed 10 headlines successfully. Trivia tests cover RSS parsing, NASA-only links, stable daily selection, changing dates, older-news labeling, future-news exclusion, empty feeds and unsafe XML rejection. External services use fixtures; private accounts remain unconnected. The new Backup and trivia UI passed syntax checks but was not independently exercised in a browser in this update. Browser checks below describe the previous version.

## Automated checks

The original 49 regression tests cover the following behavior and remain part of the 71-test suite.

- Calendar recurrence, excluded dates, moved instances, cancellations, all-day end dates, ongoing events, time-zone conversion and assignment lookback.
- Stable assignment completion identity, local completion storage and overdue/today/week/later categories.
- Saving each of seven themes; scheduled night mode, sunrise/sunset behavior, stale solar-data fallback and Red Alert priority.
- Timetable expansion, room/building labels and overnight classes.
- Countdown, class, workshop and manual shipment create/update/delete behavior.
- Layout persistence, reset presets, widget bounds and hidden-panel configuration.
- Delivered-shipment cleanup, supported tracking patterns, HTML mail parsing, future-vs-delivered status and newest-notice merging.
- Read-only IMAP folder access and BODY.PEEK; disabled connections make no requests.
- Weather request parameters, units, sunrise/sunset fields; NWS alert requests; radar manifest validation.
- API token enforcement, cross-origin rejection, hostile Host rejection, secret-feed redaction, missing-file/path rejection and invalid settings responses.
- Shared settings between HTTP clients; rollback after save failure; stale-source flags and cached-data retention on failure.
- Transient sensor updates/validation, demo-mode isolation and retention of demo assignments through theme changes.

Tests use local fixtures and mocked external services. HTTP tests start the real Python server and issue actual requests on loopback.

## Browser checks

The production frontend was tested first with fixture transport, then against the actual Python backend through the supported preview environment in isolated demo mode.

Verified against the Python backend:
- All seven theme selections render, and selected theme persists after page reload.
- Dragging moves a widget, resizing changes its dimensions, and the saved layout survives reload.
- Settings → Calendars adds a feed, marks it as an assignment source, displays the saved entry and removes it through the menu.
- Phone preview loads the actual app in a 390-pixel frame using the same backend.
- Screen blanking and click-to-wake work.
- Daily page and loaded widgets render with explicitly labeled sample data.

Additional UI checks with fixture transport:
- School, Workshop and Calendar pages render.
- Checking an assignment updates completion progress.
- Adding a class displays weekdays, times, building and room.
- Workshop checkboxes update.
- Manual shipment stage changes to Delivered.
- Calendar month navigation, radar play/pause, phone settings, and responsive layout work.
- The narrow-screen view had no horizontal document overflow at the inspected phone size.

Browser checks caught and corrected nested countdown markup, panel stacking during layout editing, and a demo-data retention defect. Resize handles were enlarged after interaction checks. The final polling code serializes overlapping refresh requests; its syntax was checked after that change.

## Not independently verified here

- Your private Google/Canvas feed access, feed freshness or completeness.
- Your mailbox provider's authentication rules and actual email templates.
- Live weather/alert/radar responses, remote tile loading, provider outages or rate limits; adapters were tested with controlled responses.
- Physical phone connectivity through your Wi-Fi/firewall (same-backend HTTP clients and the responsive phone frame were tested).
- Physical monitor backlight, long-term burn-in behavior or OS startup/kiosk configuration.
- Actual sensor hardware/calibration or engine safety limits.
- Browser fullscreen behavior across every OS/browser combination.

Screenshots were captured during development, but screenshot deliverables were omitted at your request. This report distinguishes tested application behavior from external account/hardware setup; it does not claim that every external integration is already connected.

Commute update: 102 Python regression tests and 4 frontend checks passed, plus JavaScript syntax checking. Route links encode both configured addresses. Live Google Maps behavior and full browser layout were not independently tested.

TV/ETA update: 105 Python tests and 4 frontend checks passed; JavaScript syntax passed. New tests cover two traffic-aware requests, failure/empty-route handling and key redaction/CSV persistence. The visual layout and animation have not been independently browser-tested in this update; no live paid API calls were made.

Theme/font/export update: 106 Python tests and 4 frontend checks passed; JavaScript syntax passed. Regression coverage verifies manual theme selection pauses automatic overrides. Font appearance and native Save As behavior require review in the user browser; no new full-browser check was performed.

Streamlined UI update: 106 Python regression tests and 4 frontend checks passed, plus JavaScript syntax validation. Single-page navigation, combined ETA markup and font sizing have not been independently browser-tested.

Linear font/theme update: regression tests and frontend syntax checks passed. Eight new theme palettes and three local-data tiles added; new visual appearance has not been independently browser-tested. Pairing tokens use six cryptographically random bytes encoded as eight URL-safe characters.

Unified TV scaling: 106 Python regressions and 4 frontend checks passed, plus geometry checks at equivalent 1920×1080 zoom viewports for 45%, 50%, 67%, 80%, 100%, 110%, 125%. JavaScript syntax passed. These are automated canvas geometry checks, not screenshots or full-browser zoom verification.

Theme composition update: 106 Python regressions passed; frontend checks confirm matching LCARS/Red Alert positions and different Ocean positions, plus existing zoom geometry checks. JavaScript syntax passed. Theme visuals have not been independently browser-tested.

Grid/overflow update: 106 Python regressions passed. Frontend checks include snapped movement and resizing, theme identity and zoom geometry. JavaScript syntax passed. Actual overflow animation and pointer dragging still require browser visual verification.

Restoration/theme update: 106 Python regressions passed, along with frontend checks for restored tile inventory, grid snapping, zoom geometry and identical LCARS positions. JavaScript syntax passed. Theme styling has not been independently browser-reviewed.

Default repair/redesign: 106 Python regression tests and frontend inventory, snapping, theme/zoom checks passed; JavaScript syntax passed. Existing layouts migrate once. The new structural theme visuals have not been independently browser-tested.

Save-layout fix: hidden optional tiles were appended beyond y=3000 and rejected by validation. Inventory now uses bounded three-column rows. Frontend regression checks reproduce a tall existing layout and verify every generated tile is within server bounds. 106 Python tests and frontend checks passed.

Adaptive/class-source update: 107 Python tests passed, including independent Class Times selection and persistence, plus existing frontend layout/zoom checks. JavaScript syntax passed. New visibility interactions were not independently browser-tested.

Screenshot clipping fix: saved layouts now pass through visible-tile fit validation using measured board top, active TV scale and footer reserve. Off-screen/missing tiles trigger an automatic theme reflow. Frontend regression reproduces an off-screen saved radar tile and verifies every fitted tile ends inside the available height. Clock excluded from looping and uses compact stationary composition. 107 Python tests and frontend checks passed. Full browser visual validation remains outstanding.

Radar/shipment repair: 107 Python regressions passed including hash-based radar paths and read-only IMAP parsing; frontend checks passed. Sources publish in completion order. Radar follows current documented Universal Blue/past-tile format. Live private mailbox and remote tile delivery were not independently tested.

Day/night hours update: frontend fixtures verify daytime sunset and nighttime next-sunrise hours in the ZIP timezone; 107 Python regressions passed.

Map policy update: 107 Python tests and frontend regression checks passed; JavaScript syntax passed. Corrected the referrer policy and Universal Blue scheme ID to 2, and added bounded image reuse. Provider-side unblock and live tiles have not been verified.

Row-editor update: 107 Python regressions and frontend checks passed, including proportional saved-row fitting without horizontal rearrangement. JavaScript syntax passed. Pointer panning and scroll interaction have not been independently browser-tested.

Email-only repair: 109 Python tests passed. Scan prioritizes shipping-subject candidates before applying the message cap, merges HTML with plain-text information, decodes embedded carrier destinations locally, skips malformed notices individually and retains previously detected packages through partial scans. No frontend/layout/weather changes. Private mailbox authentication and templates remain unverified.

Shipment-menu update: 108 Python tests passed, including age filtering, assumed-delivery retention and local-IP state shape; frontend checks and syntax passed. Private mailboxes remain unconnected.

Delivery cleanup: all 110 Python tests pass from the reorganized folder, plus frontend checks. A real subprocess smoke check launched run.py with default LAN binding, read the actual printed pairing link and retrieved authenticated demo state. Physical TV/phone connectivity still depends on the user network/firewall.

Assignment checkbox repair: autoscroll copies now retain usable assignment controls and receive event binding after loop creation. Added submission/failure rollback frontend checks. 110 Python tests pass; JavaScript syntax and frontend regressions pass. Native pointer interaction still requires browser verification.

Docker packaging: 110 Python tests and frontend checks passed; Unraid XML parses. Dockerfile/Compose/template inspected. Docker executable unavailable, so image build/container runtime verification remains outstanding.

Thursday alert: 111 Python tests passed, including Thursday Friday–Sunday window, completed-item exclusion, disable switch and Friday theme restoration. Frontend regressions/syntax passed. Popup styling has not been independently browser-tested.

Recurring warning/GitHub delivery: 111 Python tests pass plus frontend checks for 12-second visibility and eight-minute repeat boundary. JavaScript syntax passed. Publishing workflow included with test-before-publish and SHA/release tags. No GitHub push or image publication performed; Docker build remains unverified locally.
