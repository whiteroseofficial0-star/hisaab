import { AlertTriangle } from 'lucide-react'
import EditableTable, { parseNumber } from '../components/EditableTable'
import type { Col, Result, Row } from '../types'

const uid = () => Math.random().toString(36).slice(2, 12)
const money = (n: number | null | undefined) => (n == null ? '—' : n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }))

export function Warnings({ items }: { items: string[] }) {
  if (!items?.length) return null
  return (
    <div role="status" className="mb-5 border-l-2 border-amber-500 bg-amber-50/70 px-4 py-3 text-sm text-amber-950 dark:bg-amber-950/25 dark:text-amber-100">
      <p className="flex items-center gap-2 font-medium"><AlertTriangle className="h-4 w-4" aria-hidden /> Please check</p>
      <ul className="mt-1.5 list-disc space-y-1 pl-5 text-[13px] leading-6">{items.map((w) => <li key={w}>{w}</li>)}</ul>
    </div>
  )
}

/* ---------------------------------------------------------------- bank statement */
const BANK_COLS: Col[] = [
  { key: 'date', label: 'Date', type: 'date' },
  { key: 'value_date', label: 'Value date', type: 'date' },
  { key: 'description', label: 'Description', type: 'text', width: '16rem' },
  { key: 'reference', label: 'Reference', type: 'text', width: '9rem' },
  { key: 'cheque_no', label: 'Cheque no.', type: 'text', width: '7rem' },
  { key: 'debit', label: 'Debit', type: 'number', width: '7rem' },
  { key: 'credit', label: 'Credit', type: 'number', width: '7rem' },
  { key: 'balance', label: 'Balance', type: 'number', width: '8rem' },
  { key: 'page', label: 'Page', type: 'number', readOnly: true },
]

export function BankReview({ result, setResult }: { result: Result; setResult: (r: Result) => void }) {
  const rows: Row[] = result.transactions
  const meta = result.metadata ?? {}
  const debit = rows.reduce((s, r) => s + Math.round(((r.debit as number) || 0) * 100), 0) / 100
  const credit = rows.reduce((s, r) => s + Math.round(((r.credit as number) || 0) * 100), 0) / 100
  const setMetaNum = (k: string, v: string) => { const n = parseNumber(v); if (n !== undefined) setResult({ ...result, metadata: { ...meta, [k]: n } }) }

  const pages: { page: number; method: string }[] = result.extraction?.pages ?? []

  return (
    <div>
      <Warnings items={result.warnings} />
      {pages.length > 0 && (
        <p className="mb-5 text-xs leading-5 text-ink-muted">
          <span className="font-mono text-[9px] uppercase tracking-[0.12em]">How this file was read</span>{' '}
          <span data-testid="read-methods">
            {pages.map((p) => `Page ${p.page}: ${p.method === 'ocr' ? 'OCR (approximate)' : 'selectable text'}`).join(' · ')}
          </span>
        </p>
      )}
      <dl className="bank-meta mb-6 gap-x-6 gap-y-4 border-b border-line pb-5 text-sm">
        {[['Bank', meta.bank_name], ['Account holder', meta.account_holder], ['Account (masked)', meta.account_number_masked],
          ['Period', meta.period_from ? `${meta.period_from} to ${meta.period_to}` : null]].map(([k, v]) => (
          <div key={k as string}>
            <dt className="font-mono text-[9px] uppercase tracking-[0.12em] text-ink-muted">{k}</dt>
            <dd className="mt-1 font-medium text-ink">{(v as string) || '—'}</dd>
          </div>
        ))}
        {(['opening_balance', 'closing_balance'] as const).map((k) => (
          <div key={k}>
            <dt><label htmlFor={k} className="font-mono text-[9px] uppercase tracking-[0.12em] text-ink-muted">{k === 'opening_balance' ? 'Opening balance' : 'Closing balance'}</label></dt>
            <dd><input id={k} className="input mt-1 py-1.5 text-right tabular-nums" inputMode="decimal" defaultValue={meta[k] ?? ''} onBlur={(e) => setMetaNum(k, e.target.value)} /></dd>
          </div>
        ))}
        <div><dt className="font-mono text-[9px] uppercase tracking-[0.12em] text-ink-muted">Total debit</dt><dd className="mt-1 font-semibold tabular-nums text-ink" data-testid="total-debit">{money(debit)}</dd></div>
        <div><dt className="font-mono text-[9px] uppercase tracking-[0.12em] text-ink-muted">Total credit</dt><dd className="mt-1 font-semibold tabular-nums text-ink" data-testid="total-credit">{money(credit)}</dd></div>
      </dl>
      <EditableTable label="Transactions" columns={BANK_COLS} rows={rows} flagMessages={result.flag_messages}
        newRow={() => ({ id: uid(), date: null, value_date: null, description: '', reference: null, cheque_no: null, debit: null, credit: null, balance: null, page: null, flags: [] })}
        onChange={(transactions) => setResult({ ...result, transactions })} />
      <p className="mt-3 max-w-2xl text-xs leading-5 text-ink-muted">Balance checks use previous balance + credit − debit. Banks use different conventions, so a flag means "please compare with the original", not "wrong".</p>
    </div>
  )
}

