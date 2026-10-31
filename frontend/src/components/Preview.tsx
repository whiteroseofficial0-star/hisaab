import { useEffect, useState } from 'react'
import { fetchFileBlob } from '../services/api'
import type { JobRef, JobStatus } from '../types'

/** Shows the uploaded original next to the extracted data. Fetched with the job token and shown from a local blob URL. */
export default function Preview({ job, files }: { job: JobRef; files: JobStatus['files'] }) {
  const [idx, setIdx] = useState(0)
  const [url, setUrl] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const file = files[idx]

  useEffect(() => {
    let revoked: string | null = null
    let alive = true
    setUrl(null); setErr(null)
    if (!file) return
    fetchFileBlob(job, file.index).then((b) => {
      if (!alive) return
      revoked = URL.createObjectURL(b)
      setUrl(revoked)
    }).catch(() => alive && setErr('The original could not be loaded (it may have expired).'))
    return () => { alive = false; if (revoked) URL.revokeObjectURL(revoked) }
  }, [job.job_id, job.token, file?.index])

  if (!file) return null
  return (
    <section aria-label="Original document" className="border border-line bg-surface p-3">
      <div className="mb-3 flex items-center justify-between gap-3 border-b border-line pb-2.5">
        <h3 className="font-mono text-[10px] uppercase tracking-[0.14em] text-ink-muted">Original document</h3>
        {files.length > 1 ? (
          <label className="text-sm">
            <span className="sr-only">Choose file</span>
            <select className="input max-w-[11rem] py-1 text-xs" value={idx} onChange={(e) => setIdx(Number(e.target.value))}>
              {files.map((f, i) => <option key={f.index} value={i}>{f.name}</option>)}
            </select>
          </label>
        ) : (
          <span className="max-w-[12rem] truncate font-mono text-[9px] uppercase tracking-[0.1em] text-ink-muted">{file.name}</span>
        )}
      </div>
      {err && <p role="alert" className="py-3 text-sm text-red-800">{err}</p>}
      {!url && !err && <p className="py-3 text-sm text-ink-muted">Loading preview…</p>}
      {url && file.kind === 'pdf' && <iframe title={`Preview of ${file.name}`} src={url} className="h-[28rem] w-full border border-line lg:h-[40rem]" />}
      {url && file.kind !== 'pdf' && <img alt={`Uploaded document ${file.name}`} src={url} className="max-h-[40rem] w-full border border-line object-contain" />}
    </section>
  )
}
