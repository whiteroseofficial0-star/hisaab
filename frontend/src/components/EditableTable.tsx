import { useMemo, useState } from 'react'
import { AlertTriangle, ArrowDown, ArrowUp, Plus, Search, Trash2 } from 'lucide-react'
import type { Col, Row } from '../types'

interface Props {
  label: string
  columns: Col[]
  rows: Row[]
  onChange: (rows: Row[]) => void
  newRow: () => Row
  flagMessages?: Record<string, string>
  pageSize?: number
}

export function parseNumber(s: string): number | null | undefined {
  const t = s.replace(/[₹,\s]/g, '')
  if (t === '') return null
  return /^-?\d+(\.\d+)?$/.test(t) ? Number(t) : undefined // undefined = invalid
}

function Cell({ col, value, onCommit, rowLabel }: { col: Col; value: unknown; onCommit: (v: unknown) => void; rowLabel: string }) {
  const [draft, setDraft] = useState<string | null>(null)
  const [invalid, setInvalid] = useState(false)
  const shown = draft ?? (value === null || value === undefined ? '' : String(value))
  const aria = `${col.label}, ${rowLabel}`
  if (col.readOnly) return <span className="block px-2 py-2 text-sm text-ink-soft">{shown}</span>
  if (col.type === 'date') {
    return <input type="date" aria-label={aria} className="cell-input min-w-[9.5rem]" value={shown} onChange={(e) => onCommit(e.target.value || null)} />
  }
  return (
    <input
      aria-label={aria}
      aria-invalid={invalid}
      title={invalid ? 'Enter a number, e.g. 1234.50' : undefined}
      inputMode={col.type === 'number' ? 'decimal' : undefined}
      className={`cell-input ${col.type === 'number' ? 'text-right tabular-nums' : ''} ${invalid ? 'border-red-500 bg-red-50 dark:border-red-800 dark:bg-red-950/40' : ''}`}
      value={shown}
      onChange={(e) => {
        const v = e.target.value
        setDraft(v)
        if (col.type === 'number') {
          const n = parseNumber(v)
          setInvalid(n === undefined)
          if (n !== undefined) onCommit(n)
        } else onCommit(v)
      }}
      onBlur={() => { if (!invalid) setDraft(null) }}
    />
  )
}

