# Settings and importing your data

## Google calendars

1. Open Google Calendar in a desktop browser.
2. Go to **Settings → Settings for my calendars → [calendar name] → Integrate calendar**.
3. Copy **Secret address in iCal format**. If it is an already-public calendar, its public iCal URL also works. Do not make a private calendar public just for this dashboard.
4. In the dashboard, open **Settings → Calendars → Add calendar**.
5. Give it a name, choose a color, paste the HTTPS iCal URL and click **Save calendar**.
6. Repeat for your other calendars. Use Edit to disable, rename, recolor or remove a feed. When editing, a blank URL keeps the existing link.

The URL must be a feed, not a sharing page, calendar ID, or browser address-bar URL. Some school/work administrators disable secret feed URLs. This version does not implement Google OAuth as a fallback.

## Canvas assignment checklist

1. In Canvas, open **Calendar → Calendar Feed** and copy the feed URL.
2. If it starts with `webcal://`, change that prefix to `https://`.
3. Add it through **Settings → Calendars**, then check **Use as assignment checklist** before saving.
4. If Canvas is already subscribed through Google and Google exposes an iCal feed for that subscription, you can use that link instead. A direct Canvas link avoids the extra Google refresh delay.
5. Click assignment checkboxes in the dashboard. Progress and checkmarks are saved locally.

All events in that feed are treated as assignments. Canvas feed data can include other events and does not include Canvas To Do items. These checkmarks do not reflect or change Canvas submission status. Assignments without feed due dates cannot be inferred.

## Weather, sunrise, sunset, radar and alerts

Open **Settings → Weather**, enter your five-digit US ZIP code, choose units and save. No API key is needed. The Calendar page includes recent radar, a play/pause timeline and connection status. Active weather alerts appear above the panels. ZIP code and coordinates are sent to the respective weather/map providers.

## Email shipments

1. Optionally create a **Shipments** folder/label in your email account and filter shipping notices into it.
2. Open **Settings → Email** and enable scanning.
3. Enter your IMAP SSL hostname, email username, folder name and an app-specific password supported by the provider.
4. For personal Gmail, the server is `imap.gmail.com` and the default folder is `INBOX`. App passwords require 2-Step Verification and must be available for your account. Do not enter your normal Google password.
5. Save settings. If your account only allows OAuth, this version cannot connect to it.

The app password is saved in your private `settings.csv` and included in CSV exports. Leave the password field blank to keep it, or check “Clear the saved app password” to remove it. Keep CSV files private because passwords are readable plaintext. You may also supply the `MIRROR_EMAIL_PASSWORD` environment variable. Email scanning uses SSL port 993, read-only folder selection and BODY.PEEK, so it does not mark messages read. No mail is sent, moved or deleted. Only the newest configured number of messages within the scan window is checked. Message content is bounded to 256 KiB and interpreted locally without remote images. Shipments outside these limits may be missed.

UPS, USPS, FedEx and Amazon patterns are recognized when present as text. Numeric USPS/FedEx numbers require a tracking label. Carrier links are constructed for recognized supported numbers. No mailbox content is sent to AI services. Status reflects the newest recognizable email notice, not continuous carrier tracking.

Use **Cargo manifest → Add an order** for orders without email notices. Update an order manually through Ordered, Shipped, Out for delivery and Delivered. Old delivered items are hidden according to your Email settings retention value.

## Classes, countdowns and workshop records

- **Settings → Timetable → Add class:** set weekdays, times, building and room. These also appear in the agenda and Up next panel.
- **Settings → Countdowns:** add exams, launches or other dates. Enter target times in the dashboard's selected time zone.
- **Settings → Workshop:** add tasks, parts needed or maintenance reminders, including optional due dates and details. Completion checkboxes are local.
- **Settings → Display:** change notes, theme, automatic night behavior, intensity and layouts.

Your changes are saved automatically when you click the relevant Save button. Use the explicit Save layout button after rearranging panels.


## Keeping everything between updates

1. Open **Settings → Backup** and click **Export settings CSV**.
2. Keep the downloaded `Magic_Mirror_Settings.csv` somewhere private. It contains your saved app password, private calendar links, preferences and checklist data.
3. Replace the application folder with the updated version and launch it. On the same computer and user account, your settings load automatically from your user profile.
4. If moving computers or using a different data folder, open **Settings → Backup**, select your exported CSV, check the replacement box, and click **Import settings CSV**.
5. The app retains the previous setup in `settings.before-import.csv` in its data folder. Import that file to undo the most recent import.

The included template CSV has defaults and no credentials. Configure accounts through Settings and export afterward; manual CSV editing is unnecessary. Values use JSON inside CSV cells to preserve lists, punctuation and data types.

## Daily aerospace trivia

The former Personal log widget now shows a daily NASA headline quiz. The headline and answer display automatically; follow the source link for the full story. Headlines refresh daily; cached older material is labeled. Demo mode uses an explicitly labeled sample headline.

## Add more email accounts

