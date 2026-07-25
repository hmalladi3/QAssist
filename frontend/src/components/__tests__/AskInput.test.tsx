import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { AskInput } from '../AskInput'

describe('AskInput', () => {
  it('calls onAsk with the trimmed question and clears the input', async () => {
    const onAsk = vi.fn()
    render(<AskInput disabled={false} onAsk={onAsk} />)

    const input = screen.getByLabelText(/question/i)
    await userEvent.type(input, '  what is the notice period?  ')
    await userEvent.click(screen.getByRole('button', { name: /ask/i }))

    expect(onAsk).toHaveBeenCalledWith('what is the notice period?')
    expect(input).toHaveValue('')
  })

  it('does not call onAsk for a whitespace-only question', async () => {
    const onAsk = vi.fn()
    render(<AskInput disabled={false} onAsk={onAsk} />)

    await userEvent.type(screen.getByLabelText(/question/i), '   ')
    await userEvent.click(screen.getByRole('button', { name: /ask/i }))

    expect(onAsk).not.toHaveBeenCalled()
  })

  it('disables the input and button while a question is in flight', () => {
    render(<AskInput disabled={true} onAsk={vi.fn()} />)

    expect(screen.getByLabelText(/question/i)).toBeDisabled()
    expect(screen.getByRole('button', { name: /asking/i })).toBeDisabled()
  })
})
