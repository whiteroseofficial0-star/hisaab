import type { Health, JobCreated, JobRef, JobStatus, Result, ToolKey } from '../types'

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''
const API = `${BASE}/api/v1`

export class ApiError extends Error {
  code: string
  status: number
  constructor(message: string, code: string, status: number) {
    super(message)
    this.code = code
    this.status = status
  }
}

async function fail(res: Response): Promise<never> {
  let body: { error?: { code?: string; message?: string } } | null = null
  try { body = await res.json() } catch { /* not JSON */ }
  throw new ApiError(body?.error?.message ?? `Request failed (${res.status})`, body?.error?.code ?? 'error', res.status)
}

const headers = (job: JobRef, json = false): HeadersInit => ({
  'X-Job-Token': job.token,
  ...(json ? { 'Content-Type': 'application/json' } : {}),
})

let healthRequest: Promise<Health> | null = null
export function getHealth(): Promise<Health> {
  healthRequest ??= fetch(`${API}/health`)
    .then((res) => (res.ok ? (res.json() as Promise<Health>) : fail(res)))
    .catch((e) => { healthRequest = null; throw e })
  return healthRequest
}

/** Upload with real progress events (fetch cannot report upload progress). */
export function createJob(tool: ToolKey, files: File[], onProgress: (pct: number) => void, signal: AbortSignal, ocrLang?: string): Promise<JobCreated> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API}/jobs`)
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100)) }
    xhr.onload = () => {
      let body: any = null // eslint-disable-line @typescript-eslint/no-explicit-any
      try { body = JSON.parse(xhr.responseText) } catch { /* ignore */ }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as JobCreated)
      else reject(new ApiError(body?.error?.message ?? `Upload failed (${xhr.status})`, body?.error?.code ?? 'error', xhr.status))
    }
    xhr.onerror = () => reject(new ApiError('Could not reach the server. Check your connection and that the backend is running.', 'network', 0))
    signal.addEventListener('abort', () => { xhr.abort(); reject(new ApiError('Upload cancelled.', 'cancelled', 0)) })
    const form = new FormData()
    form.append('tool', tool)
    if (ocrLang) form.append('ocr_lang', ocrLang)
    files.forEach((f) => form.append('files', f))
    xhr.send(form)
  })
}

export async function getJob(job: JobRef): Promise<JobStatus> {
  const res = await fetch(`${API}/jobs/${job.job_id}`, { headers: headers(job) })
  return res.ok ? res.json() : fail(res)
}
export async function getResult(job: JobRef): Promise<Result> {
  const res = await fetch(`${API}/jobs/${job.job_id}/result`, { headers: headers(job) })
  return res.ok ? res.json() : fail(res)
}
export async function patchResult(job: JobRef, result: Result): Promise<Result> {
  const res = await fetch(`${API}/jobs/${job.job_id}/result`, { method: 'PATCH', headers: headers(job, true), body: JSON.stringify({ result }) })
  return res.ok ? res.json() : fail(res)
}
export async function exportResult(job: JobRef, format: 'xlsx' | 'csv' | 'zip', part?: 'details' | 'line_items' | 'flat'): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(`${API}/jobs/${job.job_id}/export`, { method: 'POST', headers: headers(job, true), body: JSON.stringify({ format, part: part ?? null }) })
  if (!res.ok) return fail(res)
  const m = /filename="([^"]+)"/.exec(res.headers.get('Content-Disposition') ?? '')
  return { blob: await res.blob(), filename: m?.[1] ?? `hisaab-export.${format}` }
}
export async function deleteJob(job: JobRef): Promise<void> {
  const res = await fetch(`${API}/jobs/${job.job_id}`, { method: 'DELETE', headers: headers(job) })
  if (!res.ok && res.status !== 404) await fail(res)
}
export async function fetchFileBlob(job: JobRef, index: number): Promise<Blob> {
  const res = await fetch(`${API}/jobs/${job.job_id}/files/${index}`, { headers: headers(job) })
  return res.ok ? res.blob() : fail(res)
}
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
