import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'
import Workbench from '../features/Workbench'
import { AdSlot, Breadcrumbs, Faqs } from '../components/Common'
import { breadcrumbLd, useSeo } from '../hooks/useSeo'
import { articleLd, collectionPageLd, howToLd, webApplicationLd, webPageLd } from '../lib/seo'
import { TOOLS, toolBySlug, toolPath } from '../data/tools'
import { GUIDES, guideBySlug } from '../data/guides'
import type { ToolKey, FileKind } from '../types'

const HOME_FAQS = [
  { q: 'Is Hisaab free?', a: 'Yes. The core conversion tools are free and open source, with no account needed.' },
  { q: 'Is my document used to train AI?', a: 'No. Documents are processed by open-source OCR and parsing tools on the server and are never used for training or sent to third-party AI services by default.' },
  { q: 'How accurate is it?', a: 'Digital PDFs are usually read well; scans and photos depend on quality. OCR is never 100% accurate, which is why every result is editable and checked before export.' },
  { q: 'How long are my files kept?', a: 'Until the job expires (60 minutes by default on a standard setup) or you press "Delete my data", whichever comes first.' },
]
const HOME_MODES: { key: string; label: string; tool: ToolKey; accept: FileKind[]; multiple: boolean }[] = [
  { key: 'bank', label: 'Bank statement', tool: 'bank_statement', accept: ['pdf'], multiple: false },
  { key: 'invoice', label: 'Invoice', tool: 'invoice', accept: ['pdf', 'jpeg', 'png', 'webp'], multiple: false },
  { key: 'receipt', label: 'Receipts', tool: 'receipt', accept: ['pdf', 'jpeg', 'png', 'webp'], multiple: true },
  { key: 'tables', label: 'PDF tables', tool: 'tables', accept: ['pdf'], multiple: false },
]
const HOME_TOOLS = TOOLS.filter((t, i, all) => all.findIndex((x) => x.tool === t.tool) === i)
const PROCESS = [
  { title: 'Upload', body: 'Choose a file. Type, size and signature are checked before anything runs.' },
  { title: 'Review', body: 'The original sits beside the extracted table. Uncertain rows are marked "Check".' },
  { title: 'Export', body: 'Your corrections are written into the Excel or CSV file you download.' },
]

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="eyebrow">{children}</p>
}

