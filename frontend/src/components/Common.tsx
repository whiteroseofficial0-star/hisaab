import { Link } from 'react-router-dom'

export function Breadcrumbs({ items }: { items: { name: string; to?: string }[] }) {
  return (
    <nav aria-label="Breadcrumb" className="mb-8 font-mono text-[10px] uppercase tracking-[0.14em] text-ink-muted">
      <ol className="flex flex-wrap items-center gap-2">
        {items.map((it, i) => (
          <li key={it.name} className="flex items-center gap-2">
            {it.to ? <Link className="transition-colors hover:text-ink" to={it.to}>{it.name}</Link> : <span className="text-ink" aria-current="page">{it.name}</span>}
            {i < items.length - 1 && <span aria-hidden className="text-ink-muted/40">/</span>}
          </li>
        ))}
      </ol>
    </nav>
  )
}

export function Faqs({ faqs }: { faqs: { q: string; a: string }[] }) {
  return (
    <section aria-labelledby="faq-h">
      <h2 id="faq-h" className="text-3xl">Frequently asked questions</h2>
      <div className="mt-6 border-t border-line">
        {faqs.map((f) => (
          <details key={f.q} className="group border-b border-line">
            <summary className="flex cursor-pointer items-start justify-between gap-6 py-5 text-[15px] font-medium text-ink">
              <span>{f.q}</span>
              <span className="faq-plus mt-0.5 shrink-0 font-sans text-xl font-light leading-none text-pine-700 transition-transform duration-200" aria-hidden>+</span>
            </summary>
            <p className="max-w-2xl pb-5 pr-8 text-sm leading-7 text-ink-soft">{f.a}</p>
          </details>
        ))}
      </div>
    </section>
  )
}

/** Optional ad slot for public marketing/guide pages only. Renders nothing unless VITE_ADS_ENABLED=true.
 *  No ad network code is included; wire your own provider here. Never place on tool/review screens. */
export function AdSlot({ id }: { id: string }) {
  if (import.meta.env.VITE_ADS_ENABLED !== 'true') return null
  return (
    <aside aria-label="Advertisement" className="my-10 border-y border-line py-4 text-center">
      <p className="eyebrow text-ink-muted">Advertisement</p>
      <div data-ad-slot={id} className="min-h-[90px]" />
    </aside>
  )
}
