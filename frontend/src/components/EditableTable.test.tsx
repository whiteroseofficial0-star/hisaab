import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import EditableTable from './EditableTable'
import type { Col, Row } from '../types'

const cols: Col[] = [{ key: 'description', label: 'Description', type: 'text' }, { key: 'debit', label: 'Debit', type: 'number' }]
function Harness({ onRows }: { onRows?: (r: Row[]) => void }) {
  const [rows, setRows] = useState<Row[]>([
    { id: 'a', description: 'Coffee', debit: 10, flags: ['balance_mismatch'] },
    { id: 'b', description: 'Rent', debit: 500 },
  ])
  return <EditableTable label="Transactions" columns={cols} rows={rows} flagMessages={{ balance_mismatch: 'Balance off' }}
    newRow={() => ({ id: 'n' + rows.length, description: '', debit: null })} onChange={(r) => { setRows(r); onRows?.(r) }} />
}

describe('EditableTable', () => {
  it('shows rows and a text flag (not colour alone)', () => {
    render(<Harness />)
    expect(screen.getByLabelText('Description, row 1')).toHaveValue('Coffee')
    expect(screen.getByText(/Check \(1\)/)).toBeInTheDocument()
  })
  it('edits a cell and keeps numbers numeric', async () => {
    let last: Row[] = []
    render(<Harness onRows={(r) => (last = r)} />)
    const cell = screen.getByLabelText('Debit, row 2')
    await userEvent.clear(cell); await userEvent.type(cell, '1,250.50')
    expect(last.find((r) => r.id === 'b')?.debit).toBe(1250.5)
  })
  it('rejects non-numeric input without committing it', async () => {
    let last: Row[] = []
    render(<Harness onRows={(r) => (last = r)} />)
    const cell = screen.getByLabelText('Debit, row 1')
    await userEvent.clear(cell); await userEvent.type(cell, 'abc')
    expect(cell).toHaveAttribute('aria-invalid', 'true')
    expect(last.find((r) => r.id === 'a')?.debit).not.toBe('abc')
  })
  it('adds and deletes rows, and filters by search', async () => {
    render(<Harness />)
    await userEvent.click(screen.getByRole('button', { name: /add row/i }))
    expect(screen.getByText('3 of 3 rows')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Delete row 2' }))
    expect(screen.getByText('2 of 2 rows')).toBeInTheDocument()
    await userEvent.type(screen.getByRole('textbox', { name: /search/i }), 'coff')
    expect(screen.getByText('1 of 2 rows')).toBeInTheDocument()
  })
})