export function Home() {
  const [mode, setMode] = useState(HOME_MODES[0])
  useSeo({
    title: 'Hisaab - Convert Documents. Extract Data. Export to Excel.', path: '/',
    description: 'Turn bank statement PDFs, invoices and receipts into editable tables and Excel or CSV files. Open source, privacy-first, no sign-up.',
    jsonLd: [webApplicationLd({
      name: 'Hisaab - Document to Excel',
      description: 'Convert bank statements, invoices, receipts and PDF tables into editable data and Excel or CSV files.',
      path: '/',
    })],
  })

  return (
    <>
      <section className="border-b border-line">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-12 px-5 pb-12 pt-12 lg:grid-cols-[1.02fr_0.98fr] lg:items-start lg:gap-16 lg:pb-16 lg:pt-16">
          <div className="min-w-0 lg:pt-4">
            <SectionLabel>Open-source document conversion</SectionLabel>
            <h1 className="mt-6 max-w-xl text-[clamp(2.9rem,5.6vw,4.55rem)] leading-[0.98]">
              Financial documents,{' '}
              <em className="text-pine-700">turned into spreadsheets.</em>
            </h1>
            <p className="mt-6 max-w-lg text-[17px] leading-8 text-ink-soft">
              Upload a bank statement, invoice, receipt or PDF table. Review the extracted data
              beside the original, correct what needs correcting, then export a real Excel or CSV
              file.
            </p>
            <p className="mt-5 max-w-md text-sm leading-6 text-ink-muted">
              No sign-up. No cloud AI. No document sitting around after you are done.
            </p>
          </div>

          <div id="convert" className="min-w-0 scroll-mt-24">
            <div className="border border-line bg-surface shadow-[0_30px_80px_-55px_rgba(28,40,35,0.55)]">
              <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
                <p className="eyebrow">Conversion desk</p>
                <span className="font-mono text-[10px] tracking-[0.12em] text-ink-muted">01 — 04</span>
              </div>

              <div role="tablist" aria-label="Document type" className="grid grid-cols-2 border-b border-line sm:grid-cols-4">
                {HOME_MODES.map((m, i) => {
                  const active = mode.key === m.key
                  return (
                    <button
                      key={m.key}
                      role="tab"
                      type="button"
                      aria-selected={active}
                      onClick={() => setMode(m)}
                      className={`relative flex flex-col items-start gap-1 border-b border-line px-3 py-3 text-left transition-colors last:border-r-0 sm:border-b-0 sm:border-r ${
                        active ? 'bg-paper text-ink' : 'text-ink-muted hover:bg-paper/60 hover:text-ink'
                      }`}
                    >
                      <span className={`font-mono text-[9px] tracking-[0.14em] ${active ? 'text-pine-700' : 'text-ink-muted/70'}`}>
                        {String(i + 1).padStart(2, '0')}
                      </span>
                      <span className="text-[12px] font-medium leading-tight">{m.label}</span>
                      {active && <span className="absolute inset-x-0 bottom-[-1px] h-0.5 bg-pine-700" aria-hidden />}
                    </button>
                  )
                })}
              </div>

              <div className="p-5 sm:p-6">
                <Workbench key={mode.key} tool={mode.tool} accept={mode.accept} multiple={mode.multiple} />
              </div>
            </div>

            <p className="mt-3 flex items-center justify-between font-mono text-[9px] uppercase tracking-[0.14em] text-ink-muted">
              <span>Private by default</span>
              <span>Files expire automatically</span>
            </p>
          </div>
        </div>

        <dl className="border-t border-line">
          <div className="mx-auto grid max-w-6xl grid-cols-2 gap-y-6 px-5 py-6 sm:grid-cols-4 sm:divide-x sm:divide-line">
            {[
              ['Accepted', 'PDF · JPG · PNG · WebP'],
              ['Account', 'Not required'],
              ['Retention', 'Expires in 60 minutes'],
              ['Output', 'XLSX · CSV'],
            ].map(([k, v]) => (
              <div key={k} className="sm:px-7 sm:first:pl-0 sm:last:pr-0">
                <dt className="font-mono text-[9px] uppercase tracking-[0.18em] text-ink-muted">{k}</dt>
                <dd className="mt-1.5 text-[13px] font-medium text-ink">{v}</dd>
              </div>
            ))}
          </div>
        </dl>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16 lg:py-20">
        <div className="flex flex-col gap-5 border-b border-line pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <SectionLabel>01 / Tools</SectionLabel>
            <h2 className="mt-3 text-4xl">Four ways in.</h2>
          </div>
          <Link to="/tools/" className="group inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-ink-muted transition-colors hover:text-ink">
            All tools <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" aria-hidden />
          </Link>
        </div>

        <div className="border-b border-line">
          {HOME_TOOLS.map((t, i) => (
            <Link
              key={t.slug}
              to={toolPath(t.slug)}
              className="group -mx-3 grid grid-cols-[2rem_1fr_auto] items-start gap-4 border-b border-line px-3 py-6 transition-colors last:border-b-0 hover:bg-surface sm:grid-cols-[2.5rem_1fr_10rem_1rem] sm:items-center sm:gap-6"
            >
              <span className="pt-1 font-mono text-[10px] tracking-[0.12em] text-ink-muted sm:pt-0">{String(i + 1).padStart(2, '0')}</span>
              <div>
                <h3 className="text-[17px] font-medium text-ink transition-colors group-hover:text-pine-700">{t.name}</h3>
                <p className="mt-1 max-w-2xl text-sm leading-6 text-ink-soft">{t.intro.split('. ')[0]}.</p>
              </div>
              <p className="hidden font-mono text-[10px] uppercase tracking-[0.12em] text-ink-muted sm:block">{t.formats}</p>
              <ArrowUpRight className="h-4 w-4 text-ink-muted transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-pine-700" aria-hidden />
            </Link>
          ))}
        </div>
      </section>

      <section className="border-y border-line bg-surface">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-12 px-5 py-16 lg:grid-cols-[0.8fr_1.2fr] lg:py-20">
          <div>
            <SectionLabel>02 / Process</SectionLabel>
            <h2 className="mt-4 max-w-sm text-4xl leading-[1.05]">The review step is the product.</h2>
            <p className="mt-5 max-w-sm text-sm leading-7 text-ink-soft">
              Automatic extraction is a first draft. Hisaab keeps the original beside the result so
              you can spot a misread digit before it reaches your books.
            </p>
          </div>

          <ol className="grid grid-cols-1 gap-8 sm:grid-cols-3 sm:gap-0">
            {PROCESS.map((step, i) => (
              <li key={step.title} className="border-line sm:border-l sm:pl-6">
                <p className="font-display text-4xl leading-none text-pine-700">{String(i + 1).padStart(2, '0')}</p>
                <h3 className="mt-5 text-sm font-semibold text-ink">{step.title}</h3>
                <p className="mt-2 text-sm leading-6 text-ink-soft">{step.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="bg-ink text-paper">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-10 px-5 py-16 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:py-20">
          <div>
            <p className="eyebrow text-pine-300">03 / Privacy</p>
            <h2 className="mt-4 max-w-lg text-4xl leading-[1.05] text-paper">Your documents are not training data.</h2>
          </div>
          <div>
            <p className="max-w-xl text-sm leading-7 text-slate-300">
              Files are processed on this server with open-source text extraction and OCR. They are
              not sent to third-party AI services, not used for training, and not kept in a public
              folder. Every job has a secret token and can be deleted at any time.
            </p>
            <ul className="mt-7 grid grid-cols-1 gap-x-8 gap-y-3 border-t border-pine-900 pt-6 text-[13px] text-paper sm:grid-cols-2">
              {['Processed on this server', 'No third-party AI', 'Jobs expire automatically', 'Delete on demand'].map((item) => (
                <li key={item} className="flex items-center gap-2.5">
                  <span className="h-1 w-1 bg-pine-300" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
            <Link to="/privacy/" className="mt-6 inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-pine-200 transition-colors hover:text-paper">
              Read the privacy note <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
            </Link>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-5 py-16 lg:py-20">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <SectionLabel>04 / Questions</SectionLabel>
            <h2 className="mt-4 text-4xl">Good to know.</h2>
            <p className="mt-5 max-w-xs text-sm leading-7 text-ink-soft">
              The short version of how the desk handles files, accuracy and retention.
            </p>
          </div>
          <Faqs faqs={HOME_FAQS} />
        </div>

        <div className="mt-16 border-t border-line pt-10">
          <div className="flex items-end justify-between gap-6">
            <div>
              <SectionLabel>05 / Guides</SectionLabel>
              <h2 className="mt-3 text-3xl">From the reading room.</h2>
            </div>
            <Link to="/guides/" className="group hidden items-center gap-2 font-mono text-[10px] uppercase tracking-[0.14em] text-ink-muted transition-colors hover:text-ink sm:inline-flex">
              All guides <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" aria-hidden />
            </Link>
          </div>
          <ul className="mt-6 grid grid-cols-1 gap-x-10 border-b border-line sm:grid-cols-2">
            {GUIDES.slice(0, 4).map((g, i) => (
              <li key={g.slug} className="border-b border-line sm:last:border-b">
                <Link to={`/guides/${g.slug}/`} className="group flex items-baseline gap-4 py-4">
                  <span className="font-mono text-[10px] tracking-[0.12em] text-ink-muted">{String(i + 1).padStart(2, '0')}</span>
                  <span className="flex-1 text-sm font-medium text-ink transition-colors group-hover:text-pine-700">{g.h1}</span>
                  <ArrowUpRight className="h-3.5 w-3.5 shrink-0 text-ink-muted transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" aria-hidden />
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <AdSlot id="home-bottom" />
      </div>
    </>
  )
}

export function ToolsIndex() {
  const description = 'Every Hisaab converter in one place: bank statement, invoice, receipt and PDF table extraction to Excel and CSV.'
  useSeo({ title: 'All Hisaab Tools: Bank Statements, Invoices, Receipts, PDF Tables', path: '/tools/',
    description,
    jsonLd: [
      breadcrumbLd([{ name: 'Home', path: '/' }, { name: 'Tools', path: '/tools/' }]),
      collectionPageLd({
        name: 'Hisaab document converters',
        description,
        path: '/tools/',
        items: TOOLS.map((t) => ({ name: t.name, path: toolPath(t.slug) })),
      }),
    ] })

  return (
    <div className="mx-auto max-w-5xl px-5 py-10">
      <Breadcrumbs items={[{ name: 'Home', to: '/' }, { name: 'Tools' }]} />
      <div className="border-b border-line pb-8">
        <SectionLabel>Index</SectionLabel>
        <h1 className="mt-4 text-[clamp(2.4rem,5vw,3.5rem)] leading-none">Every tool, one desk.</h1>
        <p className="mt-4 max-w-xl text-[15px] leading-7 text-ink-soft">
          Pick the converter that matches the document in front of you. Each one leads to the same
          review-and-export workspace.
        </p>
      </div>

      <div className="mt-2 border-b border-line">
        {TOOLS.map((t, i) => (
          <Link key={t.slug} to={toolPath(t.slug)} className="group grid grid-cols-[2rem_1fr_auto] items-start gap-4 border-b border-line py-5 transition-colors last:border-b-0 hover:bg-surface sm:grid-cols-[2.5rem_1fr_10rem_1rem] sm:items-center sm:gap-6">
            <span className="pt-1 font-mono text-[10px] tracking-[0.12em] text-ink-muted sm:pt-0">{String(i + 1).padStart(2, '0')}</span>
            <div>
              <h2 className="font-sans text-[15px] font-medium text-ink transition-colors group-hover:text-pine-700">{t.name}</h2>
              <p className="mt-1 max-w-xl text-sm leading-6 text-ink-soft">{t.intro.split('. ')[0]}.</p>
            </div>
            <p className="hidden font-mono text-[10px] uppercase tracking-[0.12em] text-ink-muted sm:block">{t.formats}</p>
            <ArrowUpRight className="h-4 w-4 text-ink-muted transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-pine-700" aria-hidden />
          </Link>
        ))}
      </div>
    </div>
  )
}

export function ToolPage() {
  const { slug } = useParams()
  const t = toolBySlug(slug)
  const path = t ? toolPath(t.slug) : '/tools/'
  useSeo({
    title: t?.title ?? 'Tool not found | Hisaab', description: t?.description ?? 'This tool page does not exist.', path,
    noindex: !t,
    jsonLd: t ? [
      webApplicationLd({ name: `Hisaab - ${t.name}`, description: t.description, path }),
      howToLd({ name: t.h1, steps: t.steps, path }),
      breadcrumbLd([{ name: 'Home', path: '/' }, { name: 'Tools', path: '/tools/' }, { name: t.name, path }]),
      { '@type': 'FAQPage', mainEntity: t.faqs.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })) },
    ] : [],
  })
  if (!t) return <div className="mx-auto max-w-3xl px-5 py-16"><h1 className="text-3xl">Tool not found</h1><p className="mt-4"><Link className="text-pine-700 underline underline-offset-2" to="/tools/">See all tools</Link></p></div>
  const related = t.related.map((s) => toolBySlug(s)).filter(Boolean)

  return (
    <>
      <section className="border-b border-line bg-surface">
        <div className="mx-auto max-w-5xl px-5 pb-12 pt-10">
          <Breadcrumbs items={[{ name: 'Home', to: '/' }, { name: 'Tools', to: '/tools/' }, { name: t.name }]} />
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_16rem] lg:items-end">
            <div>
              <SectionLabel>Converter</SectionLabel>
              <h1 className="mt-4 max-w-3xl text-[clamp(2.35rem,5vw,3.6rem)] leading-[1.02]">{t.h1}</h1>
              <p className="mt-5 max-w-2xl text-[16px] leading-8 text-ink-soft">{t.intro}</p>
            </div>
            <dl className="hidden border-l border-line pl-6 lg:block">
              <dt className="font-mono text-[9px] uppercase tracking-[0.18em] text-ink-muted">Formats</dt>
              <dd className="mt-2 text-[13px] font-medium text-ink">{t.formats}</dd>
              <dt className="mt-5 font-mono text-[9px] uppercase tracking-[0.18em] text-ink-muted">Output</dt>
              <dd className="mt-2 text-[13px] font-medium text-ink">Excel · CSV</dd>
              <dt className="mt-5 font-mono text-[9px] uppercase tracking-[0.18em] text-ink-muted">Account</dt>
              <dd className="mt-2 text-[13px] font-medium text-ink">Not required</dd>
            </dl>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-5xl px-5 py-10">
        <div className="border border-line bg-surface p-5 sm:p-6">
          <div className="mb-5 flex items-center justify-between border-b border-line pb-3.5">
            <p className="eyebrow">Conversion desk</p>
            <span className="font-mono text-[10px] tracking-[0.12em] text-ink-muted">{t.formats}</span>
          </div>
          <Workbench key={t.slug} tool={t.tool} accept={t.accept} multiple={t.multiple} />
        </div>

        <div className="mt-16 grid grid-cols-1 gap-12 lg:grid-cols-[0.62fr_1.38fr]">
          <div>
            <SectionLabel>Method</SectionLabel>
            <h2 className="mt-3 text-3xl">How to use it</h2>
            <ol className="mt-6 space-y-5">
              {t.steps.map((s, i) => (
                <li key={s} className="flex gap-4">
                  <span className="font-mono text-[10px] tracking-[0.12em] text-pine-700">{String(i + 1).padStart(2, '0')}</span>
                  <span className="text-sm leading-6 text-ink-soft">{s}</span>
                </li>
              ))}
            </ol>
            <p className="mt-6 border-t border-line pt-4 font-mono text-[10px] uppercase leading-5 tracking-[0.12em] text-ink-muted">
              Supported: {t.formats}
            </p>
          </div>

          <div className="prose-hisaab">
            {t.details.map((d) => <section key={d.h}><h2>{d.h}</h2><p>{d.p}</p></section>)}
            <section>
              <h2>Accuracy and limitations</h2>
              <p>Extraction is automatic and not perfect. OCR in particular can misread characters, so check amounts against the original before you rely on them.</p>
              <ul>{t.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
            </section>
            <section>
              <h2>Privacy</h2>
              <p>Your file is processed on the server with open-source tools, is not sent to third-party AI services, and is deleted when it expires or when you choose “Delete my data”. <Link to="/privacy/">Read the details</Link>.</p>
            </section>
          </div>
        </div>

        <AdSlot id={`tool-${t.slug}`} />

        <div className="mt-12">
          <Faqs faqs={t.faqs} />
        </div>

        <section className="mt-14 border-t border-line pt-8" aria-labelledby="rel">
          <h2 id="rel" className="text-2xl">Related</h2>
          <ul className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {related.map((r) => r && (
              <li key={r.slug}>
                <Link className="group flex items-center justify-between gap-4 border-b border-line py-3 text-sm text-ink transition-colors hover:text-pine-700" to={toolPath(r.slug)}>
                  {r.name}
                  <ArrowUpRight className="h-3.5 w-3.5 text-ink-muted" aria-hidden />
                </Link>
              </li>
            ))}
            {t.guide && (
              <li>
                <Link className="group flex items-center justify-between gap-4 border-b border-line py-3 text-sm text-ink transition-colors hover:text-pine-700" to={`/guides/${t.guide}/`}>
                  Guide: {guideBySlug(t.guide)?.h1}
                  <ArrowUpRight className="h-3.5 w-3.5 text-ink-muted" aria-hidden />
                </Link>
              </li>
            )}
          </ul>
        </section>
      </div>
    </>
  )
}

export function GuidesIndex() {
  const description = 'Practical guides on converting financial documents to Excel, working with scans and OCR, and checking the results.'
  useSeo({ title: 'Guides: Convert Bank Statements, Invoices and Receipts to Excel', path: '/guides/',
    description,
    jsonLd: [
      breadcrumbLd([{ name: 'Home', path: '/' }, { name: 'Guides', path: '/guides/' }]),
      collectionPageLd({
        name: 'Hisaab guides',
        description,
        path: '/guides/',
        items: GUIDES.map((g) => ({ name: g.h1, path: `/guides/${g.slug}/` })),
      }),
    ] })

  return (
    <div className="mx-auto max-w-4xl px-5 py-10">
      <Breadcrumbs items={[{ name: 'Home', to: '/' }, { name: 'Guides' }]} />
      <div className="border-b border-line pb-8">
        <SectionLabel>Reading room</SectionLabel>
        <h1 className="mt-4 text-[clamp(2.4rem,5vw,3.5rem)] leading-none">Guides</h1>
        <p className="mt-4 max-w-xl text-[15px] leading-7 text-ink-soft">
          Practical notes on document quality, OCR, reconciliation and getting a clean spreadsheet
          out of the other end.
        </p>
      </div>
      <ul className="mt-2 border-b border-line">
        {GUIDES.map((g, i) => (
          <li key={g.slug} className="border-b border-line last:border-b-0">
            <Link to={`/guides/${g.slug}/`} className="group grid grid-cols-[2rem_1fr_auto] items-start gap-4 py-6 transition-colors hover:bg-surface">
              <span className="pt-1 font-mono text-[10px] tracking-[0.12em] text-ink-muted">{String(i + 1).padStart(2, '0')}</span>
              <div>
                <h2 className="font-sans text-[15px] font-medium text-ink transition-colors group-hover:text-pine-700">{g.h1}</h2>
                <p className="mt-1 text-sm leading-6 text-ink-soft">{g.description}</p>
              </div>
              <ArrowUpRight className="mt-1 h-4 w-4 text-ink-muted transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-pine-700" aria-hidden />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function GuidePage() {
  const { slug } = useParams()
  const g = guideBySlug(slug)
  const path = `/guides/${slug}/`
  useSeo({ title: g ? `${g.title} | Hisaab` : 'Guide not found | Hisaab', description: g?.description ?? 'This guide does not exist.', path,
    type: 'article', noindex: !g,
    jsonLd: g ? [
      articleLd({ headline: g.h1, description: g.description, path }),
      breadcrumbLd([{ name: 'Home', path: '/' }, { name: 'Guides', path: '/guides/' }, { name: g.h1, path }]),
    ] : [] })
  if (!g) return <div className="mx-auto max-w-3xl px-5 py-16"><h1 className="text-3xl">Guide not found</h1><Link className="text-pine-700 underline underline-offset-2" to="/guides/">All guides</Link></div>

  return (
    <article className="mx-auto max-w-3xl px-5 py-10">
      <Breadcrumbs items={[{ name: 'Home', to: '/' }, { name: 'Guides', to: '/guides/' }, { name: g.h1 }]} />
      <SectionLabel>Guide</SectionLabel>
      <h1 className="mt-4 text-[clamp(2.2rem,4.8vw,3.3rem)] leading-[1.04]">{g.h1}</h1>
      <p className="mt-5 border-b border-line pb-8 text-[16px] leading-8 text-ink-soft">{g.description}</p>
      <div className="prose-hisaab">{g.sections.map((s) => <section key={s.h}><h2>{s.h}</h2>{s.p.map((p) => <p key={p}>{p}</p>)}</section>)}</div>
      <AdSlot id="guide-bottom" />
      <div className="mt-10 flex flex-col gap-4 border border-line bg-surface p-6 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-ink-soft">Ready to try it on your own document?</p>
        <Link className="btn btn-primary shrink-0" to={toolPath(g.tool)}>
          Open the converter <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
        </Link>
      </div>
    </article>
  )
}

function Doc({ path, title, description, h1, children }: { path: string; title: string; description: string; h1: string; children: React.ReactNode }) {
  useSeo({ title, description, path, jsonLd: [
    webPageLd({ name: h1, description, path }),
    breadcrumbLd([{ name: 'Home', path: '/' }, { name: h1, path }]),
  ] })
  return (
    <div className="mx-auto max-w-3xl px-5 py-10">
      <Breadcrumbs items={[{ name: 'Home', to: '/' }, { name: h1 }]} />
      <SectionLabel>Hisaab</SectionLabel>
      <h1 className="mt-4 text-[clamp(2.2rem,4.8vw,3.3rem)] leading-[1.04]">{h1}</h1>
      <div className="prose-hisaab mt-6 border-t border-line pt-6">{children}</div>
    </div>
  )
}

export const About = () => (
  <Doc path="/about/" h1="About Hisaab" title="About Hisaab | Open-Source Document to Excel Converter" description="Why Hisaab exists, how it works, and what it will and will not do.">
    <p>Hisaab (Hindi for "account" or "reckoning") is an independent open-source project that turns financial documents into structured data you can review and export.</p>
    <h2>How it works</h2><p>PDF text is read directly where it exists. Scanned pages and images are cleaned up and read with Tesseract OCR. Rows, fields and tables are then parsed with rules, checked for consistency, and shown to you for review.</p>
    <h2>What it does not do</h2><p>It does not promise perfect accuracy, give accounting or tax advice, or send your documents to third-party AI services by default. It is licensed under the MIT license; see the project repository for the code and third-party license notes.</p>
  </Doc>
)
export const Privacy = () => (
  <Doc path="/privacy/" h1="Privacy" title="Privacy and Document Handling | Hisaab" description="Exactly how Hisaab handles the documents you upload, how long they are kept, and what is logged.">
    <p>This describes how the software behaves in its default configuration. If someone else hosts a Hisaab instance, they are responsible for their own deployment; check with them.</p>
    <h2>What happens to your file</h2><ul><li>You choose a file and it is sent over HTTPS (when the host has HTTPS configured) to the server.</li><li>It is saved under a random name in a private temporary folder, not a public directory.</li><li>It is processed with open-source tools on the server. It is not sent to third-party AI or OCR services and is not used for training.</li><li>Extracted results are held in the server's memory for the life of the job.</li></ul>
    <h2>How long it is kept</h2><p>Each job expires after a configurable retention period (60 minutes by default) and is then deleted. You can delete a job immediately with "Delete my data". Jobs also disappear if the server restarts.</p>
    <h2>Logs</h2><p>Server logs record technical events such as error types. They are designed not to include document contents, account numbers, tax IDs or extracted data.</p>
    <h2>Limits of these promises</h2><p>Deletion removes the files and results the application holds. It cannot control backups, disk snapshots or logs at the hosting provider level, so do not upload documents to a host you do not trust. Uploading is your decision.</p>
    <h2>Cookies and analytics</h2><p>The application itself sets no tracking cookies. A host may add analytics or ads on public marketing pages; those must never receive document contents.</p>
  </Doc>
)
export const Terms = () => (
  <Doc path="/terms/" h1="Terms of use" title="Terms of Use | Hisaab" description="Terms for using Hisaab: acceptable use, no warranty, and your responsibility to verify results.">
    <p>These are plain-language terms for the software as shipped. The operator of a hosted instance should review and adapt them with a qualified adviser.</p>
    <h2>Use at your own responsibility</h2><p>Extraction is automatic and may be wrong. You must verify results before using them for accounting, tax, lending or legal purposes. The software is provided "as is" without warranty.</p>
    <h2>Acceptable use</h2><p>Upload only documents you are entitled to process. Do not attempt to disrupt the service, bypass limits, or access other people's jobs.</p>
    <h2>Open source</h2><p>The code is MIT licensed; the license text in the repository governs the code.</p>
  </Doc>
)
export const Contact = () => {
  const email = import.meta.env.VITE_CONTACT_EMAIL as string | undefined
  return (
    <Doc path="/contact/" h1="Contact" title="Contact Hisaab" description="How to report a bug, ask a question or report a security issue with Hisaab.">
      {email ? <p>Email <a href={`mailto:${email}`}>{email}</a> for questions or feedback.</p> : <p>The operator of this instance has not published a contact address. If you run the site, set <code>VITE_CONTACT_EMAIL</code> at build time.</p>}
      <h2>Bugs and ideas</h2><p>Open an issue in the project repository, with a description and, if possible, a synthetic (non-private) example. Never post real financial documents.</p>
      <h2>Security issues</h2><p>Please follow the process in <code>SECURITY.md</code> in the repository rather than posting details publicly.</p>
    </Doc>
  )
}
