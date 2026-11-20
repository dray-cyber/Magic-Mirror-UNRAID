# Live ETA setup — Work and School

The two tiles display traffic-aware driving minutes if you leave now. Each trip has its own starting address and destination. Google supplies the estimate; traffic data availability varies. No requests are sent until you enable the integration and supply a key.

1. Open https://console.cloud.google.com/ and create/select a project, for example “Mirror dashboard”.
2. Open Billing and link a billing account to the project. Google Routes requires billing; do not assume usage is free.
3. In APIs & Services → Library, search for **Routes API** and enable it.
4. In APIs & Services → Credentials, create an API key. Edit its API restrictions to allow **Routes API only**. This dashboard calls Google from Python on your computer, so browser/referrer restrictions are unsuitable. If you have a stable public outbound IP, use an IP restriction for that address.
5. Review current pricing: https://developers.google.com/maps/documentation/routes/usage-and-billing . Traffic-aware routing uses the Pro tier. Set a Routes API quota appropriate to your budget; create billing alerts as well. Budget alerts alone do not stop spending.
6. Launch the updated dashboard. In **Settings → Commute**, paste the key and enter the four address fields: work starting address, work destination, school starting address, school destination. Include city/state/ZIP to avoid ambiguous locations.
7. Enable Google Routes requests and Save. Click Refresh once. The two tiles should display minutes, with a last-update label. Disable requests here whenever you want to stop route polling.

The dashboard requests one route per complete address pair on each refresh. With two routes and a five-minute refresh, continuous operation is approximately 576 requests/day (17,280 per 30 days), plus manual refreshes. The shared refresh interval is in Settings → Calendars; 15 minutes reduces automatic requests to about 192/day. These are request counts, not price quotes. Disabling or hiding a tile does not stop API usage: turn off the Routes integration to stop requests. Closing Python also stops requests.

The key is saved in your private CSV and visible in Commute settings. Normal dashboard responses omit it. Addresses are sent to Google when enabled. No key or live paid service was used during development; request behavior is tested with fixtures.

If a tile displays unavailable: check the key restriction, API enablement, billing, quota and addresses, then Refresh. Allow a few minutes after enabling a new API. Never send your key in a screenshot or troubleshooting message.

Official setup: https://developers.google.com/maps/documentation/routes/get-api-key

# TV readability

Settings → Display → **TV view** fits visible tiles into a three-column screen grid (two columns on smaller screens), with larger type. Use Show / hide panels to reduce the number of visible tiles for greater readability. TV view prioritizes fitting the screen; turn it off to use your saved free-position layout. Arrange temporarily exits the fitted view so panels can be selected and hidden.

Tile content overflowing its card moves vertically in a repeating seamless loop; pointer hover pauses it. Scrollbars are hidden. Settings menus retain normal touch/wheel scrolling without visible scrollbar tracks. Browser zoom and fullscreen can be used for the TV. The interface cannot guarantee comfortable reading with every panel visible at every resolution: hide less-used tiles or use separate Daily/School/Workshop pages.
