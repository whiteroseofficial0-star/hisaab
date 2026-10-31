import { describe, expect, it } from 'vitest'
import { articleLd, collectionPageLd, howToLd, webApplicationLd, webPageLd } from './seo'

describe('SEO structured data', () => {
  it('marks the converter as a free web application', () => {
    const ld = webApplicationLd({ name: 'Hisaab', description: 'Document to Excel', path: '/tools/' })
    expect(ld['@type']).toBe('WebApplication')
    expect(ld.offers.price).toBe('0')
    expect(ld.url).toMatch(/\/tools\/$/)
  })

  it('builds HowTo steps in order', () => {
    const ld = howToLd({ name: 'Convert', steps: ['Upload', 'Review', 'Export'], path: '/tools/x/' })
    expect(ld.step).toHaveLength(3)
    expect(ld.step[1]).toMatchObject({ position: 2, text: 'Review' })
  })

  it('builds collection and article markup', () => {
    const collection = collectionPageLd({ name: 'Tools', description: 'All tools', path: '/tools/', items: [{ name: 'A', path: '/tools/a/' }] })
    expect(collection.mainEntity.numberOfItems).toBe(1)
    const article = articleLd({ headline: 'Guide', description: 'How to', path: '/guides/a/' })
    expect(article['@type']).toBe('Article')
    expect(article.inLanguage).toBe('en')
  })

  it('builds basic web page markup', () => {
    expect(webPageLd({ name: 'About', description: 'About', path: '/about/' })['@type']).toBe('WebPage')
  })
})
