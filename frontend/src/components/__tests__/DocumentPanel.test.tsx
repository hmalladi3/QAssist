import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { DocumentPanel } from '../DocumentPanel'
import type { DocumentSummary } from '../../api/types'

const DOCS: DocumentSummary[] = [
  { document_id: 'd1', filename: 'policy.pdf', page_count: 4, status: 'ready', uploaded_at: 'now' },
  { document_id: 'd2', filename: 'notes.txt', page_count: null, status: 'processing', uploaded_at: 'now' },
]

describe('DocumentPanel', () => {
  it('shows an empty state when there are no documents', () => {
    render(<DocumentPanel documents={[]} uploading={false} onUpload={vi.fn()} />)
    expect(screen.getByText(/no documents yet/i)).toBeInTheDocument()
  })

  it('lists each document with its filename and status', () => {
    render(<DocumentPanel documents={DOCS} uploading={false} onUpload={vi.fn()} />)

    expect(screen.getByText('policy.pdf')).toBeInTheDocument()
    expect(screen.getByText('ready')).toBeInTheDocument()
    expect(screen.getByText('notes.txt')).toBeInTheDocument()
    expect(screen.getByText('processing')).toBeInTheDocument()
  })

  it('calls onUpload with the chosen file', async () => {
    const onUpload = vi.fn()
    render(<DocumentPanel documents={[]} uploading={false} onUpload={onUpload} />)

    const file = new File(['content'], 'report.pdf', { type: 'application/pdf' })
    const input = screen.getByTestId('document-upload-input') as HTMLInputElement

    await userEvent.upload(input, file)

    expect(onUpload).toHaveBeenCalledWith(file)
  })

  it('disables the upload button while uploading', () => {
    render(<DocumentPanel documents={[]} uploading={true} onUpload={vi.fn()} />)
    expect(screen.getByRole('button', { name: /upload document/i })).toBeDisabled()
  })
})
