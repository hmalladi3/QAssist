import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, askQuestion, listDocuments, uploadDocument } from './client'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('listDocuments', () => {
  it('returns the parsed document list on success', async () => {
    const docs = [{ document_id: 'd1', filename: 'a.pdf', page_count: 1, status: 'ready', uploaded_at: 'now' }]
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(docs)))

    await expect(listDocuments()).resolves.toEqual(docs)
  })
})

describe('uploadDocument', () => {
  it('posts a multipart form with the file', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ document_id: 'd1', filename: 'a.txt', page_count: null, status: 'ready', uploaded_at: 'now' }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const file = new File(['hello'], 'a.txt', { type: 'text/plain' })
    const result = await uploadDocument(file)

    expect(result.document_id).toBe('d1')
    const [, options] = fetchMock.mock.calls[0]
    expect(options.method).toBe('POST')
    expect(options.body).toBeInstanceOf(FormData)
  })
})

describe('askQuestion', () => {
  it('returns answer, citations, and trace on success', async () => {
    const payload = { answer: 'The answer [1].', citations: [], trace: [] }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(payload)))

    await expect(askQuestion('what?')).resolves.toEqual(payload)
  })

  it('throws an ApiError with the server detail message on failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse({ detail: 'question must not be empty' }, 422)),
    )

    await expect(askQuestion('')).rejects.toMatchObject(
      new ApiError('question must not be empty', 422),
    )
  })

  it('falls back to statusText when the error body is not JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('not json', { status: 502, statusText: 'Bad Gateway' })),
    )

    await expect(askQuestion('anything')).rejects.toMatchObject({ status: 502, message: 'Bad Gateway' })
  })
})
