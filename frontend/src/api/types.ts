export type DocumentStatus = 'processing' | 'ready' | 'failed'

export interface DocumentSummary {
  document_id: string
  filename: string
  page_count: number | null
  status: DocumentStatus
  uploaded_at: string
}

export interface Citation {
  marker_index: number
  chunk_id: string
  filename: string
  page_number: number | null
  excerpt: string
}

export interface ToolCall {
  tool_name: string
  input: Record<string, unknown>
  result_summary: string
}

export interface AskResponse {
  answer: string
  citations: Citation[]
  trace: ToolCall[]
}

/** One question/answer exchange in the chat thread — client-side only. */
export interface Turn {
  id: string
  question: string
  pending: boolean
  answer?: string
  citations?: Citation[]
  trace?: ToolCall[]
  error?: string
}
