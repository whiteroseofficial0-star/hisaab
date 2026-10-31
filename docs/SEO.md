# SEO notes

## What is implemented

- Unique title and meta description per route, one visible H1, semantic headings, breadcrumbs and internal links.
- Canonical URL, Open Graph and Twitter `summary_large_image` cards, branded 1200×630 `og-image.png`.
- JSON-LD graph on every page: `Organization`, `WebSite`, plus the page type:
  - Home: `WebApplication` with a free offer and feature list.
  - Tool pages: `WebApplication`, `HowTo`, `BreadcrumbList`, `FAQPage`.
  - Tool index: `CollectionPage` + `ItemList`.
  - Guide index: `CollectionPage` + `ItemList`.
  - Guide pages: `Article` + `BreadcrumbList`.
  - About / privacy / terms / contact: `WebPage` + `BreadcrumbList`.
- 404 tool/guide URLs are marked `noindex, follow`.
- `sitemap.xml` and `robots.txt` are generated from `public-paths.mjs`; `/api/` is disallowed.
- Public metadata is indexed per route, not only on `/`.

## Production build with prerendering

The app is still a React SPA, but production builds can be statically prerendered so non-JavaScript crawlers and social previews receive the real page HTML:

```powershell
cd frontend
$env:SITE_URL = "https://your-domain.example"
$env:VITE_SITE_URL = "https://your-domain.example"
npm run build:seo
```

`build:seo` runs the normal build, then `scripts/prerender.mjs` loads every public route from `vite preview` and writes `dist/<route>/index.html`. It uses system Chrome by default; set `PRERENDER_EXECUTABLE` to a Chromium binary when Chrome is not installed.

The Docker build currently runs `npm run build`, not `build:seo`, so prerendering is opt-in. If you deploy with Docker and want the prerendered HTML, add Chromium to the build image and change the Dockerfile build command to `npm run build:seo`, or run the prerender step in CI and copy the resulting `dist`.

Without prerendering, Google can still render the client-side app, but indexing is slower and less reliable. Social previews may show the generic homepage card.

## Search Console setup

1. Deploy with HTTPS on your real domain; build with `SITE_URL` and `VITE_SITE_URL` set to that domain.
2. In Google Search Console add a domain property (DNS TXT) and verify it.
3. Submit `https://your-domain/sitemap.xml`.
4. Use URL Inspection on `/`, one tool page and one guide; check "Page indexing" and "Rich results".
5. Re-check after the first crawl for `FAQPage`, `HowTo`, `Article` and breadcrumb eligibility. Google may not show rich results for every eligible page.

## Content and keyword structure

Keep one page per search intent and avoid near-duplicate pages:

| Intent | Example query | Page |
|---|---|---|
| Bank statement to spreadsheet | `bank statement to excel` | `/tools/bank-statement-to-excel/` |
| Scanned statement / OCR | `scanned bank statement to excel` | `/tools/pdf-bank-statement-converter/` + OCR guide |
| Invoice extraction | `invoice pdf to excel` | `/tools/invoice-to-excel/` |
| Receipt batch | `receipt to excel` | `/tools/receipt-to-excel/` |
| PDF tables | `extract table from pdf to excel` | `/tools/pdf-table-extractor/` |
| Generic CSV | `pdf to csv` | `/tools/pdf-to-csv/` |

For each page: one primary phrase in the title, H1 and first paragraph; related phrases in subheadings, FAQs and internal links. Do not repeat the same page for several slugs without distinct content.

## Off-page basics

- Publish a clear `About` page and a real contact route.
- Get listed in relevant open-source and self-hosting directories.
- Link to the tool pages from guides with descriptive anchor text (already done).
- Do not buy spammy links or publish auto-generated location pages.

## Caveats

- No ranking, traffic or indexing outcome is promised.
- `lastmod` is intentionally not written to the sitemap unless content dates are maintained. A build timestamp on every deploy is not a useful freshness signal.
