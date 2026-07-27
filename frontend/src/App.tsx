import { useCallback, useEffect, useState } from 'react'
import './App.css'
import { askQuestion, listDocuments, uploadDocument } from './api/client'
import type { DocumentSummary, Turn } from './api/types'
import { AskInput } from './components/AskInput'
import { ChatThread } from './components/ChatThread'
import { DocumentPanel } from './components/DocumentPanel'
import { ExampleQuestions } from './components/ExampleQuestions'

const EXAMPLE_QUESTIONS = [
  "What's the refund policy if I cancel my subscription?",
  'What documents do you have, and what notice do I need to give to terminate the vendor agreement?',
  'If I cancel my contract, when do I get refunded and when is my data deleted?',
]

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback
}

/** @spec UI-DOC-001, UI-DOC-002, UI-ASK-001, UI-ANS-001, UI-TRACE-001, UI-ERR-001, UI-EXAMPLES-001 */
function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([])
  const [uploading, setUploading] = useState(false)
  const [turns, setTurns] = useState<Turn[]>([])
  const [asking, setAsking] = useState(false)
  const [banner, setBanner] = useState<string | null>(null)

  const refreshDocuments = useCallback(async () => {
    try {
      setDocuments(await listDocuments())
    } catch (err) {
      setBanner(errorMessage(err, 'Failed to load documents'))
    }
  }, [])

  useEffect(() => {
    void refreshDocuments()
  }, [refreshDocuments])

  async function handleUpload(files: File[]) {
    setUploading(true)
    setBanner(null)
    const failures: string[] = []
    for (const file of files) {
      try {
        await uploadDocument(file)
      } catch (err) {
        failures.push(`${file.name}: ${errorMessage(err, 'upload failed')}`)
      }
    }
    await refreshDocuments()
    if (failures.length > 0) {
      setBanner(failures.join('; '))
    }
    setUploading(false)
  }

  async function handleAsk(question: string) {
    const id = crypto.randomUUID()
    setTurns((prev) => [...prev, { id, question, pending: true }])
    setAsking(true)
    try {
      const result = await askQuestion(question)
      setTurns((prev) =>
        prev.map((turn) =>
          turn.id === id
            ? {
                ...turn,
                pending: false,
                answer: result.answer,
                citations: result.citations,
                trace: result.trace,
              }
            : turn,
        ),
      )
    } catch (err) {
      const message = errorMessage(err, 'Something went wrong asking that question')
      setTurns((prev) =>
        prev.map((turn) => (turn.id === id ? { ...turn, pending: false, error: message } : turn)),
      )
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <h1>QAssist</h1>
        <p className="app__tagline">Ask questions, get answers grounded in your documents.</p>
      </header>
      <div className="app__body">
        <DocumentPanel documents={documents} uploading={uploading} onUpload={handleUpload} />
        <main className="app__main">
          <ChatThread turns={turns} />
          {turns.length === 0 && (
            <ExampleQuestions questions={EXAMPLE_QUESTIONS} disabled={asking} onSelect={handleAsk} />
          )}
          <AskInput disabled={asking} onAsk={handleAsk} />
          {banner && (
            <div className="app__banner" role="alert">
              {banner}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
