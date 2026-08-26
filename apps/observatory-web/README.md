# Observatory Web Shell

Static MVP shell for the future Telperia Observatory website.

Open locally:

```bash
open apps/observatory-web/index.html
```

Or double-click `index.html` from Finder.

## What It Includes

- Company/home positioning.
- Public model directory grouped from seed result rows.
- Public model profile view with TCI category breakdowns, factual reliability breakdowns, hardware-specific Local IPW runs, throughput, energy, verification, methodology, limitations, and safe download status.
- Public comparison view for selecting two to four public model/hardware configurations side by side.
- Public Observatory seed results table.
- Clickable result detail view.
- Methodology overview.
- MVP status section.
- Local seed result data in `public-results.js` and `public-model-profiles.js` shaped like `docs/observatory-data-shape.md` and derived from `datasets/results/`.

Local IPW is shown primarily as the unscaled `TCI/Wh` value. The scaled value remains available as an explicitly labeled display score in result details.

Model profile package downloads are shown as a disabled placeholder until public reviewed download behavior exists. The static shell does not expose raw private result paths.

The comparison view uses current public-safe seed data. Latency and peak VRAM are shown as deferred/not-collected states until the runner records those measurements.

## What It Does Not Include Yet

- Hosted deployment.
- Supabase reads.
- Authentication.
- Upload forms.
- Community submissions.
- Reviewer workflow.

Those should come after Phase 6 backend ingestion is connected.
