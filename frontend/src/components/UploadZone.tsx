import { useRef, useState } from 'react'
import { Upload } from 'lucide-react'
import type { FileKind } from '../types'

const MIME: Record<FileKind, string[]> = { pdf: ['application/pdf'], jpeg: ['image/jpeg'], png: ['image/png'], webp: ['image/webp'] }
const EXT: Record<FileKind, string[]> = { pdf: ['.pdf'], jpeg: ['.jpg', '.jpeg'], png: ['.png'], webp: ['.webp'] }
const LABEL: Record<FileKind, string> = { pdf: 'PDF', jpeg: 'JPG', png: 'PNG', webp: 'WebP' }

export interface UploadRules { accept: FileKind[]; multiple: boolean; maxMb: number; maxFiles: number }

/** Quick browser-side checks for friendly errors. The server re-validates the real file signature. */
export function validateFiles(files: File[], rules: UploadRules): string | null {
  if (files.length === 0) return 'Choose a file to upload.'
  if (files.length > rules.maxFiles) return `Please choose at most ${rules.maxFiles} file${rules.maxFiles > 1 ? 's' : ''}.`
  for (const f of files) {
    const name = f.name.toLowerCase()
    const okType = rules.accept.some((k) => MIME[k].includes(f.type) || EXT[k].some((e) => name.endsWith(e)))
    if (!okType) return `"${f.name}" is not supported here. Accepted: ${rules.accept.map((k) => LABEL[k]).join(', ')}.`
    if (f.size === 0) return `"${f.name}" is empty.`
    if (f.size > rules.maxMb * 1024 * 1024) return `"${f.name}" is larger than ${rules.maxMb} MB.`
  }
  return null
}

export default function UploadZone({ rules, onFiles, disabled }: { rules: UploadRules; onFiles: (files: File[]) => void; disabled?: boolean }) {
  const input = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const formats = rules.accept.map((k) => LABEL[k]).join(', ')

  const handle = (list: FileList | null) => {
    const files = Array.from(list ?? [])
    const err = validateFiles(files, rules)
    setError(err)
    if (!err) onFiles(files)
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setOver(true) }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); if (!disabled) handle(e.dataTransfer.files) }}
        className={`flex flex-col items-center border border-dashed px-6 py-10 text-center transition-colors ${
          over ? 'border-pine-600 bg-pine-50' : 'border-slate-300 bg-paper/40'
        } ${disabled ? 'opacity-60' : ''}`}
      >
        <span className="grid h-11 w-11 place-items-center rounded-full border border-line bg-surface">
          <Upload className="h-[18px] w-[18px] text-pine-700" aria-hidden />
        </span>
        <p className="mt-5 text-[15px] font-medium text-ink">
          Drag and drop {rules.multiple ? 'your files' : 'a file'} here
        </p>
        <p className="mt-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-ink-muted">
          {formats} · up to {rules.maxMb} MB{rules.multiple ? ` each · ${rules.maxFiles} files max` : ''}
        </p>
        <input
          ref={input} id="hisaab-file-input" type="file" className="sr-only" disabled={disabled} multiple={rules.multiple}
          accept={rules.accept.flatMap((k) => [...MIME[k], ...EXT[k]]).join(',')}
          onChange={(e) => { handle(e.target.files); e.target.value = '' }}
        />
        <label
          htmlFor="hisaab-file-input"
          className={`btn btn-primary mt-6 cursor-pointer ${disabled ? 'pointer-events-none opacity-50' : ''}`}
        >
          {rules.multiple ? 'Choose files' : 'Choose a file'}
        </label>
      </div>
      {error && (
        <p role="alert" className="mt-3 border-l-2 border-red-700 bg-red-50 px-3 py-2 text-sm text-red-900 dark:bg-red-950/35 dark:text-red-100">
          {error}
        </p>
      )}
    </div>
  )
}
