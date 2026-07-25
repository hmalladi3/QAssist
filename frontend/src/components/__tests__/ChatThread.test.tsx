import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ChatThread } from '../ChatThread'
import type { Turn } from '../../api/types'

describe('ChatThread', () => {
  it('shows a prompt to ask a question when the thread is empty', () => {
    render(<ChatThread turns={[]} />)
    expect(screen.getByText(/ask a question to get started/i)).toBeInTheDocument()
  })

  it('renders one bubble per turn', () => {
    const turns: Turn[] = [
      { id: '1', question: 'first question', pending: false, answer: 'first answer' },
      { id: '2', question: 'second question', pending: false, answer: 'second answer' },
    ]
    render(<ChatThread turns={turns} />)

    expect(screen.getByText(/first question/)).toBeInTheDocument()
    expect(screen.getByText(/second question/)).toBeInTheDocument()
  })
})
