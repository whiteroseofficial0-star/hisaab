import { readFileSync } from 'node:fs'
import { TOOLS } from './tools'
import { GUIDES } from './guides'

describe('sitemap paths', () => {
  it('script lists every tool and guide page, and titles/descriptions are unique', () => {
    const src = readFileSync('scripts/public-paths.mjs', 'utf8')
    TOOLS.forEach((t) => expect(src).toContain(`/tools/${t.slug}/`))
    GUIDES.forEach((g) => expect(src).toContain(`/guides/${g.slug}/`))
    const all = [...TOOLS.map((t) => t.title), ...GUIDES.map((g) => g.title)]
    expect(new Set(all).size).toBe(all.length)
    const d = [...TOOLS.map((t) => t.description), ...GUIDES.map((g) => g.description)]
    expect(new Set(d).size).toBe(d.length)
  })
})
