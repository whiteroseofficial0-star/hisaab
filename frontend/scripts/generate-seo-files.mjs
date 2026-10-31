// Runs after `vite build`: writes dist/sitemap.xml and dist/robots.txt using SITE_URL.
// Only public pages are listed; job/processing URLs never exist as routes and are never listed.
import { writeFileSync, mkdirSync } from 'node:fs'
import { PATHS } from './public-paths.mjs'

const site = (process.env.SITE_URL || process.env.VITE_SITE_URL || '').replace(/\/$/, '')
mkdirSync('dist', { recursive: true })
if (!site) {
  console.warn('SITE_URL not set: writing robots.txt without a Sitemap line and skipping sitemap.xml')
  writeFileSync('dist/robots.txt', 'User-agent: *\nAllow: /\n')
} else {
  const urls = PATHS.map((p) => `  <url><loc>${site}${p}</loc></url>`).join('\n')
  writeFileSync('dist/sitemap.xml', `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`)
  writeFileSync('dist/robots.txt', `User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: ${site}/sitemap.xml\n`)
  console.log(`Wrote sitemap.xml (${PATHS.length} URLs) and robots.txt for ${site}`)
}
