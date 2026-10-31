import { validateFiles } from './UploadZone'

const rules = { accept: ['pdf' as const], multiple: false, maxMb: 1, maxFiles: 1 }
const file = (name: string, type: string, size = 100) => new File([new Uint8Array(size)], name, { type })

describe('validateFiles', () => {
  it('accepts a pdf', () => expect(validateFiles([file('a.pdf', 'application/pdf')], rules)).toBeNull())
  it('rejects other types with an actionable message', () => expect(validateFiles([file('a.exe', 'application/x-msdownload')], rules)).toMatch(/Accepted: PDF/))
  it('rejects oversized and empty files', () => {
    expect(validateFiles([file('a.pdf', 'application/pdf', 2 * 1024 * 1024)], rules)).toMatch(/larger than 1 MB/)
    expect(validateFiles([file('a.pdf', 'application/pdf', 0)], rules)).toMatch(/empty/)
  })
  it('limits file count', () => expect(validateFiles([file('a.pdf', 'application/pdf'), file('b.pdf', 'application/pdf')], rules)).toMatch(/at most 1/))
})
