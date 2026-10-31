import { useCallback, useEffect, useRef, useState } from 'react'
import { Check, Download, Loader2, RotateCcw, Save, Trash2, XCircle } from 'lucide-react'
import UploadZone from '../components/UploadZone'
import Preview from '../components/Preview'
import { ApiError, createJob, deleteJob, downloadBlob, exportResult, getJob, getResult, patchResult } from '../services/api'
import type { FileKind, JobRef, JobStatus, Result, ToolKey } from '../types'
import { BankReview, InvoiceReview, ReceiptReview, TablesReview } from './reviews'

type Phase =
  | { k: 'idle' }
  | { k: 'uploading'; pct: number }
  | { k: 'processing'; status: JobStatus | null }
  | { k: 'review'; status: JobStatus }
  | { k: 'error'; message: string }

const MAX_MB = Number(import.meta.env.VITE_MAX_UPLOAD_MB ?? 20)
const EXPORTS: Record<ToolKey, { label: string; format: 'xlsx' | 'csv' | 'zip'; part?: 'details' | 'line_items' }[]> = {
  bank_statement: [{ label: 'Download Excel (.xlsx)', format: 'xlsx' }, { label: 'Download CSV', format: 'csv' }],
  invoice: [{ label: 'Download Excel (.xlsx)', format: 'xlsx' }, { label: 'CSV: details', format: 'csv', part: 'details' },
    { label: 'CSV: line items', format: 'csv', part: 'line_items' }, { label: 'Both CSVs (ZIP)', format: 'zip' }],
  receipt: [{ label: 'Download Excel (.xlsx)', format: 'xlsx' }, { label: 'CSV: receipts', format: 'csv' },
    { label: 'CSV: line items', format: 'csv', part: 'line_items' }, { label: 'Both CSVs (ZIP)', format: 'zip' }],
  tables: [{ label: 'Download Excel (.xlsx)', format: 'xlsx' }, { label: 'CSV (one table)', format: 'csv' }, { label: 'CSVs (ZIP)', format: 'zip' }],
}

