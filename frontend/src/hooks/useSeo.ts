import { useEffect } from 'react'
import { SITE_NAME, SITE_URL, organizationLd, websiteLd } from '../lib/seo'

export { SITE_URL } from '../lib/seo'

function setMeta(attr: 'name' | 'property', key: string, content: string) {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`)
  if (!el) { el = document.createElement('meta'); el.setAttribute(attr, key); document.head.appendChild(el) }
  el.setAttribute('content', content)
}

function removeMeta(attr: 'name' | 'property', key: string) {
  document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`)?.remove()
}

function absolute(base: string, path: string) {
  return /^https?:\/\//.test(path) ? path : `${base}${path}`
}

/** Per-page title, description, canonical, social cards and JSON-LD. */
export function useSeo(opts: {
  title: string
  description: string
  path: string
  jsonLd?: object[]
  type?: 'website' | 'article'
  image?: string
  noindex?: boolean
  publishedTime?: string
  modifiedTime?: string
}) {
  const { title, description, path } = opts
  const ld = JSON.stringify(opts.jsonLd ?? [])
  const type = opts.type ?? 'website'
  const image = opts.image ?? '/og-image.png'
  const noindex = Boolean(opts.noindex)

  useEffect(() => {
    const base = SITE_URL || window.location.origin
    const url = `${base}${path}`
    const imageUrl = absolute(base, image)

    document.documentElement.lang = 'en'
    document.title = title

    setMeta('name', 'description', description)
    setMeta('name', 'robots', noindex ? 'noindex, follow' : 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1')
    setMeta('name', 'application-name', SITE_NAME)

    setMeta('property', 'og:title', title)
    setMeta('property', 'og:description', description)
    setMeta('property', 'og:type', type)
    setMeta('property', 'og:url', url)
    setMeta('property', 'og:site_name', SITE_NAME)
    setMeta('property', 'og:locale', 'en_US')
    setMeta('property', 'og:image', imageUrl)
    setMeta('property', 'og:image:secure_url', imageUrl)
    setMeta('property', 'og:image:width', '1200')
    setMeta('property', 'og:image:height', '630')
    setMeta('property', 'og:image:alt', `${SITE_NAME} - financial documents to Excel`)

    setMeta('name', 'twitter:card', 'summary_large_image')
    setMeta('name', 'twitter:title', title)
    setMeta('name', 'twitter:description', description)
    setMeta('name', 'twitter:image', imageUrl)
    setMeta('name', 'twitter:image:alt', `${SITE_NAME} - financial documents to Excel`)

    if (opts.publishedTime) setMeta('property', 'article:published_time', opts.publishedTime)
    else removeMeta('property', 'article:published_time')
    if (opts.modifiedTime) setMeta('property', 'article:modified_time', opts.modifiedTime)
    else removeMeta('property', 'article:modified_time')

    let link = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')
    if (!link) { link = document.createElement('link'); link.rel = 'canonical'; document.head.appendChild(link) }
    link.href = url

    document.head.querySelectorAll('script[data-seo]').forEach((n) => n.remove())
    const graph = [organizationLd(), websiteLd(), ...JSON.parse(ld)]
    const s = document.createElement('script')
    s.type = 'application/ld+json'
    s.dataset.seo = '1'
    s.text = JSON.stringify({ '@context': 'https://schema.org', '@graph': graph })
    document.head.appendChild(s)

    return () => { document.head.querySelectorAll('script[data-seo]').forEach((n) => n.remove()) }
  }, [title, description, path, ld, type, image, noindex, opts.publishedTime, opts.modifiedTime])
}

export function breadcrumbLd(items: { name: string; path: string }[]) {
  const base = SITE_URL || (typeof window !== 'undefined' ? window.location.origin : '')
  return {
    '@type': 'BreadcrumbList',
    itemListElement: items.map((it, i) => ({ '@type': 'ListItem', position: i + 1, name: it.name, item: `${base}${it.path}` })),
  }
}