/* ---------------------------------------------------------------- invoice */
const FIELDS: [string, string, 'text' | 'number' | 'date'][] = [
  ['supplier_name', 'Supplier name', 'text'], ['supplier_address', 'Supplier address', 'text'], ['supplier_tax_id', 'Supplier GSTIN / tax ID', 'text'],
  ['customer_name', 'Customer name', 'text'], ['customer_address', 'Customer address', 'text'], ['customer_tax_id', 'Customer GSTIN / tax ID', 'text'],
  ['invoice_number', 'Invoice number', 'text'], ['invoice_date', 'Invoice date', 'date'], ['due_date', 'Due date', 'date'],
  ['po_number', 'PO number', 'text'], ['currency', 'Currency', 'text'], ['payment_terms', 'Payment terms', 'text'],
  ['subtotal', 'Subtotal', 'number'], ['discount', 'Discount', 'number'], ['taxable_amount', 'Taxable amount', 'number'],
  ['cgst', 'CGST', 'number'], ['sgst', 'SGST', 'number'], ['igst', 'IGST', 'number'], ['other_taxes', 'Other taxes', 'number'],
  ['shipping', 'Shipping / charges', 'number'], ['round_off', 'Round-off', 'number'], ['grand_total', 'Grand total', 'number'],
]
const ITEM_COLS: Col[] = [
  { key: 'description', label: 'Description', type: 'text', width: '14rem' }, { key: 'hsn_sac', label: 'HSN/SAC', type: 'text', width: '6rem' },
  { key: 'quantity', label: 'Qty', type: 'number', width: '5rem' }, { key: 'unit', label: 'Unit', type: 'text', width: '5rem' },
  { key: 'unit_price', label: 'Unit price', type: 'number', width: '7rem' }, { key: 'discount', label: 'Discount', type: 'number', width: '6rem' },
  { key: 'tax_rate', label: 'Tax %', type: 'number', width: '5rem' }, { key: 'tax_amount', label: 'Tax amt', type: 'number', width: '6rem' },
  { key: 'line_total', label: 'Line total', type: 'number', width: '7rem' },
]