export default function Workbench({ tool, accept, multiple = false }: { tool: ToolKey; accept: FileKind[]; multiple?: boolean }) {
  const [phase, setPhase] = useState<Phase>({ k: 'idle' })
  const [job, setJob] = useState<JobRef | null>(null)
  const [result, setResult] = useState<Result | null>(null)
  const [dirty, setDirty] = useState(false)
  const [busy, setBusy] = useState<string | null>(null)
  const [notice, setNotice] = useState('')
  const abort = useRef<AbortController | null>(null)
  const alive = useRef(true)
  useEffect(() => { alive.current = true; return () => { alive.current = false; abort.current?.abort() } }, [])

  const reset = useCallback(() => { setPhase({ k: 'idle' }); setJob(null); setResult(null); setDirty(false); setNotice('') }, [])

  const poll = useCallback(async (ref: JobRef) => {
    for (;;) {
      if (!alive.current) return
      let status: JobStatus
      try { status = await getJob(ref) } catch (e) {
        if (alive.current) setPhase({ k: 'error', message: e instanceof ApiError ? e.message : 'Lost contact with the server.' })
        return
      }
      if (!alive.current) return
      if (status.status === 'done') {
        const res = await getResult(ref)
        if (!alive.current) return
        setResult(res); setPhase({ k: 'review', status }); setNotice('Extraction finished. Review the data below.')
        return
      }
      if (status.status === 'failed' || status.status === 'cancelled') {
        setPhase({ k: 'error', message: status.error?.message ?? 'Processing was cancelled.' })
        return
      }
      setPhase({ k: 'processing', status })
      await new Promise((r) => setTimeout(r, 1000))
    }
  }, [])

  const start = async (files: File[]) => {
    reset()
    abort.current = new AbortController()
    setPhase({ k: 'uploading', pct: 0 })
    try {
      const created = await createJob(tool, files, (pct) => setPhase({ k: 'uploading', pct }), abort.current.signal)
      const ref = { job_id: created.job_id, token: created.token }
      setJob(ref)
      setPhase({ k: 'processing', status: null })
      await poll(ref)
    } catch (e) {
      if (e instanceof ApiError && e.code === 'cancelled') { reset(); return }
      setPhase({ k: 'error', message: e instanceof ApiError ? e.message : 'Something went wrong.' })
    }
  }

  const cancel = async () => {
    abort.current?.abort()
    if (job) await deleteJob(job).catch(() => undefined)
    reset()
  }

  const save = async (): Promise<Result | null> => {
    if (!job || !result) return null
    try {
      const saved = await patchResult(job, result)
      setResult(saved); setDirty(false)
      return saved
    } catch (e) {
      setNotice(e instanceof ApiError ? `Could not save: ${e.message}` : 'Could not save your changes.')
      return null
    }
  }

  const doExport = async (e: (typeof EXPORTS)[ToolKey][number]) => {
    if (!job) return
    setBusy(e.label)
    try {
      if (dirty && !(await save())) return
      const { blob, filename } = await exportResult(job, e.format, e.part)
      downloadBlob(blob, filename)
      setNotice(`Downloaded ${filename}.`)
    } catch (err) {
      setNotice(err instanceof ApiError ? `Export failed: ${err.message}` : 'Export failed.')
    } finally { setBusy(null) }
  }

  const remove = async () => {
    if (job) await deleteJob(job).catch(() => undefined)
    reset(); setNotice('Your document and extracted data were deleted from the server.')
  }

  const update = (r: Result) => { setResult(r); setDirty(true) }

  return (
    <div id="upload" className="@container scroll-mt-24">
      <div className="sr-only" role="status" aria-live="polite">{notice}</div>

      {phase.k === 'idle' && <UploadZone rules={{ accept, multiple, maxMb: MAX_MB, maxFiles: multiple ? 10 : 1 }} onFiles={start} />}

      {phase.k === 'uploading' && (
        <div className="border border-line bg-paper/50 p-5" role="status">
          <p className="eyebrow">Uploading</p>
          <p className="mt-2 text-[15px] font-medium text-ink">{phase.pct}% transferred</p>
          <progress className="mt-3 w-full" max={100} value={phase.pct} aria-label="Upload progress" />
          <button type="button" className="btn btn-secondary mt-4" onClick={cancel}>Cancel</button>
        </div>
      )}

      {phase.k === 'processing' && (
        <div className="border border-line bg-paper/50 p-5" role="status">
          <p className="eyebrow flex items-center gap-2">
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> Working
          </p>
          <p className="mt-2 text-[15px] font-medium text-ink">
            {phase.status?.status === 'queued' || !phase.status ? 'Waiting for a free processing slot…'
              : phase.status.progress.stage === 'ocr' ? 'Reading scanned pages with OCR…' : 'Extracting data…'}
          </p>
          {phase.status?.progress.pages_total ? (
            <>
              <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.12em] text-ink-muted">
                Page {phase.status.progress.pages_done} of {phase.status.progress.pages_total}
              </p>
              <progress className="mt-2 w-full" max={phase.status.progress.pages_total} value={phase.status.progress.pages_done} aria-label="Pages processed" />
            </>
          ) : <p className="mt-2 text-sm text-ink-soft">Opening the document…</p>}
          <button type="button" className="btn btn-secondary mt-4" onClick={cancel}>Cancel</button>
        </div>
      )}

      {phase.k === 'error' && (
        <div className="border border-red-200 bg-red-50/60 p-5" role="alert">
          <p className="flex items-center gap-2 text-[15px] font-semibold text-red-900"><XCircle className="h-4 w-4" aria-hidden /> We could not process this file</p>
          <p className="mt-2 text-sm leading-6 text-ink-soft">{phase.message}</p>
          <button type="button" className="btn btn-primary mt-5" onClick={async () => { if (job) await deleteJob(job).catch(() => undefined); reset() }}>
            <RotateCcw className="h-4 w-4" aria-hidden /> Try another file
          </button>
        </div>
      )}

      {phase.k === 'review' && result && job && (
        <div>
          <div className="mb-5 flex flex-wrap items-center gap-x-3 gap-y-2 border-y border-pine-200 bg-pine-50/60 px-4 py-3">
            <span className="flex items-center gap-2 text-[13px] font-medium text-pine-900">
              <Check className="h-4 w-4 text-pine-700" aria-hidden /> Extraction ready.
            </span>
            <span className="mr-auto text-xs text-pine-800/80">Automatic extraction is never perfect. Review before you rely on it.</span>
            <button type="button" className="btn btn-secondary px-3 py-2" onClick={() => void save()} disabled={!dirty}><Save className="h-3.5 w-3.5" aria-hidden /> {dirty ? 'Save changes' : 'Saved'}</button>
            <button type="button" className="btn btn-secondary px-3 py-2" onClick={reset}><RotateCcw className="h-3.5 w-3.5" aria-hidden /> Start over</button>
            <button type="button" className="btn btn-danger px-3 py-2" onClick={remove}><Trash2 className="h-3.5 w-3.5" aria-hidden /> Delete my data</button>
          </div>
          {notice && <p className="mb-4 font-mono text-[10px] uppercase tracking-[0.12em] text-ink-muted" aria-hidden>{notice}</p>}

          <div className="grid grid-cols-1 gap-5 @[60rem]:grid-cols-[minmax(0,1.9fr)_minmax(0,1fr)]">
            <div className="min-w-0 border border-line bg-surface p-4 sm:p-5">
              {tool === 'bank_statement' && <BankReview result={result} setResult={update} />}
              {tool === 'invoice' && <InvoiceReview result={result} setResult={update} />}
              {tool === 'receipt' && <ReceiptReview result={result} setResult={update} />}
              {tool === 'tables' && <TablesReview result={result} setResult={update} />}
              <div className="mt-6 flex flex-wrap gap-2 border-t border-line pt-5" role="group" aria-label="Export">
                {EXPORTS[tool].map((e, i) => (
                  <button key={e.label} type="button" className={`btn ${i === 0 ? 'btn-primary' : 'btn-secondary'}`} disabled={busy !== null} onClick={() => void doExport(e)}>
                    {busy === e.label ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Download className="h-4 w-4" aria-hidden />} {e.label}
                  </button>
                ))}
              </div>
              <p className="mt-3 font-mono text-[9px] uppercase leading-4 tracking-[0.12em] text-ink-muted">
                Exports include all your edits · files stay on the server until they expire or you delete them
              </p>
            </div>
            <div className="min-w-0 xl:sticky xl:top-24 xl:self-start"><Preview job={job} files={phase.status.files} /></div>
          </div>
        </div>
      )}
    </div>
  )
}
