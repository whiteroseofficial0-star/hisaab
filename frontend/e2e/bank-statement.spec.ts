import { expect, test } from '@playwright/test'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// Needs: python scripts/make_samples.py (writes FICTIONAL samples to ../samples) and Tesseract only for scanned samples.
// (the package is ESM, so __dirname is not available)
const here = path.dirname(fileURLToPath(import.meta.url))
const sample = (f: string) => path.resolve(here, '../../samples', f)

test('bank statement: upload, edit, export Excel contains the edit', async ({ page }) => {
  await page.goto('/tools/bank-statement-to-excel/')
  await page.setInputFiles('input[type=file]', sample('bank-statement.pdf'))
  await expect(page.getByRole('table', { name: 'Transactions' })).toBeVisible({ timeout: 90_000 })
  await expect(page.getByLabel('Description, row 1')).toHaveValue(/FICTIONAL/)
  await page.getByLabel('Description, row 1').fill('EDITED IN E2E')
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: /Download Excel/ }).click()])
  const file = await download.path()
  const bytes = readFileSync(file!)
  expect(bytes.subarray(0, 2).toString()).toBe('PK') // xlsx is a zip
  // shared strings live in the zip; cheap check that the edited text is present once unzipped
  const { execFileSync } = await import('node:child_process')
  const xml = execFileSync('python', ['-c', `import zipfile,sys;print(zipfile.ZipFile(sys.argv[1]).read("xl/worksheets/sheet1.xml").decode()+zipfile.ZipFile(sys.argv[1]).read("xl/sharedStrings.xml").decode() if "xl/sharedStrings.xml" in zipfile.ZipFile(sys.argv[1]).namelist() else zipfile.ZipFile(sys.argv[1]).read("xl/worksheets/sheet1.xml").decode())`, file!]).toString()
  expect(xml).toContain('EDITED IN E2E')
})

test('receipt: upload a receipt image and see the total', async ({ page }) => {
  await page.goto('/tools/receipt-to-excel/')
  await page.setInputFiles('input[type=file]', sample('receipt.png'))
  await expect(page.getByRole('table', { name: 'Receipts' })).toBeVisible({ timeout: 90_000 })
  await expect(page.getByLabel('Total, row 1', { exact: true })).toHaveValue('210')
})
