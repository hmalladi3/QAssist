import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AnswerBubble } from '../AnswerBubble'
import type { Turn } from '../../api/types'

const BASE_TURN: Turn = {
  id: '1',
  question: 'What is the notice period?',
  pending: false,
}

describe('AnswerBubble', () => {
  it('shows a pending indicator while a question is in flight', () => {
    render(<AnswerBubble turn={{ ...BASE_TURN, pending: true }} />)
    expect(screen.getByText(/thinking/i)).toBeInTheDocument()
  })

  it('renders an error message when the question failed', () => {
    render(<AnswerBubble turn={{ ...BASE_TURN, error: 'upstream service unavailable' }} />)
    expect(screen.getByRole('alert')).toHaveTextContent('upstream service unavailable')
  })

  it('renders the answer text with numbered citation footnotes and a sources list', () => {
    const turn: Turn = {
      ...BASE_TURN,
      answer: 'The notice period is 30 days [1].',
      citations: [
        { marker_index: 1, chunk_id: 'c1', filename: 'policy.pdf', page_number: 4, excerpt: '30 days notice' },
      ],
    }
    render(<AnswerBubble turn={turn} />)

    expect(screen.getByText(/notice period is 30 days/i)).toBeInTheDocument()
    expect(screen.getByText(/Sources/)).toBeInTheDocument()
    expect(screen.getByText(/policy\.pdf, p\.4/)).toBeInTheDocument()
  })

  it('renders the tool-use trace as a collapsible section in order', () => {
    const turn: Turn = {
      ...BASE_TURN,
      answer: 'Answer text',
      trace: [
        { tool_name: 'search_documents', input: { query: 'notice period' }, result_summary: 'found 1 chunk' },
        { tool_name: 'search_documents', input: { query: 'refined' }, result_summary: 'found 2 chunks' },
      ],
    }
    render(<AnswerBubble turn={turn} />)

    expect(screen.getByText(/Tool trace \(2 calls\)/)).toBeInTheDocument()
    const items = screen.getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('found 1 chunk')
    expect(items[1]).toHaveTextContent('found 2 chunks')
  })

  it('renders no trace or sources sections when the answer has neither', () => {
    render(<AnswerBubble turn={{ ...BASE_TURN, answer: 'Simple answer, no citations needed.' }} />)
    expect(screen.queryByText(/Tool trace/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Sources/)).not.toBeInTheDocument()
  })
})
