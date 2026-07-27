import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ExampleQuestions } from '../ExampleQuestions'

describe('ExampleQuestions', () => {
  it('renders nothing when there are no questions', () => {
    const { container } = render(
      <ExampleQuestions questions={[]} disabled={false} onSelect={vi.fn()} />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('renders a clickable chip per question and calls onSelect with its text', async () => {
    const onSelect = vi.fn()
    render(
      <ExampleQuestions
        questions={['What is the refund policy?', 'What documents do you have?']}
        disabled={false}
        onSelect={onSelect}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: 'What is the refund policy?' }))

    expect(onSelect).toHaveBeenCalledWith('What is the refund policy?')
    expect(screen.getByRole('button', { name: 'What documents do you have?' })).toBeInTheDocument()
  })

  it('disables all chips while a question is in flight', () => {
    render(
      <ExampleQuestions questions={['question one']} disabled={true} onSelect={vi.fn()} />,
    )
    expect(screen.getByRole('button', { name: 'question one' })).toBeDisabled()
  })
})
