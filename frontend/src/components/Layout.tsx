import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { Menu, Moon, Sun, X } from 'lucide-react'

const nav = [
  { to: '/tools/', label: 'Tools' },
  { to: '/guides/', label: 'Guides' },
  { to: '/about/', label: 'About' },
]

function Wordmark({ inverted = false }: { inverted?: boolean }) {
  return (
    <span className="flex items-center gap-3">
      <span
        className={`grid h-8 w-8 place-items-center rounded-[3px] font-display text-[19px] leading-none ${
          inverted ? 'bg-[#F5F1E8] text-[#1C2823]' : 'bg-ink text-paper'
        }`}
        aria-hidden
      >
        H
      </span>
      <span className={`font-display text-[26px] leading-none tracking-[-0.02em] ${inverted ? 'text-[#F5F1E8]' : 'text-ink'}`}>
        Hisaab
      </span>
    </span>
  )
}

function ThemeToggle({ className = '' }: { className?: string }) {
  const [dark, setDark] = useState(() =>
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark'),
  )

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    try { localStorage.setItem('hisaab-theme', dark ? 'dark' : 'light') } catch { /* private mode */ }
  }, [dark])

  return (
    <button
      type="button"
      onClick={() => setDark(!dark)}
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
      aria-pressed={dark}
      title={dark ? 'Light theme' : 'Dark theme'}
      className={`grid h-9 w-9 place-items-center rounded-md border border-line bg-surface text-ink-muted transition-colors hover:border-slate-400 hover:text-ink ${className}`}
    >
      {dark ? <Sun className="h-4 w-4" aria-hidden /> : <Moon className="h-4 w-4" aria-hidden />}
    </button>
  )
}

export default function Layout() {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()

  useEffect(() => {
    setOpen(false)
    window.scrollTo(0, 0)
  }, [pathname])

  const link = ({ isActive }: { isActive: boolean }) =>
    `relative py-1 text-[11px] font-medium uppercase tracking-[0.16em] transition-colors ${
      isActive
        ? 'text-ink after:absolute after:inset-x-0 after:-bottom-1 after:h-px after:bg-pine-700'
        : 'text-ink-muted hover:text-ink'
    }`

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-surface focus:p-2"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-40 border-b border-line/80 bg-paper/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <Link to="/" aria-label="Hisaab home" className="shrink-0">
            <Wordmark />
          </Link>

          <nav aria-label="Main" className="hidden items-center gap-8 md:flex">
            {nav.map((n) => (
              <NavLink key={n.to} to={n.to} className={link}>
                {n.label}
              </NavLink>
            ))}
            <span className="h-4 w-px bg-line" aria-hidden />
            <ThemeToggle />
            <Link to="/#convert" className="btn btn-primary px-4 py-2">
              Open the converter
            </Link>
          </nav>

          <div className="flex items-center gap-2 md:hidden">
            <ThemeToggle />
            <button
              type="button"
              className="-mr-2 rounded p-2 text-ink"
              aria-label="Menu"
              aria-expanded={open}
              aria-controls="mobile-nav"
              onClick={() => setOpen(!open)}
            >
              {open ? <X aria-hidden /> : <Menu aria-hidden />}
            </button>
          </div>
        </div>

        {open && (
          <nav
            id="mobile-nav"
            aria-label="Mobile"
            className="flex flex-col gap-4 border-t border-line bg-paper px-5 py-5 md:hidden"
          >
            {nav.map((n) => (
              <NavLink key={n.to} to={n.to} className={link}>
                {n.label}
              </NavLink>
            ))}
            <Link to="/#convert" className="btn btn-primary mt-1 w-full">
              Open the converter
            </Link>
          </nav>
        )}
      </header>

      <main id="main" className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-[#0C1E19] bg-[#0C1E19] text-[#F5F1E8]">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-12 px-5 py-14 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div>
            <Wordmark inverted />
            <p className="mt-5 max-w-xs text-sm leading-6 text-slate-300">
              Documents in. Clean spreadsheets out. An open-source desk for statements, invoices and
              receipts.
            </p>
          </div>

          <nav aria-label="Footer tools">
            <p className="eyebrow text-[#93B8A7]">Tools</p>
            <ul className="mt-4 space-y-2.5 text-sm text-slate-300">
              <li><Link className="transition-colors hover:text-[#F5F1E8]" to="/tools/bank-statement-to-excel/">Bank statement to Excel</Link></li>
              <li><Link className="transition-colors hover:text-[#F5F1E8]" to="/tools/invoice-to-excel/">Invoice to Excel</Link></li>
              <li><Link className="transition-colors hover:text-[#F5F1E8]" to="/tools/receipt-to-excel/">Receipt to Excel</Link></li>
              <li><Link className="transition-colors hover:text-[#F5F1E8]" to="/tools/pdf-table-extractor/">PDF table extractor</Link></li>
            </ul>
          </nav>

          <nav aria-label="Footer company">
            <p className="eyebrow text-[#93B8A7]">Hisaab</p>
            <ul className="mt-4 space-y-2.5 text-sm text-slate-300">
              <li><Link className="transition-colors hover:text-[#F5F1E8]" to="/guides/">Guides</Link></li>
              <li><Link className="transition-colors hover:text-[#F5F1E8]" to="/about/">About</Link></li>
              <li><Link className="transition-colors hover:text-[#F5F1E8]" to="/contact/">Contact</Link></li>
            </ul>
          </nav>

          <nav aria-label="Footer legal">
            <p className="eyebrow text-[#93B8A7]">Legal</p>
            <ul className="mt-4 space-y-2.5 text-sm text-slate-300">
              <li><Link className="transition-colors hover:text-[#F5F1E8]" to="/privacy/">Privacy</Link></li>
              <li><Link className="transition-colors hover:text-[#F5F1E8]" to="/terms/">Terms</Link></li>
              <li><a className="transition-colors hover:text-[#F5F1E8]" href="https://opensource.org/license/mit">MIT licence</a></li>
            </ul>
          </nav>
        </div>

        <div className="border-t border-[#16332C]">
          <div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-5 font-mono text-[10px] uppercase tracking-[0.16em] text-slate-400 sm:flex-row sm:items-center sm:justify-between">
            <p>Open source · No account · Files expire automatically</p>
            <p>Built for careful bookkeeping</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
