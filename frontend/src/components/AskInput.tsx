import { useState } from 'react'
import type { FormEvent } from 'react'

interface AskInputProps {
  disabled: boolean
  onAsk: (question: string) => void
}

/** @spec UI-ASK-001 */
export function AskInput({ disabled, onAsk }: AskInputProps) {
  const [value, setValue] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onAsk(trimmed)
    setValue('')
  }

  return (
    <form className="ask-input" onSubmit={handleSubmit}>
      <input
        type="text"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Ask a question about your documents…"
        disabled={disabled}
        aria-label="Question"
      />
      <button type="submit" disabled={disabled || !value.trim()}>
        {disabled ? 'Asking…' : 'Ask'}
      </button>
    </form>
  )
}