export function InvoiceReview({ result, setResult }: { result: Result; setResult: (r: Result) => void }) {
  const f = result.fields
  const conf: Record<string, number> = result.field_confidence ?? {}
  const low = result.low_confidence_threshold ?? 65
  const setField = (k: string, type: string, v: string) => {
    if (type === 'number') { const n = parseNumber(v); if (n === undefined) return; setResult({ ...result, fields: { ...f, [k]: n } }) }
    else setResult({ ...result, fields: { ...f, [k]: v === '' ? null : v } })
  }
  return (
    <div>
      <Warnings items={result.warnings} />
      <h3 className="mb-3 text-lg font-semibold">Invoice details</h3>
      <div className="invoice-fields mb-8 gap-x-4 gap-y-4">
        {FIELDS.map(([k, label, type]) => {
          const uncertain = conf[k] !== undefined && conf[k] < low
          return (
            <div key={k}>
              <label htmlFor={`f-${k}`} className="font-mono text-[9px] uppercase tracking-[0.1em] text-ink-muted">{label}</label>
              <input id={`f-${k}`} className={`input mt-1 py-1.5 ${type === 'number' ? 'text-right tabular-nums' : ''} ${uncertain ? 'border-amber-500 bg-amber-50 dark:bg-amber-950/30' : ''}`}
                type={type === 'date' ? 'date' : 'text'} inputMode={type === 'number' ? 'decimal' : undefined}
                defaultValue={f[k] ?? ''} key={`${k}-${String(f[k])}`}
                onBlur={(e) => setField(k, type, e.target.value)} />
              {uncertain && <p className="mt-1 flex items-center gap-1 font-mono text-[9px] uppercase tracking-[0.08em] text-amber-800 dark:text-amber-200"><AlertTriangle className="h-3 w-3" aria-hidden /> Low confidence ({Math.round(conf[k])}%) — verify</p>}
            </div>
          )
        })}
      </div>
      <h3 className="mb-3 text-lg font-semibold">Line items</h3>
      <EditableTable label="Line items" columns={ITEM_COLS} rows={result.line_items}
        newRow={() => ({ id: uid(), description: '', hsn_sac: null, quantity: null, unit: null, unit_price: null, discount: null, tax_rate: null, tax_amount: null, line_total: null })}
        onChange={(line_items) => setResult({ ...result, line_items })} />
      <p className="mt-3 text-xs leading-5 text-ink-muted">Sum of line totals: <b className="font-semibold tabular-nums text-ink">{money(result.line_items.reduce((s: number, r: Row) => s + ((r.line_total as number) || 0), 0))}</b>
        {' · '}Computed grand total: <b className="font-semibold tabular-nums text-ink">{money(result.calculated?.computed_grand_total)}</b></p>
    </div>
  )
}

/* ---------------------------------------------------------------- receipts */
const RCOLS: Col[] = [
  { key: 'merchant', label: 'Merchant', type: 'text', width: '12rem' }, { key: 'receipt_number', label: 'Receipt no.', type: 'text', width: '7rem' },
  { key: 'date', label: 'Date', type: 'date' }, { key: 'time', label: 'Time', type: 'text', width: '5rem' },
  { key: 'description', label: 'Description', type: 'text', width: '12rem' }, { key: 'subtotal', label: 'Subtotal', type: 'number', width: '6rem' },
  { key: 'tax', label: 'Tax', type: 'number', width: '5rem' }, { key: 'discount', label: 'Discount', type: 'number', width: '5rem' },
  { key: 'total', label: 'Total', type: 'number', width: '6rem' }, { key: 'currency', label: 'Curr.', type: 'text', width: '4rem' },
  { key: 'payment_method', label: 'Payment', type: 'text', width: '6rem' }, { key: 'tax_id', label: 'Tax ID', type: 'text', width: '9rem' },
  { key: 'source_file', label: 'File', type: 'text', readOnly: true },
]
const RICOLS: Col[] = [
  { key: 'receipt_label', label: 'Receipt', type: 'text', readOnly: true }, { key: 'description', label: 'Description', type: 'text', width: '14rem' },
  { key: 'quantity', label: 'Qty', type: 'number', width: '5rem' }, { key: 'unit_price', label: 'Unit price', type: 'number', width: '6rem' },
  { key: 'amount', label: 'Amount', type: 'number', width: '6rem' },
]