1. Open **Settings → Email**. Your existing mailbox remains the primary account.
2. Under **Additional mailboxes**, click **Add email account**.
3. Enter a label, IMAP server, email username, folder and that account’s app password. Enable the mailbox and save. Repeat for each mailbox.
4. Use **Edit** to disable, change or remove any additional account.
5. Leave **Strict filter** enabled to require supported tracking numbers plus shipping status. Add unwanted sender addresses/domains to the comma-separated block field and save settings. If a real package is missing, use a dedicated shipment folder, relax the filter, or add it manually.
6. Export a fresh CSV backup after adding accounts. It includes every saved mailbox credential.

Filters cannot prove a package is real. The app never opens email links; tracking links are constructed for supported carriers. Check connection status for account-specific errors.

## Calendar and schedule settings

All controls are in **Settings → Calendars**; the Schedule card has no settings button. Each source has a **Show on schedule** checkbox. Unchecking it hides that source from Schedule and the month view while leaving its assignment checklist active. Keep **Enable syncing** and **Use as assignment checklist** checked in Edit for assignment-only calendars. Disabling syncing turns off the whole source.

Set **Schedule past days to keep** and **Schedule days ahead** independently (0–90 each). Zero past days hides finished events; a nonzero value includes events from midnight that many days ago. The future limit includes the entire last day. **Assignment days ahead** remains independent, with 14 days of assignment lookback. These ranges request calendar history and recurrence expansion; they do not archive events deleted by the calendar provider. All-day and location controls still apply to the agenda. Settings persist in CSV backups.

## Completed assignment cleanup

Checking an assignment immediately hides it from the assignment list, Schedule and month view. Assignments more than seven days overdue are automatically marked completed locally and hidden. Timed assignments use elapsed time after the due timestamp; all-day assignments use the dashboard’s local calendar date, and disappear on the eighth overdue day. Completion is saved in your CSV. This does not submit work or mark anything completed in Canvas/Google. Ordinary appointments follow your schedule date range and are not treated as assignments.

## Visible passwords and System Log

Saved app passwords are displayed as readable text in **Settings → Email** and each additional account’s Edit window. Passwords are retrieved only when opening these settings, through the paired session; they remain excluded from ordinary dashboard polling. The existing Clear saved password checkbox removes a credential.

A compact LCARS-style **SYSTEM LOG** sits above the dashboard panels. It shows timestamped calendar/email/service errors, invalid settings requests, connection problems and display errors. The latest 30 entries are shown with scrolling; repeated service errors are suppressed until the error changes or recovers. Server history lasts for the application session; browser-side history lasts until page reload. Passwords, pairing tokens and private feed URLs are redacted from server messages.

## Private iCal feeds

Open **Settings → Calendars → Add calendar** (or Edit). Paste the full private subscription URL.

- **Secret URL / no extra login:** Google/Canvas secret feed links and other tokenized subscription URLs.
- **Username and password (HTTP Basic):** subscription endpoints protected by a provider-supplied login; enter the username and password.
- **Bearer token:** enter the token required by your feed provider.

`webcal://` URLs are converted to HTTPS. Saved URLs and credentials are visible in the calendar editor and travel in CSV backups. Ordinary dashboard polling excludes the private URL, password and token. Blank credentials clear the corresponding fields when saving; use the correct authentication mode. HTTP 401/403 failures give an access-denied message in System Log. Browser-login pages, OAuth-only access and CalDAV collections are not subscription feeds and are not supported.

## Traffic to work

Set the two addresses in Settings → Commute. The Daily page has a Traffic to work tile; use Arrange to move, resize or hide it. Open its route link for live Google Maps traffic and travel estimates. No API key or account configuration is required. This version does not display live ETA inside the dashboard. Addresses are included in settings CSV backups and are sent to Google when opening the route.

## Live ETA and TV update

See **API_SETUP.md** for Google Routes setup, billing/quotas, two-address Work and School routes, and TV display instructions. Settings → Display includes TV view. Overflowing tile content loops automatically with hidden scrollbars.

## Theme, fonts and export update

Changing the selected theme pauses automatic night and Red Alert overrides. Re-enable those options in Display settings when desired. Typography now uses a consistent system sans-serif family with lighter numeric displays and clearer headings across all themes.

Settings → Backup → Export settings CSV… opens the browser Save As picker when supported (typically Chrome/Edge on localhost or HTTPS). Other browsers download using their normal settings. To force a location prompt in that case, enable “Ask where to save each file” in the browser's Downloads settings. Cancelling Save As cancels the export.

## Streamlined dashboard

The top page tabs and Daily heading are removed. The display opens the single Daily dashboard and automatic page rotation is disabled. Work and School estimates share a Travel times tile with separate labels. The Settings button and general TV text are smaller. The clock shows its active time-zone abbreviation and configured zone (set under Settings → Display). Existing extra-page data remains in backups, but those pages are no longer exposed in the navigation.

## Linear fonts, short pairing codes and extras

Settings → Display → Base font size sets dashboard text pixels at 1920px viewport width. Other widths scale linearly, with consistent proportional headings and numbers. Settings dialogs remain 16px for usable controls. Pairing tokens are now exactly eight URL-safe characters (letters, digits, dash and underscore), regenerated each launch.

