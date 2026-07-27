interface ExampleQuestionsProps {
  questions: string[]
  disabled: boolean
  onSelect: (question: string) => void
}

/** @spec UI-EXAMPLES-001 */
export function ExampleQuestions({ questions, disabled, onSelect }: ExampleQuestionsProps) {
  if (questions.length === 0) return null

  return (
    <div className="example-questions">
      <div className="example-questions__label">Try asking</div>
      <div className="example-questions__list">
        {questions.map((question) => (
          <button
            key={question}
            type="button"
            className="example-questions__chip"
            disabled={disabled}
            onClick={() => onSelect(question)}
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
