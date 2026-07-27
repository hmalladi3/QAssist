import type { Turn } from '../api/types'

interface AnswerBubbleProps {
  turn: Turn
}

const CITATION_MARKER_SPLIT_RE = /(\[\d+\])/g
const CITATION_MARKER_WHOLE_RE = /^\[\d+\]$/

/** Splits answer text on [n] footnote markers so they can be styled distinctly. */
function renderAnswerText(text: string) {
  return text.split(CITATION_MARKER_SPLIT_RE).map((part, index) =>
    CITATION_MARKER_WHOLE_RE.test(part) ? (
      <sup key={index} className="turn__citation-marker">
        {part}
      </sup>
    ) : (
      <span key={index}>{part}</span>
    ),
  )
}

/** @spec UI-ANS-001, UI-TRACE-001, UI-ERR-001 */
export function AnswerBubble({ turn }: AnswerBubbleProps) {
  return (
    <div className="turn">
      <div className="turn__question">
        <span className="turn__speaker">You</span> {turn.question}
      </div>

      {turn.pending && <div className="turn__pending">QAssist is thinking…</div>}

      {turn.error && (
        <div className="turn__error" role="alert">
          {turn.error}
        </div>
      )}

      {turn.answer !== undefined && (
        <div className="turn__answer">
          <div className="turn__answer-text">
            <span className="turn__speaker">QAssist</span> {renderAnswerText(turn.answer ?? '')}
          </div>

          {turn.trace && turn.trace.length > 0 && (
            <details className="turn__trace" open>
              <summary>
                Tool trace ({turn.trace.length} call{turn.trace.length === 1 ? '' : 's'})
              </summary>
              <ol>
                {turn.trace.map((call, index) => (
                  <li key={index}>
                    <code>{call.tool_name}</code>({JSON.stringify(call.input)}) — {call.result_summary}
                  </li>
                ))}
              </ol>
            </details>
          )}

          {turn.citations && turn.citations.length > 0 && (
            <div className="turn__sources">
              <div className="turn__sources-title">Sources</div>
              <ol>
                {turn.citations.map((citation) => (
                  <li key={citation.chunk_id}>
                    [{citation.marker_index}] {citation.filename}
                    {citation.page_number != null ? `, p.${citation.page_number}` : ''}: &ldquo;
                    {citation.excerpt}&rdquo;
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