Added eight themes: Aurora, Nebula, Amber Terminal, Deep Ocean, Solar Flare, Lunar, Forest and Retro Console. Added three optional tiles: Year in orbit, Daylight remaining and Mission progress. Enable optional tiles using Arrange → Show / hide panels. Year progress uses browser local time; daylight uses ZIP weather solar times; mission progress counts dashboard assignments and saved completions.

## Unified TV scaling

TV view uses a 1920×1080 reference canvas and fits the entire interface to the available browser viewport. Text, spacing, controls and tiles share one proportional scale, preserving the same composition as browser zoom varies. The font base remains configurable in Display settings. Fullscreen gives the best available area. Different aspect ratios use the available width/height while retaining the same type proportions. Turn TV view off to use ordinary browser zoom and saved manual layouts.

## Theme compositions and consolidated tiles

In TV view, themes now choose their own tile order, column proportions and shapes. TNG LCARS and LCARS Red Alert share exactly the same tile positions and sizes for the same visible tiles. Manual layouts outside TV view retain their saved positions. Year in Orbit appears at the bottom of the clock; Mission Progress is consolidated into the Assignment Log heading as the remaining count. The separate year/progress tiles are removed.

## Overflow and grid alignment

Cards now measure their rendered content against available interior height at the active TV scale. Content that fits stays still; overflow loops with matching content-copy spacing. Animations pause while arranging. Dragging and resizing snap to a visible grid: 1% of board width horizontally and 12 canvas pixels vertically. Save layout preserves your positions, including in TV view; a saved custom layout takes priority over theme presets.

## Restored tiles and theme identities

Arrange → Show / hide panels now lists every tile, including Radar, Workshop, Connection status, Class timetable, Sensors, Year in Orbit, Mission Progress and the optional separate School ETA. These remain available alongside the combined clock/progress and travel-time cards. Optional tiles start hidden on fresh setups. Save layout after selecting panels.

Non-TNG themes now vary row heights, tile order and column widths in automatic TV layouts, and use distinct header treatments, clipped corners, curved cards, borders and surfaces. Custom saved arrangements take precedence. LCARS and Red Alert keep matching geometry.

## Default layout repair and structural themes

This update resets the prior daily arrangement once, restoring the earlier nine-tile default: Travel times, Clock, Weather, Schedule, Assignments, Up next, Shipments, Countdowns and Trivia. All other tiles remain in Show / hide panels. Previous exported CSVs retain earlier arrangements if needed, but importing an older layout revision applies the repaired default.

LCARS and Red Alert share the same three-column geometry. Non-LCARS themes now use different feature-row structures and card architecture: side-mounted instrument labels, terminal frames, capsule headers, double borders, asymmetric panels and minimal open sections. A saved custom layout only applies to its theme family; switching themes shows the selected theme composition. Reset layout restores that theme’s default.

## Adaptive tile changes and calendar Class Times

In TV view, changing visible tiles through Arrange → Show / hide panels → Apply repacks the current theme layout to fit the selected tiles. This replaces the previous custom geometry when visibility changes. Click Save layout to persist. Moving/resizing without changing visibility retains your custom arrangement.

In Settings → Calendars, check **Use for Class Times** for each desired source (also available in Edit). The Class Times tile displays upcoming dates, start/end times, titles and locations from those enabled feeds. This is independent of Show on schedule and assignment mode. The calendar fetch range controls how far ahead classes load. The manually entered timetable remains saved, but Class Times now displays selected calendar events.

## Radar and shipment loading repair

Settings → Weather has the single shared ZIP for weather, radar, alerts and daylight. Routes still use their explicit address pairs. Radar accepts current hash-based paths and uses Universal Blue tiles; animation runs every six seconds and radar does not text-scroll. Refresh jobs publish as they finish so a slow source cannot hold completed mailbox data. Weather-dependent radar and alerts start as soon as weather succeeds. Each mailbox scan has an eight-second operation timeout and a 25-second scan deadline checked between messages, so at most one in-flight operation can exceed the deadline. The newest messages are checked first; a scan may stop before reaching the configured limit. Use a dedicated shipment folder for completeness and speed.

## Adding rows without rearranging tiles

Arrange → Add row extends the editor downward. Scroll with the wheel/touch, or drag empty grid space to pan. Only dragging a tile heading or resize handle changes that tile. Drag calculations account for page scroll. The editor opens the saved raw coordinates; Save layout fits the displayed rows vertically to the TV while preserving horizontal positions, widths, order and relative vertical placement. Showing extra tiles no longer repacks existing tiles. Empty editor space is temporary; move tiles into the new row before saving.

## Shipment tracking settings and local IP

Settings → Shipment Tracking controls maximum email age, per-account candidate scan cap, strict detection, blocked senders, assumed delivery age (0 disables it), and delivered retention. Rules apply across mailboxes. Assumed deliveries are labeled and use the last email date plus the configured age as their delivery time. This is not carrier confirmation. Maximum email age also removes older cached notices; manual orders are unaffected. Settings persist in CSV. Connection Status displays the detected IPv4 address of the Python host; multi-network computers may use their default outbound interface.
