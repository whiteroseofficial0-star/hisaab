export const SITE_NAME = 'Hisaab'
export const SITE_URL = ((import.meta.env.VITE_SITE_URL as string | undefined) ?? '').replace(/\/$/, '')

function baseUrl() {
  return SITE_URL || (typeof window !== 'undefined' ? window.location.origin : '')
}

function absolute(path: string) {
  const base = baseUrl()
  if (/^https?:\/\//.test(path)) return path
  return `${base}${path}`
}

export function organizationLd() {
  const base = baseUrl()
  return {
    '@type': 'Organization',
    '@id': `${base}/#organization`,
    name: SITE_NAME,
    url: `${base}/`,
    logo: { '@type': 'ImageObject', url: `${base}/og-image.png`, width: 1200, height: 630 },
  }
}

export function websiteLd() {
  const base = baseUrl()
  return {
    '@type': 'WebSite',
    '@id': `${base}/#website`,
    url: `${base}/`,
    name: SITE_NAME,
    inLanguage: 'en',
    publisher: { '@id': `${base}/#organization` },
  }
}

export function webApplicationLd(opts: { name: string; description: string; path: string; featureList?: string[] }) {
  return {
    '@type': 'WebApplication',
    name: opts.name,
    description: opts.description,
    url: absolute(opts.path),
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Any (web browser)',
    browserRequirements: 'Requires JavaScript',
    isAccessibleForFree: true,
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
    featureList: opts.featureList ?? [
      'Bank statement PDF to editable transactions',
      'Invoice PDF or image to details and line items',
      'Receipt batch extraction to a table',
      'PDF table extraction to Excel and CSV',
    ],
    publisher: { '@id': `${baseUrl()}/#organization` },
  }
}

export function howToLd(opts: { name: string; steps: string[]; path: string }) {
  return {
    '@type': 'HowTo',
    name: opts.name,
    step: opts.steps.map((text, i) => ({
      '@type': 'HowToStep',
      position: i + 1,
      name: `Step ${i + 1}`,
      text,
    })),
    totalTime: 'PT5M',
    tool: [{ '@type': 'HowToTool', name: 'A web browser' }],
    url: absolute(opts.path),
  }
}

export function articleLd(opts: { headline: string; description: string; path: string; image?: string; about?: string }) {
  const base = baseUrl()
  return {
    '@type': 'Article',
    headline: opts.headline,
    description: opts.description,
    mainEntityOfPage: { '@type': 'WebPage', '@id': absolute(opts.path) },
    image: absolute(opts.image ?? '/og-image.png'),
    inLanguage: 'en',
    author: { '@type': 'Organization', name: SITE_NAME, url: `${base}/` },
    publisher: { '@id': `${base}/#organization` },
    isPartOf: { '@id': `${base}/#website` },
    about: opts.about ? { '@type': 'Thing', name: opts.about } : undefined,
  }
}

export function collectionPageLd(opts: { name: string; description: string; path: string; items: { name: string; path: string }[] }) {
  return {
    '@type': 'CollectionPage',
    name: opts.name,
    description: opts.description,
    url: absolute(opts.path),
    inLanguage: 'en',
    isPartOf: { '@id': `${baseUrl()}/#website` },
    mainEntity: {
      '@type': 'ItemList',
      numberOfItems: opts.items.length,
      itemListElement: opts.items.map((item, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name: item.name,
        url: absolute(item.path),
      })),
    },
  }
}

export function webPageLd(opts: { name: string; description: string; path: string }) {
  return {
    '@type': 'WebPage',
    name: opts.name,
    description: opts.description,
    url: absolute(opts.path),
    inLanguage: 'en',
    isPartOf: { '@id': `${baseUrl()}/#website` },
  }
}
