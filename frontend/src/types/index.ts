export type ToolKey = 'bank_statement' | 'invoice' | 'receipt' | 'tables'
export type FileKind = 'pdf' | 'jpeg' | 'png' | 'webp'

export interface JobCreated { job_id: string; token: string; status: string; expires_at: number }
export interface JobStatus {
  job_id: string
  tool: ToolKey
  status: 'queued' | 'processing' | 'done' | 'failed' | 'cancelled'
  progress: { stage: string; pages_done: number; pages_total: number | null }
  error: { code: string; message: string } | null
  expires_at: number
  files: { index: number; name: string; kind: FileKind }[]
}
export interface JobRef { job_id: string; token: string }

// Results are tool specific JSON documents produced by the backend.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Result = Record<string, any>
export interface Row { id: string; flags?: string[]; [key: string]: unknown }
export type ColType = 'text' | 'number' | 'date'
export interface Col { key: string; label: string; type: ColType; readOnly?: boolean; width?: string }