export function ReceiptReview({ result, setResult }: { result: Result; setResult: (r: Result) => void }) {
  const receipts: Row[] = result.receipts
  const label = Object.fromEntries(receipts.map((r) => [r.id, String(r.merchant ?? r.source_file ?? '')]))
  const items: Row[] = result.line_items.map((i: Row) => ({ ...i, receipt_label: label[i.receipt_id as string] ?? '' }))
  return (
    <div>
      <Warnings items={result.warnings} />
      <p className="mb-4 text-xs leading-5 text-ink-muted">Suggested values only — check each receipt before using it for accounts or tax.</p>
      <EditableTable label="Receipts" columns={RCOLS} rows={receipts} flagMessages={result.flag_messages}
        newRow={() => ({ id: uid(), merchant: '', receipt_number: null, date: null, time: null, description: null, subtotal: null, tax: null, discount: null, total: null, currency: null, payment_method: null, tax_id: null, source_file: 'manual', flags: [] })}
        onChange={(r) => setResult({ ...result, receipts: r })} />
      <h3 className="mb-3 mt-9 text-lg font-semibold">Line items</h3>
      <EditableTable label="Receipt line items" columns={RICOLS} rows={items}
        newRow={() => ({ id: uid(), receipt_id: receipts[0]?.id ?? null, description: '', quantity: null, unit_price: null, amount: null })}
        onChange={(rows) => setResult({ ...result, line_items: rows.map(({ receipt_label, ...rest }) => { void receipt_label; return rest }) })} />
    </div>
  )
}

/* ---------------------------------------------------------------- tables */
export function TablesReview({ result, setResult }: { result: Result; setResult: (r: Result) => void }) {
  const tables: Result[] = result.tables
  const setTable = (id: string, patch: Result) => setResult({ ...result, tables: tables.map((t) => (t.id === id ? { ...t, ...patch } : t)) })
  return (
    <div className="space-y-8">
      <Warnings items={result.warnings} />
      {tables.map((t) => {
        const cols: Col[] = t.columns.map((c: string, i: number) => ({ key: `c${i}`, label: c, type: 'text' as const, width: '8rem' }))
        const rows: Row[] = t.rows.map((r: string[], ri: number) => ({ id: String(ri), ...Object.fromEntries(r.map((v, i) => [`c${i}`, v])) }))
        return (
          <section key={t.id} className="border border-line bg-surface p-4" aria-label={t.name}>
            <div className="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-line pb-3">
              <label className="flex items-center gap-2 text-sm font-medium">
                <input type="checkbox" className="accent-pine-700" checked={t.selected} onChange={(e) => setTable(t.id, { selected: e.target.checked })} /> Export this table
              </label>
              <label className="text-sm"><span className="sr-only">Table name</span>
                <input className="input w-48 py-1 text-sm" value={t.name} onChange={(e) => setTable(t.id, { name: e.target.value })} /></label>
              <span className="ml-auto font-mono text-[9px] uppercase tracking-[0.1em] text-ink-muted">Page {t.page} · {t.method === 'ocr' ? 'OCR (approximate)' : 'Selectable text'}</span>
            </div>
            {t.warnings?.map((w: string) => <p key={w} className="mb-2 text-xs text-amber-800 dark:text-amber-200">⚠ {w}</p>)}
            <fieldset className="table-cols mb-4 gap-2">
              <legend className="mb-2 font-mono text-[9px] uppercase tracking-[0.12em] text-ink-muted">Column names</legend>
              {t.columns.map((c: string, i: number) => (
                <label key={i} className="text-xs"><span className="sr-only">Column {i + 1} name</span>
                  <input className="input py-1 text-xs" value={c} onChange={(e) => setTable(t.id, { columns: t.columns.map((x: string, j: number) => (j === i ? e.target.value : x)) })} /></label>
              ))}
            </fieldset>
            <EditableTable label={t.name} columns={cols} rows={rows}
              newRow={() => ({ id: uid(), ...Object.fromEntries(t.columns.map((_: string, i: number) => [`c${i}`, ''])) })}
              onChange={(rs) => setTable(t.id, { rows: rs.map((r) => t.columns.map((_: string, i: number) => String(r[`c${i}`] ?? ''))) })} />
          </section>
        )
      })}
    </div>
  )
}
