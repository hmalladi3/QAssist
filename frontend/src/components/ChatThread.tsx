import type { Turn } from '../api/types'
import { AnswerBubble } from './AnswerBubble'

interface ChatThreadProps {
  turns: Turn[]
}

export function ChatThread({ turns }: ChatThreadProps) {
  if (turns.length === 0) {
    return <p className="chat-thread__empty">Ask a question to get started.</p>
  }

  return (
    <div className="chat-thread">
      {turns.map((turn) => (
        <AnswerBubble key={turn.id} turn={turn} />
      ))}
    </div>
  )
}
