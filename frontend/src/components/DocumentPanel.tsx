import { useRef } from 'react'
import type { ChangeEvent } from 'react'
import type { DocumentSummary } from '../api/types'

interface DocumentPanelProps {
  documents: DocumentSummary[]
  uploading: boolean
  onUpload: (file: File) => void
}

/** @spec UI-DOC-001 */
export function DocumentPanel({ documents, uploading, onUpload }: DocumentPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (file) onUpload(file)
    event.target.value = ''
  }

  return (
    <aside className="document-panel">
      <div className="document-panel__header">
        <h2>Documents</h2>
        <button
          type="button"
          className="document-panel__upload-button"
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          aria-label="Upload document"
        >
          {uploading ? '…' : '+'}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
          onChange={handleFileChange}
          hidden
          data-testid="document-upload-input"
        />
      </div>
      <ul className="document-panel__list">
        {documents.length === 0 && <li className="document-panel__empty">No documents yet</li>}
        {documents.map((doc) => (
          <li key={doc.document_id} className="document-panel__item">
            <span className="document-panel__filename">{doc.filename}</span>
            <span className={`document-panel__status document-panel__status--${doc.status}`}>
              {doc.status}
            </span>
          </li>
        ))}
      </ul>
    </aside>
  )
}