export default function EditableTable({ label, columns, rows, onChange, newRow, flagMessages = {}, pageSize = 25 }: Props) {
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState<{ key: string; dir: 1 | -1 } | null>(null)
  const [page, setPage] = useState(0)

  const view = useMemo(() => {
    const q = query.trim().toLowerCase()
    let out = q ? rows.filter((r) => columns.some((c) => String(r[c.key] ?? '').toLowerCase().includes(q))) : rows.slice()
    if (sort) {
      out = out.slice().sort((a, b) => {
        const x = a[sort.key], y = b[sort.key]
        if (x == null || x === '') return 1
        if (y == null || y === '') return -1
        return (typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y))) * sort.dir
      })
    }
    return out
  }, [rows, columns, query, sort])

  const pages = Math.max(1, Math.ceil(view.length / pageSize))
  const cur = Math.min(page, pages - 1)
  const slice = view.slice(cur * pageSize, cur * pageSize + pageSize)

  const update = (id: string, key: string, v: unknown) => onChange(rows.map((r) => (r.id === id ? { ...r, [key]: v } : r)))

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <label className="relative">
          <span className="sr-only">Search {label}</span>
          <Search className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-ink-muted" aria-hidden />
          <input className="input w-44 py-1.5 pl-8 text-[13px]" placeholder="Search…" value={query} onChange={(e) => { setQuery(e.target.value); setPage(0) }} />
        </label>
        <button type="button" className="btn btn-secondary px-3 py-2" onClick={() => { onChange([...rows, newRow()]); setPage(Math.floor(rows.length / pageSize)); setQuery('') }}>
          <Plus className="h-3.5 w-3.5" aria-hidden /> Add row
        </button>
        <span className="ml-auto font-mono text-[9px] uppercase tracking-[0.12em] text-ink-muted" role="status">{view.length} of {rows.length} rows</span>
      </div>

      <div className="overflow-x-auto border border-line">
        <table className="min-w-full text-left">
          <caption className="sr-only">{label}</caption>
          <thead className="bg-paper/70 text-ink-muted">
            <tr className="border-b border-line">
              <th scope="col" className="px-2 py-2.5 font-mono text-[9px] font-medium uppercase tracking-[0.12em]">Review</th>
              {columns.map((c) => (
                <th key={c.key} scope="col" className="px-2 py-2.5" aria-sort={sort?.key === c.key ? (sort.dir === 1 ? 'ascending' : 'descending') : 'none'}>
                  <button type="button" className="inline-flex items-center gap-1 font-mono text-[9px] font-medium uppercase tracking-[0.12em] transition-colors hover:text-ink"
                    onClick={() => setSort(sort?.key === c.key ? (sort.dir === 1 ? { key: c.key, dir: -1 } : null) : { key: c.key, dir: 1 })}>
                    {c.label}
                    {sort?.key === c.key && (sort.dir === 1 ? <ArrowUp className="h-3 w-3" aria-hidden /> : <ArrowDown className="h-3 w-3" aria-hidden />)}
                  </button>
                </th>
              ))}
              <th scope="col" className="px-2 py-2.5"><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {slice.map((r, i) => {
              const flags = r.flags ?? []
              const rowLabel = `row ${cur * pageSize + i + 1}`
              return (
                <tr key={r.id} className={`border-t border-line/70 align-top transition-colors first:border-t-0 hover:bg-paper/40 ${flags.length ? 'bg-amber-50/60 dark:bg-amber-950/20' : ''}`}>
                  <td className="px-2 py-2 text-xs">
                    {flags.length > 0 && (
                      <span className="inline-flex items-center gap-1 font-mono text-[9px] font-medium uppercase tracking-[0.08em] text-amber-800 dark:text-amber-200" title={flags.map((f) => flagMessages[f] ?? f).join('\n')}>
                        <AlertTriangle className="h-3.5 w-3.5" aria-hidden /> Check ({flags.length})
                        <span className="sr-only">: {flags.map((f) => flagMessages[f] ?? f).join('; ')}</span>
                      </span>
                    )}
                  </td>
                  {columns.map((c) => (
                    <td key={c.key} className="px-1 py-1" style={c.width ? { minWidth: c.width } : undefined}>
                      <Cell col={c} value={r[c.key]} rowLabel={rowLabel} onCommit={(v) => update(r.id, c.key, v)} />
                    </td>
                  ))}
                  <td className="px-1 py-1">
                    <button type="button" className="rounded p-1.5 text-ink-muted transition-colors hover:bg-red-50 hover:text-red-700" aria-label={`Delete ${rowLabel}`}
                      onClick={() => onChange(rows.filter((x) => x.id !== r.id))}>
                      <Trash2 className="h-3.5 w-3.5" aria-hidden />
                    </button>
                  </td>
                </tr>
              )
            })}
            {slice.length === 0 && (
              <tr><td colSpan={columns.length + 2} className="px-3 py-8 text-center text-sm text-ink-muted">No rows to show.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <nav className="mt-4 flex items-center gap-3 text-sm" aria-label={`${label} pages`}>
          <button type="button" className="btn btn-secondary px-3 py-2" disabled={cur === 0} onClick={() => setPage(cur - 1)}>Previous</button>
          <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-ink-muted">Page {cur + 1} of {pages}</span>
          <button type="button" className="btn btn-secondary px-3 py-2" disabled={cur >= pages - 1} onClick={() => setPage(cur + 1)}>Next</button>
        </nav>
      )}
    </div>
  )
}
