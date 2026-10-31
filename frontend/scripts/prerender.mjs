/**
 * Optional static prerender for the public pages.
 *
 * The app is client-rendered, so crawlers that do not execute JavaScript only see the
 * generic index.html shell. This script loads every public route from a production
 * preview build and writes the rendered HTML back to dist/<route>/index.html.
 *
 * Usage:
 *   SITE_URL=https://example.com npm run build:seo
 *
 * It needs a Chromium-based browser. It uses system Chrome by default; set
 * PRERENDER_EXECUTABLE to a Chromium binary if Chrome is not installed.
 */
import { spawn } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { chromium } from 'playwright'
import { PATHS } from './public-paths.mjs'

const port = process.env.PRERENDER_PORT || '4173'
const base = `http://127.0.0.1:${port}`
const site = process.env.SITE_URL || process.env.VITE_SITE_URL || ''
const viteBin = join(process.cwd(), 'node_modules', 'vite', 'bin', 'vite.js')

if (!site) {
  console.warn('SITE_URL is not set. Prerendered canonical/OG URLs will point at the local preview host.')
}

const server = spawn(process.execPath, [viteBin, 'preview', '--host', '127.0.0.1', '--port', port, '--strictPort'], {
  stdio: 'pipe',
  windowsHide: true,
})

server.stdout.on('data', (chunk) => process.stdout.write(chunk))
server.stderr.on('data', (chunk) => process.stderr.write(chunk))

async function waitForServer() {
  for (let i = 0; i < 80; i += 1) {
    try {
      const res = await fetch(base)
      if (res.ok) return
    } catch {
      // not listening yet
    }
    await new Promise((resolve) => setTimeout(resolve, 250))
  }
  throw new Error(`Preview server did not start on ${base}`)
}

async function launchBrowser() {
  if (process.env.PRERENDER_EXECUTABLE) {
    return chromium.launch({ executablePath: process.env.PRERENDER_EXECUTABLE })
  }
  try {
    return await chromium.launch({ channel: 'chrome' })
  } catch {
    return chromium.launch()
  }
}

let browser
try {
  await waitForServer()
  browser = await launchBrowser()
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } })

  for (const path of PATHS) {
    await page.goto(`${base}${path}`, { waitUntil: 'networkidle' })
    await page.waitForSelector('#main h1', { timeout: 15000 })
    await page.waitForTimeout(100)

    const html = await page.content()
    const out = path === '/' ? join('dist', 'index.html') : join('dist', path.replace(/^\//, ''), 'index.html')
    mkdirSync(dirname(out), { recursive: true })
    writeFileSync(out, html)
    console.log(`prerendered ${path} -> ${out}`)
  }

  console.log(`Prerendered ${PATHS.length} public pages.`)
} finally {
  await browser?.close()
  server.kill()
}
